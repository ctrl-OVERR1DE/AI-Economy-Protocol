"""
x402 Payment Gateway - Standalone Service

This is a standalone payment gateway that enforces x402 paywall restrictions
for all agents in the AEP system. It handles:
- Payment claim requests from service providers
- Proof-of-work verification
- Escrow payment release
- x402 protocol enforcement

Architecture:
- Agents submit proofs to escrow
- Agents request payment via gateway
- Gateway checks proof verification
- Gateway returns 402 if proof not verified
- Gateway releases payment if proof verified

Port: 8001
"""

import sys
import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Import gateway modules
from agents.x402.proof_verifier import ProofVerifier
from agents.x402.payment_handler import PaymentHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable httpx logging to prevent API key exposure
logging.getLogger("httpx").setLevel(logging.WARNING)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize modules
proof_verifier = ProofVerifier()
payment_handler = PaymentHandler()

# Configuration
GATEWAY_PORT = 8001


@app.route('/', methods=['GET'])
def index():
    """Gateway info endpoint."""
    return jsonify({
        "service": "AEP x402 Payment Gateway",
        "version": "1.0.0",
        "protocol": "x402",
        "description": "Standalone payment gateway for autonomous agent payments",
        "endpoints": {
            "/claim-payment": "POST - Claim payment from escrow (x402 protected)",
            "/verify-proof": "POST - Verify proof status for escrow",
            "/health": "GET - Health check"
        },
        "features": [
            "x402 paywall enforcement",
            "Proof-of-work verification",
            "Escrow payment release",
            "Multi-agent support"
        ]
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "x402 Payment Gateway",
        "port": GATEWAY_PORT
    }), 200


@app.route('/verify-proof', methods=['POST'])
def verify_proof():
    """
    Verify proof status for an escrow.
    
    Request:
        {
            "escrow_pda": "string"
        }
    
    Response:
        {
            "verified": bool,
            "status": "pending" | "verified" | "not_found",
            "details": "string"
        }
    """
    try:
        data = request.get_json()
        escrow_pda = data.get('escrow_pda')
        
        if not escrow_pda:
            return jsonify({
                "error": "Missing escrow_pda"
            }), 400
        
        logger.info(f"🔍 Verifying proof for escrow: {escrow_pda}")
        
        # Verify proof using async verification
        import nest_asyncio
        nest_asyncio.apply()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            verified, status, details = loop.run_until_complete(
                proof_verifier.verify_proof(escrow_pda)
            )
        finally:
            loop.close()
        
        if verified:
            logger.info(f"✅ Proof verified for {escrow_pda}")
        else:
            logger.info(f"❌ Proof not verified: {details}")
        
        return jsonify({
            "verified": verified,
            "status": status,
            "details": details
        }), 200
        
    except Exception as e:
        logger.error(f"Error verifying proof: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Proof verification failed",
            "details": str(e)
        }), 500


@app.route('/claim-payment', methods=['POST'])
def claim_payment():
    """
    x402 Paywall: Claim payment from escrow.
    
    This is the core x402 paywall endpoint. It enforces that providers
    can only claim payment AFTER submitting and verifying proof-of-work.
    
    Request:
        {
            "escrow_pda": "string",
            "provider_address": "string"
        }
    
    Response (402 - Payment Required):
        {
            "error": "Proof not verified",
            "details": "Submit proof of work first",
            "escrow_pda": "string",
            "status": "pending"
        }
    
    Response (200 - Success):
        {
            "status": "Payment released",
            "escrow_pda": "string",
            "amount": float,
            "tx_signature": "string",
            "explorer_url": "string"
        }
    """
    try:
        data = request.get_json()
        escrow_pda = data.get('escrow_pda')
        provider_address = data.get('provider_address')
        
        if not escrow_pda:
            return jsonify({
                "error": "Missing escrow_pda"
            }), 400
        
        if not provider_address:
            return jsonify({
                "error": "Missing provider_address"
            }), 400
        
        logger.info(f"\n{'='*70}")
        logger.info(f"💰 Payment Claim Request")
        logger.info(f"{'='*70}")
        logger.info(f"Escrow PDA: {escrow_pda}")
        logger.info(f"Provider: {provider_address}")
        
        # Step 1: Verify proof using async verification
        logger.info("🔍 Step 1: Verifying proof...")
        
        import nest_asyncio
        nest_asyncio.apply()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            verified, status, details = loop.run_until_complete(
                proof_verifier.verify_proof(escrow_pda)
            )
        finally:
            loop.close()
        
        if not verified:
            # x402 PAYWALL: Proof not verified
            logger.info(f"❌ x402 PAYWALL BLOCKED")
            logger.info(f"   Reason: {details}")
            logger.info(f"   Status: {status}")
            logger.info(f"{'='*70}\n")
            
            return jsonify({
                "error": "Proof not verified",
                "details": details,
                "escrow_pda": escrow_pda,
                "status": status,
                "message": "Submit and verify proof of work before claiming payment"
            }), 402  # 402 Payment Required
        
        # Step 2: Proof verified, release payment
        logger.info("✅ Proof verified!")
        logger.info("💸 Step 2: Releasing payment...")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success, tx_signature, amount, error = loop.run_until_complete(
                payment_handler.release_payment(escrow_pda, provider_address)
            )
        finally:
            loop.close()
        
        if not success:
            logger.error(f"❌ Payment release failed: {error}")
            logger.info(f"{'='*70}\n")
            return jsonify({
                "error": "Payment release failed",
                "details": error,
                "escrow_pda": escrow_pda
            }), 500
        
        # Success!
        logger.info(f"✅ Payment released successfully!")
        logger.info(f"   Transaction: {tx_signature}")
        logger.info(f"   Amount: {amount} Tokens")
        logger.info(f"   🔗 https://explorer.solana.com/tx/{tx_signature}?cluster=devnet")
        logger.info(f"{'='*70}\n")
        
        return jsonify({
            "status": "Payment released",
            "escrow_pda": escrow_pda,
            "amount": amount,
            "tx_signature": tx_signature,
            "explorer_url": f"https://explorer.solana.com/tx/{tx_signature}?cluster=devnet"
        }), 200
        
    except Exception as e:
        logger.error(f"Error claiming payment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Payment claim failed",
            "details": str(e)
        }), 500


def main():
    """Start the x402 Payment Gateway."""
    print("="*70)
    print("🚀 AEP x402 Payment Gateway")
    print("="*70)
    print(f"📍 Listening on http://localhost:{GATEWAY_PORT}")
    print(f"🔐 Protocol: x402 (Payment Required)")
    print(f"💰 Features: Proof verification + Payment release")
    print("="*70)
    print("\nEndpoints:")
    print(f"  GET  /              - Gateway info")
    print(f"  GET  /health        - Health check")
    print(f"  POST /verify-proof  - Verify proof status")
    print(f"  POST /claim-payment - Claim payment (x402 protected)")
    print("\n" + "="*70)
    print("Gateway ready to enforce x402 paywall!")
    print("Agents can now claim payments after proof verification")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=GATEWAY_PORT, debug=False)


if __name__ == "__main__":
    main()
