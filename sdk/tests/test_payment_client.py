import requests_mock
import pytest
from aep import AEPConfig
from aep.payments import PaymentClient
from aep.errors import PaymentRequired


GW_BASE = "http://gw.test"
API_BASE = "http://api.test"


def make_client() -> PaymentClient:
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
    return PaymentClient(cfg)


def test_gateway_health_typed():
    client = make_client()
    with requests_mock.Mocker() as m:
        m.get(f"{GW_BASE}/health", json={"status": "healthy", "service": "x402 Payment Gateway"}, status_code=200)
        model = client.health_typed()
        assert model.status == "healthy"


def test_verify_proof():
    client = make_client()
    with requests_mock.Mocker() as m:
        m.post(f"{GW_BASE}/verify-proof", json={"verified": False, "status": "pending", "details": "not yet"}, status_code=200)
        res = client.verify_proof("escrow123")
        assert res.get("status") == "pending"


def test_claim_payment_402_raises():
    client = make_client()
    with requests_mock.Mocker() as m:
        m.post(
            f"{GW_BASE}/claim-payment",
            json={"error": "Proof not verified", "status": "pending"},
            status_code=402,
        )
        with pytest.raises(PaymentRequired):
            client.claim_payment(escrow_pda="escrow123", provider_address="prov111", retry_402=False)
