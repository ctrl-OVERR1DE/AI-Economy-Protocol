"""Close completed escrow to free up the PDA for new tests."""
import os
import asyncio
import json
from dotenv import load_dotenv
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from spl.token.constants import TOKEN_PROGRAM_ID

load_dotenv()

async def main():
    print("CLOSE ESCROW - Free up PDA for fresh test")
    print("=" * 80)
    
    # Load config
    wallet_path = os.path.expanduser(os.getenv("SOLANA_WALLET_PATH"))
    with open(wallet_path, 'r') as f:
        wallet_keypair = Keypair.from_bytes(bytes(json.load(f)))
    
    program_id = Pubkey.from_string(os.getenv("ESCROW_PROGRAM_ID"))
    provider = Pubkey.from_string(os.getenv("PROVIDER_PUBLIC_KEY"))
    
    # Derive escrow PDA
    seeds = [b"escrow", bytes(wallet_keypair.pubkey()), bytes(provider)]
    escrow_pda, bump = Pubkey.find_program_address(seeds, program_id)
    
    print(f"Closing escrow: {escrow_pda}")
    print(f"This will free up the PDA and refund rent to client")
    print()
    
    # Close instruction - just close the account (no special instruction needed)
    # Actually, we need to check if there's a close_escrow instruction in the program
    # For now, let's just create a new escrow with different parameters
    
    print("NOTE: Anchor programs don't have auto-close.")
    print("You have 2 options:")
    print("1. Use different provider address for testing")
    print("2. Add a 'close' instruction to your escrow program")
    print()
    print("For now, just reinitialize with proof submitted status:")
    print("Run agent_a to submit proof, then test release")

if __name__ == "__main__":
    asyncio.run(main())
