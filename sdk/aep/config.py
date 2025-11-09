from __future__ import annotations
from dataclasses import dataclass
import os


@dataclass
class AEPConfig:
    """Configuration for AEP SDK.

    Attributes:
        api_base: Base URL for the Marketplace API, e.g. http://localhost:8000
        gateway_url: Base URL for the x402 Payment Gateway, e.g. http://localhost:8001
        token_mint: SPL token mint address (optional)
        timeout: Default request timeout in seconds
        api_key: Optional API key for authenticated requests (Authorization: Bearer ...)
        user_agent: User-Agent header to send with requests
        max_retries: Number of retries for transient failures (5xx/429/network)
        backoff_factor: Base backoff factor for retries (exponential)
        enable_logging: Enable SDK logging
        log_level: Log level for SDK loggers (e.g. INFO, DEBUG)
        enable_otel: Enable OpenTelemetry spans if opentelemetry is available
        otel_service_name: OTEL service name to use when creating tracer
    """

    api_base: str
    gateway_url: str
    token_mint: str | None = None
    timeout: float = 10.0
    api_key: str | None = None
    user_agent: str = "aep-sdk/0.1 (+https://github.com/ctrl-OVERR1DE/AI-Economy-Protocol)"
    max_retries: int = 2
    backoff_factor: float = 0.5
    enable_logging: bool = True
    log_level: str = "INFO"
    enable_otel: bool = False
    otel_service_name: str = "aep-sdk"

    @classmethod
    def from_env(cls) -> "AEPConfig":
        api = os.getenv("AEP_API_BASE") or os.getenv("NEXT_PUBLIC_API_BASE") or "http://localhost:8000"
        gw = os.getenv("AEP_GATEWAY_URL") or os.getenv("NEXT_PUBLIC_GATEWAY_URL") or "http://localhost:8001"
        mint = os.getenv("AEP_TOKEN_MINT") or os.getenv("NEXT_PUBLIC_TOKEN_MINT")
        api_key = os.getenv("AEP_API_KEY")
        ua = os.getenv("AEP_USER_AGENT") or "aep-sdk/0.1 (+https://github.com/ctrl-OVERR1DE/AI-Economy-Protocol)"
        try:
            retries = int(os.getenv("AEP_MAX_RETRIES", "2"))
        except ValueError:
            retries = 2
        try:
            backoff = float(os.getenv("AEP_BACKOFF", "0.5"))
        except ValueError:
            backoff = 0.5
        enable_logging = (os.getenv("AEP_ENABLE_LOGGING", "true").lower() in ("1", "true", "yes"))
        log_level = os.getenv("AEP_LOG_LEVEL", "INFO")
        enable_otel = (os.getenv("AEP_ENABLE_OTEL", "false").lower() in ("1", "true", "yes"))
        otel_service_name = os.getenv("AEP_OTEL_SERVICE_NAME", "aep-sdk")
        return cls(
            api_base=api.rstrip("/"),
            gateway_url=gw.rstrip("/"),
            token_mint=mint,
            api_key=api_key,
            user_agent=ua,
            max_retries=retries,
            backoff_factor=backoff,
            enable_logging=enable_logging,
            log_level=log_level,
            enable_otel=enable_otel,
            otel_service_name=otel_service_name,
        )
