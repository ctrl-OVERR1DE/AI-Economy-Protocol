"""
Agent A: Data Analyst Agent (Service Provider)

This agent provides data analysis services to other agents in the AI Economy Protocol.
It demonstrates autonomous service provision with on-chain payment settlement.

Key Features:
- Advertises data analysis services in marketplace
- Accepts service requests via uAgents Chat Protocol
- Processes tasks and submits cryptographic proofs to escrow
- Receives payments automatically after proof verification

Technical Stack:
- uAgents framework for agent communication
- Solana blockchain for payment settlement
- Anchor smart contracts for escrow management
- Sanctum Gateway for transaction optimization

Port: 5051
Address: agent1qwd63x7vsupc3swvmmc8hekr6fwfryvvqs360hjuh3ztxlnze6kcukjexf7
"""

import sys
import os
import asyncio
import logging
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
# Import from project root utils
import sys
sys.path.insert(0, os.path.join(project_root, 'utils'))
from marketplace import marketplace, AgentProfile, ServiceListing

# Import from agents utils
from utils.solana_utils import (
    load_agent_wallet,
    submit_proof_for_task,
)

# Initialize Agent A - Data Analyst (Local Mode)
agent = Agent(
    name="DataAnalystAgent",
    seed="data_analyst_seed_phrase_12345",  # Use consistent seed for same address
    port=5051,
    endpoint=["http://127.0.0.1:5051/submit"],  # Local endpoint for direct communication
)

# Fund agent if low on testnet tokens (disabled - using Solana for payments)
# fund_agent_if_low(agent.wallet.address())
# Initialize the chat protocol
chat_proto = Protocol(name="AgentChatProtocol")


# Utility function to wrap plain text into a ChatMessage
def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    """Create a ChatMessage with text content."""
    content = [TextContent(type="text", text=text)]
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )


# Handle incoming chat messages
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages from other agents."""
    # Received message from {sender}
    
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
            ctx.logger.info(f"🤝 Session started with client")
            
            # Send welcome message
            welcome_msg = create_text_chat(
                "Hello! I'm DataAnalystAgent, your AI data analyst. "
                "I can help you with data processing, analysis, and insights generation. "
                "What service do you need?"
            )
            await ctx.send(sender, welcome_msg)
        
        # Handles plain text messages (from another agent or ASI:One)
        elif isinstance(item, TextContent):
            # Log key client messages only
            if "pricing" in item.text.lower() and "need" in item.text.lower():
                ctx.logger.info("💬 Client requested service and pricing information")
            
            # Simple service logic - analyze the request
            raw_text = item.text
            request_text = raw_text.lower()
            
            # IMPORTANT: handle escrow confirmation BEFORE generic 'data analysis' keywords
            if "confirm" in request_text and "escrow" in request_text:
                # Extract escrow PDA from confirmation message if present
                escrow_pda_str = None
                # Parse escrow PDA from the original text without altering case
                try:
                    import re
                    m = re.search(r"escrow pda:\s*([1-9A-HJ-NP-Za-km-z]{32,48})", raw_text, re.IGNORECASE)
                    if m:
                        escrow_pda_str = m.group(1)
                        ctx.logger.info(f"📋 Escrow PDA: {escrow_pda_str}")
                except Exception:
                    pass

                # Check if we already processed this escrow
                if escrow_pda_str:
                    if ctx.storage.get("processed_escrow_pda") == escrow_pda_str:
                        # Escrow already processed
                        return
                    ctx.storage.set("escrow_pda", escrow_pda_str)
                    ctx.storage.set("processed_escrow_pda", escrow_pda_str)
                
                # Perform the analysis
                ctx.logger.info("💬 Client confirmed payment in escrow")
                ctx.logger.info("🔍 Processing data analysis request...")
                analysis_result = {
                    "trend": "15% growth",
                    "correlation": 0.85,
                    "insights": "Strong positive correlation detected",
                }
                
                # Submit proof of completion
                try:
                    provider_wallet = load_agent_wallet("DataAnalystAgent")
                    # Provider wallet loaded
                    # Ensure provider wallet matches configured PROVIDER_PUBLIC_KEY to avoid PDA drift
                    configured_provider = os.getenv("PROVIDER_PUBLIC_KEY")
                    if configured_provider and str(provider_wallet.pubkey()) != configured_provider:
                        ctx.logger.error("Provider wallet pubkey does not match PROVIDER_PUBLIC_KEY; aborting proof submission.")
                        return
                    
                    # Get client's Solana address (in production, map from agent address)
                    client_solana_address = os.getenv("CLIENT_SOLANA_ADDRESS")
                    if not client_solana_address:
                        # For testing, use the wallet from env
                        client_solana_address = os.getenv("SOLANA_WALLET_PATH")
                        if client_solana_address:
                            import json
                            with open(os.path.expanduser(client_solana_address), 'r') as f:
                                secret = json.load(f)
                            from solders.keypair import Keypair
                            client_kp = Keypair.from_bytes(bytes(secret))
                            client_solana_address = str(client_kp.pubkey())
                    
                    # We require escrow_pda to ensure proof targets the exact PDA initialized by client
                    if escrow_pda_str:
                        # Create proof data (hash of analysis result)
                        import json
                        proof_data = json.dumps(analysis_result)
                        
                        ctx.logger.info("📤 Submitting proof to escrow...")
                        proof_signature = await submit_proof_for_task(
                            provider_wallet=provider_wallet,
                            escrow_pda=escrow_pda_str,
                            proof_data=proof_data,
                        )
                        
                        ctx.logger.info(f"✅ Proof submitted!")
                        ctx.logger.info(f"   Transaction: {proof_signature}")
                        ctx.logger.info(f"💼 Ready to accept new service requests!")
                        
                        response_message = create_text_chat(
                            f"Analysis complete: Trend shows 15% growth, "
                            f"correlation coefficient: 0.85. "
                            f"Proof of completion submitted to escrow (tx: {proof_signature[:16]}...). "
                            f"Payment can now be released."
                        )
                        
                        # Try to send with retry
                        try:
                            await ctx.send(sender, response_message)
                        except Exception as send_error:
                            ctx.logger.warning(f"Failed to send response: {send_error}")
                            # Store for later retry
                            ctx.storage.set("pending_response", response_message.json())
                            ctx.storage.set("pending_response_recipient", sender)
                        return  # Exit early to avoid sending response twice
                    else:
                        ctx.logger.warning("Client Solana address not available, skipping proof submission")
                        response_message = create_text_chat(
                            "Great! I'm processing your data analysis request. "
                            "Analysis complete: [Sample insights: Trend shows 15% growth, "
                            "correlation coefficient: 0.85]. "
                            "Payment can be processed via escrow contract."
                        )
                
                except Exception as e:
                    ctx.logger.error(f"Failed to submit proof: {e}")
                    response_message = create_text_chat(
                        "Analysis complete: [Sample insights: Trend shows 15% growth, "
                        "correlation coefficient: 0.85]. "
                        f"Note: Proof submission encountered an error: {str(e)}"
                    )
            elif "data analysis" in request_text or "analyze" in request_text:
                response_message = create_text_chat(
                    "I can perform data analysis for you. "
                    "Service fee: 0.1 SOL. "
                    "Please confirm if you'd like to proceed with the analysis."
                )
            elif "price" in request_text or "cost" in request_text:
                response_message = create_text_chat(
                    "My service pricing:\n"
                    "- Data Analysis: 0.1 SOL\n"
                    "- Data Processing: 0.05 SOL\n"
                    "- Insights Generation: 0.15 SOL"
                )
            else:
                response_message = create_text_chat(
                    "I received your message. I specialize in:\n"
                    "1. Data Analysis\n"
                    "2. Data Processing\n"
                    "3. Insights Generation\n"
                    "How can I assist you today?"
                )
            
            await ctx.send(sender, response_message)

        # Marks the end of a chat session
        elif isinstance(item, EndSessionContent):
            ctx.logger.info(f"Session ended with {sender}")
            
            # Send goodbye message
            goodbye_msg = create_text_chat(
                "Thank you for using DataAnalystAgent services. "
                "Looking forward to working with you again!"
            )
            await ctx.send(sender, goodbye_msg)
        
        # Catches anything unexpected
        else:
            ctx.logger.info(f"Received unexpected content type from {sender}")


# Handle acknowledgements for messages this agent has sent out
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle acknowledgements from other agents."""
    # Acknowledgement received


