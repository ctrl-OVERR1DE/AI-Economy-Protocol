"""
Agent B: Client Agent (Service Consumer)

This agent requests and consumes services from other agents in the AI Economy Protocol.
It demonstrates autonomous service discovery, negotiation, and payment execution.

Key Features:
- Discovers available services in marketplace
- Negotiates pricing with service providers
- Locks payments in escrow via Sanctum Gateway
- Releases payments after service completion

Payment Flow:
1. Discover services (marketplace or direct contact)
2. Request service and receive pricing quote
3. Initialize escrow with payment lock (via Gateway)
4. Wait for provider to complete task
5. Release payment from escrow (via Gateway)

Technical Stack:
- uAgents framework for agent communication
- Solana blockchain for payment settlement
- Anchor smart contracts for escrow management
- Sanctum Gateway for transaction optimization

Port: 5050
Address: agent1qdkv6m4z9qgllndchyzpppqkv3zf285q4r22r7h6lthwc90n9236x5jnvj4
Budget: 1000 Tokens (~$1000 for services)
"""

import sys
import os
import asyncio
import logging
import requests
from datetime import datetime
from uuid import uuid4

# Suppress verbose logs for demo
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# Import AI client for intelligent decision-making
from agents.ai.gemini_client import GeminiClient


# Module-level flag to ensure we only request a service once per agent run
SERVICE_REQUESTED = False


# Initialize Agent B - Client (Local Mode)
agent = Agent(
    name="ClientAgent",
    seed="client_agent_seed_phrase_67890",  # Use consistent seed for same address
    port=5050,
    endpoint=["http://127.0.0.1:5050/submit"],  # Local endpoint for direct communication
)

# Fund agent if low on testnet tokens (disabled - using Solana for payments)
# fund_agent_if_low(agent.wallet.address())

# Initialize the chat protocol
chat_proto = Protocol(name="AgentChatProtocol")

# Initialize AI client for intelligent decision-making
gemini_client = GeminiClient()

# Provider agent addresses (specialized agents)
PROVIDER_AGENTS = {
    "ContentAnalyst": "agent1qfr4dqkv7p9jlh8wvqxwqz6z0z8z0z8z0z8z0z8z0z8z0z8z0z8z0z8qyqyqy",  # Will be updated on first run
    "CodeReview": "agent1qw6f033x0pmyjks3wlwd2akfpnc8nrvem77z89f0k46n23r54e73wqx6kap",  # From your output
    "Translator": "agent1qfr4dqkv7p9jlh8wvqxwqz6z0z8z0z8z0z8z0z8z0z8z0z8z0z8z0z8qyqyqy",  # Will be updated on first run
}

# Service descriptions for AI decision-making
SERVICE_CATALOG = {
    "CodeReview": {
        "name": "Code Review Service",
        "description": "AI-powered code analysis with quality scoring, security checks, and best practices",
        "typical_use": "Review code for bugs, security issues, and improvements",
        "base_price": 8,  # Tokens (~$8 - complex AI analysis)
    },
    "ContentAnalyst": {
        "name": "Content Analysis Service",
        "description": "AI-powered content analysis with sentiment, readability, and insights",
        "typical_use": "Analyze articles, documents, or text for insights",
        "base_price": 5,  # Tokens (~$5 - medium complexity)
    },
    "Translator": {
        "name": "Translation Service",
        "description": "AI-powered translation with context preservation and cultural adaptation",
        "typical_use": "Translate text between languages with high accuracy",
        "base_price": 3,  # Tokens (~$3 - simpler task)
    },
}

# Legacy Agent A address (for backwards compatibility)
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


async def ai_select_service(ctx: Context) -> dict:
    """Use AI to intelligently select which service to request."""
    try:
        # Create prompt for AI decision
        prompt = f"""You are an intelligent agent deciding which service to request.

Available Services:
{chr(10).join(f"- {name}: {info['description']}" for name, info in SERVICE_CATALOG.items())}

Current Scenario: You need to test the AI agent marketplace by requesting a service.

Task: Select ONE service that would be most interesting to demonstrate for a hackathon.
Consider: Code Review would show real AI analysis of code quality and security.

Respond in JSON format:
{{
    "selected_service": "ServiceName",
    "reason": "Brief reason for selection",
    "test_input": "Sample input to test the service"
}}"""

        response = await gemini_client.generate_content(prompt)
        
        # Parse JSON response
        import json
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            decision = json.loads(json_match.group())
            ctx.logger.info(f"🤖 AI Decision: {decision['selected_service']}")
            ctx.logger.info(f"   Reason: {decision['reason']}")
            return decision
        else:
            # Fallback to CodeReview
            return {
                "selected_service": "CodeReview",
                "reason": "Default selection for demo",
                "test_input": "Sample code for review"
            }
    except Exception as e:
        ctx.logger.warning(f"AI selection failed: {e}, using default")
        return {
            "selected_service": "CodeReview",
            "reason": "Fallback selection",
            "test_input": "Sample code for review"
        }


