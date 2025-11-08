"""
Test Marketplace API

Quick test to verify marketplace is working.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_marketplace():
    """Test marketplace endpoints."""
    print("="*70)
    print("🧪 TESTING MARKETPLACE API")
    print("="*70)
    print()
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("   ⚠️  Make sure marketplace is running: python start_marketplace.py")
        return
    
    # Test 2: Register a provider
    print("\n2. Registering test provider...")
    provider_data = {
        "agent_address": "agent1qtest123",
        "agent_name": "TestCodeReviewAgent",
        "solana_address": "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",
        "port": 5052,
        "endpoint": "http://localhost:5052/submit",
        "services": [{
            "service_type": "code_review",
            "base_price": 0.1,
            "description": "AI-powered code review",
            "features": ["Quality scoring", "Security analysis", "Best practices"],
            "avg_completion_time": 30,
            "success_rate": 1.0
        }]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/providers/register", json=provider_data)
        if response.status_code == 200:
            print("   ✅ Provider registered successfully")
        else:
            print(f"   ❌ Registration failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Get online providers
    print("\n3. Getting online providers...")
    try:
        response = requests.get(f"{BASE_URL}/providers/online")
        if response.status_code == 200:
            providers = response.json()['providers']
            print(f"   ✅ Found {len(providers)} online provider(s)")
            for p in providers:
                print(f"      - {p['agent_name']} ({p['agent_address'][:20]}...)")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Discover services
    print("\n4. Discovering services...")
    try:
        response = requests.get(f"{BASE_URL}/services")
        if response.status_code == 200:
            services = response.json()['services']
            print(f"   ✅ Found {len(services)} service(s)")
            for s in services:
                print(f"      - {s['service_type']}: {s['base_price']} SOL by {s['provider_name']}")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Find best provider
    print("\n5. Finding best provider for code review...")
    try:
        response = requests.get(
            f"{BASE_URL}/services/code_review/best",
            params={"max_price": 0.15, "min_rating": 4.0}
        )
        if response.status_code == 200:
            provider = response.json()['provider']
            print(f"   ✅ Best provider: {provider['provider_name']}")
            print(f"      Price: {provider['base_price']} SOL")
            print(f"      Rating: {provider['provider_rating']}/5.0")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: Get marketplace stats
    print("\n6. Getting marketplace statistics...")
    try:
        response = requests.get(f"{BASE_URL}/stats")
        if response.status_code == 200:
            stats = response.json()['stats']
            print(f"   ✅ Marketplace Stats:")
            print(f"      Total Providers: {stats['total_providers']}")
            print(f"      Online Providers: {stats['online_providers']}")
            print(f"      Total Services: {stats['total_services']}")
            print(f"      Total Transactions: {stats['total_transactions']}")
            print(f"      Total Volume: {stats['total_volume']} SOL")
            print(f"      Average Rating: {stats['avg_rating']}/5.0")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("="*70)
    print("✅ MARKETPLACE TEST COMPLETE!")
    print("="*70)
    print()
    print("📖 API Documentation: http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    test_marketplace()
