from __future__ import annotations
import asyncio
from typing import Any, Dict, Optional
import httpx
import logging
import contextlib

from .config import AEPConfig
from .errors import GatewayError, PaymentRequired
from .types import JSON
from .models import HealthModel

try:  # Optional OTEL
    from opentelemetry import trace as otel_trace  # type: ignore
except Exception:  # pragma: no cover
    otel_trace = None  # type: ignore

_STATUS_RETRY = {429, 500, 502, 503, 504}
_ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


class AsyncPaymentClient:
    """Async client for the x402 Payment Gateway."""

    def __init__(
        self,
        config: Optional[AEPConfig] = None,
        *,
        gateway_url: Optional[str] = None,
        timeout: Optional[float] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.config = config or AEPConfig.from_env()
        self.base_url = (gateway_url or self.config.gateway_url).rstrip("/")
        self.timeout = timeout or self.config.timeout
        self.client = client or self._build_client()
        self._logger = logging.getLogger("aep.sdk.gateway.async")
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
                with self._span(f"AsyncPaymentClient {method} {path}"):
                    resp = await self.client.request(method, url, json=json, params=params, timeout=self.timeout)
                try:
                    data = resp.json()
                except Exception:
                    data = {"text": resp.text}
                if resp.status_code == 402:
                    raise PaymentRequired("x402: Proof not verified (HTTP 402)", status=402, payload=data)
                if resp.status_code in _STATUS_RETRY and attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.backoff_factor * (2 ** attempt))
                    attempt += 1
                    continue
                if 200 <= resp.status_code < 300:
                    self._logger.debug("HTTP %s %s -> %s", method, url, resp.status_code)
                    return data
                self._logger.error("Gateway error HTTP %s: %s", resp.status_code, data if isinstance(data, dict) and any(k in data for k in ("error", "detail")) else "")
                raise GatewayError(
                    message=f"Gateway error: HTTP {resp.status_code}",
                    status=resp.status_code,
                    payload=data,
                )
            except (httpx.TimeoutException, httpx.NetworkError) as e:  # type: ignore[attr-defined]
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.backoff_factor * (2 ** attempt))
                    attempt += 1
                    continue
                self._logger.error("Gateway network error: %s", e)
                raise GatewayError(str(e))

    # Convenience methods
    async def health(self) -> JSON:
        return await self._request("GET", "/health")

    async def health_typed(self) -> HealthModel:
        return HealthModel.parse_obj(await self.health())

    async def verify_proof(self, escrow_pda: str) -> JSON:
        return await self._request("POST", "/verify-proof", json={"escrow_pda": escrow_pda})

    async def claim_payment(
        self,
        *,
        escrow_pda: str,
        provider_address: str,
        retry_402: bool = False,
        max_retries: int = 3,
        backoff: float = 1.5,
    ) -> JSON:
        attempt = 0
        while True:
            try:
                return await self._request(
                    "POST",
                    "/claim-payment",
                    json={
                        "escrow_pda": escrow_pda,
                        "provider_address": provider_address,
                    },
                )
            except PaymentRequired:
                if not retry_402 or attempt >= max_retries:
                    raise
                await asyncio.sleep(backoff ** attempt)
                attempt += 1
