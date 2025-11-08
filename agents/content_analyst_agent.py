"""
Content Analyst Agent

Specialized AI agent that provides content analysis services.
Uses Gemini AI to analyze articles, documents, and text content.
"""

import sys
import os
import asyncio
import logging
import requests
from datetime import datetime
from uuid import uuid4

# Suppress verbose logs
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
    ChatMessage,
    ChatAcknowledgement,
    StartSessionContent,
    TextContent,
    EndSessionContent,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import services
from agents.services.content_analyzer import ContentAnalyzer
from agents.utils.solana_utils import (
    load_agent_wallet,
    submit_proof_for_task,
)
from agents.utils.gateway_client import GatewayClient

# Agent configuration
AGENT_NAME = "ContentAnalystAgent"
AGENT_PORT = 5051
AGENT_SEED = "content_analyst_seed_phrase_unique_12345"

# Service configuration
PROVIDER_WALLET = load_agent_wallet("ContentAnalystAgent")
PROVIDER_PUBLIC_KEY = str(PROVIDER_WALLET.pubkey())

# Initialize agent
agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=AGENT_PORT,
    endpoint=f"http://localhost:{AGENT_PORT}/submit",
)

# Initialize service
content_analyzer = ContentAnalyzer()

# Create chat protocol
chat_proto = Protocol(name="ContentAnalystProtocol")


# Utility function to create text chat message
def create_text_chat(text: str) -> ChatMessage:
    """Create a ChatMessage with text content."""
    content = [TextContent(type="text", text=text)]
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )


@agent.on_event("startup")
async def startup(ctx: Context):
    """Log agent information on startup."""
    # Reset session flags on startup
    ctx.storage.set("pricing_sent", False)
    ctx.storage.set("processed_escrow_pda", None)
    
    ctx.logger.info("\n" + "="*70)
    ctx.logger.info("🤖 CONTENT ANALYST AGENT - AI-Powered Service Provider")
    ctx.logger.info("="*70)
    ctx.logger.info(f"Address: {agent.address}")
    ctx.logger.info(f"Port: {AGENT_PORT}")
    ctx.logger.info(f"✅ Service: Content Analysis (Gemini AI)")
    ctx.logger.info(f"💰 Base Pricing: {content_analyzer.BASE_PRICE} Tokens (~${content_analyzer.BASE_PRICE})")
    ctx.logger.info(f"📊 Features:")
    for feature in content_analyzer.get_service_info()['features']:
        ctx.logger.info(f"   - {feature}")
    ctx.logger.info(f"📝 Analysis Types:")
    types = ['Articles', 'Blog posts', 'Social media', 'Documents', 'Reviews']
    ctx.logger.info(f"   {', '.join(types)}")
    ctx.logger.info(f"⏳ Waiting for client requests...")
    ctx.logger.info("="*70)
    ctx.logger.info("")
    
    # Register in marketplace
    try:
        response = requests.post(
            "http://localhost:8000/providers/register",
            json={
                "agent_address": agent.address,
                "agent_name": AGENT_NAME,
                "solana_address": PROVIDER_PUBLIC_KEY,
                "port": AGENT_PORT,
                "endpoint": f"http://localhost:{AGENT_PORT}/submit",
                "services": [{
                    "service_type": "content_analysis",
                    "base_price": content_analyzer.BASE_PRICE,
                    "description": "AI-powered content analysis with Gemini",
                    "features": content_analyzer.get_service_info()['features'][:5],
                    "avg_completion_time": 25,
                    "success_rate": 1.0
                }]
            },
            timeout=2
        )
        if response.status_code == 200:
            ctx.logger.info("✅ Registered in marketplace")
        else:
            ctx.logger.warning(f"⚠️  Marketplace registration failed: {response.status_code}")
    except Exception as e:
        ctx.logger.warning(f"⚠️  Marketplace unavailable (will work without it): {e}")


