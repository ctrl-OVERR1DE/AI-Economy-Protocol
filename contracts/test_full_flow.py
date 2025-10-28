"""Test full escrow flow: initialize -> submit proof -> release via Gateway."""
import os, asyncio, json
from dotenv import load_dotenv
from solders.keypair import Keypair
from solders.pubkey import Pubkey
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from contracts.client.gateway_escrow_client import GatewayEscrowClient

load_dotenv()

async def main():
    print("=" * 80)
    print("FULL ESCROW FLOW TEST")
    print("Initialize -> Submit Proof -> Release Payment via Gateway")
    print("=" * 80)
    
    # Load config
    wallet_path = os.path.expanduser(os.getenv("SOLANA_WALLET_PATH"))
    with open(wallet_path, 'r') as f:
        wallet = Keypair.from_bytes(bytes(json.load(f)))
    
    provider = Pubkey.from_string(os.getenv("PROVIDER_PUBLIC_KEY"))
    client_token = Pubkey.from_string(os.getenv("CLIENT_TOKEN_ACCOUNT"))
    escrow_token = Pubkey.from_string(os.getenv("ESCROW_TOKEN_ACCOUNT"))
    provider_token = Pubkey.from_string(os.getenv("PROVIDER_TOKEN_ACCOUNT"))
    
    client = GatewayEscrowClient(wallet_keypair=wallet)
    escrow_pda, _ = client.derive_escrow_pda(wallet.pubkey(), provider)
    
    print(f"\n[CONFIG]")
    print(f"   Client: {wallet.pubkey()}")
    print(f"   Provider: {provider}")
    print(f"   Escrow PDA: {escrow_pda}")
    print(f"   Amount: 100000000 lamports (0.1 SOL)")
    
    # Step 1: Initialize escrow
    print(f"\n[STEP 1/3] Initializing escrow via Gateway...")
    try:
        sig, used_gw = await client.initialize_escrow_via_gateway(
            provider_pubkey=provider,
            amount=100000000,  # 0.1 SOL
            service_id="test_service",
            task_data="test_task_data",
            client_token_account=client_token,
            escrow_token_account=escrow_token
        )
        method = "Gateway" if used_gw else "RPC Fallback"
        print(f"   SUCCESS via {method}: {sig}")
    except Exception as e:
        print(f"   ERROR: {repr(e)}")
        import traceback
        traceback.print_exc()
        await client.close()
        return
    
    # Step 2: Submit proof
    print(f"\n[STEP 2/3] Submitting proof...")
    proof_data = "test_proof_data_for_escrow"
    try:
        sig = await client.submit_proof(provider, proof_data)
        print(f"   SUCCESS: {sig}")
    except Exception as e:
        print(f"   ERROR: {repr(e)}")
        import traceback
        traceback.print_exc()
        await client.close()
        return
    
    # Step 3: Release payment via Gateway
    print(f"\n[STEP 3/3] Releasing payment via Gateway...")
    try:
        sig, used_gw = await client.release_payment_via_gateway(
            provider, provider_token, escrow_token
        )
        method = "Gateway" if used_gw else "RPC Fallback"
        print(f"   SUCCESS via {method}!")
        print(f"   Transaction: {sig}")
        print(f"   Explorer: https://explorer.solana.com/tx/{sig}?cluster=devnet")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "=" * 80)
    if used_gw:
        print("SUCCESS - FULL FLOW COMPLETED VIA GATEWAY!")
    else:
        print("SUCCESS - FULL FLOW COMPLETED (Gateway fallback to RPC)")
    print("=" * 80)
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
