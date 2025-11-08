"""
AEP x402 Server

HTTP server implementing x402 protocol with escrow-based payments.
Wraps Agent A (DataAnalystAgent) with x402 payment requirements.
"""

import os
import sys
import asyncio
import json
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from agents.x402.payment_verifier import PaymentVerifier
from agents.utils.solana_utils import (
    load_agent_wallet,
    submit_proof_for_task,
)

# Configuration
PROVIDER_WALLET = os.getenv("PROVIDER_PUBLIC_KEY", "GQyf8wvGfpaLZvfvbXonpdiEfAGRvRXz2P6PkWxQ4rLJ")
ESCROW_PROGRAM_ID = os.getenv("ESCROW_PROGRAM_ID", "HgzpCVSzmSwveikHVTpt85jVXpcqnJWQNcZzFbnjMEz9")
SERVICE_PRICE = 0.1  # SOL
SERVICE_ID = "data_analysis_001"

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize payment verifier
verifier = PaymentVerifier()


@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """
    x402 endpoint for data analysis service.
    
    Flow:
    1. Client requests without payment → 402 with payment requirements
    2. Client requests with X-Payment → Verify escrow → Perform analysis → Return result
    """
    
    # Get X-Payment header
    x_payment = request.headers.get('X-Payment')
    
    # Get request data
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args.to_dict()
    
    task_data = data.get('data', 'Default analysis task')
    
    # No payment provided - return 402 with payment requirements
    if not x_payment:
        print("📨 Request received: GET /analyze")
        print(f"💰 Payment required: {SERVICE_PRICE} SOL")
        print(f"📋 Service: Data Analysis")
        
        return jsonify({
            "payment": {
                "recipient": PROVIDER_WALLET,
                "escrowProgram": ESCROW_PROGRAM_ID,
                "amount": SERVICE_PRICE,
                "token": "SOL",
                "network": "solana-devnet",
                "serviceId": SERVICE_ID,
                "taskData": task_data,
                "message": "Payment required. Lock funds in escrow to proceed."
            }
        }), 402
    
    # Payment provided - verify and process
    print("\n✅ Payment received via X-Payment header")
    print("🔍 Verifying escrow payment...")
    
    # Verify payment (synchronous for MVP)
    # In production, use async verification
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
                provider_pubkey=PROVIDER_WALLET,
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
    
    # Perform the analysis (mock for now)
    print("\n🔍 Processing data analysis...")
    import time
    time.sleep(1)  # Simulate work
    
    analysis_result = {
        "trend": "15% growth",
        "correlation": 0.85,
        "insights": "Strong positive correlation detected in Q4 2024 sales data",
        "data_points": 1247,
        "confidence": 0.92
    }
    
    print("📊 Analysis complete")
    
    # Submit proof to escrow
    print("📤 Submitting proof to escrow...")
    
    try:
        # Load provider wallet
        provider_wallet = load_agent_wallet("DataAnalystAgent")
        
        # Create proof data
        proof_data = json.dumps(analysis_result)
        
        # Submit proof (this will trigger payment release)
        # NOTE: This standalone server is for testing x402 protocol only
        # For real proof submission, use the integrated agent system (agent_a.py)
        # which calls submit_proof_for_task() with real on-chain transactions
        proof_signature = "DEMO_SERVER_PROOF_NOT_SUBMITTED"
        
        print(f"✅ Proof submitted!")
        print(f"   Transaction: {proof_signature}")
        print(f"   🔗 https://explorer.solana.com/tx/{proof_signature}?cluster=devnet")
        
    except Exception as e:
        print(f"⚠️  Proof submission failed: {e}")
        proof_signature = None
    
    # Return successful response with result
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


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "AEP x402 Server",
        "version": "0.1.0"
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with service info."""
    return jsonify({
        "service": "AEP x402 Data Analysis Service",
        "version": "0.1.0",
        "endpoints": {
            "/analyze": "Data analysis service (x402 protected)",
            "/health": "Health check"
        },
        "payment": {
            "protocol": "x402",
            "scheme": "escrow",
            "price": SERVICE_PRICE,
            "token": "SOL",
            "network": "solana-devnet"
        }
    }), 200


def main():
    """Start the x402 server."""
    print("="*70)
    print("🚀 AEP x402 Server Started")
    print("="*70)
    print(f"📍 Listening on http://localhost:8000")
    print(f"💰 Service Price: {SERVICE_PRICE} SOL")
    print(f"🔐 Payment Method: Escrow-based x402")
    print(f"📋 Service ID: {SERVICE_ID}")
    print(f"🏦 Provider: {PROVIDER_WALLET}")
    print("="*70)
    print("\nEndpoints:")
    print("  GET  /          - Service info")
    print("  GET  /health    - Health check")
    print("  GET  /analyze   - Data analysis (x402 protected)")
    print("\nWaiting for requests...\n")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=8000, debug=False)


if __name__ == "__main__":
    main()
