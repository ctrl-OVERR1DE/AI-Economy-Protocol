# AI Economy Protocol (AEP)

![tag:sanctum](https://img.shields.io/badge/Sanctum_Gateway-FF6B6B)
![tag:solana](https://img.shields.io/badge/Solana-14F195)
![tag:autonomous-agents](https://img.shields.io/badge/Autonomous_Agents-9945FF)

> Hackathon Submission: Main Track + Sanctum Gateway Side Track

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
- **Address**: TBD (after Agentverse registration)
- **Role**: Service provider offering data analysis services
- **Capabilities**: Data processing, analysis, and insights generation

### Agent B: Client Agent
- **Name**: ClientAgent
- **Address**: TBD (after Agentverse registration)
- **Role**: Client requesting and consuming services
- **Capabilities**: Service discovery, task requests, payment management

## Project Structure

```
AEP/
├── agents/              # AI agent implementations
├── contracts/           # Solana smart contracts (Stage 2)
├── utils/               # Utility functions and helpers
├── tests/               # Test files
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # This file
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
# Edit .env with your configuration
```

## Usage

### Quick Start (5 Minutes)

For a concurrency demo, see `RUN_MULTI_CLIENT_DEMO.md`.

```bash
# Terminal 1 - Run Agent A (Service Provider)
python agents/agent_a.py
# Click the Inspector URL → Connect → Select "Mailbox" → Finish

# Terminal 2 - Run Agent B (Client)
python agents/agent_b.py
# Click the Inspector URL → Connect → Select "Mailbox" → Finish

# Terminal 3 (Optional) - View Marketplace
python utils/marketplace_cli.py
```

### Mailbox Agents

Agents use **mailbox mode** to connect to Agentverse:
- ✅ No public endpoint required
- ✅ Runs locally on your machine
- ✅ Connects to Agentverse automatically
- ✅ Discoverable on ASI:One
- ✅ Secure communication via mailbox

### Marketplace Features

The marketplace provides:
- **Agent Registration**: Automatic registration of agents on startup
- **Service Advertisement**: Agents can advertise their services with pricing
- **Service Discovery**: Clients can search for services by category and price
- **Transaction Tracking**: Monitor agent transactions and reputation
- **CLI Interface**: Real-time marketplace viewing and management

## Payments Layer: Sanctum Gateway (Side Track)

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
```
[Gateway] buildGatewayTransaction response: {...}
[Gateway] sendTransaction response: {'result': '<signature>'}
[Gateway] Transaction sent successfully via Gateway!
✅ Escrow initialized!
✅ Proof submitted!
[Gateway] Payment released via Gateway!
✅ Payment released!
```

## Technical Implementation

### Smart Contract (Anchor)
- **Escrow Program**: `HgzpCVSzmSwveikHVTpt85jVXpcqnJWQNcZzFbnjMEz9`
- **Task-Hash PDAs**: Unique escrow per task prevents reuse collisions
- **State Machine**: Pending → ProofSubmitted → Completed
- **Proof Verification**: SHA256 hash validation on-chain

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

## Resources

- [Sanctum Gateway Documentation](https://gateway.sanctum.so/docs)
- [Sanctum Gateway Platform](https://gateway.sanctum.so/)
- [Solana Devnet Explorer](https://explorer.solana.com/?cluster=devnet)
- [Anchor Framework](https://www.anchor-lang.com/)

## License

MIT License

## Contact

For questions or support, please open an issue in the repository.
