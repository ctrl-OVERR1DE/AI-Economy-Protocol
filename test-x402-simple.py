"""
Simple test to verify x402 flow works.
Tests transaction creation without RPC dependency.
"""

import asyncio
from agents.x402.client import X402Client


async def main():
    print("="*70)
    print("Simple x402 Test")
    print("="*70)
    
    try:
        # Initialize client
        print("\n1. Initializing client...")
        client = X402Client(agent_name="ClientAgent")
        print(f"   Wallet: {client.wallet.pubkey()}")
        
        # Make request
        print("\n2. Making request...")
        status, response = await client.get_with_payment(
            url="http://localhost:8000/analyze",
            params={"data": "Test analysis"}
        )
        
        print(f"\n3. Result:")
        print(f"   Status: {status}")
        if status == 200:
            print("   ✅ SUCCESS!")
            if 'result' in response:
                print(f"   Result: {response['result']}")
        else:
            print(f"   ❌ FAILED")
            print(f"   Response: {response}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
