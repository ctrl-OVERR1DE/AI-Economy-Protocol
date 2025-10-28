"""
Test script to verify agent communication setup.
This script checks if agents can be imported and initialized correctly.
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test if all required imports work."""
    print("Testing imports...")
    try:
        from uagents import Agent, Context, Protocol
        from uagents_core.contrib.protocols.chat import (
            ChatAcknowledgement,
            ChatMessage,
            EndSessionContent,
            StartSessionContent,
            TextContent,
            chat_protocol_spec,
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_agent_creation():
    """Test if agents can be created."""
    print("\nTesting agent creation...")
    try:
        from uagents import Agent
        
        # Create test agents
        test_agent_a = Agent(
            name="TestAgentA",
            seed="test_seed_a",
            port=9000,
        )
        
        test_agent_b = Agent(
            name="TestAgentB",
            seed="test_seed_b",
            port=9001,
        )
        
        print(f"✓ Agent A created: {test_agent_a.address}")
        print(f"✓ Agent B created: {test_agent_b.address}")
        return True
    except Exception as e:
        print(f"✗ Agent creation failed: {e}")
        return False


def test_chat_protocol():
    """Test if chat protocol can be initialized."""
    print("\nTesting chat protocol...")
    try:
        from uagents import Protocol
        from uagents_core.contrib.protocols.chat import chat_protocol_spec
        
        chat_proto = Protocol(spec=chat_protocol_spec)
        print("✓ Chat protocol initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Chat protocol initialization failed: {e}")
        return False


def test_message_creation():
    """Test if chat messages can be created."""
    print("\nTesting message creation...")
    try:
        from datetime import datetime
        from uuid import uuid4
        from uagents_core.contrib.protocols.chat import (
            ChatMessage,
            TextContent,
        )
        
        # Create a test message
        content = [TextContent(type="text", text="Test message")]
        msg = ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=content,
        )
        
        print(f"✓ Message created with ID: {msg.msg_id}")
        return True
    except Exception as e:
        print(f"✗ Message creation failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("AI ECONOMY PROTOCOL - AGENT COMMUNICATION TESTS")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_agent_creation,
        test_chat_protocol,
        test_message_creation,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Agents are ready to run.")
        print("\nNext steps:")
        print("1. Run Agent A: python agents/agent_a.py")
        print("2. Run Agent B: python agents/agent_b.py")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
