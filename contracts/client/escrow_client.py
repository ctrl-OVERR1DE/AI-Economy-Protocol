"""
Python client for Agent Escrow smart contract.
Handles escrow initialization, proof submission, and payment release.
"""

import os
import hashlib
from typing import Optional, Tuple
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from anchorpy import Provider, Wallet, Program, Idl
import asyncio


class EscrowClient:
    """Client for interacting with the Agent Escrow smart contract."""
    
    PROGRAM_ID = Pubkey.from_string(os.getenv("ESCROW_PROGRAM_ID", "HgzpCVSzmSwveikHVTpt85jVXpcqnJWQNcZzFbnjMEz9"))
    
    def __init__(
        self,
        rpc_url: str = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com"),
        wallet_keypair: Optional[Keypair] = None
    ):
        """
        Initialize escrow client.
        
        Args:
            rpc_url: Solana RPC endpoint
            wallet_keypair: Keypair for signing transactions
        """
        self.rpc_url = rpc_url
        self.client = AsyncClient(rpc_url, commitment=Confirmed)
        self.wallet_keypair = wallet_keypair or self._load_wallet()
        self.wallet = Wallet(self.wallet_keypair)
        self.provider = Provider(self.client, self.wallet)
        
    def _load_wallet(self) -> Keypair:
        """Load wallet from environment or create new one."""
        wallet_path = os.path.expanduser("~/.config/solana/id.json")
        if os.path.exists(wallet_path):
            with open(wallet_path, 'r') as f:
                import json
                secret_key = json.load(f)
                return Keypair.from_bytes(bytes(secret_key))
        else:
            # Create new keypair for testing
            return Keypair()
    
    def derive_escrow_pda(
        self,
        client_pubkey: Pubkey,
        provider_pubkey: Pubkey,
        service_id: Optional[str] = None,
        task_hash: Optional[bytes] = None,
    ) -> Tuple[Pubkey, int]:
        """
        Derive the escrow PDA (Program Derived Address).
        Prefer task_hash if provided (32 bytes), otherwise fall back to legacy seeds.
        
        Args:
            client_pubkey: Client's public key
            provider_pubkey: Provider's public key
            service_id: Optional legacy additive seed (deprecated)
            task_hash: Optional 32-byte hash to derive unique escrow per task
            
        Returns:
            Tuple of (escrow_pubkey, bump)
        """
        seeds = [
            b"escrow",
            bytes(client_pubkey),
            bytes(provider_pubkey),
        ]
        
        # New design: include task_hash exactly as used on-chain
        if task_hash is not None:
            if not isinstance(task_hash, (bytes, bytearray)) or len(task_hash) != 32:
                raise ValueError("task_hash must be 32 bytes")
            seeds.append(bytes(task_hash))
        elif service_id:
            # Legacy fallback to support old deployments (keep <= 16 bytes)
            service_hash = hashlib.sha256(service_id.encode()).digest()[:16]
            seeds.append(service_hash)
        
        return Pubkey.find_program_address(seeds, self.PROGRAM_ID)
    
    async def check_escrow_exists(
        self,
        client_pubkey: Pubkey,
        provider_pubkey: Pubkey,
        service_id: Optional[str] = None,
        task_hash: Optional[bytes] = None,
    ) -> Tuple[bool, Optional[Pubkey]]:
        """
        Check if an escrow account exists and is in a reusable state.
        
        Args:
            client_pubkey: Client's public key
            provider_pubkey: Provider's public key
            service_id: Optional service ID
            task_hash: Optional task hash
            
        Returns:
            Tuple of (can_reuse, escrow_pda)
            - can_reuse is True only if escrow exists AND status is Pending
        """
        escrow_pda, _ = self.derive_escrow_pda(client_pubkey, provider_pubkey, service_id, task_hash)
        
        try:
            # Try to fetch the account
            account_info = await self.client.get_account_info(escrow_pda)
            
            # If account doesn't exist, we can create a new one
            if account_info.value is None or not account_info.value.data:
                print(f"[Escrow] No escrow found at {escrow_pda}")
                return (False, escrow_pda)
            
            # Account exists - check status (byte offset 137 for status enum in Escrow struct)
            # Escrow layout: client(32) + provider(32) + amount(8) + service_id(4+64) + task_hash(32) + proof_hash(33) + status(1) + ...
            # Status offset: 8 (discriminator) + 32 + 32 + 8 + 68 + 32 + 33 = 213
            data = account_info.value.data
            if len(data) < 214:
                print(f"[Escrow] Escrow account data too short, treating as non-reusable")
                return (False, escrow_pda)
            
            status_byte = data[213]
            status_names = {0: "Pending", 1: "ProofSubmitted", 2: "Completed", 3: "Cancelled"}
            status = status_names.get(status_byte, f"Unknown({status_byte})")
            
            print(f"[Escrow] Found existing escrow at {escrow_pda} with status: {status}")
            
            # Only reuse if status is Pending (fresh escrow that was never used)
            if status_byte == 0:  # Pending
                return (True, escrow_pda)
            else:
                print(f"[Escrow] Cannot reuse escrow in {status} state - will create new escrow")
                return (False, escrow_pda)
                
        except Exception as e:
            # Escrow doesn't exist yet (expected for new escrows)
            return (False, escrow_pda)
    
    @staticmethod
    def hash_task(task_data: str) -> bytes:
        """
        Create a hash of task data.
        
        Args:
            task_data: Task description or data
            
        Returns:
            32-byte hash
        """
        return hashlib.sha256(task_data.encode()).digest()
    
    async def initialize_escrow(
        self,
        provider_pubkey: Pubkey,
        amount: int,
        service_id: str,
        task_data: str
    ) -> str:
        """
        Initialize a new escrow for a service request.
        
        Args:
            provider_pubkey: Provider's public key
            amount: Amount in lamports to lock
            service_id: Service identifier
            task_data: Task description/data
            
        Returns:
            Transaction signature
        """
        task_hash = self.hash_task(task_data)
        escrow_pda, bump = self.derive_escrow_pda(
            self.wallet.public_key,
            provider_pubkey
        )
        
        # TODO: Load program IDL and create instruction
        # For now, return placeholder
        print(f"Initializing escrow:")
        print(f"  Client: {self.wallet.public_key}")
        print(f"  Provider: {provider_pubkey}")
        print(f"  Amount: {amount} lamports")
        print(f"  Service: {service_id}")
        print(f"  Escrow PDA: {escrow_pda}")
        
        return "placeholder_signature"
    
    async def submit_proof(
        self,
        provider_pubkey: Pubkey,
        proof_data: str
    ) -> str:
        """
        Submit proof of task completion.
        
        Args:
            provider_pubkey: Provider's public key
            proof_data: Proof of completion
            
        Returns:
            Transaction signature
        """
        proof_hash = hashlib.sha256(proof_data.encode()).digest()
        escrow_pda, _ = self.derive_escrow_pda(
            self.wallet.public_key,
            provider_pubkey
        )
        
        print(f"Submitting proof for escrow: {escrow_pda}")
        return "placeholder_signature"
    
    async def release_payment(
        self,
        client_pubkey: Pubkey,
        provider_pubkey: Pubkey
    ) -> str:
        """
        Release payment to provider after verification.
        
        Args:
            client_pubkey: Client's public key
            provider_pubkey: Provider's public key
            
        Returns:
            Transaction signature
        """
        escrow_pda, _ = self.derive_escrow_pda(client_pubkey, provider_pubkey)
        
        print(f"Releasing payment from escrow: {escrow_pda}")
        return "placeholder_signature"
    
    async def cancel_escrow(
        self,
        provider_pubkey: Pubkey
    ) -> str:
        """
        Cancel escrow and refund client.
        
        Args:
            provider_pubkey: Provider's public key
            
        Returns:
            Transaction signature
        """
        escrow_pda, _ = self.derive_escrow_pda(
            self.wallet.public_key,
            provider_pubkey
        )
        
        print(f"Cancelling escrow: {escrow_pda}")
        return "placeholder_signature"
    
    async def get_escrow_state(
        self,
        client_pubkey: Pubkey,
        provider_pubkey: Pubkey
    ) -> dict:
        """
        Get current state of an escrow.
        
        Args:
            client_pubkey: Client's public key
            provider_pubkey: Provider's public key
            
        Returns:
            Escrow state dictionary
        """
        escrow_pda, _ = self.derive_escrow_pda(client_pubkey, provider_pubkey)
        
        # TODO: Fetch and deserialize account data
        return {
            "escrow_address": str(escrow_pda),
            "status": "pending",
            "amount": 0,
        }
    
    async def close(self):
        """Close the RPC client connection."""
        await self.client.close()


# Example usage
async def main():
    """Example usage of EscrowClient."""
    client = EscrowClient()
    
    # Example provider pubkey (replace with actual)
    provider = Pubkey.from_string("11111111111111111111111111111111")
    
    # Initialize escrow
    sig = await client.initialize_escrow(
        provider_pubkey=provider,
        amount=100_000_000,  # 0.1 SOL
        service_id="data_analysis_001",
        task_data="Analyze sales data for Q4 2024"
    )
    print(f"Escrow initialized: {sig}")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
