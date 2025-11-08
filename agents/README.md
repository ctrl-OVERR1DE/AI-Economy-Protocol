# AEP Agents

Provider and client agents that demonstrate autonomous service delivery with escrowed, token-based payments and x402 proof gating.

---

## Agents

- CodeReviewAgent (provider)
- ContentAnalystAgent (provider)
- TranslatorAgent (provider)
- ClientAgent (consumer)

All providers register with the Marketplace API on startup and appear in the Dashboard. The ClientAgent discovers a provider, initializes escrow, and drives an end-to-end demo.

---

## Prerequisites

- Python 3.10+
- pip
- Solana CLI (for wallets): https://docs.solana.com/cli/install-solana-cli-tools
- A Devnet SPL token mint (see TEST_MINT)

---

## Environment

Copy the root `.env.example` to `.env` and review:

- SOLANA_RPC_URL (default Devnet RPC)
- TEST_MINT (SPL mint used as the payment currency)
- Optional: SOLANA_WALLET_PATH (fallback if agent-specific wallet not found)

Wallets expected by agents (auto-loaded):
- `~/.config/solana/clientagent_id.json`
- `~/.config/solana/codereviewagent_id.json`
- `~/.config/solana/contentanalystagent_id.json`
- `~/.config/solana/translatoragent_id.json`

If these files are absent, set `SOLANA_WALLET_PATH` to a valid keypair JSON.

---

## Wallets & Tokens Setup (Recommended)

1) Create agent wallets (bash paths shown)
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
- (Optional) `CLIENT_TOKEN_ACCOUNT`, `ESCROW_TOKEN_ACCOUNT`

5) Dashboard config
- In `dashboard/frontend/.env.local`, set:
```
NEXT_PUBLIC_TOKEN_MINT=<same TEST_MINT>
```

Sanity check
- `solana balance -k ~/.config/solana/clientagent_id.json` shows some SOL
- `spl-token balance <TEST_MINT> --owner $(solana address -k ~/.config/solana/clientagent_id.json)` shows ~1000 Tokens

---

## Install

```bash
pip install -r requirements.txt
```

---

## Run Providers

In separate terminals:

```bash
python agents/code_review_agent.py
python agents/content_analyst_agent.py
python agents/translator_agent.py
```

Each provider will register with the Marketplace (http://localhost:8000) and show up on the Dashboard.

---

## Run Client (optional demo)

```bash
python agents/agent_b.py
```

What happens:
- Client discovers a provider and requests pricing
- Client initializes escrow with amount in Tokens (SPL, 6 decimals)
- Provider completes work and submits proof on-chain
- Provider claims payment via x402 gateway; Marketplace stats update

---

## Notes on Tokens and Accounts

- The system uses an SPL token mint (`TEST_MINT`) for payments.
- Token accounts (ATA) are derived automatically for client, escrow PDA, and provider when needed.
- For real on-chain transfers, ensure the Client wallet holds sufficient balance of the SPL mint on Devnet.

---

## Troubleshooting

- Provider not visible on Dashboard
  - Ensure Marketplace API is running (http://localhost:8000)
  - Check provider startup logs for `/providers/register` status

- Jobs/volume remain 0
  - Ensure providers use `GatewayClient` which creates/updates Marketplace requests automatically
  - Check `marketplace/data/requests.json` and `/stats`

- Payment not released (x402 loop)
  - Proof might not be verified yet. Provider will retry automatically.
  - Confirm the correct `escrow_pda` is used and proof was submitted by provider.

- Balances show 0
  - Providers' on-chain balances are fetched by the dashboard from the Marketplace API via RPC (HELIUS_RPC_URL). Ensure the provider wallet actually holds the mint.

---

## License

MIT
