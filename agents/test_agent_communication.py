"""
Simple test to verify agent communication and payment flow.
Agent B directly messages Agent A to request a service.
"""
import asyncio
from uagents import Agent, Context
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    TextContent,
)

# Agent addresses (from your running agents)
AGENT_A_ADDRESS = "agent1qwd63x7vsupc3swvmmc8hekr6fwfryvvqs360hjuh3ztxlnze6kcukjexf7"
AGENT_B_ADDRESS = "agent1qdkv6m4z9qgllndchyzpppqkv3zf285q4r22r7h6lthwc90n9236x5jnvj4"


async def send_test_message():
    """Send a test message from Agent B to Agent A."""
    # Create a simple agent for sending
    test_agent = Agent(
        name="TestSender",
        seed="test_sender_seed_123",
        port=8002,
    )
    
    @test_agent.on_event("startup")
    async def startup(ctx: Context):
        ctx.logger.info("Test agent started")
        ctx.logger.info(f"Sending test message to Agent A: {AGENT_A_ADDRESS}")
        
        # Create a chat message
        message = ChatMessage(
            type="agent_chat_message",
            session_id="test_session_001",
            content=[
                TextContent(
                    type="text",
                    text="Hello Agent A! I need data analysis services. What's your pricing?"
                )
            ],
        )
        
        try:
            await ctx.send(AGENT_A_ADDRESS, message)
            ctx.logger.info("✓ Message sent successfully!")
        except Exception as e:
            ctx.logger.error(f"Failed to send message: {e}")
        
        # Wait a bit for response
        await asyncio.sleep(5)
        ctx.logger.info("Test complete. Check Agent A's terminal for the message.")
    
    test_agent.run()


if __name__ == "__main__":
    print("="*80)
    print("  AGENT COMMUNICATION TEST")
    print("="*80)
    print()
    print("This will send a test message from a test agent to Agent A.")
    print("Make sure Agent A is running on port 8000.")
    print()
    print(f"Agent A address: {AGENT_A_ADDRESS}")
    print()
    print("Starting test...")
    print("="*80)
    print()
    
    asyncio.run(send_test_message())
