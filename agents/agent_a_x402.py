"""
Agent A with x402 HTTP Server Integration

This extends Agent A (Data Analyst) with an HTTP server that uses x402 protocol
for payment-required endpoints. Agent A now has dual interfaces:
1. uAgents Chat Protocol (existing)
2. HTTP with x402 (new)

The x402 HTTP server runs on port 8001 and protects the /analyze endpoint.
"""

import sys
import os
import asyncio
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import uAgents
from uagents import Agent, Protocol

# Create Agent A instance (separate from agent_a.py to avoid conflicts)
agent = Agent(
    name="DataAnalystAgent",
    seed="data_analyst_seed_phrase_12345",
    port=5051,
    endpoint=["http://127.0.0.1:5051/submit"],
)

# Create chat protocol
chat_proto = Protocol(name="AgentChatProtocol")

# Import x402 components
from agents.x402.payment_verifier import PaymentVerifier
from agents.utils.solana_utils import load_agent_wallet, submit_proof_for_task
import json
import time

# Configuration
SERVICE_PRICE = 0.1  # SOL
SERVICE_ID = "data_analysis_001"
HTTP_PORT = 8001

# Load Agent A's wallet
PROVIDER_WALLET = load_agent_wallet("DataAnalystAgent")
PROVIDER_PUBLIC_KEY = str(PROVIDER_WALLET.pubkey())

# Initialize x402 payment verifier
verifier = PaymentVerifier()

# Create Flask app for HTTP endpoints
app = Flask(__name__)
CORS(app)

