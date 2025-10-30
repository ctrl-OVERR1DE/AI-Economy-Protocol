"""
Gateway Escrow Client

Extends the base EscrowClient with Sanctum Gateway integration for optimized
transaction delivery. This client handles escrow operations (initialize, release)
with automatic Gateway optimization and RPC fallback.

Key Features:
- buildGatewayTransaction: Optimizes compute units, priority fees, fresh blockhash
- sendTransaction: Dual-path routing (RPC + Jito bundles)
- Automatic Jito refunds when RPC lands first
- Graceful fallback to RPC when Gateway unavailable
- Real-time transaction monitoring and logging

Usage:
    client = GatewayEscrowClient(wallet_keypair=keypair)
    signature, used_gateway = await client.initialize_escrow_via_gateway(...)
    
Returns:
    Tuple of (transaction_signature, used_gateway_bool)
    - used_gateway=True: Transaction sent via Gateway
    - used_gateway=False: Transaction sent via RPC fallback
"""

import os
import struct
import base64
from typing import Optional

from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.hash import Hash
from spl.token.constants import TOKEN_PROGRAM_ID

from .escrow_client import EscrowClient
from .gateway_client import GatewayClient


class GatewayEscrowClient(EscrowClient):
    """
    Escrow client with Sanctum Gateway integration.
    
    Provides optimized transaction delivery for escrow operations using
    Sanctum Gateway's dual-path routing and automatic Jito refunds.
    """

    def __init__(
        self,
        rpc_url: str = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com"),
        wallet_keypair=None,
        gateway_api_key: Optional[str] = None,
    ):
        super().__init__(rpc_url=rpc_url, wallet_keypair=wallet_keypair)
        self.gateway = GatewayClient(gateway_api_key)

    async def initialize_escrow_via_gateway(
        self,
        provider_pubkey: Pubkey,
        amount: int,
        service_id: str,
        task_data: str,
        client_token_account: Pubkey,
        escrow_token_account: Pubkey,
    ) -> tuple[str, bool]:
        """
        Build initialize_escrow instruction manually, send through Gateway, return signature.
        
        Returns:
            Tuple of (signature, used_gateway) where used_gateway is True if Gateway succeeded
        """
        task_hash = self.hash_task(task_data)

        # Check if escrow already exists using task_hash (matches on-chain seeds)
        exists, escrow_pda = await self.check_escrow_exists(
            self.wallet.public_key,
            provider_pubkey,
            service_id=None,
            task_hash=task_hash,
        )
        
        if exists:
            # Reusing existing escrow
            # Return a placeholder signature since no transaction was sent
            return ("ESCROW_ALREADY_EXISTS", False)
        
        # Derive escrow PDA using task_hash to match on-chain seeds
        escrow_pda, bump = self.derive_escrow_pda(
            self.wallet.public_key, 
            provider_pubkey,
            service_id=None,
            task_hash=task_hash,
        )

        # Build instruction data: discriminator (8 bytes) + amount (u64) + service_id (string) + task_hash ([u8;32])
        # Anchor discriminator for initialize_escrow: first 8 bytes of sha256("global:initialize_escrow")
        discriminator = bytes([243, 160, 77, 153, 11, 92, 48, 209])
        
        # Encode amount as little-endian u64
        amount_bytes = struct.pack("<Q", amount)
        
        # Encode service_id as Rust String (length prefix + utf8 bytes)
        service_id_bytes = service_id.encode("utf-8")
        service_id_len = struct.pack("<I", len(service_id_bytes))
        
        # task_hash is 32 bytes
        data = discriminator + amount_bytes + service_id_len + service_id_bytes + task_hash

        # Build accounts list per IDL order
        accounts = [
            AccountMeta(pubkey=escrow_pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=self.wallet.public_key, is_signer=True, is_writable=True),
            AccountMeta(pubkey=provider_pubkey, is_signer=False, is_writable=False),
            AccountMeta(pubkey=client_token_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=escrow_token_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        ]

        ix = Instruction(program_id=self.PROGRAM_ID, accounts=accounts, data=data)

        # Build unsigned transaction with placeholder blockhash so Gateway sets a fresh one
        placeholder = Hash.from_string("11111111111111111111111111111111")
        msg = MessageV0.try_compile(
            payer=self.wallet.public_key,
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=placeholder,
        )
        tx_initial = VersionedTransaction(msg, [self.wallet_keypair])

        # Try Gateway Builder + Send flow
        cluster = os.getenv("GATEWAY_CLUSTER", "devnet")
        try:
            build_options = {}
            build_resp = await self.gateway.build_gateway_transaction(
                bytes(tx_initial), cluster=cluster, options=build_options
            )
            # Gateway build successful (verbose response suppressed for demo)
            result = build_resp.get("result") if isinstance(build_resp, dict) else None
            if not isinstance(result, dict) or "transaction" not in result:
                raise RuntimeError(f"Unexpected buildGatewayTransaction response: {build_resp}")

            built_b64 = result["transaction"]
            built_bytes = base64.b64decode(built_b64)

            # Decode returned transaction and sign it with our wallet
            built_tx = VersionedTransaction.from_bytes(built_bytes)
            tx_to_send = VersionedTransaction(built_tx.message, [self.wallet_keypair])

            # Send via Gateway
            send_resp = await self.gateway.send_transaction(bytes(tx_to_send), cluster=cluster)
            send_res = send_resp.get("result") if isinstance(send_resp, dict) else None
            if isinstance(send_res, str):
                print(f"✅ Gateway: Escrow initialized")
                return (send_res, True)  # Gateway success
            if isinstance(send_res, dict):
                sig = send_res.get("signature") or (send_res.get("signatures") or [None])[0]
                if sig:
                    print(f"✅ Gateway: Escrow initialized")
                    return (str(sig), True)  # Gateway success
            raise RuntimeError(f"Unexpected sendTransaction response: {send_resp}")
        except Exception as e:
            print(f"[Gateway] Gateway failed: {e}")
            print(f"[Gateway] Falling back to RPC...")

        # Fallback: rebuild with fresh blockhash and send to RPC (skip_preflight to avoid blockhash expiry)
        from solana.rpc.types import TxOpts
        recent2 = await self.client.get_latest_blockhash()
        msg2 = MessageV0.try_compile(
            payer=self.wallet.public_key,
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=recent2.value.blockhash,
        )
        tx2 = VersionedTransaction(msg2, [self.wallet_keypair])
        resp = await self.client.send_raw_transaction(bytes(tx2), opts=TxOpts(skip_preflight=True, max_retries=3))
        print(f"✅ RPC: Escrow initialized")
        return (str(resp.value), False)  # RPC fallback used

    async def release_payment_via_gateway(
        self,
        escrow_pda: Pubkey,
        provider_pubkey: Pubkey,
        provider_token_account: Pubkey,
        escrow_token_account: Pubkey,
    ) -> tuple[str, bool]:
        """
        Release payment to provider via Gateway/RPC.
        
        Returns:
            Tuple of (signature, used_gateway)
        """
        # Build instruction data: discriminator (8 bytes) for release_payment
        # Anchor discriminator for release_payment: first 8 bytes of sha256("global:release_payment")
        # Correct: 1822bf5691a0b7e9 = [0x18, 0x22, 0xbf, 0x56, 0x91, 0xa0, 0xb7, 0xe9]
        discriminator = bytes([0x18, 0x22, 0xbf, 0x56, 0x91, 0xa0, 0xb7, 0xe9])
        data = discriminator
        
        # Build accounts list per IDL order (must match Rust program exactly!)
        # ReleasePayment accounts: escrow, escrow_token_account, provider_token_account, authority, token_program
        accounts = [
            AccountMeta(pubkey=escrow_pda, is_signer=False, is_writable=True),              # 0: escrow
            AccountMeta(pubkey=escrow_token_account, is_signer=False, is_writable=True),    # 1: escrow_token_account
            AccountMeta(pubkey=provider_token_account, is_signer=False, is_writable=True),  # 2: provider_token_account
            AccountMeta(pubkey=self.wallet.public_key, is_signer=True, is_writable=False),  # 3: authority (client)
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),       # 4: token_program
        ]
        
        ix = Instruction(program_id=self.PROGRAM_ID, accounts=accounts, data=data)
        
        # Build unsigned transaction
        placeholder = Hash.from_string("11111111111111111111111111111111")
        msg = MessageV0.try_compile(
            payer=self.wallet.public_key,
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=placeholder,
        )
        tx_initial = VersionedTransaction(msg, [self.wallet_keypair])
        
        # Try Gateway first
        cluster = os.getenv("GATEWAY_CLUSTER", "devnet")
        try:
            build_resp = await self.gateway.build_gateway_transaction(
                bytes(tx_initial), cluster=cluster, options={}
            )
            # Gateway build successful (verbose response suppressed for demo)
            result = build_resp.get("result") if isinstance(build_resp, dict) else None
            if not isinstance(result, dict) or "transaction" not in result:
                raise RuntimeError(f"Unexpected buildGatewayTransaction response: {build_resp}")
            
            built_b64 = result["transaction"]
            built_bytes = base64.b64decode(built_b64)
            built_tx = VersionedTransaction.from_bytes(built_bytes)
            tx_to_send = VersionedTransaction(built_tx.message, [self.wallet_keypair])
            
            send_resp = await self.gateway.send_transaction(bytes(tx_to_send), cluster=cluster)
            send_res = send_resp.get("result") if isinstance(send_resp, dict) else None
            if isinstance(send_res, str):
                print(f"✅ Gateway: Payment released")
                return (send_res, True)
            if isinstance(send_res, dict):
                sig = send_res.get("signature") or (send_res.get("signatures") or [None])[0]
                if sig:
                    print(f"✅ Gateway: Payment released")
                    return (str(sig), True)
            raise RuntimeError(f"Unexpected sendTransaction response: {send_resp}")
        except Exception as e:
            print(f"[Gateway] Gateway failed: {e}")
            print(f"[Gateway] Falling back to RPC...")
        
        # Fallback to RPC
        from solana.rpc.types import TxOpts
        recent = await self.client.get_latest_blockhash()
        msg2 = MessageV0.try_compile(
            payer=self.wallet.public_key,
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=recent.value.blockhash,
        )
        tx2 = VersionedTransaction(msg2, [self.wallet_keypair])
        resp = await self.client.send_raw_transaction(bytes(tx2), opts=TxOpts(skip_preflight=True, max_retries=3))
        print(f"✅ RPC: Payment released")
        return (str(resp.value), False)
    
    async def submit_proof(self, provider_pubkey: Pubkey, proof_data: str) -> str:
        """Submit proof of task completion via Gateway/RPC."""
        import hashlib
        proof_hash = hashlib.sha256(proof_data.encode()).digest()
        
        # Derive escrow PDA to maintain backward compatibility, then delegate to explicit method
        escrow_pda, _ = self.derive_escrow_pda(self.wallet.public_key, provider_pubkey)
        return await self.submit_proof_with_pda(escrow_pda, provider_pubkey, proof_data)

    async def submit_proof_with_pda(self, escrow_pda: Pubkey, provider_pubkey: Pubkey, proof_data: str) -> str:
        """Submit proof using an explicit escrow PDA to avoid derivation drift between agents."""
        import hashlib
        proof_hash = hashlib.sha256(proof_data.encode()).digest()
        
        # Build instruction data: discriminator (8 bytes) + proof_hash ([u8;32])
        # Anchor discriminator for submit_proof: first 8 bytes of sha256("global:submit_proof")
        discriminator = bytes([54, 241, 46, 84, 4, 212, 46, 94])
        data = discriminator + proof_hash
        
        # Build accounts list per IDL order
        accounts = [
            AccountMeta(pubkey=escrow_pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=provider_pubkey, is_signer=True, is_writable=False),
        ]
        
        ix = Instruction(program_id=self.PROGRAM_ID, accounts=accounts, data=data)
        
        # Build and send transaction with fresh blockhash
        from solana.rpc.types import TxOpts
        recent = await self.client.get_latest_blockhash()
        msg = MessageV0.try_compile(
            payer=self.wallet.public_key,
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=recent.value.blockhash,
        )
        tx = VersionedTransaction(msg, [self.wallet_keypair])
        
        resp = await self.client.send_raw_transaction(bytes(tx), opts=TxOpts(skip_preflight=True, max_retries=3))
        return str(resp.value)

    async def release_payment(self, client_pubkey: Pubkey, provider_pubkey: Pubkey) -> str:
        """Release payment to provider after verification via Gateway/RPC."""
        # Derive escrow PDA
        escrow_pda, _ = self.derive_escrow_pda(client_pubkey, provider_pubkey)
        
        # Get token accounts from env
        escrow_ata_str = os.getenv("ESCROW_TOKEN_ACCOUNT")
        if not escrow_ata_str:
            raise ValueError("ESCROW_TOKEN_ACCOUNT not set in environment")
        escrow_token_account = Pubkey.from_string(escrow_ata_str)
        
        # For provider token account, derive or use env
        # In production, this would be the provider's ATA for the mint
        provider_token_account_str = os.getenv("PROVIDER_TOKEN_ACCOUNT")
        if provider_token_account_str:
            provider_token_account = Pubkey.from_string(provider_token_account_str)
        else:
            # Fallback: use client token account for testing (same wallet)
            client_ata_str = os.getenv("CLIENT_TOKEN_ACCOUNT")
            if not client_ata_str:
                raise ValueError("PROVIDER_TOKEN_ACCOUNT or CLIENT_TOKEN_ACCOUNT must be set")
            provider_token_account = Pubkey.from_string(client_ata_str)
        
        # Build instruction data: discriminator only (no args)
        # Anchor discriminator for release_payment: first 8 bytes of sha256("global:release_payment")
        discriminator = bytes([24, 34, 191, 86, 145, 160, 183, 233])
        data = discriminator
        
        # Build accounts list per IDL order
        accounts = [
            AccountMeta(pubkey=escrow_pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=escrow_token_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=provider_token_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=self.wallet.public_key, is_signer=True, is_writable=False),
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        ]
        
        ix = Instruction(program_id=self.PROGRAM_ID, accounts=accounts, data=data)
        
        # Build and send transaction with fresh blockhash
        from solana.rpc.types import TxOpts
        recent = await self.client.get_latest_blockhash()
        msg = MessageV0.try_compile(
            payer=self.wallet.public_key,
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=recent.value.blockhash,
        )
        tx = VersionedTransaction(msg, [self.wallet_keypair])
        
        print(f"[release_payment] Sending transaction with skip_preflight=True...")
        resp = await self.client.send_raw_transaction(bytes(tx), opts=TxOpts(skip_preflight=True, max_retries=3))
        print(f"[release_payment] Transaction signature: {resp.value}")
        return str(resp.value)
