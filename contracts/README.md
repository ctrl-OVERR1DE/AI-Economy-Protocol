# AEP Contracts (Escrow + Token Setup)

This folder contains the Solana escrow program (pre-deployed on Devnet) and helper scripts for SPL token setup used by the demo.

---

## Do I need to deploy anything?

No. The demo points to a pre-deployed escrow program on Devnet via `ESCROW_PROGRAM_ID` in `.env`.

- Program: `HgzpCVSzmSwveikHVTpt85jVXpcqnJWQNcZzFbnjMEz9`
- Network: Devnet

Ensure your `.env` contains:

```env
SOLANA_RPC_URL=https://api.devnet.solana.com
ESCROW_PROGRAM_ID=HgzpCVSzmSwveikHVTpt85jVXpcqnJWQNcZzFbnjMEz9
TEST_MINT=8Pv3AGNmtRdFyzu93THwCFVURme2XvF1cYTubdP3iwGi
```

`TEST_MINT` is the SPL token mint used as “Tokens” (6 decimals) in this project.

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

3) Create mint and credit 1,000 Tokens to the client (helper script)
```
python contracts/scripts/create_token_accounts.py
```
Paste printed values into `.env`:
- `TEST_MINT=<printed mint>`
- (Optional) `CLIENT_TOKEN_ACCOUNT`, `ESCROW_TOKEN_ACCOUNT` (auto-derived if omitted)

4) Dashboard config
- In `dashboard/frontend/.env.local`, set:
```
NEXT_PUBLIC_TOKEN_MINT=<same TEST_MINT>
```

Notes
- Agents auto-load wallets from `~/.config/solana/{agentname}_id.json` (lowercase names).
- You can override with `SOLANA_WALLET_PATH` in `.env` if needed.

---

## Optional: Create a fresh test mint and ATAs

If you prefer to create your own test mint and token accounts, use:

```bash
python contracts/scripts/create_token_accounts.py
```

It will print values to add to your `.env`:

- `TEST_MINT`
- `CLIENT_TOKEN_ACCOUNT`
- `ESCROW_TOKEN_ACCOUNT`
- `PROVIDER_PUBLIC_KEY`

Note: The demo code derives missing ATAs automatically when needed, so this step is not required.

---

## Where the program is used

- Agents lock Tokens in escrow via the `GatewayEscrowClient`
- Providers submit proofs; the x402 gateway releases payment after verification

You can update `SOLANA_RPC_URL` to any Devnet RPC. For dashboard balances, the Marketplace can also use `HELIUS_RPC_URL` to fetch token accounts reliably.

---

## Troubleshooting

- Program ID mismatch
  - Ensure `ESCROW_PROGRAM_ID` in `.env` matches the program deployed on Devnet (see above).

- Insufficient Tokens
  - Fund the client wallet’s token account for the configured mint.

- Wallet not found
  - Agents load wallets from `~/.config/solana/<agent>_id.json` or `SOLANA_WALLET_PATH`. Create with `solana-keygen new`.

---

## License

MIT