print(f"Agent A x402 HTTP Server")
print(f"Provider: {PROVIDER_PUBLIC_KEY}")


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with service info."""
    return jsonify({
        "service": "AEP Agent A - Data Analysis Service",
        "agent": "DataAnalystAgent",
        "version": "1.0.0",
        "endpoints": {
            "/analyze": "Data analysis service (x402 protected)",
            "/health": "Health check"
        },
        "payment": {
            "protocol": "x402",
            "scheme": "escrow",
            "price": SERVICE_PRICE,
            "token": "SOL",
            "network": "solana-devnet",
            "provider": PROVIDER_PUBLIC_KEY
        },
        "uagents": {
            "address": agent.address,
            "port": 5051,
            "protocol": "chat"
        }
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Agent A x402 HTTP Server",
        "agent": "DataAnalystAgent",
        "provider": PROVIDER_PUBLIC_KEY
    }), 200


@app.route('/analyze', methods=['GET', 'POST'])
async def analyze():
    """
    Data analysis endpoint protected by x402.
    
    Flow:
    1. Client requests without payment → 402
    2. Client creates escrow and sends X-Payment header
    3. Server verifies payment and performs analysis
    4. Server returns result
    """
    # Get task data from request
    if request.method == 'GET':
        task_data = request.args.get('data', '')
    else:
        task_data = request.json.get('data', '') if request.json else ''
    
    # Check for X-Payment header
    x_payment = request.headers.get('X-Payment')
    
    if not x_payment:
        # No payment provided - return 402 Payment Required
        print(f"\n📨 Request received: {request.method} /analyze")
        print(f"💰 Payment required: {SERVICE_PRICE} SOL")
        print(f"📋 Service: Data Analysis")
        
        return jsonify({
            "payment": {
                "recipient": PROVIDER_PUBLIC_KEY,
                "escrowProgram": os.getenv("ESCROW_PROGRAM_ID"),
                "amount": SERVICE_PRICE,
                "token": "SOL",
                "network": "solana-devnet",
                "serviceId": SERVICE_ID,
                "taskData": task_data
            }
        }), 402
    
    # Payment provided - verify and process
    print("\n✅ Payment received via X-Payment header")
    print("🔍 Verifying escrow payment...")
    
    # Verify payment using async verification
    try:
        import asyncio
        import nest_asyncio
        nest_asyncio.apply()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            is_valid, error, payment_details = loop.run_until_complete(verifier.verify_x_payment_header(
                x_payment_header=x_payment,
                expected_amount=SERVICE_PRICE,
                service_id=SERVICE_ID,
                task_data=task_data,
                provider_pubkey=PROVIDER_PUBLIC_KEY,
            ))
        finally:
            loop.close()
    except Exception as e:
        is_valid = False
        error = f"Verification error: {str(e)}"
        payment_details = None
        import traceback
        traceback.print_exc()
    
    if not is_valid:
        print(f"❌ Payment verification failed: {error}")
        return jsonify({
            "error": "Payment verification failed",
            "details": error
        }), 402
    
    escrow_pda = payment_details['escrowPDA']
    print(f"🔒 Escrow PDA: {escrow_pda}")
    print(f"💸 Amount locked: {SERVICE_PRICE} SOL")
    
    # Perform the analysis
    print("\n🔍 Processing data analysis...")
    time.sleep(1)  # Simulate work
    
    analysis_result = {
        "trend": "15% growth",
        "correlation": 0.85,
        "insights": f"Analysis of: {task_data}",
        "data_points": 1247,
        "confidence": 0.92,
        "processed_by": "Agent A (DataAnalystAgent)"
    }
    
    print("📊 Analysis complete")
    
    # Submit proof to escrow - REAL ON-CHAIN TRANSACTION
    print("📤 Submitting proof to escrow...")
    try:
        from agents.utils.solana_utils import submit_proof_for_task, load_agent_wallet
        import json
        
        provider_wallet = load_agent_wallet("DataAnalystAgent")
        proof_data = json.dumps(analysis_result)
        
        proof_signature = await submit_proof_for_task(
            provider_wallet=provider_wallet,
            escrow_pda=escrow_pda,
            proof_data=proof_data
        )
        
        print(f"✅ Proof submitted!")
        print(f"   Transaction: {proof_signature}")
        print(f"   🔗 https://explorer.solana.com/tx/{proof_signature}?cluster=devnet")
    except Exception as e:
        print(f"❌ Proof submission failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Proof submission failed"}), 500
    
    # Return successful response
    print("\n🎉 Service completed successfully")
    
    return jsonify({
        "result": analysis_result,
        "paymentDetails": {
            "escrowPDA": escrow_pda,
            "proofSubmitTx": proof_signature,
            "amountPaid": SERVICE_PRICE,
            "serviceId": SERVICE_ID,
            "explorerUrls": {
                "proof": f"https://explorer.solana.com/tx/{proof_signature}?cluster=devnet" if proof_signature else None,
            }
        }
    }), 200


def run_http_server():
    """Run Flask HTTP server in a separate thread."""
    print("="*70)
    print("🚀 Agent A x402 HTTP Server Started")
    print("="*70)
    print(f"📍 HTTP Listening on http://localhost:{HTTP_PORT}")
    print(f"💰 Service Price: {SERVICE_PRICE} SOL")
    print(f"🔐 Payment Method: Escrow-based x402")
    print(f"📋 Service ID: {SERVICE_ID}")
    print(f"🏦 Provider: {PROVIDER_PUBLIC_KEY}")
    print("="*70)
    print("\nEndpoints:")
    print(f"  GET  /          - Service info")
    print(f"  GET  /health    - Health check")
    print(f"  GET  /analyze   - Data analysis (x402 protected)")
    print("\nWaiting for requests...")
    print()
    
    app.run(host='0.0.0.0', port=HTTP_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    # Start HTTP server in a separate thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Include the chat protocol
    agent.include(chat_proto)
    
    print("\n" + "="*70)
    print("🤖 Agent A (DataAnalystAgent) - Dual Interface Mode")
    print("="*70)
    print(f"📡 uAgents Chat Protocol: Port 5051")
    print(f"🌐 HTTP x402 Server: Port {HTTP_PORT}")
    print(f"🏦 Solana Wallet: {PROVIDER_PUBLIC_KEY}")
    print("="*70)
    print("\nAgent A is ready to:")
    print("  1. Accept chat messages from other agents (uAgents)")
    print("  2. Serve x402-protected HTTP requests")
    print("\nPress Ctrl+C to stop")
    print("="*70)
    print()
    
    # Run the uAgents agent
    agent.run()