@agent.on_event("shutdown")
async def shutdown(ctx: Context):
    """Unregister from marketplace on shutdown."""
    try:
        response = requests.post(
            "http://localhost:8000/providers/status",
            json={
                "agent_address": agent.address,
                "status": "offline"
            },
            timeout=2
        )
        if response.status_code == 200:
            ctx.logger.info("✅ Unregistered from marketplace")
    except Exception:
        pass  # Silently fail if marketplace unavailable


# Handle incoming chat messages
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages from other agents."""
    
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
            
            # Reset session state for new client
            ctx.storage.set("pricing_sent", False)
            ctx.storage.set("processed_escrow_pda", None)
            
            # Send welcome message
            service_info = content_analyzer.get_service_info()
            welcome_msg = create_text_chat(
                f"Hello! I'm {AGENT_NAME}, your AI content analyst powered by Gemini. "
                f"I specialize in sentiment analysis, readability scoring, and content insights. "
                f"What content would you like me to analyze?"
            )
            await ctx.send(sender, welcome_msg)
        
        # Handles plain text messages (from another agent or ASI:One)
        elif isinstance(item, TextContent):
            # Simple service logic - analyze the request
            raw_text = item.text
            request_text = raw_text.lower()
            
            # IMPORTANT: handle thank you messages FIRST
            if "thank you" in request_text or "thanks" in request_text:
                # Client is thanking us after service completion - no response needed
                ctx.logger.info("💬 Client sent acknowledgment")
                return
            
            # Handle escrow confirmation
            elif "confirm" in request_text and "escrow" in request_text:
                # Extract escrow PDA from confirmation message if present
                escrow_pda_str = None
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
                
                # Perform the content analysis
                ctx.logger.info("💬 Client confirmed payment in escrow")
                ctx.logger.info("🔍 Processing content analysis request...")
                
                # For demo, use sample code (in production, extract from message)
                sample_content = """
