"""
Test script for marketplace functionality.
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.marketplace import MarketplaceRegistry, AgentProfile, ServiceListing
from datetime import datetime


def test_agent_registration():
    """Test agent registration."""
    print("Testing agent registration...")
    
    marketplace = MarketplaceRegistry()
    
    # Register Agent A
    profile_a = AgentProfile(
        agent_address="agent1test123",
        agent_name="TestAgentA",
        agent_type="provider",
    )
    
    result = marketplace.register_agent(profile_a)
    assert result == True, "Agent registration should succeed"
    
    # Try to register same agent again
    result = marketplace.register_agent(profile_a)
    assert result == False, "Duplicate registration should fail"
    
    # Verify agent is registered
    retrieved = marketplace.get_agent_profile("agent1test123")
    assert retrieved is not None, "Agent should be retrievable"
    assert retrieved.agent_name == "TestAgentA", "Agent name should match"
    
    print("✓ Agent registration tests passed")
    return True


def test_service_registration():
    """Test service registration."""
    print("\nTesting service registration...")
    
    marketplace = MarketplaceRegistry()
    
    # Register an agent first
    profile = AgentProfile(
        agent_address="agent1provider",
        agent_name="ProviderAgent",
        agent_type="provider",
    )
    marketplace.register_agent(profile)
    
    # Register a service
    service = ServiceListing(
        service_id="test_service_001",
        service_name="Test Service",
        description="A test service",
        price_sol=0.1,
        provider_address="agent1provider",
        provider_name="ProviderAgent",
        category="Testing",
    )
    
    result = marketplace.register_service(service)
    assert result == True, "Service registration should succeed"
    
    # Verify service is registered
    retrieved = marketplace.get_service("test_service_001")
    assert retrieved is not None, "Service should be retrievable"
    assert retrieved.service_name == "Test Service", "Service name should match"
    
    # Verify agent's services list is updated
    agent = marketplace.get_agent_profile("agent1provider")
    assert "test_service_001" in agent.services_offered, "Service should be in agent's list"
    
    print("✓ Service registration tests passed")
    return True


def test_service_search():
    """Test service search functionality."""
    print("\nTesting service search...")
    
    marketplace = MarketplaceRegistry()
    
    # Register agent
    profile = AgentProfile(
        agent_address="agent1search",
        agent_name="SearchAgent",
        agent_type="provider",
    )
    marketplace.register_agent(profile)
    
    # Register multiple services
    services = [
        ServiceListing(
            service_id="search_001",
            service_name="Cheap Service",
            description="Low price service",
            price_sol=0.05,
            provider_address="agent1search",
            provider_name="SearchAgent",
            category="Budget",
        ),
        ServiceListing(
            service_id="search_002",
            service_name="Premium Service",
            description="High price service",
            price_sol=0.5,
            provider_address="agent1search",
            provider_name="SearchAgent",
            category="Premium",
        ),
        ServiceListing(
            service_id="search_003",
            service_name="Mid Service",
            description="Medium price service",
            price_sol=0.2,
            provider_address="agent1search",
            provider_name="SearchAgent",
            category="Budget",
        ),
    ]
    
    for service in services:
        marketplace.register_service(service)
    
    # Test search by category
    results = marketplace.search_services(category="Budget")
    assert len(results) == 2, "Should find 2 budget services"
    
    # Test search by max price
    results = marketplace.search_services(max_price=0.1)
    assert len(results) == 1, "Should find 1 service under 0.1 SOL"
    
    # Test search by category and price
    results = marketplace.search_services(category="Budget", max_price=0.1)
    assert len(results) == 1, "Should find 1 budget service under 0.1 SOL"
    
    print("✓ Service search tests passed")
    return True


def test_marketplace_stats():
    """Test marketplace statistics."""
    print("\nTesting marketplace statistics...")
    
    marketplace = MarketplaceRegistry()
    
    # Register 2 agents
    for i in range(2):
        profile = AgentProfile(
            agent_address=f"agent1stats{i}",
            agent_name=f"StatsAgent{i}",
            agent_type="provider",
        )
        marketplace.register_agent(profile)
    
    # Register 3 services
    for i in range(3):
        service = ServiceListing(
            service_id=f"stats_service_{i}",
            service_name=f"Stats Service {i}",
            description="Test service",
            price_sol=0.1,
            provider_address="agent1stats0",
            provider_name="StatsAgent0",
            category="Testing",
        )
        marketplace.register_service(service)
    
    stats = marketplace.get_stats()
    assert stats['total_agents'] == 2, "Should have 2 agents"
    assert stats['total_services'] == 3, "Should have 3 services"
    assert stats['active_services'] == 3, "Should have 3 active services"
    
    print("✓ Marketplace statistics tests passed")
    return True


def test_transaction_tracking():
    """Test transaction count tracking."""
    print("\nTesting transaction tracking...")
    
    marketplace = MarketplaceRegistry()
    
    # Register agent
    profile = AgentProfile(
        agent_address="agent1tx",
        agent_name="TxAgent",
        agent_type="provider",
    )
    marketplace.register_agent(profile)
    
    # Increment transaction count
    result = marketplace.increment_transaction_count("agent1tx")
    assert result == True, "Transaction increment should succeed"
    
    # Verify count
    agent = marketplace.get_agent_profile("agent1tx")
    assert agent.total_transactions == 1, "Transaction count should be 1"
    
    # Increment again
    marketplace.increment_transaction_count("agent1tx")
    agent = marketplace.get_agent_profile("agent1tx")
    assert agent.total_transactions == 2, "Transaction count should be 2"
    
    print("✓ Transaction tracking tests passed")
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print(" " * 15 + "MARKETPLACE FUNCTIONALITY TESTS")
    print("=" * 70)
    
    tests = [
        test_agent_registration,
        test_service_registration,
        test_service_search,
        test_marketplace_stats,
        test_transaction_tracking,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            results.append(False)
        except Exception as e:
            print(f"✗ Test error: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All marketplace tests passed!")
    else:
        print("✗ Some tests failed.")
    
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
