"""
Fix token account configuration for escrow.
Creates proper ATAs for escrow PDA and provider.
"""
import os
import asyncio
import json
from dotenv import load_dotenv
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address

load_dotenv()


async def main():
    # Load configuration
    rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    wallet_path = os.path.expanduser(os.getenv("SOLANA_WALLET_PATH", "~/.config/solana/id.json"))
    mint_str = os.getenv("TEST_MINT")
    provider_str = os.getenv("PROVIDER_PUBLIC_KEY")
    program_id_str = os.getenv("ESCROW_PROGRAM_ID")
    
    if not all([mint_str, provider_str, program_id_str]):
        print("❌ Missing required environment variables")
        return
    
    # Load wallet
    with open(wallet_path, 'r') as f:
        secret = json.load(f)
    wallet = Keypair.from_bytes(bytes(secret))
    client_pubkey = wallet.pubkey()
    
    mint = Pubkey.from_string(mint_str)
    provider = Pubkey.from_string(provider_str)
    program_id = Pubkey.from_string(program_id_str)
    
    print(f"Configuration:")
    print(f"  Client: {client_pubkey}")
    print(f"  Provider: {provider}")
    print(f"  Mint: {mint}")
    print(f"  Program: {program_id}")
    print()
    
    # Derive escrow PDA
    seeds = [b"escrow", bytes(client_pubkey), bytes(provider)]
    escrow_pda, bump = Pubkey.find_program_address(seeds, program_id)
    print(f"Escrow PDA: {escrow_pda}")
    print(f"Escrow bump: {bump}")
    print()
    
    # Calculate ATAs
    client_ata = get_associated_token_address(client_pubkey, mint)
    provider_ata = get_associated_token_address(provider, mint)
    escrow_ata = get_associated_token_address(escrow_pda, mint)
    
    print(f"Token Accounts:")
    print(f"   Client ATA: {client_ata}")
    print(f"   Provider ATA: {provider_ata}")
    print(f"   Escrow PDA ATA: {escrow_ata}")
    print()
    
    # Check which ATAs exist
    rpc_client = AsyncClient(rpc_url)
    
    print("Checking existing accounts...")
    client_ata_info = await rpc_client.get_account_info(client_ata)
    provider_ata_info = await rpc_client.get_account_info(provider_ata)
    escrow_ata_info = await rpc_client.get_account_info(escrow_ata)
    
    client_exists = client_ata_info.value is not None
    provider_exists = provider_ata_info.value is not None
    escrow_exists = escrow_ata_info.value is not None
    
    print(f"   Client ATA: {'EXISTS' if client_exists else 'MISSING'}")
    print(f"   Provider ATA: {'EXISTS' if provider_exists else 'MISSING'}")
    print(f"   Escrow ATA: {'EXISTS' if escrow_exists else 'MISSING'}")
    print()
    
    await rpc_client.close()
    
    # Generate .env updates
    print("=" * 80)
    print("UPDATE YOUR .env FILE WITH THESE VALUES:")
    print("=" * 80)
    print(f"CLIENT_TOKEN_ACCOUNT={client_ata}")
    print(f"PROVIDER_TOKEN_ACCOUNT={provider_ata}")
    print(f"ESCROW_TOKEN_ACCOUNT={escrow_ata}")
    print("=" * 80)
    print()
    
    if not all([client_exists, provider_exists, escrow_exists]):
        print("WARNING: Some ATAs don't exist yet!")
        print("   They will be created automatically when you:")
        print("   1. Initialize the escrow (creates escrow ATA)")
        print("   2. Transfer tokens to provider (creates provider ATA if needed)")
        print()
        print("   OR create them manually with:")
        if not client_exists:
            print(f"   spl-token create-account {mint} --owner {client_pubkey}")
        if not provider_exists:
            print(f"   spl-token create-account {mint} --owner {provider}")
        if not escrow_exists:
            print(f"   spl-token create-account {mint} --owner {escrow_pda}")


if __name__ == "__main__":
    asyncio.run(main())
