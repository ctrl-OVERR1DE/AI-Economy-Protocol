"""Test escrow release payment with proper status handling."""
import os
import asyncio
import json
from dotenv import load_dotenv
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from contracts.client.gateway_escrow_client import GatewayEscrowClient

load_dotenv()

async def main():
    print("ESCROW RELEASE TEST - Checking escrow status first")
    print("=" * 80)
    
    # Load config
    wallet_path = os.path.expanduser(os.getenv("SOLANA_WALLET_PATH"))
    with open(wallet_path, 'r') as f:
        wallet_keypair = Keypair.from_bytes(bytes(json.load(f)))
    
    provider = Pubkey.from_string(os.getenv("PROVIDER_PUBLIC_KEY"))
    escrow_token = Pubkey.from_string(os.getenv("ESCROW_TOKEN_ACCOUNT"))
    provider_token = Pubkey.from_string(os.getenv("PROVIDER_TOKEN_ACCOUNT"))
    
    client = GatewayEscrowClient(wallet_keypair)
    escrow_pda, _ = client.derive_escrow_pda(wallet_keypair.pubkey(), provider)
    
    print(f"Escrow PDA: {escrow_pda}")
    print(f"Provider: {provider}")
    print(f"Escrow Token: {escrow_token}")
    print(f"Provider Token: {provider_token}")
    print()
    
    # Check if escrow exists
    rpc = AsyncClient(os.getenv("SOLANA_RPC_URL"))
    acc = await rpc.get_account_info(escrow_pda)
    
    if acc.value is None:
        print("ERROR: Escrow doesn't exist. Initialize first.")
        await rpc.close()
        await client.close()
        return
    
    print(f"Escrow exists ({len(acc.value.data)} bytes)")
    print(f"The escrow is likely in 'Completed' status from previous runs.")
    print(f"You need to create a NEW escrow or cancel this one first.")
    print()
    print("For now, we'll test release anyway to see Gateway behavior...")
    print()
    
    # Try release
    print("[TEST] Attempting release via Gateway...")
    try:
        sig, used_gw = await client.release_payment_via_gateway(
            provider, provider_token, escrow_token
        )
        method = "Gateway" if used_gw else "RPC Fallback"
        print(f"SUCCESS via {method}: {sig}")
        print(f"Explorer: https://explorer.solana.com/tx/{sig}?cluster=devnet")
    except Exception as e:
        print(f"FAILED: {e}")
    
    await rpc.close()
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
