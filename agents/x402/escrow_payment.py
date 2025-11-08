"""
x402 Escrow Payment Module

Creates escrow transactions for x402 payment flow.
"""

import os
import sys
import hashlib
import base64
from typing import Tuple, Optional
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from contracts.client.gateway_escrow_client import GatewayEscrowClient


async def create_escrow_transaction(
    client_wallet: Keypair,
    provider_address: str,
    service_id: str,
    task_data: str,
    amount_sol: float,
) -> Tuple[VersionedTransaction, Pubkey, str]:
    """
    Create an escrow initialization transaction (but don't submit it).
    This transaction will be sent in the X-Payment header.
    
    IMPORTANT: Uses EXACT same logic as initialize_escrow_for_service()
    but returns the transaction instead of submitting it.
    
    Args:
        client_wallet: Client's Solana wallet keypair
        provider_address: Provider's Solana address (Pubkey string)
        service_id: Service identifier
        task_data: Task description/data
        amount_sol: Amount to lock in escrow (in SOL)
    
    Returns:
        Tuple of (signed_transaction, escrow_pda, task_hash_hex)
    """
    # Convert SOL to lamports
    amount_lamports = int(amount_sol * 1_000_000_000)
    
    # Initialize escrow client
    escrow_client = GatewayEscrowClient(wallet_keypair=client_wallet)
    
    # Convert provider address to Pubkey
    provider_pubkey = Pubkey.from_string(provider_address)
    
    # Derive escrow PDA using task_hash with nonce for uniqueness
    # IMPORTANT: Each request gets a unique escrow (proper x402 behavior)
    import time
    nonce = int(time.time() * 1000)  # Millisecond timestamp for uniqueness
    combined = f"{service_id}:{task_data}:{nonce}"
    task_hash = hashlib.sha256(combined.encode()).digest()
    escrow_pda, _ = escrow_client.derive_escrow_pda(
        client_wallet.pubkey(), 
        provider_pubkey,
        service_id=None,
        task_hash=task_hash,
    )
    
    # Get client token account from env (EXACT same as solana_utils.py)
    client_ata_str = os.getenv("CLIENT_TOKEN_ACCOUNT")
    if not client_ata_str:
        raise ValueError("CLIENT_TOKEN_ACCOUNT not set in environment")
    client_token_account = Pubkey.from_string(client_ata_str)
    
    # Calculate escrow token account dynamically
    from spl.token.instructions import get_associated_token_address, create_associated_token_account
    from solana.rpc.async_api import AsyncClient
    
    mint_str = os.getenv("TEST_MINT")
    if not mint_str:
        raise ValueError("TEST_MINT not set in environment")
    mint = Pubkey.from_string(mint_str)
    
    # Each unique escrow PDA has its own ATA
    escrow_token_account = get_associated_token_address(escrow_pda, mint)
    
    # Check if escrow ATA exists, create if not (EXACT same as solana_utils.py)
    rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    
    instructions = []
    
    try:
        rpc = AsyncClient(rpc_url)
        ata_info = await rpc.get_account_info(escrow_token_account)
        
        if ata_info.value is None:
            # Create the ATA instruction
            create_ata_ix = create_associated_token_account(
                payer=client_wallet.pubkey(),
                owner=escrow_pda,
                mint=mint
            )
            instructions.append(create_ata_ix)
        
        await rpc.close()
    except Exception as e:
        # If RPC check fails, always include ATA creation instruction
        # (it will fail gracefully if ATA already exists)
        print(f"   Warning: Could not check ATA existence: {e}")
        print(f"   Including ATA creation instruction (will skip if exists)")
        create_ata_ix = create_associated_token_account(
            payer=client_wallet.pubkey(),
            owner=escrow_pda,
            mint=mint
        )
        instructions.append(create_ata_ix)
    
    # Build the escrow initialization instruction
    import struct
    from solders.instruction import Instruction, AccountMeta
    from solders.system_program import ID as SYS_PROGRAM_ID
    from spl.token.constants import TOKEN_PROGRAM_ID
    from solders.hash import Hash
    from solders.message import MessageV0
    
    # Get escrow program ID from env
    escrow_program_id_str = os.getenv("ESCROW_PROGRAM_ID")
    if not escrow_program_id_str:
        raise ValueError("ESCROW_PROGRAM_ID not set in environment")
    escrow_program_id = Pubkey.from_string(escrow_program_id_str)
    
    # Build instruction data: discriminator + amount + service_id + task_hash
    discriminator = bytes([243, 160, 77, 153, 11, 92, 48, 209])
    amount_bytes = struct.pack("<Q", amount_lamports)
    service_id_bytes = service_id.encode("utf-8")
    service_id_len = struct.pack("<I", len(service_id_bytes))
    data = discriminator + amount_bytes + service_id_len + service_id_bytes + task_hash
    
    # Build accounts list
    accounts = [
        AccountMeta(pubkey=escrow_pda, is_signer=False, is_writable=True),
        AccountMeta(pubkey=client_wallet.pubkey(), is_signer=True, is_writable=True),
        AccountMeta(pubkey=provider_pubkey, is_signer=False, is_writable=False),
        AccountMeta(pubkey=client_token_account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=escrow_token_account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    
    escrow_ix = Instruction(program_id=escrow_program_id, accounts=accounts, data=data)
    instructions.append(escrow_ix)
    
    # Build transaction with fresh blockhash
    try:
        rpc = AsyncClient(rpc_url)
        recent_blockhash_resp = await rpc.get_latest_blockhash()
        recent_blockhash = recent_blockhash_resp.value.blockhash
        await rpc.close()
    except Exception as e:
        # If RPC fails, use a placeholder (Gateway will replace it)
        print(f"   Warning: Could not fetch blockhash: {e}")
        print(f"   Using placeholder (will be replaced by Gateway)")
        recent_blockhash = Hash.from_string("11111111111111111111111111111111")
    
    # Create message
    msg = MessageV0.try_compile(
        payer=client_wallet.pubkey(),
        instructions=instructions,
        address_lookup_table_accounts=[],
        recent_blockhash=recent_blockhash,
    )
    
    # Create and sign transaction
    tx = VersionedTransaction(msg, [client_wallet])
    
    # Return transaction, escrow PDA, task hash, and nonce (for X-Payment header)
    task_hash_hex = task_hash.hex()
    
    return tx, escrow_pda, task_hash_hex, nonce


def serialize_transaction_for_x_payment(tx: VersionedTransaction) -> str:
    """
    Serialize a transaction to base64 for X-Payment header.
    
    Args:
        tx: Signed VersionedTransaction
    
    Returns:
        Base64 encoded transaction bytes
    """
    return base64.b64encode(bytes(tx)).decode('utf-8')
