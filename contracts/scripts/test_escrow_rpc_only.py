"""
Test escrow initialization via direct RPC (no Gateway) to verify instruction correctness.
"""
import os
import asyncio

from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
import json

from client.gateway_escrow_client import GatewayEscrowClient


async def main():
    load_dotenv()

    rpc = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    program_id_str = os.getenv("ESCROW_PROGRAM_ID")
    if not program_id_str:
        raise RuntimeError("ESCROW_PROGRAM_ID not set in environment")

    provider_pubkey_str = os.getenv("PROVIDER_PUBLIC_KEY")
    client_ata_str = os.getenv("CLIENT_TOKEN_ACCOUNT")
    escrow_ata_str = os.getenv("ESCROW_TOKEN_ACCOUNT")

    missing = [name for name, val in [
        ("PROVIDER_PUBLIC_KEY", provider_pubkey_str),
        ("CLIENT_TOKEN_ACCOUNT", client_ata_str),
        ("ESCROW_TOKEN_ACCOUNT", escrow_ata_str),
    ] if not val]
    if missing:
        raise RuntimeError("Missing required env vars: " + ", ".join(missing))

    provider_pubkey = Pubkey.from_string(provider_pubkey_str)
    client_ata = Pubkey.from_string(client_ata_str)
    escrow_ata = Pubkey.from_string(escrow_ata_str)

    amount = int(os.getenv("ESCROW_AMOUNT", "100000000"))
    service_id = os.getenv("ESCROW_SERVICE_ID", "data_analysis_001")
    task_data = os.getenv("ESCROW_TASK_DATA", "Analyze sales data")

    # Load wallet
    wallet_path = os.path.expanduser(os.getenv("SOLANA_WALLET_PATH", "~/.config/solana/id.json"))
    with open(wallet_path, "r") as f:
        secret = json.load(f)
    payer = Keypair.from_bytes(bytes(secret))

    client = AsyncClient(rpc, commitment=Confirmed)

    # Build instruction manually
    from solders.instruction import Instruction, AccountMeta
    from solders.transaction import VersionedTransaction
    from solders.message import MessageV0
    from solders.system_program import ID as SYS_PROGRAM_ID
    from spl.token.constants import TOKEN_PROGRAM_ID
    import struct
    import hashlib

    program_id = Pubkey.from_string(program_id_str)
    
    # Derive escrow PDA
    seeds = [b"escrow", bytes(payer.pubkey()), bytes(provider_pubkey)]
    escrow_pda, bump = Pubkey.find_program_address(seeds, program_id)
    print(f"Escrow PDA: {escrow_pda}")

    # Hash task
    task_hash = hashlib.sha256(task_data.encode()).digest()

    # Build instruction data
    discriminator = bytes([243, 160, 77, 153, 11, 92, 48, 209])
    amount_bytes = struct.pack("<Q", amount)
    service_id_bytes = service_id.encode("utf-8")
    service_id_len = struct.pack("<I", len(service_id_bytes))
    data = discriminator + amount_bytes + service_id_len + service_id_bytes + task_hash

    # Build accounts
    accounts = [
        AccountMeta(pubkey=escrow_pda, is_signer=False, is_writable=True),
        AccountMeta(pubkey=payer.pubkey(), is_signer=True, is_writable=True),
        AccountMeta(pubkey=provider_pubkey, is_signer=False, is_writable=False),
        AccountMeta(pubkey=client_ata, is_signer=False, is_writable=True),
        AccountMeta(pubkey=escrow_ata, is_signer=False, is_writable=True),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]

    ix = Instruction(program_id=program_id, accounts=accounts, data=data)

    # Build and send transaction with fresh blockhash
    recent = await client.get_latest_blockhash()
    msg = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=recent.value.blockhash,
    )
    tx = VersionedTransaction(msg, [payer])

    print(f"Sending transaction via RPC (skip_preflight=True to avoid blockhash expiry)...")
    resp = await client.send_transaction(tx, opts=TxOpts(skip_preflight=True, max_retries=3))
    print(f"✅ Transaction signature: {resp.value}")
    
    # Wait for confirmation
    print(f"Waiting for confirmation...")
    await asyncio.sleep(2)
    
    # Check transaction status
    sig_status = await client.get_signature_statuses([resp.value])
    if sig_status.value and sig_status.value[0]:
        status = sig_status.value[0]
        if status.err:
            print(f"❌ Transaction failed: {status.err}")
        else:
            print(f"✅ Transaction confirmed in slot {status.slot}")
    else:
        print(f"⏳ Transaction pending, check: https://explorer.solana.com/tx/{resp.value}?cluster=devnet")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
