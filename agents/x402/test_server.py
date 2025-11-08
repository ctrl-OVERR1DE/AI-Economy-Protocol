"""
Simple test script for x402 server.
Tests the 402 response without payment.
"""

import requests

def test_server():
    """Test x402 server endpoints."""
    
    print("="*70)
    print("Testing AEP x402 Server")
    print("="*70)
    
    # Test health endpoint
    print("\n1. Testing /health endpoint...")
    try:
        resp = requests.get("http://localhost:8000/health")
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test root endpoint
    print("\n2. Testing / endpoint...")
    try:
        resp = requests.get("http://localhost:8000/")
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test /analyze without payment (should get 402)
    print("\n3. Testing /analyze without payment (expect 402)...")
    try:
        resp = requests.get("http://localhost:8000/analyze", params={"data": "Test data"})
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 402:
            print("   [PASS] Correctly returned 402 Payment Required")
            payment_req = resp.json()
            print(f"   Payment requirements:")
            print(f"      Recipient: {payment_req['payment']['recipient']}")
            print(f"      Amount: {payment_req['payment']['amount']} SOL")
            print(f"      Service ID: {payment_req['payment']['serviceId']}")
            print(f"      Network: {payment_req['payment']['network']}")
            print(f"      Escrow Program: {payment_req['payment']['escrowProgram']}")
        else:
            print(f"   [FAIL] Expected 402, got {resp.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "="*70)
    print("Test complete!")
    print("="*70)


if __name__ == "__main__":
    test_server()