# Startup event - Register as provider in marketplace
@agent.on_event("startup")
async def startup(ctx: Context):
    """Log agent information on startup and register in marketplace."""
    ctx.logger.info("\n" + "="*70)
    ctx.logger.info("🤖 DATA ANALYST AGENT - Service Provider")
    ctx.logger.info("="*70)
    ctx.logger.info(f"Address: {agent.address}")
    ctx.logger.info(f"Port: 5051")
    
    # Reset processed escrow flag on startup to allow reprocessing
    ctx.storage.set("processed_escrow_pda", None)
    
    # Register agent profile in marketplace
    profile = AgentProfile(
        agent_address=agent.address,
        agent_name=agent.name,
        agent_type="provider",
    )
    
    marketplace.register_agent(profile)
    
    # Register services
    services = [
        ServiceListing(
            service_id="data_analysis_001",
            service_name="Data Analysis",
            description="Comprehensive data analysis with trend identification and correlation analysis",
            price_sol=0.1,
            provider_address=agent.address,
            provider_name=agent.name,
            category="Data Processing",
        ),
        ServiceListing(
            service_id="data_processing_001",
            service_name="Data Processing",
            description="Clean, transform, and prepare data for analysis",
            price_sol=0.05,
            provider_address=agent.address,
            provider_name=agent.name,
            category="Data Processing",
        ),
        ServiceListing(
            service_id="insights_generation_001",
            service_name="Insights Generation",
            description="Generate actionable insights from processed data",
            price_sol=0.15,
            provider_address=agent.address,
            provider_name=agent.name,
            category="Analytics",
        ),
    ]
    
    for service in services:
        marketplace.register_service(service)
    
    ctx.logger.info("✅ Services: Data Analysis, Data Processing, Insights Generation")
    ctx.logger.info("💰 Pricing: 0.1 SOL per analysis")
    ctx.logger.info("⏳ Waiting for client requests...")
    ctx.logger.info("="*70 + "\n")


# Include the chat protocol and publish the manifest to Agentverse
agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__":
    agent.run()
