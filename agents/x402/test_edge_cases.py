"""
Test edge cases for x402 integration.
"""

import asyncio
import sys
import os
import requests

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


async def test_edge_cases():
    """
    Test various edge cases:
    1. Request without payment (should get 402)
    2. Invalid X-Payment header
    3. Server not running
    4. Malformed request
    """
    print("="*70)
    print("Testing x402 Edge Cases")
    print("="*70)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Request without payment (should get 402)
    print("\n[Test 1] Request without payment (expect 402)")
    print("-" * 70)
    try:
        resp = requests.get(f"{base_url}/analyze", params={"data": "test"})
        if resp.status_code == 402:
            print("✅ PASS: Got 402 Payment Required")
            payment_info = resp.json().get('payment', {})
            print(f"   Recipient: {payment_info.get('recipient')}")
            print(f"   Amount: {payment_info.get('amount')} SOL")
        else:
            print(f"❌ FAIL: Expected 402, got {resp.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 2: Invalid X-Payment header
    print("\n[Test 2] Invalid X-Payment header (expect 402)")
    print("-" * 70)
    try:
        resp = requests.get(
            f"{base_url}/analyze",
            params={"data": "test"},
            headers={"X-Payment": "invalid_base64_data"}
        )
        if resp.status_code == 402:
            print("✅ PASS: Rejected invalid payment")
            error = resp.json().get('details', '')
            print(f"   Error: {error}")
        else:
            print(f"❌ FAIL: Expected 402, got {resp.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 3: Health check
    print("\n[Test 3] Health check endpoint")
    print("-" * 70)
    try:
        resp = requests.get(f"{base_url}/health")
        if resp.status_code == 200:
            print("✅ PASS: Health check successful")
            health = resp.json()
            print(f"   Status: {health.get('status')}")
            print(f"   Service: {health.get('service')}")
        else:
            print(f"❌ FAIL: Expected 200, got {resp.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 4: Root endpoint
    print("\n[Test 4] Root endpoint (service info)")
    print("-" * 70)
    try:
        resp = requests.get(base_url)
        if resp.status_code == 200:
            print("✅ PASS: Root endpoint accessible")
            info = resp.json()
            print(f"   Service: {info.get('service')}")
            print(f"   Protocol: {info.get('payment', {}).get('protocol')}")
            print(f"   Price: {info.get('payment', {}).get('price')} SOL")
        else:
            print(f"❌ FAIL: Expected 200, got {resp.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 5: Missing data parameter
    print("\n[Test 5] Missing data parameter (expect 402)")
    print("-" * 70)
    try:
        resp = requests.get(f"{base_url}/analyze")
        if resp.status_code == 402:
            print("✅ PASS: Got 402 even without data parameter")
        else:
            print(f"⚠️  WARNING: Expected 402, got {resp.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "="*70)
    print("Edge Case Testing Complete")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_edge_cases())
