"""
Code Review Agent

Specialized AI agent that provides code review services.
Uses Gemini AI to review code for quality, security, and best practices.
"""

import sys
import os
import asyncio
import logging
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
from agents.services.code_reviewer import CodeReviewer
from agents.utils.solana_utils import (
    load_agent_wallet,
    submit_proof_for_task,
)
from agents.utils.gateway_client import GatewayClient

# Agent configuration
AGENT_NAME = "CodeReviewAgent"
AGENT_PORT = 5052
AGENT_SEED = "code_review_seed_phrase_unique_67890"

# Service configuration
PROVIDER_WALLET = load_agent_wallet("DataAnalystAgent")  # Reuse wallet for now
PROVIDER_PUBLIC_KEY = str(PROVIDER_WALLET.pubkey())

# Initialize agent
agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=AGENT_PORT,
    endpoint=f"http://localhost:{AGENT_PORT}/submit",
)

# Initialize service
code_reviewer = CodeReviewer()

# Create chat protocol
chat_proto = Protocol(name="CodeReviewProtocol")


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
    ctx.logger.info("🤖 CODE REVIEW AGENT - AI-Powered Service Provider")
    ctx.logger.info("="*70)
    ctx.logger.info(f"Address: {agent.address}")
    ctx.logger.info(f"Port: {AGENT_PORT}")
    ctx.logger.info(f"✅ Service: Code Review (Gemini AI)")
    ctx.logger.info(f"💰 Base Pricing: {code_reviewer.BASE_PRICE} SOL (AI-dynamic)")
    ctx.logger.info(f"📊 Features:")
    for feature in code_reviewer.get_service_info()['features']:
        ctx.logger.info(f"   - {feature}")
    ctx.logger.info(f"🔧 Supported Languages:")
    langs = code_reviewer.get_service_info()['supported_languages']
    ctx.logger.info(f"   {', '.join(langs[:5])}...")
    ctx.logger.info(f"⏳ Waiting for client requests...")
    ctx.logger.info("="*70)
    ctx.logger.info("")


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
            
            # Send welcome message
            service_info = code_reviewer.get_service_info()
            welcome_msg = create_text_chat(
                f"Hello! I'm {AGENT_NAME}, your AI code reviewer powered by Gemini. "
                f"I specialize in code quality analysis, security reviews, and best practices. "
                f"Base price: {service_info['base_price']} SOL (dynamic based on complexity). "
                f"What code would you like me to review?"
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
                
                # Perform the code review
                ctx.logger.info("💬 Client confirmed payment in escrow")
                ctx.logger.info("🔍 Processing code review request...")
                
                # For demo, use sample code (in production, extract from message)
                sample_code = """
def transfer_funds(from_account, to_account, amount):
    from_account.balance -= amount
    to_account.balance += amount
    return True
"""
                
                try:
                    # Perform AI-powered code review
                    result = await code_reviewer.review(sample_code, language="python")
                    review = result['output']
                    
                    ctx.logger.info(f"✅ Code review complete!")
                    ctx.logger.info(f"   Quality Score: {review['quality_score']}/10")
                    ctx.logger.info(f"   Issues: {len(review['issues'])}")
                    
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
                            provider_address=PROVIDER_PUBLIC_KEY,
                            max_retries=3,
                            retry_delay=5
                        )
                        
                        if payment_success:
                            ctx.logger.info(f"✅ Payment claimed successfully!")
                            ctx.logger.info(f"   Amount: {payment_data.get('amount')} SOL")
                            ctx.logger.info(f"   TX: {payment_data.get('tx_signature')}")
                            payment_msg = f"Payment of {payment_data.get('amount')} SOL claimed (tx: {payment_data.get('tx_signature', '')[:16]}...)."
                        else:
                            ctx.logger.warning(f"⚠️  Payment claim pending: {payment_error}")
                            payment_msg = "Payment claim in progress. Will be released after verification."
                        
                        ctx.logger.info(f"💼 Ready to accept new service requests!")
                        
                        # Send review results to client
                        response_message = create_text_chat(
                            f"✅ Code Review Complete!\n\n"
                            f"Quality Score: {review['quality_score']}/10\n"
                            f"Assessment: {review['overall_assessment']}\n"
                            f"Issues Found: {len(review['issues'])}\n"
                            f"Security Concerns: {len(review['security_concerns'])}\n\n"
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
                    ctx.logger.error(f"Failed to perform code review: {e}")
                    import traceback
                    traceback.print_exc()
                    response_message = create_text_chat(
                        f"Code review encountered an error: {str(e)}"
                    )
                    await ctx.send(sender, response_message)
                    return
            
            elif "code review" in request_text or "review" in request_text:
                ctx.logger.info("💬 Client requested code review service")
                # Check if we already sent pricing to this client
                if ctx.storage.get("pricing_sent"):
                    # Already sent pricing, don't repeat
                    return
                
                ctx.storage.set("pricing_sent", True)
                response_message = create_text_chat(
                    "I can perform AI-powered code review for you. "
                    f"Service fee: {code_reviewer.BASE_PRICE} SOL (dynamic based on complexity). "
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
                service_info = code_reviewer.get_service_info()
                response_message = create_text_chat(
                    f"My code review service pricing:\n"
                    f"- Base Price: {service_info['base_price']} SOL\n"
                    f"- Typical Range: {service_info['typical_price_range']}\n"
                    f"- Pricing Model: {service_info['pricing_model']}\n\n"
                    f"Features:\n" + "\n".join(f"  • {f}" for f in service_info['features'][:4])
                )
                await ctx.send(sender, response_message)
            
            else:
                # Generic fallback - only if no other condition matched
                response_message = create_text_chat(
                    "I received your message. I specialize in:\n"
                    "1. AI-powered code analysis\n"
                    "2. Security vulnerability detection\n"
                    "3. Best practices suggestions\n"
                    "4. Quality scoring\n"
                    "How can I assist you today?"
                )
                await ctx.send(sender, response_message)

        # Marks the end of a chat session
        elif isinstance(item, EndSessionContent):
            ctx.logger.info(f"Session ended with {sender}")
            
            # Send goodbye message
            goodbye_msg = create_text_chat(
                "Thank you for using CodeReviewAgent services. "
                "Looking forward to reviewing your code again!"
            )
            await ctx.send(sender, goodbye_msg)


# Include the chat protocol
agent.include(chat_proto)


if __name__ == "__main__":
    agent.run()
