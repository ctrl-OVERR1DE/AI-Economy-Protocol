# AEP Python SDK

Python SDK for the AI Economy Protocol (AEP): Marketplace API + x402 Payment Gateway.

## Install (local)

```bash
# From repo root
python -m venv .venv && source .venv/bin/activate  # or use your env
pip install -r sdk/requirements.txt
pip install -e sdk
```

## Configuration

The SDK reads configuration from environment variables, with sensible defaults:

- `AEP_API_BASE` (fallback: `NEXT_PUBLIC_API_BASE`, default: `http://localhost:8000`)
- `AEP_GATEWAY_URL` (fallback: `NEXT_PUBLIC_GATEWAY_URL`, default: `http://localhost:8001`)
- `AEP_TOKEN_MINT` (fallback: `NEXT_PUBLIC_TOKEN_MINT`, optional)
- `AEP_API_KEY` (optional; if set, used as `Authorization: Bearer <key>`)
- `AEP_MAX_RETRIES` (optional; default `2`) – retries for 429/5xx and network errors
- `AEP_BACKOFF` (optional; default `0.5`) – exponential backoff factor for retries
- `AEP_USER_AGENT` (optional) – overrides default `aep-sdk/0.1 (...)`
- `AEP_ENABLE_LOGGING` (default `true`) – enable/disable SDK logs
- `AEP_LOG_LEVEL` (default `INFO`) – e.g. `DEBUG`, `INFO`
- `AEP_ENABLE_OTEL` (default `false`) – enable OpenTelemetry spans if OTEL is installed
- `AEP_OTEL_SERVICE_NAME` (default `aep-sdk`) – service name for OTEL tracer

You can also pass values directly into the clients.

## Quick Start

```python
from aep import AEPConfig, MarketplaceClient, PaymentClient, PaymentRequired

# Load from environment or pass explicit URLs
config = AEPConfig.from_env()

market = MarketplaceClient(config)
# Typed helpers (Pydantic models)
print("Marketplace health (typed):", market.health_typed())
print("Marketplace stats (typed):", market.stats_typed())

x402 = PaymentClient(config)
print("Gateway health (typed):", x402.health_typed())

# Example payment claim (will return 402 if proof not verified)
# try:
#     result = x402.claim_payment(escrow_pda="...", provider_address="...")
#     print("Payment released:", result)
# except PaymentRequired as e:
#     print("Payment blocked (x402):", e.payload)
```

## What’s Included

- MarketplaceClient: health, stats, providers, discovery, requests/jobs/reviews
- PaymentClient: health, verify_proof, claim_payment with 402 handling
- Auth & retries: optional `Authorization: Bearer` + configurable retries/backoff
- Typed helpers (Pydantic): `health_typed`, `stats_typed`, `get_provider_typed`, `create_request_typed`
- Config loader with env fallbacks
- Typed errors for clean error handling

## Logging & Observability

- Logging is enabled by default; control with `AEP_ENABLE_LOGGING` and `AEP_LOG_LEVEL`.
- Optional OpenTelemetry spans can be enabled via `AEP_ENABLE_OTEL=true` (requires OTEL packages installed by your app). The SDK will create spans for HTTP calls with the service name `AEP_OTEL_SERVICE_NAME`.

## Roadmap

- Async client variants
- Stronger types and models
- Escrow helpers (Solana) and signing utilities
- Tests and CI