# Handle incoming chat messages
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages from other agents."""
    # Received message
    
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
            pass  # Session started
        
        # Handles plain text messages (from another agent or ASI:One)
        elif isinstance(item, TextContent):
            # Always log provider messages for transparency
            ctx.logger.info(f"💬 Provider: {item.text[:100]}{'...' if len(item.text) > 100 else ''}")
            
            # Client logic - respond to service provider
            response_text = item.text.lower()
            
            if "welcome" in response_text or "what service" in response_text or "what code" in response_text:
                # Provider introduced themselves - request service details
                selected_service = ctx.storage.get("selected_service_name") or "CodeReview"
                
                if "code" in response_text.lower():
                    ctx.logger.info("💬 Client: Requesting code review service details")
                    request_msg = create_text_chat(
                        "I need code review services. What's your pricing and capabilities?"
                    )
                else:
                    ctx.logger.info("💬 Client: Requesting service details")
                    request_msg = create_text_chat(
                        "I need your services. What's your pricing?"
                    )
                await ctx.send(sender, request_msg)
            
            elif ("base price" in response_text or "service fee" in response_text) and ("token" in response_text or "pricing" in response_text):
                # Check if escrow already initialized
                if ctx.storage.get("escrow_initialized"):
                    # Escrow already initialized
                    return
                
                # Extract price from message (look for "8 Tokens" pattern)
                import re
                price_match = re.search(r'(\d+\.?\d*)\s*tokens?', response_text, re.IGNORECASE)
                quoted_price = float(price_match.group(1)) if price_match else 8
                
                # Initialize escrow before confirming service
                ctx.logger.info(f"💬 Provider quoted {quoted_price} Tokens for service")
                ctx.logger.info("🔒 Initializing escrow for service payment...")
                
                try:
                    # Load client's Solana wallet
                    client_wallet = load_agent_wallet("ClientAgent")
                    # Client wallet loaded
                    
                    # Get provider's Solana address from storage (set during service discovery)
                    # For now, use a placeholder - in production, map agent address to Solana address
                    provider_solana_address = ctx.storage.get("provider_solana_address")
                    ctx.logger.info(f"🔍 Retrieved provider Solana address from storage: {provider_solana_address}")
                    
                    if not provider_solana_address:
                        # Fallback: use env var for testing
                        provider_solana_address = os.getenv("PROVIDER_PUBLIC_KEY")
                        ctx.logger.info(f"🔍 Fallback to env var: {provider_solana_address}")
                    
                    if not provider_solana_address:
                        ctx.logger.error("Provider Solana address not found")
                        ctx.logger.error("Storage keys: " + str(list(ctx.storage._data.keys()) if hasattr(ctx.storage, '_data') else "N/A"))
                        error_msg = create_text_chat(
                            "Error: Unable to initialize payment escrow. Provider address not configured."
                        )
                        await ctx.send(sender, error_msg)
                        return
                    
                    # Initialize escrow with unique service_id for each transaction
                    import time, secrets
                    selected_service = ctx.storage.get("selected_service_name") or "CodeReview"
                    
                    # High-entropy service_id to avoid any collision across quick reruns
                    service_id = f"{selected_service.lower()}_{int(time.time()*1000)}_{secrets.token_hex(4)}"
                    
                    # Service-specific task data
                    if selected_service == "CodeReview":
                        task_data = f"Review Python code for quality and security | sid={service_id}"
                    elif selected_service == "ContentAnalyst":
                        task_data = f"Analyze content for insights | sid={service_id}"
                    elif selected_service == "Translator":
                        task_data = f"Translate text to target language | sid={service_id}"
                    else:
                        task_data = f"Service request | sid={service_id}"
                    
                    amount_sol = quoted_price
                    
                    # Import token conversion function
                    from agents.utils.solana_utils import tokens_to_smallest_unit
                    
                    signature, escrow_pda = await initialize_escrow_for_service(
                        client_wallet=client_wallet,
                        provider_address=provider_solana_address,
                        service_id=service_id,
                        task_data=task_data,
                        amount_lamports=tokens_to_smallest_unit(amount_sol, decimals=6),  # SPL tokens have 6 decimals
                        agent_name="ClientAgent",
                    )
                    
                    # Check if escrow was reused
                    if signature == "ESCROW_ALREADY_EXISTS":
                        ctx.logger.info(f"♻️  Reusing existing escrow: {escrow_pda}")
                    else:
                        ctx.logger.info(f"✅ Escrow initialized!")
                        ctx.logger.info(f"   Transaction: {signature}")
                        ctx.logger.info(f"   Escrow PDA: {escrow_pda}")
                        ctx.logger.info(f"   Amount locked: {amount_sol} Tokens")
                    
                    # Store escrow info and mark as initialized
                    ctx.storage.set("escrow_signature", signature)
                    ctx.storage.set("escrow_pda", str(escrow_pda))
                    ctx.storage.set("service_id", service_id)  # Store for release later
                    ctx.storage.set("escrow_initialized", True)
                    ctx.storage.set("provider_sender", sender)  # Store for payment release
                    
                    # Confirm the service with escrow details
                    service_action = {
                        "CodeReview": "code review",
                        "ContentAnalyst": "content analysis",
                        "Translator": "translation"
                    }.get(selected_service, "service")
                    
                    ctx.logger.info(f"💬 Client: Confirming escrow and requesting {service_action}")
                    confirm_msg = create_text_chat(
                        f"Yes, I confirm. Payment of {amount_sol} SOL has been locked in escrow. "
                        f"Escrow PDA: {escrow_pda}. "
                        f"Please proceed with the {service_action}."
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
            
            elif ("complete" in response_text or "review complete" in response_text) and "proof" in response_text:
                # Service completed - log the results
                ctx.logger.info("✅ Service completed! Provider submitted proof.")
                ctx.logger.info("💰 Payment automatically claimed via x402 gateway")
                ctx.logger.info("🎉 Transaction successful! Session complete.")
                
                # Mark as completed - no need to release payment (provider already claimed via x402)
                ctx.storage.set("service_completed", True)
                ctx.storage.set("payment_released", True)
                
                # Send thank you message
                thank_you_msg = create_text_chat(
                    "Thank you for the excellent service! Payment has been processed."
                )
                await ctx.send(sender, thank_you_msg)
                
                # Reset session state for next service request
                ctx.logger.info("🔄 Session complete. Agent ready for next request.")
                ctx.logger.info("   (Restart client to request another service)")
                ctx.storage.set("service_requested", False)
                ctx.storage.set("escrow_initialized", False)
                ctx.storage.set("service_completed", False)
                ctx.storage.set("payment_released", False)
                
                return  # Exit early - no manual payment release needed
                
                # OLD CODE BELOW (kept for reference but never executed)
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
                ctx.logger.info("✅ Service completed. Session ended.")

        # Marks the end of a chat session
        elif isinstance(item, EndSessionContent):
            pass  # Session ended
        
        # Catches anything unexpected
        else:
            pass  # Unexpected content


# Handle acknowledgements for messages this agent has sent out
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle acknowledgements from other agents."""
    # Acknowledgement received


