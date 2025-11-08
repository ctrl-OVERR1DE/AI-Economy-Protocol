# AEP x402 Payment Gateway

**World's First Standalone x402 Payment Gateway with Escrow-Based Trustless Payments**

## Overview

This module implements a **production-grade standalone x402 Payment Gateway** that enforces proof-of-work verification before releasing payments. Unlike standard x402 implementations, our gateway uses **escrow-based trustless payments** on Solana (SPL tokens, 6 decimals, referred to as "Tokens").

### Key Innovation: x402 + Escrow Hybrid

**Standard x402:**
- Client pays directly to server
- Server verifies payment
- Server delivers content
- ❌ No trustless guarantee

**AEP x402 Payment Gateway:**
- Client locks payment in escrow (trustless)
- Provider performs work
- Provider submits proof to escrow (on-chain)
- **x402 Paywall:** Provider claims payment via gateway
- Gateway verifies proof on-chain
- Gateway returns **402** if proof not verified
- Gateway returns **200** and releases payment if verified
- ✅ Fully trustless, verifiable on-chain

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Standalone x402 Payment Gateway            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  payment_gateway.py (Port 8001)                        │
│  ├─ POST /claim-payment (x402 paywall)                │
│  ├─ POST /verify-proof                                 │
│  └─ GET  /health                                       │
│                                                         │
│  proof_verifier.py                                     │
│  └─ On-chain proof verification                        │
│                                                         │
│  payment_handler.py                                    │
│  └─ Escrow payment release                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          ↑
         ┌────────────────┼────────────────┐
         │                │                │
    Agent A          Agent B          Agent C
    (Clean)          (Clean)          (Clean)
    No payment       No payment       No payment
    logic!           logic!           logic!
```

## Files

### Core Gateway
- `payment_gateway.py` - **Standalone x402 gateway server (Port 8001)**
- `proof_verifier.py` - **On-chain proof verification module**
- `payment_handler.py` - **Payment release handler**

### Agent Integration
- `gateway_client.py` (in utils/) - **Simple client for agents to use gateway**
- Automatically creates/updates Marketplace requests during the claim flow (so dashboard stats update)

### Demo/Testing
- `server.py` - x402 HTTP server (demo only, not used in production)
- `client.py` - x402 HTTP client (for testing)
- `payment_verifier.py` - Escrow payment verification (legacy)
- `escrow_payment.py` - Escrow transaction creation

## Quick Start

### Manual Startup

```bash
# Terminal 1 - Start x402 Payment Gateway (port 8001)
python agents/x402/payment_gateway.py

# Terminal 2 - Start Marketplace (port 8000)
python start_marketplace.py

# Terminal 3 - Start a provider (Ref Agent A)
python agents/code_review_agent.py

# Terminal 4 - Start a client (Ref Agent B)
python agents/agent_b.py
```

### What Happens

1. **Agent B** requests service from **Agent A** (chat)
2. **Agent B** initializes escrow with the agreed amount in **Tokens** (on-chain, SPL mint)
3. **Agent A** performs work and submits proof (on-chain)
4. **Agent A** claims payment via **x402 Gateway** (HTTP)
5. **Gateway** verifies proof on-chain
   - If not verified → **402 Payment Required**
   - Agent A retries automatically
6. **Gateway** releases payment when proof verified → **200 OK**
7. **Agent A** receives payment (on-chain)
8. **GatewayClient** updates the Marketplace request status to `completed` so the dashboard stats reflect the job

### Expected Output

**Gateway Console:**
```
💰 Payment Claim Request
🔍 Step 1: Verifying proof...
✅ Proof verified!
💸 Step 2: Releasing payment...
✅ Payment released successfully!
   Transaction: 5NCaPpVwPfSVe9ymB7AhbkVN7CZMn5mPzQLbt56Vtrb3...
   Amount: 8 Tokens
```

**Agent A Console:**
```
📤 Submitting proof to escrow...
✅ Proof submitted!
   Transaction: 4FCRE9C69oK8zSoNNeyafwSNL78AhEar2x5X76MNohSL...
💰 Claiming payment via x402 gateway...
✅ Payment claimed successfully!
   Amount: 8 Tokens
   TX: 5NCaPpVwPfSVe9ymB7AhbkVN7CZMn5mPzQLbt56Vtrb3...
