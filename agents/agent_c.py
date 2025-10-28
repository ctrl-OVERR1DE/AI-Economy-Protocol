"""
Agent C: Client Agent (Third Client)
Demonstrates multi-client scalability - requests services concurrently with Agent B.
"""

import sys
import os
import asyncio
from datetime import datetime
from uuid import uuid4

# Add parent directory to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
agents_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, agents_dir)

from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
)
# Import from project root utils
import sys
sys.path.insert(0, os.path.join(project_root, 'utils'))
from marketplace import marketplace, AgentProfile

# Import from agents utils
from utils.solana_utils import (
    load_agent_wallet,
    initialize_escrow_for_service,
    sol_to_lamports,
    release_payment_from_escrow,
)


# Module-level flag to ensure we only request a service once per agent run
SERVICE_REQUESTED = False


# Initialize Agent C - Client (Local Mode)
agent = Agent(
    name="ClientAgentC",
    seed="client_agent_c_seed_2025",  # Unique seed for Agent C
    port=5049,
    endpoint=["http://127.0.0.1:5049/submit"],  # Local endpoint for direct communication
)

# Fund agent if low on testnet tokens (disabled - using Solana for payments)
# fund_agent_if_low(agent.wallet.address())

# Initialize the chat protocol
chat_proto = Protocol(name="AgentChatProtocol")

# Agent A's address
AGENT_A_ADDRESS = "agent1qwd63x7vsupc3swvmmc8hekr6fwfryvvqs360hjuh3ztxlnze6kcukjexf7"


# Utility function to wrap plain text into a ChatMessage
def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    """Create a ChatMessage with text content."""
    content = [TextContent(type="text", text=text)]
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )


# Utility function to start a session
def create_start_session() -> ChatMessage:
    """Create a ChatMessage to start a session."""
    content = [StartSessionContent(type="start-session")]
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )


# Utility function to end a session
def create_end_session() -> ChatMessage:
    """Create a ChatMessage to end a session."""
    content = [EndSessionContent(type="end-session")]
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )


# Handle incoming chat messages
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages from other agents."""
    ctx.logger.info(f"Received message from {sender}")
    
    # Always send back an acknowledgement when a message is received
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.utcnow(),
            acknowledged_msg_id=msg.msg_id
        )
    )

    # Process each content item inside the chat message
    for item in msg.content:
        # Marks the start of a chat session
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Session started with {sender}")
        
        # Handles plain text messages (from another agent or ASI:One)
        elif isinstance(item, TextContent):
            ctx.logger.info(f"Text message from {sender}: {item.text}")
            
            # Client logic - respond to service provider
            response_text = item.text.lower()
            
            if "welcome" in response_text or "what service" in response_text:
                # Request data analysis service
                request_msg = create_text_chat(
                    "I need data analysis for my dataset. "
                    "Can you provide pricing information?"
                )
                await ctx.send(sender, request_msg)
            
            elif "service fee" in response_text or "0.1 sol" in response_text:
                # Check if escrow already initialized
                if ctx.storage.get("escrow_initialized"):
                    ctx.logger.info("Escrow already initialized, skipping...")
                    return
                
                # Initialize escrow before confirming service
                ctx.logger.info("Initializing escrow for service payment...")
                
                try:
                    # Load client's Solana wallet
                    client_wallet = load_agent_wallet("ClientAgent")
                    ctx.logger.info(f"Client wallet loaded: {client_wallet.pubkey()}")
                    
                    # Get provider's Solana address from storage (set during service discovery)
                    # For now, use a placeholder - in production, map agent address to Solana address
                    provider_solana_address = ctx.storage.get("provider_solana_address")
                    if not provider_solana_address:
                        # Fallback: use env var for testing
                        provider_solana_address = os.getenv("PROVIDER_PUBLIC_KEY")
                    
                    if not provider_solana_address:
                        ctx.logger.error("Provider Solana address not found")
                        error_msg = create_text_chat(
                            "Error: Unable to initialize payment escrow. Provider address not configured."
                        )
                        await ctx.send(sender, error_msg)
                        return
                    
                    # Initialize escrow with unique service_id for each transaction
                    import time, secrets
                    # High-entropy service_id to avoid any collision across quick reruns
                    service_id = f"data_analysis_{int(time.time()*1000)}_{secrets.token_hex(4)}"
                    # Include service_id in task_data so task_hash (and PDA) is unique per run
                    task_data = f"Analyze sales data for Q4 2024 | sid={service_id}"
                    amount_sol = 0.1
                    
                    signature, escrow_pda = await initialize_escrow_for_service(
                        client_wallet=client_wallet,
                        provider_address=provider_solana_address,
                        service_id=service_id,
                        task_data=task_data,
                        amount_lamports=sol_to_lamports(amount_sol),
                        agent_name="ClientAgent",
                    )
                    
                    # Check if escrow was reused
                    if signature == "ESCROW_ALREADY_EXISTS":
                        ctx.logger.info(f"♻️  Reusing existing escrow!")
                        ctx.logger.info(f"   Escrow PDA: {escrow_pda}")
                        ctx.logger.info(f"   No transaction needed - escrow already active")
                    else:
                        ctx.logger.info(f"✅ Escrow initialized!")
                        ctx.logger.info(f"   Transaction: {signature}")
                        ctx.logger.info(f"   Escrow PDA: {escrow_pda}")
                        ctx.logger.info(f"   Amount locked: {amount_sol} SOL")
                    
                    # Store escrow info and mark as initialized
                    ctx.storage.set("escrow_signature", signature)
                    ctx.storage.set("escrow_pda", str(escrow_pda))
                    ctx.storage.set("service_id", service_id)  # Store for release later
                    ctx.storage.set("escrow_initialized", True)
                    ctx.storage.set("provider_sender", sender)  # Store for payment release
                    
                    # Confirm the service with escrow details
                    confirm_msg = create_text_chat(
                        f"Yes, I confirm. Payment of {amount_sol} SOL has been locked in escrow. "
                        f"Escrow PDA: {escrow_pda}. "
                        f"Please proceed with the data analysis."
                    )
                    await ctx.send(sender, confirm_msg)
                    
                    # Schedule payment release check after 10 seconds (time for proof submission)
                    ctx.storage.set("payment_release_scheduled", True)
                    
                except Exception as e:
                    ctx.logger.error(f"Failed to initialize escrow: {e}")
                    error_msg = create_text_chat(
                        f"Error initializing payment escrow: {str(e)}. Please try again."
                    )
                    await ctx.send(sender, error_msg)
            
            elif "analysis complete" in response_text and "proof" in response_text:
                # Service completed - release payment from escrow
                ctx.logger.info("Service completed! Releasing payment from escrow...")
                
                try:
                    # Load client wallet
                    client_wallet = load_agent_wallet("ClientAgent")
                    
                    # Get provider's Solana address and escrow_pda
                    provider_solana_address = ctx.storage.get("provider_solana_address")
                    if not provider_solana_address:
                        provider_solana_address = os.getenv("PROVIDER_PUBLIC_KEY")
                    escrow_pda = ctx.storage.get("escrow_pda")
                    if not escrow_pda:
                        ctx.logger.error("escrow_pda not found in storage")
                        return
                    
                    if provider_solana_address:
                        # Import the release function
                        from utils.solana_utils import release_payment_from_escrow
                        
                        # Release payment to provider with explicit escrow_pda
                        release_signature = await release_payment_from_escrow(
                            client_wallet=client_wallet,
                            provider_address=provider_solana_address,
                            escrow_pda=escrow_pda,
                            agent_name="ClientAgent",
                        )
                        
                        ctx.logger.info(f"✅ Payment released!")
                        ctx.logger.info(f"   Transaction: {release_signature}")
                        
                        # Send confirmation
                        thanks_msg = create_text_chat(
                            f"Thank you for the analysis! Payment of 0.1 SOL has been released. "
                            f"Release transaction: {release_signature[:16]}..."
                        )
                        await ctx.send(sender, thanks_msg)
                    else:
                        ctx.logger.warning("Provider address not found, skipping payment release")
                        thanks_msg = create_text_chat(
                            "Thank you for the analysis! The insights are very helpful."
                        )
                        await ctx.send(sender, thanks_msg)
                
                except Exception as e:
                    ctx.logger.error(f"Failed to release payment: {e}")
                    error_msg = create_text_chat(
                        "Analysis received, but payment release encountered an error. "
                        "Please contact support."
                    )
                    await ctx.send(sender, error_msg)
                
                # End the session
                ctx.logger.info("Service completed. Ending session.")

        # Marks the end of a chat session
        elif isinstance(item, EndSessionContent):
            ctx.logger.info(f"Session ended with {sender}")
        
        # Catches anything unexpected
        else:
            ctx.logger.info(f"Received unexpected content type from {sender}")


# Handle acknowledgements for messages this agent has sent out
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle acknowledgements from other agents."""
    ctx.logger.info(
        f"Received acknowledgement from {sender} for message {msg.acknowledged_msg_id}"
    )


