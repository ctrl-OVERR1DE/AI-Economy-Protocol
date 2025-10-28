"""Submit proof to set escrow to ProofSubmitted status."""
import os, asyncio, json
from dotenv import load_dotenv
from solders.keypair import Keypair
from solders.pubkey import Pubkey
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from contracts.client.gateway_escrow_client import GatewayEscrowClient

load_dotenv()

async def main():
    wallet_path = os.path.expanduser(os.getenv("SOLANA_WALLET_PATH"))
    with open(wallet_path, 'r') as f:
        wallet = Keypair.from_bytes(bytes(json.load(f)))
    
    provider = Pubkey.from_string(os.getenv("PROVIDER_PUBLIC_KEY"))
    client = GatewayEscrowClient(wallet)
    
    proof_hash = b"test_proof_12345678901234567890"  # 32 bytes
    proof_hash = proof_hash + b"\x00" * (32 - len(proof_hash))
    
    try:
        sig = await client.submit_proof(wallet.pubkey(), provider, proof_hash)
        print(f"Proof submitted: {sig}")
    except Exception as e:
        print(f"Error (expected if already in Completed): {e}")
    
    await client.close()

asyncio.run(main())
