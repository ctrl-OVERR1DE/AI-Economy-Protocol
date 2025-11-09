from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class HealthModel(BaseModel):
    status: str
    service: Optional[str] = None
    port: Optional[int] = None
    version: Optional[str] = None


class MarketplaceStatsModel(BaseModel):
    total_providers: int = 0
    online_providers: int = 0
    total_services: int = 0
    total_transactions: int = 0
    total_volume: float = 0.0
    avg_rating: float = 5.0


class ServiceOfferingModel(BaseModel):
    service_type: str
    base_price: float
    description: str
    features: List[str]
    avg_completion_time: int
    success_rate: float = 1.0


class ProviderModel(BaseModel):
    agent_address: str
    agent_name: str
    solana_address: str
    port: int
    endpoint: str
    services: List[ServiceOfferingModel] = []

    status: str = "online"
    last_seen: Optional[str] = None

    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    total_earned: float = 0.0

    rating: float = 5.0
    review_count: int = 0

    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ReviewModel(BaseModel):
    review_id: str
    provider_address: str
    client_address: str
    service_type: str
    rating: float
    comment: str
    transaction_signature: str
    created_at: Optional[str] = None


class ServiceRequestModel(BaseModel):
    request_id: str
    client_address: str
    service_type: str
    provider_address: Optional[str] = None
    status: str = "pending"
    escrow_pda: Optional[str] = None
    amount: float = 0.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
