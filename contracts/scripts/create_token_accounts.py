"""
Create a test mint and token accounts on devnet for Gateway escrow testing.
Prints the addresses to add to .env
"""
import os
import asyncio
import json

from dotenv import load_dotenv
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import (
    get_associated_token_address,
    create_associated_token_account,
    initialize_mint,
    InitializeMintParams,
    mint_to,
    MintToParams,
)
from spl.token._layouts import MINT_LAYOUT
from solders.system_program import create_account, CreateAccountParams
from solders.transaction import VersionedTransaction
from solders.message import MessageV0


async def main():
    load_dotenv()

    rpc = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    program_id_str = os.getenv("ESCROW_PROGRAM_ID")
    if not program_id_str:
        raise RuntimeError("ESCROW_PROGRAM_ID not set in .env")
    program_id = Pubkey.from_string(program_id_str)

    # Load payer wallet
    wallet_path = os.path.expanduser(os.getenv("SOLANA_WALLET_PATH", "~/.config/solana/id.json"))
    with open(wallet_path, "r") as f:
        secret = json.load(f)
    payer = Keypair.from_bytes(bytes(secret))

    client = AsyncClient(rpc, commitment=Confirmed)

    print("Creating mint and token accounts on devnet...")
    print(f"Payer (client): {payer.pubkey()}")

    # Generate a new provider keypair for testing
    provider = Keypair()
    print(f"Provider (generated): {provider.pubkey()}")

    # Derive escrow PDA
    seeds = [b"escrow", bytes(payer.pubkey()), bytes(provider.pubkey())]
    escrow_pda, bump = Pubkey.find_program_address(seeds, program_id)
    print(f"Escrow PDA: {escrow_pda}")

    # Create a new mint manually
    mint_kp = Keypair()
    mint_pubkey = mint_kp.pubkey()
    print(f"\nCreating mint: {mint_pubkey}")

    # Get rent for mint account
    rent_resp = await client.get_minimum_balance_for_rent_exemption(MINT_LAYOUT.sizeof())
    rent_lamports = rent_resp.value

    # Create mint account instruction
    create_mint_acc_ix = create_account(
        CreateAccountParams(
            from_pubkey=payer.pubkey(),
            to_pubkey=mint_pubkey,
            lamports=rent_lamports,
            space=MINT_LAYOUT.sizeof(),
            owner=TOKEN_PROGRAM_ID,
        )
    )

    # Initialize mint instruction
    init_mint_ix = initialize_mint(
        InitializeMintParams(
            program_id=TOKEN_PROGRAM_ID,
            mint=mint_pubkey,
            decimals=6,
            mint_authority=payer.pubkey(),
            freeze_authority=None,
        )
    )

    # Build and send transaction
    recent_blockhash_resp = await client.get_latest_blockhash()
    recent_blockhash = recent_blockhash_resp.value.blockhash

    msg = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=[create_mint_acc_ix, init_mint_ix],
        address_lookup_table_accounts=[],
        recent_blockhash=recent_blockhash,
    )
    tx = VersionedTransaction(msg, [payer, mint_kp])
    await client.send_transaction(tx)
    print(f"✓ Mint created")

    # Create client ATA
    print(f"Creating client token account...")
    client_ata = get_associated_token_address(owner=payer.pubkey(), mint=mint_pubkey)
    create_client_ata_ix = create_associated_token_account(
        payer=payer.pubkey(),
        owner=payer.pubkey(),
        mint=mint_pubkey,
    )

    recent_blockhash_resp = await client.get_latest_blockhash()
    recent_blockhash = recent_blockhash_resp.value.blockhash
    msg = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=[create_client_ata_ix],
        address_lookup_table_accounts=[],
        recent_blockhash=recent_blockhash,
    )
    tx = VersionedTransaction(msg, [payer])
    await client.send_transaction(tx)
    print(f"Client ATA: {client_ata}")

    # Create escrow PDA ATA (allow owner off-curve)
    print(f"Creating escrow PDA token account (owner off-curve)...")
    escrow_ata = get_associated_token_address(owner=escrow_pda, mint=mint_pubkey)
    create_ata_ix = create_associated_token_account(
        payer=payer.pubkey(),
        owner=escrow_pda,
        mint=mint_pubkey,
    )

    recent_blockhash_resp = await client.get_latest_blockhash()
    recent_blockhash = recent_blockhash_resp.value.blockhash
    msg = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=[create_ata_ix],
        address_lookup_table_accounts=[],
        recent_blockhash=recent_blockhash,
    )
    tx = VersionedTransaction(msg, [payer])
    await client.send_transaction(tx)
    print(f"Escrow PDA ATA: {escrow_ata}")

    # Mint tokens to client ATA
    print(f"\nMinting 1,000 tokens to client ATA...")
    mint_to_ix = mint_to(
        MintToParams(
            program_id=TOKEN_PROGRAM_ID,
            mint=mint_pubkey,
            dest=client_ata,
            mint_authority=payer.pubkey(),
            amount=1_000_000_000,  # 1,000 tokens with 6 decimals
        )
    )

    recent_blockhash_resp = await client.get_latest_blockhash()
    recent_blockhash = recent_blockhash_resp.value.blockhash
    msg = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=[mint_to_ix],
        address_lookup_table_accounts=[],
        recent_blockhash=recent_blockhash,
    )
    tx = VersionedTransaction(msg, [payer])
    await client.send_transaction(tx)
    print(f"✓ Minted 1,000 tokens")

    await client.close()

    print("\n" + "="*60)
    print("✅ Setup complete! Add these to your .env file:")
    print("="*60)
    print(f"PROVIDER_PUBLIC_KEY={provider.pubkey()}")
    print(f"CLIENT_TOKEN_ACCOUNT={client_ata}")
    print(f"ESCROW_TOKEN_ACCOUNT={escrow_ata}")
    print(f"TEST_MINT={mint_pubkey}")
    print("="*60)
    print("\nNow run: python scripts/init_escrow_via_gateway.py")


if __name__ == "__main__":
    asyncio.run(main())
