"""
AI Economy Protocol - Marketplace Registry
Handles agent registration, service advertisement, and discovery.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ServiceListing:
    """Represents a service offered by an agent."""
    service_id: str
    service_name: str
    description: str
    price_sol: float
    provider_address: str
    provider_name: str
    category: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "service_id": self.service_id,
            "service_name": self.service_name,
            "description": self.description,
            "price_sol": self.price_sol,
            "provider_address": self.provider_address,
            "provider_name": self.provider_name,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
            "active": self.active,
        }


@dataclass
class AgentProfile:
    """Represents an agent's profile in the marketplace."""
    agent_address: str
    agent_name: str
    agent_type: str  # "provider" or "client"
    services_offered: List[str] = field(default_factory=list)
    reputation_score: float = 0.0
    total_transactions: int = 0
    registered_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "agent_address": self.agent_address,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "services_offered": self.services_offered,
            "reputation_score": self.reputation_score,
            "total_transactions": self.total_transactions,
            "registered_at": self.registered_at.isoformat(),
        }


class MarketplaceRegistry:
    """
    Central registry for agent marketplace.
    In production, this would be stored on-chain or in a distributed database.
    For now, we use in-memory storage.
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentProfile] = {}
        self.services: Dict[str, ServiceListing] = {}
        self.service_categories: Dict[str, List[str]] = {}
    
    def register_agent(self, profile: AgentProfile) -> bool:
        """Register an agent in the marketplace."""
        if profile.agent_address in self.agents:
            return False
        
        self.agents[profile.agent_address] = profile
        return True
    
    def update_agent_profile(self, agent_address: str, **kwargs) -> bool:
        """Update an agent's profile."""
        if agent_address not in self.agents:
            return False
        
        profile = self.agents[agent_address]
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        return True
    
    def register_service(self, service: ServiceListing) -> bool:
        """Register a service in the marketplace."""
        if service.service_id in self.services:
            return False
        
        self.services[service.service_id] = service
        
        # Add to category index
        if service.category not in self.service_categories:
            self.service_categories[service.category] = []
        self.service_categories[service.category].append(service.service_id)
        
        # Update agent's services list
        if service.provider_address in self.agents:
            self.agents[service.provider_address].services_offered.append(service.service_id)
        
        return True
    
    def get_agent_profile(self, agent_address: str) -> Optional[AgentProfile]:
        """Get an agent's profile."""
        return self.agents.get(agent_address)
    
    def get_service(self, service_id: str) -> Optional[ServiceListing]:
        """Get a service listing."""
        return self.services.get(service_id)
    
    def search_services(
        self, 
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        provider_address: Optional[str] = None
    ) -> List[ServiceListing]:
        """Search for services based on criteria."""
        results = []
        
        # Start with all services or category-filtered services
        if category:
            service_ids = self.service_categories.get(category, [])
            services = [self.services[sid] for sid in service_ids if sid in self.services]
        else:
            services = list(self.services.values())
        
        # Apply filters
        for service in services:
            if not service.active:
                continue
            
            if max_price is not None and service.price_sol > max_price:
                continue
            
            if provider_address and service.provider_address != provider_address:
                continue
            
            results.append(service)
        
        return results
    
    def get_all_agents(self) -> List[AgentProfile]:
        """Get all registered agents."""
        return list(self.agents.values())
    
    def get_all_services(self) -> List[ServiceListing]:
        """Get all active services."""
        return [s for s in self.services.values() if s.active]
    
    def get_categories(self) -> List[str]:
        """Get all service categories."""
        return list(self.service_categories.keys())
    
    def increment_transaction_count(self, agent_address: str) -> bool:
        """Increment an agent's transaction count."""
        if agent_address not in self.agents:
            return False
        
        self.agents[agent_address].total_transactions += 1
        return True
    
    def update_reputation(self, agent_address: str, new_score: float) -> bool:
        """Update an agent's reputation score."""
        if agent_address not in self.agents:
            return False
        
        self.agents[agent_address].reputation_score = new_score
        return True
    
    def export_to_json(self) -> str:
        """Export marketplace data to JSON."""
        data = {
            "agents": {addr: profile.to_dict() for addr, profile in self.agents.items()},
            "services": {sid: service.to_dict() for sid, service in self.services.items()},
        }
        return json.dumps(data, indent=2)
    
    def get_stats(self) -> dict:
        """Get marketplace statistics."""
        return {
            "total_agents": len(self.agents),
            "total_services": len(self.services),
            "active_services": len([s for s in self.services.values() if s.active]),
            "categories": len(self.service_categories),
            "total_transactions": sum(a.total_transactions for a in self.agents.values()),
        }


# Global marketplace instance (in production, this would be decentralized)
marketplace = MarketplaceRegistry()