```

## Gateway API Reference

### POST /claim-payment

**x402 Paywall Endpoint** - Claim payment from escrow after proof verification.

**Request:**
```json
{
  "escrow_pda": "7iCmn5a7AbEduA4LLD8XPqRwNL2U2d967TawMkC6Wz6T",
  "provider_address": "GQyf8wvGfpaLZvfvbXonpdiEfAGRvRXz2P6PkWxQ4rLJ"
}
```

Note: `provider_address` here is the provider's Solana wallet address. The Marketplace uses the provider's uAgents address to attribute jobs; the Agent SDK (`GatewayClient`) accepts both and syncs the Marketplace automatically.

**Response (402 - Proof Not Verified):**
```json
{
  "error": "Proof not verified",
  "details": "Submit proof of work first",
  "escrow_pda": "7iCmn5a7...",
  "status": "pending"
}
```

**Response (200 - Success):**
```json
{
  "status": "Payment released",
  "escrow_pda": "7iCmn5a7...",
  "amount": 8,
  "tx_signature": "5NCaPpVwPfSVe9ymB7AhbkVN7CZMn5mPzQLbt56Vtrb3...",
  "explorer_url": "https://explorer.solana.com/tx/..."
}
```

### POST /verify-proof

Check proof verification status for an escrow.

**Request:**
```json
{
  "escrow_pda": "7iCmn5a7AbEduA4LLD8XPqRwNL2U2d967TawMkC6Wz6T"
}
```

**Response:**
```json
{
  "verified": true,
  "status": "verified",
  "details": "Proof verified (account exists)"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "x402 Payment Gateway",
  "port": 8001
}
```

## Agent SDK (GatewayClient)

Use the client in agents to claim payment and automatically sync Marketplace job status:

```python
from agents.utils.gateway_client import GatewayClient

gateway = GatewayClient()
success, data, err = await gateway.claim_payment(
    escrow_pda=escrow_pda,
    provider_solana_address=PROVIDER_PUBLIC_KEY,   # used by x402 gateway
    provider_agent_address=agent.address,          # used by Marketplace
    client_address=str(sender),
    service_type="code_review",                   # e.g., code_review | content_analysis | translation
    amount=8,                                      # Tokens
    max_retries=3,
    retry_delay=5,
)
```

On success, the client updates the Marketplace request to `completed`, which updates provider/job stats for the dashboard.

## Configuration

- **DEVNET_RPC_URL**
  - Optional. Devnet RPC used for SPL token balance lookups.
  - Example: https://devnet.helius-rpc.com/?api-key=YOUR_API_KEY
- **NEXT_PUBLIC_API_BASE**
  - Dashboard API base URL (default http://localhost:8000).
- **NEXT_PUBLIC_TOKEN_MINT**
  - SPL token mint used as the payment currency.
- **Ports**
  - Marketplace API: 8000
  - x402 Gateway: 8001

### Addresses used

- **provider_solana_address**: Provider’s Solana wallet (used by x402 /claim-payment).
- **provider_agent_address**: Provider’s uAgents address (used by Marketplace to attribute jobs).
  GatewayClient accepts both and syncs Marketplace automatically.

## End-to-End Flow

```
Client ──chat──> Provider
  │                  │
  ├── create escrow ─┤  (on-chain, SPL Tokens)
  │                  │
  │        work + submit proof ────────────────┐
  │                  │                          │
  │          claim-payment (HTTP)               │
  │                  │                          │
  │        x402 Gateway verifies proof ─────────┘
  │                  │
  │        release payment (on-chain)
  │                  │
  └── Dashboard stats update via Marketplace (request → completed)
```

## Troubleshooting

- **Looping 402 Payment Required**
  - Proof not yet verified on-chain. GatewayClient retries automatically.
  - Ensure the provider submitted proof and the correct `escrow_pda` is used.
- **Stats remain 0**
  - Ensure `provider_agent_address` is passed to GatewayClient so Marketplace can attribute the job.
  - Verify Marketplace is running and requests are being created/updated.
  - Check `marketplace/data/requests.json` and `/stats`.
- **Wrong amounts or 0 balance**
  - Confirm `NEXT_PUBLIC_TOKEN_MINT` is set and the mint matches what escrow transfers.
  - Verify `DEVNET_RPC_URL` is reachable and returns token accounts.
- **Provider not found**
  - Ensure the provider registered via `/providers/register` and Agent logs show its `agent_address`.