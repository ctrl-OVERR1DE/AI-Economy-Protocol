# Examples

## Health checks
```python
from aep import AEPConfig, MarketplaceClient, PaymentClient

config = AEPConfig.from_env()
market = MarketplaceClient(config)
x402 = PaymentClient(config)

print(market.health())
print(market.stats())
print(x402.health())
```

## Claim payment with retries
```python
from aep import PaymentClient, AEPConfig, PaymentRequired

client = PaymentClient(AEPConfig.from_env())
try:
    res = client.claim_payment(
        escrow_pda="<ESCROW_PDA>",
        provider_address="<PROVIDER_PUBKEY>",
        retry_402=True,
        max_retries=5,
        backoff=1.5,
    )
    print("Payment released:", res)
except PaymentRequired as e:
    print("Still blocked by x402:", e.payload)
```
