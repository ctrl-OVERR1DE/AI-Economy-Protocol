"""
Agent B with x402 HTTP Client Integration

This extends Agent B (Client) with x402 HTTP client capabilities.
Agent B can now:
1. Use uAgents Chat Protocol (existing)
2. Make HTTP requests with x402 payment (new)

When Agent B needs data analysis from Agent A, it uses the x402 HTTP client
to automatically handle payment and receive results.
"""

import sys
import os
import asyncio

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import uAgents
from uagents import Agent, Protocol

# Create Agent B instance (separate from agent_b.py to avoid conflicts)
agent = Agent(
    name="ClientAgent",
    seed="client_agent_seed_phrase_67890",
    port=5050,
    endpoint=["http://127.0.0.1:5050/submit"],
)

# Create chat protocol
chat_proto = Protocol(name="AgentChatProtocol")

# Agent A's address
AGENT_A_ADDRESS = "agent1qwd63x7vsupc3swvmmc8hekr6fwfryvvqs360hjuh3ztxlnze6kcukjexf7"

# Import x402 client
from agents.x402.client import X402Client
from agents.utils.solana_utils import load_agent_wallet

# Configuration
AGENT_A_HTTP_URL = "http://localhost:8001"

# Load Agent B's wallet
CLIENT_WALLET = load_agent_wallet("ClientAgent")
CLIENT_PUBLIC_KEY = str(CLIENT_WALLET.pubkey())

# Initialize x402 client
x402_client = X402Client(wallet_keypair=CLIENT_WALLET, agent_name="ClientAgent")

print(f"Agent B x402 HTTP Client")
print(f"Client: {CLIENT_PUBLIC_KEY}")


async def request_analysis_via_x402(data: str):
    """
    Request data analysis from Agent A via x402 HTTP.
    
    This demonstrates autonomous agent-to-agent payment using x402 protocol.
    
    Args:
        data: Data to analyze
    
    Returns:
        Tuple of (success, result_or_error)
    """
    print("\n" + "="*70)
    print("🤖 Agent B → Agent A: x402 Payment Flow")
    print("="*70)
    print(f"📊 Requesting analysis: {data}")
    
    try:
        status, response = await x402_client.get_with_payment(
            url=f"{AGENT_A_HTTP_URL}/analyze",
            params={"data": data}
        )
        
        if status == 200:
            print("\n✅ Analysis received successfully!")
            result = response.get('result', {})
            payment_details = response.get('paymentDetails', {})
            
            print(f"\n📊 Analysis Result:")
            for key, value in result.items():
                print(f"   {key}: {value}")
            
            print(f"\n💸 Payment Details:")
            print(f"   Escrow PDA: {payment_details.get('escrowPDA')}")
            print(f"   Amount Paid: {payment_details.get('amountPaid')} SOL")
            
            print("\n" + "="*70)
            return True, result
        else:
            print(f"\n❌ Request failed with status {status}")
            print(f"Response: {response}")
            print("\n" + "="*70)
            return False, response
            
    except Exception as e:
        print(f"\n❌ Error during x402 request: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*70)
        return False, str(e)


async def demo_x402_flow():
    """
    Demonstrate Agent B using x402 to request service from Agent A.
    
    This runs automatically when Agent B starts, showing the autonomous
    agent-to-agent payment flow.
    """
    print("\n" + "="*70)
    print("🎬 Starting x402 Demo Flow")
    print("="*70)
    print("Agent B will request data analysis from Agent A")
    print("Payment will be handled automatically via x402 + escrow")
    print("="*70)
    
    # Wait a moment for Agent A to be ready
    await asyncio.sleep(2)
    
    # Request analysis
    success, result = await request_analysis_via_x402(
        "Q4 2024 sales data - autonomous agent request"
    )
    
    if success:
        print("\n✅ x402 Demo Complete - Payment and Service Successful!")
    else:
        print("\n❌ x402 Demo Failed - Check logs above")
    
    print("\n" + "="*70)
    print("Agent B continues running...")
    print("You can trigger more requests via chat or HTTP")
    print("="*70)


if __name__ == "__main__":
    # Include the chat protocol
    agent.include(chat_proto)
    
    print("\n" + "="*70)
    print("🤖 Agent B (ClientAgent) - x402 Enabled")
    print("="*70)
    print(f"📡 uAgents Chat Protocol: Port 5050")
    print(f"🌐 x402 HTTP Client: Ready")
    print(f"🏦 Solana Wallet: {CLIENT_PUBLIC_KEY}")
    print(f"🎯 Target: Agent A at {AGENT_A_HTTP_URL}")
    print("="*70)
    print("\nAgent B is ready to:")
    print("  1. Accept chat messages from other agents (uAgents)")
    print("  2. Make x402-protected HTTP requests to Agent A")
    print("\nPress Ctrl+C to stop")
    print("="*70)
    print()
    
    # Schedule the demo to run after agent starts
    @agent.on_event("startup")
    async def startup(ctx):
        """Run x402 demo on startup."""
        await demo_x402_flow()
    
    # Run the uAgents agent
    agent.run()
