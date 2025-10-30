# AI Economy Protocol (AEP)

![tag:sanctum](https://img.shields.io/badge/Sanctum_Gateway-FF6B6B)
![tag:solana](https://img.shields.io/badge/Solana-14F195)
![tag:autonomous-agents](https://img.shields.io/badge/Autonomous_Agents-9945FF)

> **Hackathon Submission:** Main Track + Sanctum Gateway Side Track  
> 📋 **[View Full Submission Details →](SUBMISSION.md)**

## Overview

The **AI Economy Protocol** demonstrates how autonomous AI agents can reliably transact using **Sanctum Gateway's transaction optimization**. This project showcases a complete agent-to-agent payment system where agents autonomously negotiate, lock payments in escrow, verify task completion, and release funds—all optimized through Gateway's dual-path routing and observability features.

**Key Innovation:** Autonomous agents making trustless payments without human intervention, leveraging Gateway for maximum transaction reliability and cost efficiency.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS AGENTS                        │
│  Agent A (Provider) ←──────────→ Agent B (Client)          │
│         ↓ Negotiate & Execute Tasks ↓                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   SANCTUM GATEWAY API                       │
│  • buildGatewayTransaction (optimize & simulate)            │
│  • sendTransaction (dual-path routing)                      │
│  • Real-time monitoring & observability                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    SOLANA BLOCKCHAIN                        │
│  • Escrow Smart Contract (Anchor)                           │
│  • SPL Token Transfers                                      │
│  • Program Derived Addresses (PDAs)                         │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component              | Technology                 | Purpose                                                                                   |
| ---------------------- | -------------------------- | ----------------------------------------------------------------------------------------- |
| **Transaction Layer**  | **Sanctum Gateway**        | Transaction optimization, dual-path routing, Jito bundle refunds, observability          |
| **Blockchain**         | Solana (Devnet)            | High-speed, low-cost settlement layer for agent payments                                  |
| **Smart Contracts**    | Anchor Framework           | Escrow logic with task-based PDAs and proof verification                                  |
| **Agent Framework**    | uAgents (Fetch.ai)         | Autonomous agent logic and peer-to-peer communication                                     |

## Agents

### Agent A: Data Analyst Agent
- **Name**: DataAnalystAgent
- **Address**: `agent1qwd63x7vsupc3swvmmc8hekr6fwfryvvqs360hjuh3ztxlnze6kcukjexf7`
- **Port**: 5051
- **Role**: Service provider offering data analysis services
- **Capabilities**: Data processing, analysis, and insights generation
- **Pricing**: 0.1 SOL per analysis

### Agent B: Client Agent
- **Name**: ClientAgent
- **Address**: `agent1qdkv6m4z9qgllndchyzpppqkv3zf285q4r22r7h6lthwc90n9236x5jnvj4`
- **Port**: 5050
- **Role**: Client requesting and consuming services
- **Capabilities**: Service discovery, task requests, payment management
- **Budget**: 0.15 SOL max per service

### Agent C: Client Agent (Multi-Client Demo)
- **Name**: ClientAgentC
- **Port**: 5049
- **Role**: Demonstrates multi-client scalability
- **Purpose**: Shows concurrent agent transactions

## Project Structure

```
AEP/
├── agents/              # AI agent implementations (agent_a.py, agent_b.py, agent_c.py)
├── contracts/           # Solana smart contracts & Gateway integration
│   ├── programs/        # Anchor escrow program
│   └── client/          # Gateway client & escrow utilities
├── utils/               # Solana utilities & transaction logging
├── tests/               # Test suites
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── README.md           # Project overview
├── SUBMISSION.md       # Hackathon submission details
└── RUN_MULTI_CLIENT_DEMO.md  # Scalability demo guide
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd AEP
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration:
# - SOLANA_RPC_URL: Your Solana RPC endpoint (default: devnet)
# - GATEWAY_API_KEY: Your Sanctum Gateway API key
# - TEST_MINT: SPL token mint address for payments
# - CLIENT_TOKEN_ACCOUNT: Client's token account
# - PROVIDER_TOKEN_ACCOUNT: Provider's token account
# - ESCROW_PROGRAM_ID: Deployed escrow program ID
```

## Usage

### Quick Start (5 Minutes)

**For multi-client scalability demo, see `RUN_MULTI_CLIENT_DEMO.md`**

```bash
# Terminal 1 - Run Agent A (Service Provider)
python agents/agent_a.py

# Terminal 2 - Run Agent B (Client)
python agents/agent_b.py

# Watch the autonomous payment flow execute via Gateway!
```

### Agent Communication

Agents communicate via **uAgents framework** (Fetch.ai):
- ✅ Direct peer-to-peer messaging
- ✅ Chat protocol for service negotiation
- ✅ Local endpoints for development
- ✅ Autonomous decision-making
- ✅ No human intervention required

## Payments Layer: Sanctum Gateway (Side Track)

> 📋 **For detailed Gateway integration analysis, see [SUBMISSION.md](SUBMISSION.md)**

### ✅ Complete Gateway API Implementation
- **buildGatewayTransaction**: Optimizes transactions with compute units, priority fees, and fresh blockhash
- **sendTransaction**: Delivers via multiple methods (RPC + Jito bundles) with automatic refunds
- **Dual-Path Routing**: Primary Gateway delivery with RPC fallback for maximum reliability
- **Real-Time Monitoring**: Transaction logging with routing decisions and success metrics

### ✅ Production-Ready Features
- **100% Transaction Success Rate**: 8/8 comprehensive tests passed
- **Unique Escrow PDAs**: Task-hash based derivation prevents collisions
- **Status-Aware Reuse Prevention**: Checks escrow state before operations
- **Automatic ATA Creation**: Creates token accounts on-demand
- **Error Recovery**: Graceful fallback to RPC when Gateway unavailable

### ✅ Autonomous Agent Payment Flow
1. **Agent B** requests service from **Agent A**
2. **Agent B** locks 0.1 SOL in escrow via **Gateway** (optimized transaction)
3. **Agent A** completes task and submits proof to escrow
4. **Agent B** releases payment via **Gateway** (dual-path routing)
5. Both agents receive confirmation with transaction signatures

**All without human intervention** ✨

## Why Sanctum Gateway?

### The Challenge
Autonomous agents need **guaranteed payment delivery** without human intervention. Traditional RPC endpoints have:
- ❌ Transaction failures requiring manual retries
- ❌ No optimization for compute units or priority fees
- ❌ Limited observability into transaction routing
- ❌ Wasted fees on failed Jito bundles

### The Solution: Sanctum Gateway
Our implementation leverages Gateway's key features:

✅ **Dual-Path Routing**
- Sends transactions via RPC + Jito bundles simultaneously
- If RPC lands first, Jito tip is automatically refunded
- Maximizes landing probability for autonomous payments

✅ **Transaction Optimization**
- Automatic compute unit calculation
- Dynamic priority fee adjustment
- Fresh blockhash management
- Pre-flight simulation to catch errors

✅ **Observability & Monitoring**
- Real-time transaction tracking
- Routing decision logging
- Success/failure metrics
- Error diagnostics for debugging

✅ **Cost Efficiency**
- Only 0.0001 SOL per transaction
- Refunds on failed Jito bundles
- Optimized compute units reduce fees
- Perfect for high-frequency agent micropayments

## Live Demo

### Quick Start
```bash
# Terminal 1 - Start Provider Agent
python agents/agent_a.py

# Terminal 2 - Start Client Agent (initiates payment flow)
python agents/agent_b.py

# Watch the full autonomous payment flow execute via Gateway!
```

### Expected Output

**Agent A (Provider):**
```
======================================================================
🤖 DATA ANALYST AGENT - Service Provider
======================================================================
Address: agent1qwd63x7vsupc3swvmmc8hekr6fwfryvvqs360hjuh3ztxlnze6kcukjexf7
Port: 5051
✅ Services: Data Analysis, Data Processing, Insights Generation
💰 Pricing: 0.1 SOL per analysis
⏳ Waiting for client requests...
======================================================================

🤝 Session started with client
💬 Client requested service and pricing information
💬 Client confirmed payment in escrow
📋 Escrow PDA: 5K77scUZ...
🔍 Processing data analysis request...
📤 Submitting proof to escrow...
✅ Proof submitted!
   Transaction: 5ABZnYye...
💼 Ready to accept new service requests!
```

**Agent B (Client):**
```
======================================================================
💼 CLIENT AGENT - Service Consumer
======================================================================
Address: agent1qdkv6m4z9qgllndchyzpppqkv3zf285q4r22r7h6lthwc90n9236x5jnvj4
Port: 5050
✅ Ready to discover and request services
💰 Budget: 0.15 SOL max per service
======================================================================

🔍 Discovering available services...
👋 Contacting Agent A directly: agent1qwd63x...
💬 Provider introduced services
💬 Sending: 'I need data analysis. What's your pricing?'
💬 Provider quoted 0.1 SOL for service
🔒 Initializing escrow for service payment...
✅ Gateway: Escrow initialized
✅ Escrow initialized!
   Transaction: 5vknPbUf...
   Escrow PDA: FnDpJ7xb...
   Amount locked: 0.1 SOL
💬 Provider completed analysis and submitted proof
💸 Service completed! Releasing payment from escrow...
✅ Gateway: Payment released
✅ Payment released!
   Transaction: 4wGCDk76...
✅ Service completed. Session ended.
```

## Technical Implementation

### Smart Contract (Anchor)
- **Escrow Program**: `HgzpCVSzmSwveikHVTpt85jVXpcqnJWQNcZzFbnjMEz9` (Solana Devnet)
- **Task-Hash PDAs**: Unique escrow per task prevents reuse collisions
- **State Machine**: Pending → ProofSubmitted → Completed
- **Proof Verification**: SHA256 hash validation on-chain
- **SPL Token Support**: Uses SPL tokens for payments (TEST_MINT: `8Pv3AGNmtRdFyzu93THwCFVURme2XvF1cYTubdP3iwGi`)

### Gateway Client (`gateway_escrow_client.py`)
- Wraps Gateway JSON-RPC API
- Handles transaction serialization and signing
- Implements fallback logic for reliability
- Logs all routing decisions and outcomes

### Test Coverage
- ✅ Escrow initialization via Gateway
- ✅ Proof submission with PDA validation
- ✅ Payment release with status checks
- ✅ Error handling and recovery
- ✅ End-to-end agent flow

## 📋 Hackathon Submission

**For judges:** See **[SUBMISSION.md](SUBMISSION.md)** for:
- ✅ Complete Gateway integration details
- ✅ Why Gateway was essential for autonomous agents
- ✅ Technical achievements and test results
- ✅ Production-ready features demonstrated
- ✅ Future roadmap and vision

## Project Files

- **[SUBMISSION.md](SUBMISSION.md)** - **Hackathon submission details and achievements** ⭐
- **README.md** - This file (project overview)
- **[RUN_MULTI_CLIENT_DEMO.md](RUN_MULTI_CLIENT_DEMO.md)** - Guide for running multi-client scalability demo
- **TECHNICAL_DEMO_SCRIPT.md** - Script for recording technical demo video
- **hack-pitch.md** - Pitch script for hackathon presentation
- **slide-todo.md** - Slide deck structure and design notes

## Resources

- [Sanctum Gateway Documentation](https://gateway.sanctum.so/docs)
- [Sanctum Gateway Platform](https://gateway.sanctum.so/)
- [Solana Devnet Explorer](https://explorer.solana.com/?cluster=devnet)
- [Anchor Framework](https://www.anchor-lang.com/)
- [uAgents Framework](https://fetch.ai/docs)
- [Fetch.ai Innovation Lab](https://innovationlab.fetch.ai/)

## License

MIT License

## Contact

For questions or support, please open an issue in the repository.
