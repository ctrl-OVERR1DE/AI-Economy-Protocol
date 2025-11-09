import pytest
import respx
import httpx
from aep import AEPConfig
from aep.async_client import AsyncMarketplaceClient
from aep.async_payments import AsyncPaymentClient
from aep.errors import PaymentRequired


API_BASE = "http://api.test"
GW_BASE = "http://gw.test"


@pytest.mark.asyncio
async def test_async_market_health_and_stats_typed():
    cfg = AEPConfig(
        api_base=API_BASE,
        gateway_url=GW_BASE,
        token_mint=None,
        timeout=5.0,
        api_key=None,
        user_agent="aep-sdk-tests/0.1",
        max_retries=0,
        backoff_factor=0.0,
    )
    client = AsyncMarketplaceClient(cfg)
    try:
        with respx.mock as router:
            router.get(f"{API_BASE}/health").mock(return_value=httpx.Response(200, json={"status": "healthy"}))
            router.get(f"{API_BASE}/stats").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "stats": {
                            "total_providers": 2,
                            "online_providers": 1,
                            "total_services": 3,
                            "total_transactions": 4,
                            "total_volume": 1.23,
                            "avg_rating": 4.9,
                        }
                    },
                )
            )
            health = await client.health_typed()
            assert health.status == "healthy"
            stats = await client.stats_typed()
            assert stats.total_providers == 2
            assert stats.online_providers == 1
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_async_payment_claim_402():
    cfg = AEPConfig(
        api_base=API_BASE,
        gateway_url=GW_BASE,
        token_mint=None,
        timeout=5.0,
        api_key=None,
        user_agent="aep-sdk-tests/0.1",
        max_retries=0,
        backoff_factor=0.0,
    )
    client = AsyncPaymentClient(cfg)
    try:
        with respx.mock as router:
            router.get(f"{GW_BASE}/health").mock(return_value=httpx.Response(200, json={"status": "healthy"}))
            router.post(f"{GW_BASE}/claim-payment").mock(
                return_value=httpx.Response(402, json={"error": "Proof not verified", "status": "pending"})
            )
            # sanity health
            health = await client.health_typed()
            assert health.status == "healthy"
            with pytest.raises(PaymentRequired):
                await client.claim_payment(escrow_pda="escrow123", provider_address="prov111", retry_402=False)
    finally:
        await client.aclose()
