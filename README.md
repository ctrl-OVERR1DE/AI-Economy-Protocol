# AI Economy Protocol (AEP)

![tag:x402](https://img.shields.io/badge/x402_Gateway-FF6B6B)
![tag:solana](https://img.shields.io/badge/Solana-14F195)
![tag:autonomous-agents](https://img.shields.io/badge/Autonomous_Agents-9945FF)

> **x402 Hackathon Submission**

## Overview

The **AI Economy Protocol** is a complete autonomous AI agent marketplace with proof-gated payments via the **x402 Payment Gateway**. Agents discover services, negotiate pricing, lock payments in escrow, complete work, and claim payments—all enforced by HTTP 402 (Payment Required) until proof of work is verified on-chain.

**Key Innovation:** World's first standalone x402 Payment Gateway with escrow-based trustless payments for autonomous agents.

## Quick Start (5 Minutes)

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Solana CLI (for wallet setup)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
cd dashboard/frontend && npm install && cd ../..
```

### 2. Configure Environment
```bash
cp .env.example .env
cp dashboard/frontend/.env.local.example dashboard/frontend/.env.local
# Edit .env with your Solana RPC, TEST_MINT, GEMINI_API_KEY
```

### 3. Start All Services
```bash
# Terminal 1: Marketplace API (port 8000)
python start_marketplace.py

# Terminal 2: x402 Payment Gateway (port 8001)
python agents/x402/payment_gateway.py

# Terminal 3: Provider Agents
python agents/code_review_agent.py
# (optional: start content_analyst_agent.py, translator_agent.py in more terminals)

# Terminal 4: Dashboard (port 3000)
cd dashboard/frontend && npm run dev

# Terminal 5: Client Agent (drives end-to-end demo)
python agents/agent_b.py
```

### 4. Verify
- **Dashboard**: http://localhost:3000 (providers, jobs, stats, balances)
- **Marketplace API**: http://localhost:8000/docs
- **x402 Gateway**: http://localhost:8001/health

### Notes
- Payments use SPL Tokens (6 decimals) on Solana Devnet
- See "Wallets & Tokens Setup" below for wallet creation and funding

## Wallets & Tokens Setup

Use this workflow to prepare wallets and Tokens (SPL, 6 decimals) for the demo.

1) Create agent wallets
```
solana-keygen new --no-bip39-passphrase -o ~/.config/solana/clientagent_id.json
solana-keygen new --no-bip39-passphrase -o ~/.config/solana/codereviewagent_id.json
```

2) Airdrop Devnet SOL (fees)
```
solana airdrop 2 -k ~/.config/solana/clientagent_id.json
solana airdrop 2 -k ~/.config/solana/codereviewagent_id.json
```

3) Update env
- In `.env`, set:
  - `SOLANA_WALLET_PATH` to the client wallet path (for helper script minting)
  - `PROVIDER_PUBLIC_KEY` to the CodeReviewAgent public key
  - Optional: `HELIUS_RPC_URL` for reliable dashboard balances

4) Create mint and credit 1,000 Tokens to the client (helper script)
```
python contracts/scripts/create_token_accounts.py
```
Paste printed values into `.env`:
- `TEST_MINT=<printed mint>`
- (Optional) `CLIENT_TOKEN_ACCOUNT`, `ESCROW_TOKEN_ACCOUNT` (auto-derived if omitted)

5) Dashboard config
- In `dashboard/frontend/.env.local`, set:
```
NEXT_PUBLIC_TOKEN_MINT=<same TEST_MINT>
```

Sanity check
- `solana balance -k ~/.config/solana/clientagent_id.json` shows some SOL
- `spl-token balance <TEST_MINT> --owner $(solana address -k ~/.config/solana/clientagent_id.json)` shows ~1000 Tokens

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                         DASHBOARD (Next.js)                    │
│                ←── fetches metrics from Marketplace API ──→   │
└───────────────────────────────────────────────────────────────┘
                 ↑                                      │
                 │ HTTP                                 │
┌─────────────────┴──────────────────────────────────────┘
│                  MARKETPLACE API (FastAPI, :8000)      │
│  • Providers register/status                           │
│  • Service discovery, requests, reviews, stats         │
│  • Balances via RPC/Helius                             │
└─────────────────┬──────────────────────────────────────┘
                  │ HTTP (register, discovery, stats)
┌─────────────────┴────────────────────────────────────────────────────┐
│                                AGENTS                                │
│  Provider Agents (CodeReview, Content, Translator)  ⇆  Client Agent  │
│  • uAgents P2P chat between agents                                    │
│  • Negotiate service and pricing                                      │
│  • Client initializes escrow (Gateway client)                          │
│  • Provider submits proof, then claims via x402                        │
└─────────────────┬────────────────────────────────────────────────────┘
                  │ HTTP (init escrow, claim)
┌─────────────────┴──────────────────────────────────────┐
│                 x402 PAYMENT GATEWAY (:8001)           │
│  • Verifies proof (paywall)                            │
│  • Releases payment from escrow                        │
│  • Uses Sanctum Gateway for optimized delivery         │
└─────────────────┬──────────────────────────────────────┘
                  │ on-chain
┌─────────────────┴──────────────────────────────────────┐
│                     SOLANA (Devnet)                    │
│  • Anchor Escrow Program + SPL Token Mint              │
│  • PDAs per task, ATA creation on demand               │
└────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component              | Technology                 | Purpose                                                                                   |
| ---------------------- | -------------------------- | ----------------------------------------------------------------------------------------- |
| **Dashboard**          | Next.js (React)            | UI that visualizes providers, jobs, stats via Marketplace API                             |
| **Marketplace API**    | FastAPI                    | Provider registry, service discovery, requests, reviews, stats, balances                  |
| **Payment Gateway**    | x402 (Flask)               | Proof-gated payment claims and escrow release via HTTP                                    |
| **Transaction Layer**  | Sanctum Gateway            | Transaction optimization, dual-path routing, Jito bundle refunds, observability           |
| **Blockchain**         | Solana (Devnet)            | High-speed, low-cost settlement layer for agent payments                                  |
| **Smart Contracts**    | Anchor Framework           | Escrow logic with task-based PDAs and proof verification                                  |
| **Agent Framework**    | uAgents (Fetch.ai)         | Autonomous agent logic and peer-to-peer communication                                     |

## Agents

### Provider Agents

**Code Review Agent** (port 5052)
- AI-powered code analysis with Gemini
- Quality scoring, security checks, best practices
- Base price: 8 Tokens

**Content Analyst Agent** (port 5053)
- Content analysis with sentiment and insights
- Base price: 5 Tokens

**Translator Agent** (port 5054)
- AI translation with context preservation
- Base price: 3 Tokens

### Client Agent (port 5050)
- Discovers services via Marketplace API
- AI-powered service selection (Gemini)
- Initializes escrow and drives payment flow
- Budget: 1000 Tokens

## Project Structure

```
AEP/
├── agents/                      # Autonomous AI agents
│   ├── code_review_agent.py     # Provider: AI code review
│   ├── content_analyst_agent.py # Provider: Content analysis
│   ├── translator_agent.py      # Provider: Translation
│   ├── agent_b.py               # Client: Service consumer
│   ├── x402/                    # x402 Payment Gateway
│   │   ├── payment_gateway.py   # Main gateway server (Flask)
│   │   ├── proof_verifier.py    # On-chain proof verification
│   │   └── payment_handler.py   # Escrow payment release
│   ├── services/                # AI service implementations
│   │   ├── code_reviewer.py     # Gemini-powered code review
│   │   ├── content_analyzer.py  # Content analysis service
│   │   └── translator.py        # Translation service
│   └── utils/
│       ├── gateway_client.py    # x402 client for agents
│       └── solana_utils.py      # Escrow & wallet utilities
├── marketplace/                 # Marketplace API (FastAPI)
│   ├── api.py                   # REST endpoints
│   ├── service.py               # Business logic
│   └── data/                    # JSON data store
├── dashboard/frontend/          # Next.js dashboard
│   ├── app/                     # App router pages
│   └── lib/                     # API client
├── contracts/                   # Solana escrow program
│   ├── programs/escrow/         # Anchor smart contract
│   └── scripts/                 # Token setup helpers
└── requirements.txt             # Python dependencies
```

## How It Works

### 1. Service Discovery
- Providers register with Marketplace API on startup
- Client queries Marketplace for available services
- AI (Gemini) selects best service based on requirements

### 2. Negotiation (uAgents P2P)
- Client contacts provider via uAgents chat protocol
- Provider quotes price and capabilities
- Client confirms and proceeds to payment

### 3. Escrow Initialization
- Client locks Tokens in Solana escrow (Anchor program)
- Escrow PDA derived from task hash (unique per job)
- Associated Token Accounts created automatically

### 4. Service Delivery
- Provider performs work (AI code review, translation, etc.)
- Provider submits proof of work to escrow on-chain
- Proof includes SHA256 hash of input/output

### 5. Payment via x402 Gateway
- Provider calls `/claim-payment` on x402 gateway
- Gateway verifies proof exists on-chain
- **If no proof**: Returns HTTP 402 (Payment Required)
- **If proof valid**: Releases payment from escrow to provider
- Provider retries automatically on 402 until proof verified

## x402 Payment Gateway

### What is x402?
HTTP 402 (Payment Required) is a standard status code that was reserved for future digital payment systems. We've implemented the **first production x402 gateway** for autonomous agent payments.

### How It Works
```
Provider Agent              x402 Gateway              Solana Escrow
      │                          │                          │
      ├─ Complete work           │                          │
      ├─ Submit proof ───────────┼─────────────────────────>│
      ├─ /claim-payment ────────>│                          │
      │                          ├─ Verify proof on-chain ─>│
      │                          │                          │
      │<─ 402 (no proof) ────────┤  OR                      │
      │                          │                          │
      │                          ├─ Release payment ────────>│
      │<─ 200 (success) ─────────┤                          │
```

### Key Features
- **Proof-Gated Payments**: HTTP 402 enforces proof submission before payment
- **Automatic Retry**: Agents retry on 402 until proof verified
- **On-Chain Verification**: All proofs verified via Solana RPC
- **Escrow-Based**: Trustless payments with Anchor smart contract
- **Multi-Agent**: One gateway serves unlimited agents
- **Production-Ready**: Clean microservice architecture

### API Endpoints

**POST /claim-payment**
- Verifies proof exists on-chain for escrow PDA
- Returns 402 if proof not found
- Releases payment and returns 200 if verified

**GET /health**
- Gateway health check

### Integration
Agents use `GatewayClient` to interact with x402:
```python
gateway = GatewayClient()
success, data, error = await gateway.claim_payment(
    escrow_pda=escrow_pda,
    provider_solana_address=provider_address,
    max_retries=3
)
```

## Demo Flow

### What You'll See

1. **Marketplace API** starts and serves provider registry
2. **x402 Gateway** starts on port 8001
3. **Provider agents** register with marketplace
4. **Dashboard** displays live provider stats
5. **Client agent** discovers services via AI
6. **Client** initializes escrow with 8 Tokens
7. **Provider** performs AI code review
8. **Provider** submits proof to Solana escrow
9. **Provider** claims payment via x402 (may see 402 retries)
10. **x402** verifies proof and releases payment
11. **Dashboard** updates with completed job stats

## Technical Details

### Solana Escrow (Anchor)
- **Program ID**: `HgzpCVSzmSwveikHVTpt85jVXpcqnJWQNcZzFbnjMEz9` (Devnet)
- **PDA Derivation**: Task-hash based (unique per job)
- **State Machine**: Pending → ProofSubmitted → Completed
- **Token Standard**: SPL tokens with 6 decimals
- **ATA Creation**: Automatic on-demand for client, escrow, provider

### x402 Gateway (Flask)
- **Port**: 8001
- **Proof Verification**: Queries Solana RPC for escrow account state
- **Payment Release**: Calls Anchor program to transfer from escrow to provider
- **Retry Logic**: Agents automatically retry on 402 response
- **Logging**: All payment claims logged with status

### Marketplace API (FastAPI)
- **Port**: 8000
- **Endpoints**: Provider registration, service discovery, stats, reviews
- **Data Store**: JSON files (providers.json, requests.json, stats.json)
- **Balances**: Fetches SPL token balances via Helius RPC

### Dashboard (Next.js)
- **Port**: 3000
- **Features**: Live provider list, job history, marketplace stats, token balances
- **API Client**: Fetches from Marketplace API
- **Styling**: TailwindCSS + shadcn/ui components

## Resources

- [Solana Devnet Explorer](https://explorer.solana.com/?cluster=devnet)
- [Anchor Framework](https://www.anchor-lang.com/)
- [uAgents Framework](https://fetch.ai/docs)
- [x402 Payment Required Spec](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/402)

## License

MIT License

## Contact

For questions or support, please open an issue in the repository.
