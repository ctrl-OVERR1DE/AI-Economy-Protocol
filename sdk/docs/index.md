# AEP Python SDK

The AEP Python SDK provides a simple interface to the AI Economy Protocol: the Marketplace API and the x402 Payment Gateway.

- Sync clients: `MarketplaceClient`, `PaymentClient`
- Async clients: `AsyncMarketplaceClient`, `AsyncPaymentClient`
- Features: Auth headers, retries/backoff, typed models (Pydantic), logging, optional OpenTelemetry spans

## Install

```bash
pip install -r sdk/requirements.txt
pip install -e sdk
```

## Configuration

Environment variables (all optional):

- `AEP_API_BASE` (default: http://localhost:8000)
- `AEP_GATEWAY_URL` (default: http://localhost:8001)
- `AEP_API_KEY` (Authorization: Bearer)
- `AEP_MAX_RETRIES` (default: 2)
- `AEP_BACKOFF` (default: 0.5)
- `AEP_USER_AGENT` (default: aep-sdk/0.1 (...))
- `AEP_ENABLE_LOGGING` (default: true)
- `AEP_LOG_LEVEL` (default: INFO)
- `AEP_ENABLE_OTEL` (default: false)
- `AEP_OTEL_SERVICE_NAME` (default: aep-sdk)

## Quick Start (sync)

```python
from aep import AEPConfig, MarketplaceClient, PaymentClient

cfg = AEPConfig.from_env()
market = MarketplaceClient(cfg)
x402 = PaymentClient(cfg)

print(market.health_typed())
print(market.stats_typed())
print(x402.health_typed())
```

## Quick Start (async)

```python
import asyncio
from aep import AEPConfig, AsyncMarketplaceClient, AsyncPaymentClient

async def main():
    cfg = AEPConfig.from_env()
    market = AsyncMarketplaceClient(cfg)
    x402 = AsyncPaymentClient(cfg)
    print(await market.health_typed())
    print(await market.stats_typed())
    print(await x402.health_typed())
    await market.aclose()
    await x402.aclose()

asyncio.run(main())
```

See the API Reference for all endpoints and typed helpers.