The quick brown fox jumps over the lazy dog. This is a sample text for content analysis. It demonstrates various writing styles and tones.
"""
                
                try:
                    # Perform AI-powered content analysis
                    result = await content_analyzer.analyze(sample_content)
                    analysis = result['output']
                    
                    ctx.logger.info(f"✅ Content analysis complete!")
                    ctx.logger.info(f"   Summary: {analysis.get('summary', 'N/A')[:50]}...")
                    ctx.logger.info(f"   Sentiment: {analysis.get('sentiment', 'N/A')}")
                    ctx.logger.info(f"   Topics: {len(analysis.get('topics', []))}")
                    
                    # Submit proof of completion
                    if escrow_pda_str:
                        # Create proof data
                        import json
                        proof_data = json.dumps(result['proof'])
                        
                        ctx.logger.info("📤 Submitting proof to escrow...")
                        proof_signature = await submit_proof_for_task(
                            provider_wallet=PROVIDER_WALLET,
                            escrow_pda=escrow_pda_str,
                            proof_data=proof_data,
                        )
                        
                        ctx.logger.info(f"✅ Proof submitted!")
                        ctx.logger.info(f"   Transaction: {proof_signature}")
                        
                        # Claim payment via x402 Payment Gateway
                        ctx.logger.info("💰 Claiming payment via x402 gateway...")
                        gateway = GatewayClient()
                        
                        payment_success, payment_data, payment_error = await gateway.claim_payment(
                            escrow_pda=escrow_pda_str,
                            provider_solana_address=PROVIDER_PUBLIC_KEY,
                            provider_agent_address=agent.address,
                            client_address=str(sender),
                            service_type="content_analysis",
                            amount=content_analyzer.BASE_PRICE,
                            max_retries=3,
                            retry_delay=5
                        )
                        
                        if payment_success:
                            ctx.logger.info(f"✅ Payment claimed successfully!")
                            ctx.logger.info(f"   Amount: {payment_data.get('amount')} Tokens")
                            ctx.logger.info(f"   TX: {payment_data.get('tx_signature')}")
                            payment_msg = f"Payment of {payment_data.get('amount')} Tokens claimed (tx: {payment_data.get('tx_signature', '')[:16]}...)."
                        else:
                            ctx.logger.warning(f"⚠️  Payment claim pending: {payment_error}")
                            payment_msg = "Payment claim in progress. Will be released after verification."
                        
                        ctx.logger.info(f"💼 Ready to accept new service requests!")
                        
                        # Send analysis results to client
                        response_message = create_text_chat(
                            f"✅ Content Analysis Complete!\n\n"
                            f"Summary: {analysis.get('summary', 'N/A')[:100]}...\n"
                            f"Sentiment: {analysis.get('sentiment', 'N/A')}\n"
                            f"Topics: {', '.join(analysis.get('topics', [])[:3])}\n"
                            f"Key Points: {len(analysis.get('key_points', []))}\n\n"
                            f"Proof submitted to escrow (tx: {proof_signature[:16]}...). "
                            f"{payment_msg}"
                        )
                        
                        # Try to send with retry
                        try:
                            await ctx.send(sender, response_message)
                        except Exception as send_error:
                            ctx.logger.warning(f"Failed to send response: {send_error}")
                        return  # Exit early to avoid sending response twice
                    
                except Exception as e:
                    ctx.logger.error(f"Failed to perform content analysis: {e}")
                    import traceback
                    traceback.print_exc()
                    response_message = create_text_chat(
                        f"Code review encountered an error: {str(e)}"
                    )
                    await ctx.send(sender, response_message)
                    return
            
            elif "content analysis" in request_text or "review" in request_text:
                ctx.logger.info("💬 Client requested content analysis service")
                # Check if we already sent pricing to this client
                if ctx.storage.get("pricing_sent"):
                    # Already sent pricing, don't repeat
                    return
                
                ctx.storage.set("pricing_sent", True)
                response_message = create_text_chat(
                    "I can perform AI-powered content analysis for you. "
                    f"Service fee: {content_analyzer.BASE_PRICE} Tokens (~${content_analyzer.BASE_PRICE}). "
                    "Please confirm if you'd like to proceed with the review."
                )
                await ctx.send(sender, response_message)
            
            elif "price" in request_text or "cost" in request_text or "pricing" in request_text:
                ctx.logger.info("💬 Client requested pricing information")
                # Check if we already sent pricing to this client
                if ctx.storage.get("pricing_sent"):
                    # Already sent pricing, don't repeat
                    return
                
                ctx.storage.set("pricing_sent", True)
                service_info = content_analyzer.get_service_info()
                response_message = create_text_chat(
                    f"My content analysis service pricing:\n"
                    f"- Base Price: {service_info['base_price']} Tokens\n"
                    f"- Typical Range: {service_info['typical_price_range']}\n"
                    f"- Pricing Model: {service_info['pricing_model']}\n\n"
                    f"Features:\n" + "\n".join(f"  • {f}" for f in service_info['features'][:4])
                )
                await ctx.send(sender, response_message)
            
            else:
                # Generic fallback - only if no other condition matched
                response_message = create_text_chat(
                    "I received your message. I specialize in:\n"
                    "1. AI-powered content analysis\n"
                    "2. Sentiment analysis\n"
                    "3. Readability scoring\n"
                    "4. Key insights extraction\n"
                    "How can I assist you today?"
                )
                await ctx.send(sender, response_message)

        # Marks the end of a chat session
        elif isinstance(item, EndSessionContent):
            ctx.logger.info(f"Session ended with {sender}")
            
            # Send goodbye message
            goodbye_msg = create_text_chat(
                "Thank you for using ContentAnalystAgent services. "
                "Looking forward to analyzing your content again!"
            )
            await ctx.send(sender, goodbye_msg)


# Include the chat protocol
agent.include(chat_proto)


if __name__ == "__main__":
    agent.run()
