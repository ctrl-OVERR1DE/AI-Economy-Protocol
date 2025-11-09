from __future__ import annotations
import asyncio
from typing import Any, Dict, Optional
import httpx
import logging
import contextlib

from .config import AEPConfig
from .errors import APIError
from .types import JSON
from .models import HealthModel, MarketplaceStatsModel, ProviderModel, ServiceRequestModel

try:  # Optional OTEL
    from opentelemetry import trace as otel_trace  # type: ignore
except Exception:  # pragma: no cover
    otel_trace = None  # type: ignore


_STATUS_RETRY = {429, 500, 502, 503, 504}
_ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


class AsyncMarketplaceClient:
    """Async client for the AEP Marketplace API."""

    def __init__(
        self,
        config: Optional[AEPConfig] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.config = config or AEPConfig.from_env()
        self.base_url = (base_url or self.config.api_base).rstrip("/")
        self.timeout = timeout or self.config.timeout
        self.client = client or self._build_client()
        self._logger = logging.getLogger("aep.sdk.marketplace.async")
        try:
            self._logger.setLevel(getattr(logging, str(self.config.log_level).upper(), logging.INFO))
        except Exception:
            self._logger.setLevel(logging.INFO)
        self._logger.disabled = not bool(self.config.enable_logging)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _build_client(self) -> httpx.AsyncClient:
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return httpx.AsyncClient(headers=headers)

    def _span(self, name: str):
        if self.config.enable_otel and otel_trace is not None:  # pragma: no cover
            tracer = otel_trace.get_tracer(self.config.otel_service_name)
            return tracer.start_as_current_span(name)
        return contextlib.nullcontext()

    async def aclose(self) -> None:
        await self.client.aclose()

    async def _request(self, method: str, path: str, *, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> JSON:
        method = method.upper()
        assert method in _ALLOWED_METHODS
        attempt = 0
        while True:
            try:
                url = self._url(path)
                if attempt == 0:
                    self._logger.debug("%s %s", method, url)
                with self._span(f"AsyncMarketplaceClient {method} {path}"):
                    resp = await self.client.request(method, url, json=json, params=params, timeout=self.timeout)
                try:
                    data = resp.json()
                except Exception:
                    data = {"text": resp.text}
                if resp.status_code in _STATUS_RETRY and attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.backoff_factor * (2 ** attempt))
                    attempt += 1
                    continue
                if 200 <= resp.status_code < 300:
                    self._logger.debug("HTTP %s %s -> %s", method, url, resp.status_code)
                    return data
                self._logger.error("Marketplace API error HTTP %s: %s", resp.status_code, data if isinstance(data, dict) and any(k in data for k in ("error", "detail")) else "")
                raise APIError(
                    message=f"Marketplace API error: HTTP {resp.status_code}",
                    status=resp.status_code,
                    payload=data,
                )
            except (httpx.TimeoutException, httpx.NetworkError) as e:  # type: ignore[attr-defined]
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.backoff_factor * (2 ** attempt))
                    attempt += 1
                    continue
                self._logger.error("Marketplace API network error: %s", e)
                raise APIError(str(e))

    # Basic verbs
    async def get(self, path: str, **kwargs: Any) -> JSON:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs: Any) -> JSON:
        return await self._request("POST", path, json=json, **kwargs)

    async def put(self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs: Any) -> JSON:
        return await self._request("PUT", path, json=json, **kwargs)

    # Convenience
    async def health(self) -> JSON:
        return await self.get("/health")

    async def stats(self) -> JSON:
        return await self.get("/stats")

    # Typed helpers
    async def health_typed(self) -> HealthModel:
        return HealthModel.parse_obj(await self.health())

    async def stats_typed(self) -> MarketplaceStatsModel:
        data = await self.stats()
        stats_dict = data.get("stats", data)
        return MarketplaceStatsModel.parse_obj(stats_dict)

    # Provider endpoints
    async def register_provider(self, payload: JSON) -> JSON:
        return await self.post("/providers/register", json=payload)

    async def unregister_provider(self, agent_address: str) -> JSON:
        return await self.post("/providers/unregister", params={"agent_address": agent_address})

    async def update_provider_status(self, agent_address: str, status: str) -> JSON:
        return await self.post("/providers/status", json={"agent_address": agent_address, "status": status})

    async def get_all_providers(self) -> JSON:
        return await self.get("/providers")

    async def get_online_providers(self) -> JSON:
        return await self.get("/providers/online")

    async def get_provider(self, agent_address: str) -> JSON:
        return await self.get(f"/providers/{agent_address}")

    async def get_provider_typed(self, agent_address: str) -> ProviderModel:
        data = await self.get_provider(agent_address)
        provider = data.get("provider", data)
        return ProviderModel.parse_obj(provider)

    async def get_provider_stats(self, agent_address: str) -> JSON:
        return await self.get(f"/providers/{agent_address}/stats")

    async def get_provider_reviews(self, agent_address: str) -> JSON:
        return await self.get(f"/providers/{agent_address}/reviews")

    async def get_provider_requests(self, agent_address: str, *, limit: int = 10) -> JSON:
        return await self.get(f"/providers/{agent_address}/requests", params={"limit": limit})

    async def get_provider_balance(self, agent_address: str, *, mint: str, rpc_url: Optional[str] = None) -> JSON:
        params: Dict[str, Any] = {"mint": mint}
        if rpc_url:
            params["rpc_url"] = rpc_url
        return await self.get(f"/providers/{agent_address}/balance", params=params)

    # Service discovery
    async def discover_services(self, service_type: Optional[str] = None) -> JSON:
        params = {"service_type": service_type} if service_type else None
        return await self.get("/services", params=params)

    async def get_providers_by_service(self, service_type: str) -> JSON:
        return await self.get(f"/services/{service_type}/providers")

    async def find_best_provider(self, service_type: str, *, max_price: Optional[float] = None, min_rating: Optional[float] = None) -> JSON:
        params: Dict[str, Any] = {}
        if max_price is not None:
            params["max_price"] = max_price
        if min_rating is not None:
            params["min_rating"] = min_rating
        return await self.get(f"/services/{service_type}/best", params=params or None)

    # Requests / jobs / reviews
    async def create_request(self, *, client_address: str, service_type: str, provider_address: Optional[str] = None) -> JSON:
        body: Dict[str, Any] = {"client_address": client_address, "service_type": service_type}
        if provider_address:
            body["provider_address"] = provider_address
        return await self.post("/requests", json=body)

    async def create_request_typed(self, *, client_address: str, service_type: str, provider_address: Optional[str] = None) -> ServiceRequestModel:
        data = await self.create_request(client_address=client_address, service_type=service_type, provider_address=provider_address)
        req = data.get("request", data)
        return ServiceRequestModel.parse_obj(req)

    async def update_request(self, *, request_id: str, status: str, escrow_pda: Optional[str] = None, amount: Optional[float] = None) -> JSON:
        body: Dict[str, Any] = {"request_id": request_id, "status": status}
        if escrow_pda is not None:
            body["escrow_pda"] = escrow_pda
        if amount is not None:
            body["amount"] = amount
        return await self.put("/requests", json=body)

    async def record_job_completion(self, *, provider_address: str, success: bool, amount: float) -> JSON:
        return await self.post("/jobs/complete", json={
            "provider_address": provider_address,
            "success": success,
            "amount": amount,
        })

    async def add_review(
        self,
        *,
        provider_address: str,
        client_address: str,
        service_type: str,
        rating: float,
        comment: str,
        transaction_signature: str,
    ) -> JSON:
        return await self.post("/reviews", json={
            "provider_address": provider_address,
            "client_address": client_address,
            "service_type": service_type,
            "rating": rating,
            "comment": comment,
            "transaction_signature": transaction_signature,
        })

    async def search_providers(
        self,
        *,
        service_type: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_price: Optional[float] = None,
        status: str = "online",
    ) -> JSON:
        params: Dict[str, Any] = {"status": status}
        if service_type is not None:
            params["service_type"] = service_type
        if min_rating is not None:
            params["min_rating"] = min_rating
        if max_price is not None:
            params["max_price"] = max_price
        return await self.get("/search", params=params)
