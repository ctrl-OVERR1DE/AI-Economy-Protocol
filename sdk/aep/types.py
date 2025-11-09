from __future__ import annotations
from typing import TypedDict, Optional, Dict, Any


class HealthResponse(TypedDict, total=False):
    status: str
    service: str
    port: int
    version: str


class Stats(TypedDict, total=False):
    providers: int
    requests: int
    completed: int
    in_progress: int
    volume: float
    token_symbol: str


JSON = Dict[str, Any]
