"""
Test script for x402 client.
Tests the full payment flow with escrow.
"""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from agents.x402.client import X402Client


async def test_x402_flow():
    """
    Test the complete x402 payment flow.
    
    Prerequisites:
    - Server must be running on http://localhost:8000
    - Client wallet must have sufficient funds
    - All env variables must be set correctly
    """
    print("="*70)
    print("Testing AEP x402 Client - Full Payment Flow")
    print("="*70)
    
    try:
        # Initialize client
        print("\n1. Initializing x402 client...")
        client = X402Client(agent_name="ClientAgent")
        print(f"   Client wallet: {client.wallet.pubkey()}")
        
        # Test request with payment
        print("\n2. Making request to x402-protected endpoint...")
        status, response = await client.get_with_payment(
            url="http://localhost:8000/analyze",
            params={"data": "Analyze Q4 2024 sales data"}
        )
        
        # Check result
        print("\n3. Checking result...")
        if status == 200:
            print("   [PASS] Request successful!")
            
            if 'result' in response:
                print(f"\n   Analysis Result:")
                result = response['result']
                for key, value in result.items():
                    print(f"      {key}: {value}")
            
            if 'paymentDetails' in response:
                print(f"\n   Payment Details:")
                details = response['paymentDetails']
                print(f"      Escrow PDA: {details.get('escrowPDA')}")
                print(f"      Amount Paid: {details.get('amountPaid')} SOL")
                print(f"      Service ID: {details.get('serviceId')}")
                
                if details.get('explorerUrls', {}).get('proof'):
                    print(f"      Proof TX: {details['explorerUrls']['proof']}")
        else:
            print(f"   [FAIL] Request failed with status {status}")
            print(f"   Response: {response}")
        
        print("\n" + "="*70)
        print("Test complete!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_x402_flow())
