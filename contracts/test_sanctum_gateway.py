"""
Sanctum Gateway Integration Test
Based on official Sanctum Gateway documentation.

Tests the complete flow:
1. Build unsigned transaction with NULL blockhash
2. Call buildGatewayTransaction to optimize and set blockhash
3. Sign the built transaction
4. Call sendTransaction to deliver via Gateway
5. Verify on-chain
"""
import os
import asyncio
import json
import base64
from dotenv import load_dotenv

# Solana imports
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.hash import Hash
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed

# Load environment
load_dotenv()

from client.gateway_client import GatewayClient


async def test_gateway_full_flow():
    """
    Test complete Gateway flow using buildGatewayTransaction + sendTransaction.
    This matches the official Sanctum docs example.
    """
    print("\n" + "="*80)
    print("SANCTUM GATEWAY INTEGRATION TEST")
    print("Testing: buildGatewayTransaction + sendTransaction")
    print("="*80 + "\n")
    
    # Load wallet
    wallet_path = os.path.expanduser(os.getenv("SOLANA_WALLET_PATH", "~/.config/solana/id.json"))
    print(f"[1/7] Loading wallet from: {wallet_path}")
    with open(wallet_path, 'r') as f:
        secret = json.load(f)
    wallet = Keypair.from_bytes(bytes(secret))
    print(f"      Wallet: {wallet.pubkey()}")
    
    # Create simple transfer instruction (to self for testing)
    recipient = wallet.pubkey()
    amount = 1_000_000  # 0.001 SOL
    
    print(f"\n[2/7] Creating transfer instruction")
    print(f"      From: {wallet.pubkey()}")
    print(f"      To: {recipient}")
    print(f"      Amount: {amount} lamports (0.001 SOL)")
    
    ix = transfer(TransferParams(
        from_pubkey=wallet.pubkey(),
        to_pubkey=recipient,
        lamports=amount
    ))
    
    # Build UNSIGNED transaction with NULL blockhash
    # Per docs: "Since buildGatewayTransaction will set the blockhash for you,
    #            we can avoid fetching the latest blockhash here"
    print(f"\n[3/7] Building unsigned transaction with NULL blockhash")
    NULL_BLOCKHASH = Hash.from_string("11111111111111111111111111111111")
    
    msg = MessageV0.try_compile(
        payer=wallet.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=NULL_BLOCKHASH,
    )
    unsigned_tx = VersionedTransaction(msg, [wallet])
    unsigned_tx_bytes = bytes(unsigned_tx)
    
    print(f"      Transaction size: {len(unsigned_tx_bytes)} bytes")
    print(f"      Blockhash: {NULL_BLOCKHASH} (placeholder)")
    
    # Initialize Gateway client
    gateway = GatewayClient()
    cluster = os.getenv("GATEWAY_CLUSTER", "devnet")
    
    print(f"\n[4/7] Calling Gateway buildGatewayTransaction")
    print(f"      Cluster: {cluster}")
    print(f"      Endpoint: https://tpg.sanctum.so/v1/{cluster}")
    
    try:
        # Call buildGatewayTransaction
        # This will: simulate, set CU price, add tips, set real blockhash
        build_resp = await gateway.build_gateway_transaction(
            unsigned_tx_bytes,
            cluster=cluster,
            options={
                # All optional - defaults to project dashboard parameters
                # "skipSimulation": False,
                # "skipPriorityFee": False,
                # "cuPriceRange": "medium",
                # "jitoTipRange": "medium",
                # "expireInSlots": 150,
                # "deliveryMethodType": "sanctum-sender"
            }
        )
        
        # Check for errors
        if "error" in build_resp:
            print(f"\n[ERROR] buildGatewayTransaction failed:")
            print(f"        Code: {build_resp['error'].get('code')}")
            print(f"        Message: {build_resp['error'].get('message')}")
            if 'data' in build_resp['error']:
                print(f"        Data: {build_resp['error']['data']}")
            await gateway.close()
            return False
        
        # Extract result
        result = build_resp.get("result")
        if not result or "transaction" not in result:
            print(f"\n[ERROR] Invalid response format")
            print(f"        Response: {build_resp}")
            await gateway.close()
            return False
        
        print(f"      [OK] Transaction built successfully")
        
        # Extract blockhash info
        latest_blockhash_info = result.get("latestBlockhash", {})
        blockhash_str = latest_blockhash_info.get("blockhash", "N/A")
        last_valid_height = latest_blockhash_info.get("lastValidBlockHeight", "N/A")
        
        print(f"      Latest blockhash: {blockhash_str}")
        print(f"      Last valid height: {last_valid_height}")
        
        # Decode the built transaction
        print(f"\n[5/7] Decoding and signing built transaction")
        built_tx_b64 = result["transaction"]
        built_tx_bytes = base64.b64decode(built_tx_b64)
        built_tx = VersionedTransaction.from_bytes(built_tx_bytes)
        
        print(f"      Built tx has {len(built_tx.message.instructions)} instructions")
        
        # Sign the transaction
        signed_tx = VersionedTransaction(built_tx.message, [wallet])
        signed_tx_bytes = bytes(signed_tx)
        
        print(f"      Transaction signed")
        print(f"      Signed tx has {len(signed_tx.message.instructions)} instructions")
        print(f"      Signed tx size: {len(signed_tx_bytes)} bytes")
        
        # Send via Gateway
        print(f"\n[6/7] Calling Gateway sendTransaction")
        send_resp = await gateway.send_transaction(signed_tx_bytes, cluster=cluster)
        
        # Check for errors
        if "error" in send_resp:
            print(f"\n[ERROR] sendTransaction failed:")
            print(f"        Code: {send_resp['error'].get('code')}")
            print(f"        Message: {send_resp['error'].get('message')}")
            if 'data' in send_resp['error']:
                print(f"        Data: {send_resp['error']['data']}")
            await gateway.close()
            return False
        
        # Extract signature
        send_result = send_resp.get("result")
        if not send_result:
            print(f"\n[ERROR] Invalid sendTransaction response")
            print(f"        Response: {send_resp}")
            await gateway.close()
            return False
        
        # Result is the transaction signature string
        signature = send_result if isinstance(send_result, str) else send_result.get("signature")
        
        if not signature:
            print(f"\n[ERROR] No signature in response")
            print(f"        Response: {send_resp}")
            await gateway.close()
            return False
        
        print(f"      [OK] Transaction sent via Gateway")
        print(f"      Signature: {signature}")
        print(f"      Explorer: https://explorer.solana.com/tx/{signature}?cluster={cluster}")
        
        # Verify transaction landed on-chain
        print(f"\n[7/7] Verifying transaction on-chain...")
        rpc_url = "https://api.devnet.solana.com" if cluster == "devnet" else "https://api.mainnet-beta.solana.com"
        rpc_client = AsyncClient(rpc_url, commitment=Confirmed)
        
        # Wait for transaction to land
        await asyncio.sleep(3)
        
        from solders.signature import Signature
        sig_obj = Signature.from_string(signature)
        
        tx_status = await rpc_client.get_transaction(sig_obj, max_supported_transaction_version=0)
        
        await rpc_client.close()
        await gateway.close()
        
        if tx_status.value is not None:
            print(f"      [OK] Transaction CONFIRMED on-chain!")
            print(f"      Slot: {tx_status.value.slot}")
            print(f"\n" + "="*80)
            print("[SUCCESS] SANCTUM GATEWAY INTEGRATION WORKING!")
            print("="*80 + "\n")
            return True
        else:
            print(f"      [WARNING] Transaction not found on-chain yet")
            print(f"      This could mean:")
            print(f"      - Transaction is still pending (check explorer)")
            print(f"      - Transaction failed (check Gateway dashboard)")
            print(f"      - Devnet congestion (try again)")
            print(f"\n" + "="*80)
            print("[PARTIAL SUCCESS] Gateway accepted tx, but not confirmed yet")
            print("="*80 + "\n")
            return False
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception:")
        print(f"        {e}")
        import traceback
        traceback.print_exc()
        await gateway.close()
        return False


async def main():
    """Run Gateway integration test."""
    print("\n[TEST] Sanctum Gateway Integration Test")
    print("Based on official Sanctum Gateway documentation")
    print("Docs: https://gateway.sanctum.so/docs\n")
    
    success = await test_gateway_full_flow()
    
    if success:
        print("\n[RESULT] Gateway integration is working correctly!")
        print("         Ready for hackathon submission.")
    else:
        print("\n[RESULT] Gateway integration needs attention")
        print("         Check:")
        print("         1. Gateway dashboard delivery methods configured")
        print("         2. API key is valid")
        print("         3. Devnet has sufficient SOL")
        print("         4. Transaction logs in Gateway dashboard")


if __name__ == "__main__":
    asyncio.run(main())
