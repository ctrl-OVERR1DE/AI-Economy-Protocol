from __future__ import annotations
import json
from typing import Any, Dict, Optional
import logging
import contextlib
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:  # Optional OTEL
    from opentelemetry import trace as otel_trace  # type: ignore
except Exception:  # pragma: no cover
    otel_trace = None  # type: ignore

from .config import AEPConfig
from .errors import APIError
from .types import JSON
from .models import HealthModel, MarketplaceStatsModel, ProviderModel, ServiceRequestModel


class MarketplaceClient:
    """Client for the AEP Marketplace API."""

    def __init__(
        self,
        config: Optional[AEPConfig] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.config = config or AEPConfig.from_env()
        self.base_url = (base_url or self.config.api_base).rstrip("/")
        self.timeout = timeout or self.config.timeout
        self.session = session or requests.Session()
        self._configure_session()
        self._logger = logging.getLogger("aep.sdk.marketplace")
        try:
            self._logger.setLevel(getattr(logging, str(self.config.log_level).upper(), logging.INFO))
        except Exception:
            self._logger.setLevel(logging.INFO)
        self._logger.disabled = not bool(self.config.enable_logging)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _handle(self, resp: requests.Response) -> JSON:
        try:
            data = resp.json()
        except Exception:
            data = {"text": resp.text}
        if resp.ok:
            self._logger.debug("HTTP %s %s -> %s", resp.request.method if resp.request else "?", resp.request.url if resp.request else "?", resp.status_code)
            return data
        self._logger.error("Marketplace API error HTTP %s: %s", resp.status_code, data if isinstance(data, dict) and any(k in data for k in ("error", "detail")) else "")
        raise APIError(
            message=f"Marketplace API error: HTTP {resp.status_code}",
            status=resp.status_code,
            payload=data,
        )

    def _span(self, name: str):
        if self.config.enable_otel and otel_trace is not None:  # pragma: no cover
            tracer = otel_trace.get_tracer(self.config.otel_service_name)
            return tracer.start_as_current_span(name)
        return contextlib.nullcontext()

    def get(self, path: str, **kwargs: Any) -> JSON:
        url = self._url(path)
        self._logger.debug("GET %s", url)
        with self._span(f"MarketplaceClient GET {path}"):
            resp = self.session.get(url, timeout=self.timeout, **kwargs)
            return self._handle(resp)

    def post(self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs: Any) -> JSON:
        url = self._url(path)
        self._logger.debug("POST %s", url)
        with self._span(f"MarketplaceClient POST {path}"):
            resp = self.session.post(url, json=json, timeout=self.timeout, **kwargs)
            return self._handle(resp)

    def put(self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs: Any) -> JSON:
        url = self._url(path)
        self._logger.debug("PUT %s", url)
        with self._span(f"MarketplaceClient PUT {path}"):
            resp = self.session.put(url, json=json, timeout=self.timeout, **kwargs)
            return self._handle(resp)

    def _configure_session(self) -> None:
        retry = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        self.session.headers.update(headers)

    # Convenience methods
    def health(self) -> JSON:
        """GET /health"""
        return self.get("/health")

    def stats(self) -> JSON:
        """GET /stats"""
        return self.get("/stats")

    # Typed variants
    def health_typed(self) -> HealthModel:
        return HealthModel.parse_obj(self.health())

    def stats_typed(self) -> MarketplaceStatsModel:
        data = self.stats()
        stats_dict = data.get("stats", data)
        return MarketplaceStatsModel.parse_obj(stats_dict)

    # ===== Provider Endpoints =====
    def register_provider(self, payload: JSON) -> JSON:
        """POST /providers/register

        Expected payload keys:
        - agent_address, agent_name, solana_address, port, endpoint, services
        """
        return self.post("/providers/register", json=payload)

    def unregister_provider(self, agent_address: str) -> JSON:
        """POST /providers/unregister?agent_address=..."""
        resp = self.session.post(self._url("/providers/unregister"), params={"agent_address": agent_address}, timeout=self.timeout)
        return self._handle(resp)

    def update_provider_status(self, agent_address: str, status: str) -> JSON:
        """POST /providers/status with JSON body"""
        return self.post("/providers/status", json={"agent_address": agent_address, "status": status})

    def get_all_providers(self) -> JSON:
        return self.get("/providers")

    def get_online_providers(self) -> JSON:
        return self.get("/providers/online")

    def get_provider(self, agent_address: str) -> JSON:
        return self.get(f"/providers/{agent_address}")

    def get_provider_typed(self, agent_address: str) -> ProviderModel:
        data = self.get_provider(agent_address)
        provider = data.get("provider", data)
        return ProviderModel.parse_obj(provider)

    def get_provider_stats(self, agent_address: str) -> JSON:
        return self.get(f"/providers/{agent_address}/stats")

    def get_provider_reviews(self, agent_address: str) -> JSON:
        return self.get(f"/providers/{agent_address}/reviews")

    def get_provider_requests(self, agent_address: str, *, limit: int = 10) -> JSON:
        return self.get(f"/providers/{agent_address}/requests", params={"limit": limit})

    def get_provider_balance(self, agent_address: str, *, mint: str, rpc_url: Optional[str] = None) -> JSON:
        params: Dict[str, Any] = {"mint": mint}
        if rpc_url:
            params["rpc_url"] = rpc_url
        return self.get(f"/providers/{agent_address}/balance", params=params)

    # ===== Service Discovery =====
    def discover_services(self, service_type: Optional[str] = None) -> JSON:
        params = {"service_type": service_type} if service_type else None
        return self.get("/services", params=params)

    def get_providers_by_service(self, service_type: str) -> JSON:
        return self.get(f"/services/{service_type}/providers")

    def find_best_provider(self, service_type: str, *, max_price: Optional[float] = None, min_rating: Optional[float] = None) -> JSON:
        params: Dict[str, Any] = {}
        if max_price is not None:
            params["max_price"] = max_price
        if min_rating is not None:
            params["min_rating"] = min_rating
        return self.get(f"/services/{service_type}/best", params=params or None)

    # ===== Requests / Jobs / Reviews =====
    def create_request(self, *, client_address: str, service_type: str, provider_address: Optional[str] = None) -> JSON:
        body: Dict[str, Any] = {"client_address": client_address, "service_type": service_type}
        if provider_address:
            body["provider_address"] = provider_address
        return self.post("/requests", json=body)

    def update_request(self, *, request_id: str, status: str, escrow_pda: Optional[str] = None, amount: Optional[float] = None) -> JSON:
        body: Dict[str, Any] = {"request_id": request_id, "status": status}
        if escrow_pda is not None:
            body["escrow_pda"] = escrow_pda
        if amount is not None:
            body["amount"] = amount
        # PUT method
        return self.put("/requests", json=body)

    def record_job_completion(self, *, provider_address: str, success: bool, amount: float) -> JSON:
        return self.post("/jobs/complete", json={
            "provider_address": provider_address,
            "success": success,
            "amount": amount,
        })

    def add_review(
        self,
        *,
        provider_address: str,
        client_address: str,
        service_type: str,
        rating: float,
        comment: str,
        transaction_signature: str,
    ) -> JSON:
        return self.post("/reviews", json={
            "provider_address": provider_address,
            "client_address": client_address,
            "service_type": service_type,
            "rating": rating,
            "comment": comment,
            "transaction_signature": transaction_signature,
        })

    def search_providers(
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
        return self.get("/search", params=params)

    # Typed create_request
    def create_request_typed(self, *, client_address: str, service_type: str, provider_address: Optional[str] = None) -> ServiceRequestModel:
        data = self.create_request(client_address=client_address, service_type=service_type, provider_address=provider_address)
        req = data.get("request", data)
        return ServiceRequestModel.parse_obj(req)
