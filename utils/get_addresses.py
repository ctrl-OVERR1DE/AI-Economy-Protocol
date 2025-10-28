"""
Utility script to get agent addresses without running the full agents.
This helps configure Agent B with Agent A's address.
"""

from uagents import Agent

# Create temporary agents with same seeds to get addresses
agent_a = Agent(
    name="DataAnalystAgent",
    seed="data_analyst_seed_phrase_12345",
    port=8000,
)

agent_b = Agent(
    name="ClientAgent",
    seed="client_agent_seed_phrase_67890",
    port=8001,
)

print("=" * 60)
print("AI ECONOMY PROTOCOL - AGENT ADDRESSES")
print("=" * 60)
print(f"\nAgent A (DataAnalystAgent):")
print(f"  Address: {agent_a.address}")
print(f"  Name: {agent_a.name}")
print(f"\nAgent B (ClientAgent):")
print(f"  Address: {agent_b.address}")
print(f"  Name: {agent_b.name}")
print("\n" + "=" * 60)
print("\nNext Steps:")
print("1. Copy Agent A's address")
print("2. Update AGENT_A_ADDRESS in agents/agent_b.py")
print("3. Run both agents in separate terminals")
print("=" * 60)
