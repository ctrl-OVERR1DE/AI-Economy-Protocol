from __future__ import annotations
from typing import Any, Optional


class AEPError(Exception):
    """Base exception for AEP SDK."""


class APIError(AEPError):
    def __init__(self, message: str, status: Optional[int] = None, payload: Optional[Any] = None) -> None:
        super().__init__(message)
        self.status = status
        self.payload = payload


class GatewayError(AEPError):
    def __init__(self, message: str, status: Optional[int] = None, payload: Optional[Any] = None) -> None:
        super().__init__(message)
        self.status = status
        self.payload = payload


class PaymentRequired(GatewayError):
    """Raised when x402 returns HTTP 402 (proof not verified)."""
    pass
