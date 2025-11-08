"""
Test multiple sequential x402 requests.
Verifies that each request creates a unique escrow with different nonce.
"""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from agents.x402.client import X402Client


async def test_multiple_requests():
    """
    Test multiple sequential requests to verify:
    1. Each request creates unique escrow
    2. Nonces are different
    3. All requests succeed
    """
    print("="*70)
    print("Testing Multiple Sequential x402 Requests")
    print("="*70)
    
    client = X402Client(agent_name="ClientAgent")
    print(f"\nClient wallet: {client.wallet.pubkey()}")
    
    results = []
    
    # Make 3 sequential requests
    for i in range(1, 4):
        print(f"\n{'='*70}")
        print(f"Request #{i}")
        print(f"{'='*70}")
        
        try:
            status, response = await client.get_with_payment(
                url="http://localhost:8000/analyze",
                params={"data": f"Test analysis request #{i}"}
            )
            
            if status == 200:
                payment_details = response.get('paymentDetails', {})
                result = {
                    'request': i,
                    'status': 'SUCCESS',
                    'escrow_pda': payment_details.get('escrowPDA'),
                    'amount': payment_details.get('amountPaid'),
                }
                results.append(result)
                print(f"\n✅ Request #{i} SUCCESS")
            else:
                results.append({
                    'request': i,
                    'status': 'FAILED',
                    'error': response
                })
                print(f"\n❌ Request #{i} FAILED: {response}")
        
        except Exception as e:
            results.append({
                'request': i,
                'status': 'ERROR',
                'error': str(e)
            })
            print(f"\n❌ Request #{i} ERROR: {e}")
        
        # Small delay between requests
        await asyncio.sleep(1)
    
    # Summary
    print(f"\n{'='*70}")
    print("Summary")
    print(f"{'='*70}")
    
    successful = [r for r in results if r['status'] == 'SUCCESS']
    print(f"\nTotal requests: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(results) - len(successful)}")
    
    if successful:
        print(f"\n✅ Escrow PDAs (should all be different):")
        escrow_pdas = set()
        for r in successful:
            pda = r['escrow_pda']
            print(f"   Request #{r['request']}: {pda}")
            escrow_pdas.add(pda)
        
        if len(escrow_pdas) == len(successful):
            print(f"\n✅ SUCCESS: All {len(successful)} escrows are unique!")
        else:
            print(f"\n❌ FAILURE: Some escrows were reused!")
    
    print(f"\n{'='*70}")


if __name__ == "__main__":
    asyncio.run(test_multiple_requests())
