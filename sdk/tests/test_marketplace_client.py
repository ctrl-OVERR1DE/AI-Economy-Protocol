import requests_mock
from aep import AEPConfig
from aep.client import MarketplaceClient
from aep.errors import APIError


API_BASE = "http://api.test"
GW_BASE = "http://gw.test"


def make_client(api_key: str | None = None) -> MarketplaceClient:
    cfg = AEPConfig(
        api_base=API_BASE,
        gateway_url=GW_BASE,
        token_mint=None,
        timeout=5.0,
        api_key=api_key,
        user_agent="aep-sdk-tests/0.1",
        max_retries=0,
        backoff_factor=0.0,
    )
    return MarketplaceClient(cfg)


def test_health_ok():
    client = make_client()
    with requests_mock.Mocker() as m:
        m.get(f"{API_BASE}/health", json={"status": "healthy"}, status_code=200)
        res = client.health()
        assert res["status"] == "healthy"


def test_stats_typed():
    client = make_client()
    with requests_mock.Mocker() as m:
        m.get(
            f"{API_BASE}/stats",
            json={"stats": {"total_providers": 2, "online_providers": 1, "total_services": 3, "total_transactions": 4, "total_volume": 1.23, "avg_rating": 4.9}},
            status_code=200,
        )
        stats = client.stats_typed()
        assert stats.total_providers == 2
        assert stats.online_providers == 1


def test_register_provider():
    client = make_client(api_key="XYZ")
    with requests_mock.Mocker() as m:
        m.post(f"{API_BASE}/providers/register", json={"success": True}, status_code=200)
        payload = {
            "agent_address": "agent-1",
            "agent_name": "Test Agent",
            "solana_address": "SoL111",
            "port": 9000,
            "endpoint": "/infer",
            "services": [{"service_type": "code_review", "base_price": 0.1, "description": "", "features": [], "avg_completion_time": 60, "success_rate": 1.0}],
        }
        res = client.register_provider(payload)
        assert res.get("success") is True
        # Auth header applied
        assert client.session.headers.get("Authorization") == "Bearer XYZ"
        assert "aep-sdk-tests" in client.session.headers.get("User-Agent", "")


def test_update_request_put():
    client = make_client()
    with requests_mock.Mocker() as m:
        m.put(f"{API_BASE}/requests", json={"success": True}, status_code=200)
        res = client.update_request(request_id="req-1", status="in_progress", escrow_pda="pda", amount=0.5)
        assert res.get("success") is True


def test_get_provider_typed():
    client = make_client()
    with requests_mock.Mocker() as m:
        m.get(
            f"{API_BASE}/providers/agent-1",
            json={"provider": {"agent_address": "agent-1", "agent_name": "Test", "solana_address": "SoL111", "port": 9000, "endpoint": "/", "services": []}},
            status_code=200,
        )
        provider = client.get_provider_typed("agent-1")
        assert provider.agent_address == "agent-1"
