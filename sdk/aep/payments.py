from __future__ import annotations
from typing import Any, Dict, Optional
import time
import requests
import logging
import contextlib
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import AEPConfig
from .errors import GatewayError, PaymentRequired
from .types import JSON
from .models import HealthModel

try:  # Optional OTEL
    from opentelemetry import trace as otel_trace  # type: ignore
except Exception:  # pragma: no cover
    otel_trace = None  # type: ignore


class PaymentClient:
    """Client for the x402 Payment Gateway."""

    def __init__(
        self,
        config: Optional[AEPConfig] = None,
        *,
        gateway_url: Optional[str] = None,
        timeout: Optional[float] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.config = config or AEPConfig.from_env()
        self.base_url = (gateway_url or self.config.gateway_url).rstrip("/")
        self.timeout = timeout or self.config.timeout
        self.session = session or requests.Session()
        self._configure_session()
        self._logger = logging.getLogger("aep.sdk.gateway")
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
        if resp.status_code == 402:
            raise PaymentRequired(
                message="x402: Proof not verified (HTTP 402)",
                status=resp.status_code,
                payload=data,
            )
        if resp.ok:
            self._logger.debug("HTTP %s %s -> %s", resp.request.method if resp.request else "?", resp.request.url if resp.request else "?", resp.status_code)
            return data
        self._logger.error("Gateway error HTTP %s: %s", resp.status_code, data if isinstance(data, dict) and any(k in data for k in ("error", "detail")) else "")
        raise GatewayError(
            message=f"Gateway error: HTTP {resp.status_code}",
            status=resp.status_code,
            payload=data,
        )

    def _span(self, name: str):
        if self.config.enable_otel and otel_trace is not None:  # pragma: no cover
            tracer = otel_trace.get_tracer(self.config.otel_service_name)
            return tracer.start_as_current_span(name)
        return contextlib.nullcontext()

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

    def get(self, path: str, **kwargs: Any) -> JSON:
        url = self._url(path)
        self._logger.debug("GET %s", url)
        with self._span(f"PaymentClient GET {path}"):
            resp = self.session.get(url, timeout=self.timeout, **kwargs)
            return self._handle(resp)

    def post(self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs: Any) -> JSON:
        url = self._url(path)
        self._logger.debug("POST %s", url)
        with self._span(f"PaymentClient POST {path}"):
            resp = self.session.post(url, json=json, timeout=self.timeout, **kwargs)
            return self._handle(resp)

    # Convenience methods
    def health(self) -> JSON:
        """GET /health"""
        return self.get("/health")

    def health_typed(self) -> HealthModel:
        return HealthModel.parse_obj(self.health())

    def verify_proof(self, escrow_pda: str) -> JSON:
        """POST /verify-proof"""
        return self.post("/verify-proof", json={"escrow_pda": escrow_pda})

    def claim_payment(
        self,
        *,
        escrow_pda: str,
        provider_address: str,
        retry_402: bool = False,
        max_retries: int = 3,
        backoff: float = 1.5,
    ) -> JSON:
        """POST /claim-payment

        If `retry_402` is True, will backoff and retry on HTTP 402 up to `max_retries` times.
        """
        attempt = 0
        while True:
            try:
                return self.post(
                    "/claim-payment",
                    json={
                        "escrow_pda": escrow_pda,
                        "provider_address": provider_address,
                    },
                )
            except PaymentRequired as e:
                if not retry_402 or attempt >= max_retries:
                    raise
                sleep_s = backoff ** attempt
                time.sleep(sleep_s)
                attempt += 1