# OLD: Periodic task to check and release payment (DISABLED - using x402 gateway now)
# Payment is now automatically released by provider via x402 gateway after proof verification
# @agent.on_interval(period=10.0)
# async def check_and_release_payment(ctx: Context):
#     """Check if payment should be released and release it."""
#     # This function is disabled because we use x402 gateway for payment release


# Periodic task to discover and request services (runs every 5 seconds)
@agent.on_interval(period=5.0)
async def discover_and_request_service(ctx: Context):
    """Discover available services and request one using AI decision-making."""
    # Only run once to avoid spam
    global SERVICE_REQUESTED
    if SERVICE_REQUESTED or ctx.storage.get("service_requested"):
        return
    
    ctx.logger.info("🔍 Discovering available services...")
    ctx.logger.info("🤖 Using AI to select best service...")
    
    # Use AI to select service
    ai_decision = await ai_select_service(ctx)
    selected_service_name = ai_decision.get("selected_service", "CodeReview")
    
    # Try to discover from marketplace first
    provider_address = None
    provider_data = None
    service_type_map = {
        "CodeReview": "code_review",
        "ContentAnalyst": "content_analysis",
        "Translator": "translation"
    }
    
    try:
        # Query marketplace for best provider of AI-selected service
        service_type = service_type_map.get(selected_service_name, "code_review")
        response = requests.get(
            f"http://localhost:8000/services/{service_type}/best",
            params={"max_price": 10, "min_rating": 4.0},  # Max 10 tokens per service
            timeout=2
        )
        
        if response.status_code == 200:
            provider_data = response.json()['provider']
            provider_address = provider_data['provider_address']
            provider_solana_address = provider_data.get('solana_address')
            ctx.logger.info(f"📍 Found provider in marketplace: {provider_data['provider_name']}")
            ctx.logger.info(f"   Rating: {provider_data['provider_rating']}/5.0")
            ctx.logger.info(f"   Price: {provider_data['base_price']} Tokens")
            ctx.logger.info(f"🎯 AI selected: {selected_service_name}")
            
            # Store provider's Solana address for payment
            if provider_solana_address:
                ctx.logger.info(f"💾 Storing provider Solana address: {provider_solana_address}")
                ctx.storage.set("provider_solana_address", provider_solana_address)
            else:
                ctx.logger.warning("⚠️  No Solana address in marketplace data!")
        elif response.status_code == 404:
            # No provider for this service type, try to find ANY available service
            ctx.logger.warning(f"⚠️  No {selected_service_name} provider available")
            ctx.logger.info("🔄 Looking for alternative services...")
            
            # Get all available services
            all_services_response = requests.get(
                "http://localhost:8000/services",
                timeout=2
            )
            
            if all_services_response.status_code == 200:
                all_services = all_services_response.json()['services']
                if all_services:
                    # Pick the first available service
                    provider_data = all_services[0]
                    provider_address = provider_data['provider_address']
                    provider_solana_address = provider_data.get('solana_address')
                    # Update selected service name based on what we found
                    reverse_map = {v: k for k, v in service_type_map.items()}
                    selected_service_name = reverse_map.get(provider_data['service_type'], selected_service_name)
                    
                    ctx.logger.info(f"📍 Found alternative: {provider_data['provider_name']}")
                    ctx.logger.info(f"   Service: {provider_data['service_type']}")
                    ctx.logger.info(f"   Rating: {provider_data['provider_rating']}/5.0")
                    ctx.logger.info(f"   Price: {provider_data['base_price']} Tokens")
                    ctx.logger.info(f"🎯 Using: {selected_service_name}")
                    
                    # Store provider's Solana address for payment
                    if provider_solana_address:
                        ctx.logger.info(f"💾 Storing provider Solana address (failover): {provider_solana_address}")
                        ctx.storage.set("provider_solana_address", provider_solana_address)
                    else:
                        ctx.logger.warning("⚠️  No Solana address in failover marketplace data!")
    except Exception as e:
        ctx.logger.warning(f"⚠️  Marketplace unavailable: {e}")
    
    # Fallback to hardcoded addresses if marketplace fails
    if not provider_address:
        ctx.logger.info("⚠️  No services in marketplace, using fallback")
        ctx.logger.info(f"🎯 AI selected: {selected_service_name}")
        provider_address = PROVIDER_AGENTS.get(selected_service_name)
    
    if provider_address:
        service_info = SERVICE_CATALOG.get(selected_service_name, {})
        ctx.logger.info(f"👋 Contacting {selected_service_name} Agent: {provider_address}")
        
        # Start a session with selected agent
        start_msg = create_start_session()
        await ctx.send(provider_address, start_msg)
        # Give agent a moment to register the session
        await asyncio.sleep(0.3)
        
        # Create AI-powered request message
        request_msg = create_text_chat(
            f"Hello! I need {service_info.get('name', 'service')}. "
            f"What's your pricing and capabilities?"
        )
        await ctx.send(provider_address, request_msg)
        
        # Store selection
        ctx.storage.set("selected_service_name", selected_service_name)
    else:
        # Fallback to legacy Agent A
        ctx.logger.info(f"👋 Contacting Agent A directly: {AGENT_A_ADDRESS}")
        
        # Start a session with Agent A
        start_msg = create_start_session()
        await ctx.send(AGENT_A_ADDRESS, start_msg)
        await asyncio.sleep(0.3)
        request_msg = create_text_chat("Hello! I need data analysis services. What's your pricing?")
        await ctx.send(AGENT_A_ADDRESS, request_msg)
    
    # Mark as requested
    ctx.storage.set("service_requested", True)
    ctx.storage.set("selected_service", selected_service_name)
    SERVICE_REQUESTED = True


# Startup event - Register as client in marketplace
@agent.on_event("startup")
async def startup(ctx: Context):
    """Log agent information on startup and register in marketplace."""
    ctx.logger.info("\n" + "="*70)
    ctx.logger.info("💼 CLIENT AGENT - AI-Powered Service Consumer")
    ctx.logger.info("="*70)
    ctx.logger.info(f"Address: {agent.address}")
    ctx.logger.info(f"Port: 5050")
    ctx.logger.info(f"🤖 AI Engine: Gemini (Intelligent service selection)")
    ctx.logger.info(f"💰 Budget: 1000 Tokens (~$1000 for services)")
    ctx.logger.info(f"📋 Available Services:")
    for service_name, service_info in SERVICE_CATALOG.items():
        ctx.logger.info(f"   - {service_name}: {service_info['description'][:50]}...")
    
    # Register agent profile in marketplace
    profile = AgentProfile(
        agent_address=agent.address,
        agent_name=agent.name,
        agent_type="client",
    )
    
    marketplace.register_agent(profile)
    
    ctx.logger.info("✅ Ready to discover and request services with AI")
    ctx.logger.info("="*70 + "\n")
    
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
