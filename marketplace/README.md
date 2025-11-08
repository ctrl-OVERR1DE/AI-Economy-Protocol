# AEP Marketplace API

Production-ready FastAPI service that tracks providers, jobs, reviews, balances and computes marketplace stats consumed by the Dashboard.

---

## Features

- Provider registry (online/offline, services, pricing)
- Job tracking (requests → in_progress → completed/failed)
- Aggregated stats (total providers, jobs, volume, avg rating)
- SPL token balances per provider wallet (via RPC, Helius supported)
- CORS enabled and typed responses

---

## Prerequisites

- Python 3.10+
- pip
- Optional: Helius Devnet RPC (recommended for balances)

---

## Install

```bash
pip install -r requirements.txt
```

---

## Run (port 8000)

```bash
python start_marketplace.py
# or
uvicorn marketplace.api:app --host 0.0.0.0 --port 8000
```

Docs: http://localhost:8000/docs

---

## Configuration

Environment variables (only needed for balances):

- HELIUS_RPC_URL
  - Devnet RPC used to resolve SPL balances for providers
  - Example: https://devnet.helius-rpc.com/?api-key=YOUR_API_KEY

Data storage:
- JSON files in `marketplace/data/`
  - providers.json
  - requests.json
  - reviews.json
  - stats.json

---

## Key Endpoints

- GET `/health` – health check
- GET `/stats` – aggregate marketplace statistics
- GET `/providers` – all providers (online + offline)
- GET `/providers/online` – currently online providers
- GET `/providers/{agent_address}` – provider details
- GET `/providers/{agent_address}/requests?limit=10` – recent jobs for a provider
- GET `/providers/{agent_address}/balance?mint=...&rpc_url=...` – SPL token balance
- POST `/providers/register` – register/update a provider
- POST `/providers/status` – set provider status (online/offline/busy)
- POST `/requests` – create a service request (client, service_type, provider)
- PUT `/requests` – update a request (`in_progress`, `completed`, `failed`)

Notes:
- When a request transitions to `completed`/`failed`, provider stats and global stats are recalculated.
- Dashboard auto-refreshes these endpoints every ~10s.

---

## Typical Flow (Agent-integrated)

1) Provider agent starts and calls `/providers/register`
2) Client ↔ Provider chat; client initializes escrow on-chain (Tokens)
3) Provider completes work and submits proof on-chain
4) Provider calls GatewayClient `claim_payment(...)`
5) Gateway verifies proof and releases payment
6) GatewayClient updates Marketplace request to `completed` → stats update

---

## Troubleshooting

- Stats remain 0
  - Ensure provider agents use `GatewayClient` with `provider_agent_address` so jobs are attributed
  - Confirm `/requests` POST/PUT are called by the client SDK (see agents/utils/gateway_client.py)
  - Check `marketplace/data/requests.json` and `/stats`

- Balance shows 0
  - Set `HELIUS_RPC_URL` to a valid Devnet RPC URL
  - Confirm the provider wallet holds the configured SPL mint

- CORS / browser fetch fails
  - Verify the API is on http://localhost:8000 and accessible

- Resetting the DB
  - Stop the API and delete JSON files in `marketplace/data/` (they will be recreated)

---

## License

MIT
