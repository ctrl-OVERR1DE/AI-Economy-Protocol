from aep import AEPConfig, MarketplaceClient, PaymentClient, PaymentRequired


def main() -> None:
    cfg = AEPConfig.from_env()

    market = MarketplaceClient(cfg)
    print("Marketplace /health:", market.health())
    try:
        print("Marketplace /stats:", market.stats())
    except Exception as e:
        print("/stats error:", e)

    x402 = PaymentClient(cfg)
    print("Gateway /health:", x402.health())

    # Example claim (will typically be 402 until proof is verified)
    # try:
    #     res = x402.claim_payment(
    #         escrow_pda="<ESCROW_PDA>",
    #         provider_address="<PROVIDER_SOL_PUBKEY>",
    #         retry_402=True,
    #     )
    #     print("Payment released:", res)
    # except PaymentRequired as e:
    #     print("x402 blocked:", e.payload)


if __name__ == "__main__":
    main()
