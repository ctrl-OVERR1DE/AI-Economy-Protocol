import asyncio
from aep import AEPConfig, AsyncMarketplaceClient, AsyncPaymentClient, PaymentRequired


async def main() -> None:
    cfg = AEPConfig.from_env()

    market = AsyncMarketplaceClient(cfg)
    print("Marketplace /health (typed):", await market.health_typed())
    print("Marketplace /stats (typed):", await market.stats_typed())

    x402 = AsyncPaymentClient(cfg)
    print("Gateway /health (typed):", await x402.health_typed())

    # Example 402 retry
    # try:
    #     res = await x402.claim_payment(escrow_pda="...", provider_address="...", retry_402=True)
    #     print("Payment released:", res)
    # except PaymentRequired as e:
    #     print("x402 blocked:", e.payload)

    await market.aclose()
    await x402.aclose()


if __name__ == "__main__":
    asyncio.run(main())