# Periodic task to check and release payment (runs every 10 seconds)
@agent.on_interval(period=10.0)
async def check_and_release_payment(ctx: Context):
    """Check if payment should be released and release it."""
    if not ctx.storage.get("payment_release_scheduled"):
        return
    
    if ctx.storage.get("payment_released"):
        return  # Already released
    
    ctx.logger.info("⏰ Auto-releasing payment after proof submission...")
    
    try:
        # Load client wallet
        client_wallet = load_agent_wallet("ClientAgent")
        
        # Get provider's Solana address and escrow_pda
        provider_solana_address = ctx.storage.get("provider_solana_address")
        if not provider_solana_address:
            provider_solana_address = os.getenv("PROVIDER_PUBLIC_KEY")
        
        escrow_pda = ctx.storage.get("escrow_pda")
        if not escrow_pda:
            ctx.logger.error("escrow_pda not found in storage")
            return
        
        if provider_solana_address:
            # Release payment to provider
            release_signature = await release_payment_from_escrow(
                client_wallet=client_wallet,
                provider_address=provider_solana_address,
                escrow_pda=escrow_pda,
                agent_name="ClientAgent",
            )
            
            ctx.logger.info(f"✅ Payment released!")
            ctx.logger.info(f"   Transaction: {release_signature}")
            ctx.storage.set("payment_released", True)
            ctx.storage.set("payment_release_scheduled", False)
        else:
            ctx.logger.warning("Provider address not found")
    
    except Exception as e:
        ctx.logger.error(f"Failed to auto-release payment: {e}")


# Periodic task to discover and request services (runs every 5 seconds)
@agent.on_interval(period=5.0)
async def discover_and_request_service(ctx: Context):
    """Discover available services and request one."""
    # Only run once to avoid spam
    global SERVICE_REQUESTED
    if SERVICE_REQUESTED or ctx.storage.get("service_requested"):
        return
    ctx.logger.info("Discovering available services in marketplace...")
    # Search for data analysis services
    services = marketplace.search_services(category="Data Processing", max_price=0.15)
    if services:
        ctx.logger.info(f"Found {len(services)} available services:")
        for service in services:
            ctx.logger.info(
                f"  - {service.service_name}: {service.price_sol} SOL "
                f"(Provider: {service.provider_name})"
            )
            
            # Select the first service (in production, this would be more sophisticated)
            selected_service = services[0]
            ctx.logger.info(f"Selected service: {selected_service.service_name}")
            
            # Get provider address
            provider_address = selected_service.provider_address
            ctx.logger.info(f"Initiating service request to: {provider_address}")
            
            # Start a session with the provider
            start_msg = create_start_session()
            await ctx.send(provider_address, start_msg)
            
            # Mark as requested
            ctx.storage.set("service_requested", True)
            ctx.storage.set("selected_service", selected_service.service_id)
            SERVICE_REQUESTED = True
    else:
        ctx.logger.info("No services found in marketplace yet.")
        ctx.logger.info("Directly contacting Agent A (hardcoded address)...")
        
        # Directly contact Agent A using hardcoded address
        ctx.logger.info(f"Initiating service request to Agent A: {AGENT_A_ADDRESS}")
        
        # Start a session with Agent A, then send the greeting after a short delay
        start_msg = create_start_session()
        await ctx.send(AGENT_A_ADDRESS, start_msg)
        # Give Agent A a moment to register the session
        await asyncio.sleep(0.3)
        request_msg = create_text_chat("Hello! I need data analysis services. What's your pricing?")
        await ctx.send(AGENT_A_ADDRESS, request_msg)
        
        # Mark as requested
        ctx.storage.set("service_requested", True)
        ctx.storage.set("selected_service", "data_analysis_001")
        SERVICE_REQUESTED = True


# Startup event - Register as client in marketplace
@agent.on_event("startup")
async def startup(ctx: Context):
    """Log agent information on startup and register in marketplace."""
    ctx.logger.info(f"Agent C (ClientAgentC) started")
    ctx.logger.info(f"Agent address: {agent.address}")
    ctx.logger.info(f"Agent name: {agent.name}")
    ctx.logger.info(f"Listening on port: 5049")
    
    # Register agent profile in marketplace
    profile = AgentProfile(
        agent_address=agent.address,
        agent_name=agent.name,
        agent_type="client",
    )
    
    if marketplace.register_agent(profile):
        ctx.logger.info("✓ Agent registered in marketplace as client")
    else:
        ctx.logger.info("Agent already registered in marketplace")
    
    # Display marketplace stats
    stats = marketplace.get_stats()
    ctx.logger.info(f"Marketplace stats: {stats}")
    ctx.logger.info("Ready to discover and request services!")
    
    # Reset flags to ensure discovery runs on this startup
    global SERVICE_REQUESTED
    SERVICE_REQUESTED = False
    ctx.storage.set("service_requested", False)
    ctx.storage.set("escrow_initialized", False)
    
    # Trigger immediate service discovery instead of waiting 5 seconds
    await discover_and_request_service(ctx)


# Include the chat protocol and publish the manifest to Agentverse
agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__":
    agent.run()
