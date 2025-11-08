"""
Marketplace Data Models

Defines data structures for providers, services, and reviews.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class ServiceType(Enum):
    """Available service types in the marketplace."""
    CODE_REVIEW = "code_review"
    CONTENT_ANALYSIS = "content_analysis"
    TRANSLATION = "translation"


class ProviderStatus(Enum):
    """Provider online status."""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"


@dataclass
class ServiceOffering:
    """A service offered by a provider."""
    service_type: str  # ServiceType enum value
    base_price: float  # In SOL
    description: str
    features: List[str]
    avg_completion_time: int  # In seconds
    success_rate: float = 1.0  # 0.0 to 1.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Provider:
    """A service provider in the marketplace."""
    agent_address: str  # uAgents address
    agent_name: str
    solana_address: str  # Solana wallet address
    port: int
    endpoint: str
    
    # Services offered
    services: List[ServiceOffering] = field(default_factory=list)
    
    # Status
    status: str = ProviderStatus.ONLINE.value
    last_seen: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Statistics
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    total_earned: float = 0.0  # In SOL
    
    # Ratings
    rating: float = 5.0  # 0.0 to 5.0
    review_count: int = 0
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['services'] = [s.to_dict() if isinstance(s, ServiceOffering) else s for s in self.services]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Provider':
        """Create from dictionary."""
        # Convert services list
        if 'services' in data:
            data['services'] = [
                ServiceOffering(**s) if isinstance(s, dict) else s
                for s in data['services']
            ]
        return cls(**data)
    
    def update_status(self, status: ProviderStatus):
        """Update provider status."""
        self.status = status.value
        self.last_seen = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
    
    def add_service(self, service: ServiceOffering):
        """Add a service offering."""
        self.services.append(service)
        self.updated_at = datetime.utcnow().isoformat()
    
    def record_job_completion(self, success: bool, amount: float):
        """Record a completed job."""
        self.total_jobs += 1
        if success:
            self.completed_jobs += 1
            self.total_earned += amount
        else:
            self.failed_jobs += 1
        self.updated_at = datetime.utcnow().isoformat()
    
    def update_rating(self, new_rating: float):
        """Update provider rating."""
        # Calculate new average rating
        total_rating = self.rating * self.review_count
        self.review_count += 1
        self.rating = (total_rating + new_rating) / self.review_count
        self.updated_at = datetime.utcnow().isoformat()


@dataclass
class Review:
    """A review for a provider."""
    review_id: str
    provider_address: str
    client_address: str
    service_type: str
    rating: float  # 1.0 to 5.0
    comment: str
    transaction_signature: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Review':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ServiceRequest:
    """A service request from a client."""
    request_id: str
    client_address: str
    service_type: str
    provider_address: Optional[str] = None
    status: str = "pending"  # pending, accepted, in_progress, completed, failed
    escrow_pda: Optional[str] = None
    amount: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ServiceRequest':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class MarketplaceStats:
    """Overall marketplace statistics."""
    total_providers: int = 0
    online_providers: int = 0
    total_services: int = 0
    total_transactions: int = 0
    total_volume: float = 0.0  # In SOL
    avg_rating: float = 5.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
