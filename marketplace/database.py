"""
Marketplace Database

Simple JSON-based database for storing marketplace data.
For production, this should be replaced with a proper database (PostgreSQL, MongoDB, etc.)
"""

import json
import os
from typing import List, Optional, Dict
from datetime import datetime
from .models import Provider, Review, ServiceRequest, MarketplaceStats


class MarketplaceDatabase:
    """Simple JSON-based database for marketplace data."""
    
    def __init__(self, data_dir: str = "marketplace/data"):
        """Initialize database."""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.providers_file = os.path.join(data_dir, "providers.json")
        self.reviews_file = os.path.join(data_dir, "reviews.json")
        self.requests_file = os.path.join(data_dir, "requests.json")
        self.stats_file = os.path.join(data_dir, "stats.json")
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Initialize JSON files if they don't exist."""
        if not os.path.exists(self.providers_file):
            self._write_json(self.providers_file, {})
        if not os.path.exists(self.reviews_file):
            self._write_json(self.reviews_file, [])
        if not os.path.exists(self.requests_file):
            self._write_json(self.requests_file, [])
        if not os.path.exists(self.stats_file):
            self._write_json(self.stats_file, MarketplaceStats().to_dict())
    
    def _read_json(self, filepath: str) -> any:
        """Read JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return {} if 'providers' in filepath or 'stats' in filepath else []
    
    def _write_json(self, filepath: str, data: any):
        """Write JSON file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
    
    # ===== Provider Operations =====
    
    def add_provider(self, provider: Provider) -> bool:
        """Add or update a provider."""
        try:
            providers = self._read_json(self.providers_file)
            providers[provider.agent_address] = provider.to_dict()
            self._write_json(self.providers_file, providers)
            self._update_stats()
            return True
        except Exception as e:
            print(f"Error adding provider: {e}")
            return False
    
    def get_provider(self, agent_address: str) -> Optional[Provider]:
        """Get a provider by address."""
        try:
            providers = self._read_json(self.providers_file)
            if agent_address in providers:
                return Provider.from_dict(providers[agent_address])
            return None
        except Exception as e:
            print(f"Error getting provider: {e}")
            return None
    
    def get_all_providers(self) -> List[Provider]:
        """Get all providers."""
        try:
            providers = self._read_json(self.providers_file)
            return [Provider.from_dict(p) for p in providers.values()]
        except Exception as e:
            print(f"Error getting all providers: {e}")
            return []
    
    def get_online_providers(self) -> List[Provider]:
        """Get all online providers."""
        all_providers = self.get_all_providers()
        return [p for p in all_providers if p.status == "online"]
    
    def get_providers_by_service(self, service_type: str) -> List[Provider]:
        """Get providers offering a specific service."""
        all_providers = self.get_all_providers()
        return [
            p for p in all_providers
            if any(s.service_type == service_type for s in p.services)
        ]
    
    def update_provider_status(self, agent_address: str, status: str) -> bool:
        """Update provider status."""
        try:
            provider = self.get_provider(agent_address)
            if provider:
                provider.status = status
                provider.last_seen = datetime.utcnow().isoformat()
                provider.updated_at = datetime.utcnow().isoformat()
                return self.add_provider(provider)
            return False
        except Exception as e:
            print(f"Error updating provider status: {e}")
            return False
    
    def remove_provider(self, agent_address: str) -> bool:
        """Remove a provider."""
        try:
            providers = self._read_json(self.providers_file)
            if agent_address in providers:
                del providers[agent_address]
                self._write_json(self.providers_file, providers)
                self._update_stats()
                return True
            return False
        except Exception as e:
            print(f"Error removing provider: {e}")
            return False
    
    # ===== Review Operations =====
    
    def add_review(self, review: Review) -> bool:
        """Add a review."""
        try:
            reviews = self._read_json(self.reviews_file)
            reviews.append(review.to_dict())
            self._write_json(self.reviews_file, reviews)
            
            # Update provider rating
            provider = self.get_provider(review.provider_address)
            if provider:
                provider.update_rating(review.rating)
                self.add_provider(provider)
            
            return True
        except Exception as e:
            print(f"Error adding review: {e}")
            return False
    
    def get_provider_reviews(self, provider_address: str) -> List[Review]:
        """Get all reviews for a provider."""
        try:
            reviews = self._read_json(self.reviews_file)
            return [
                Review.from_dict(r) for r in reviews
                if r['provider_address'] == provider_address
            ]
        except Exception as e:
            print(f"Error getting provider reviews: {e}")
            return []
    
    # ===== Service Request Operations =====
    
    def add_request(self, request: ServiceRequest) -> bool:
        """Add a service request."""
        try:
            requests = self._read_json(self.requests_file)
            requests.append(request.to_dict())
            self._write_json(self.requests_file, requests)
            return True
        except Exception as e:
            print(f"Error adding request: {e}")
            return False
    
    def get_request(self, request_id: str) -> Optional[ServiceRequest]:
        """Get a service request by ID."""
        try:
            requests = self._read_json(self.requests_file)
            for r in requests:
                if r['request_id'] == request_id:
                    return ServiceRequest.from_dict(r)
            return None
        except Exception as e:
            print(f"Error getting request: {e}")
            return None
    
    def update_request(self, request: ServiceRequest) -> bool:
        """Update a service request."""
        try:
            requests = self._read_json(self.requests_file)
            for i, r in enumerate(requests):
                if r['request_id'] == request.request_id:
                    requests[i] = request.to_dict()
                    self._write_json(self.requests_file, requests)
                    return True
            return False
        except Exception as e:
            print(f"Error updating request: {e}")
            return False
    
    def get_provider_requests(self, provider_address: str) -> List[ServiceRequest]:
        """Get all requests for a provider."""
        try:
            requests = self._read_json(self.requests_file)
            return [
                ServiceRequest.from_dict(r) for r in requests
                if r.get('provider_address') == provider_address
            ]
        except Exception as e:
            print(f"Error getting provider requests: {e}")
            return []
    
    # ===== Statistics Operations =====
    
    def _update_stats(self):
        """Update marketplace statistics."""
        try:
            providers = self.get_all_providers()
            online_providers = [p for p in providers if p.status == "online"]
            
            total_services = sum(len(p.services) for p in providers)
            total_transactions = sum(p.total_jobs for p in providers)
            total_volume = sum(p.total_earned for p in providers)
            
            ratings = [p.rating for p in providers if p.review_count > 0]
            avg_rating = sum(ratings) / len(ratings) if ratings else 5.0
            
            stats = MarketplaceStats(
                total_providers=len(providers),
                online_providers=len(online_providers),
                total_services=total_services,
                total_transactions=total_transactions,
                total_volume=total_volume,
                avg_rating=avg_rating
            )
            
            self._write_json(self.stats_file, stats.to_dict())
        except Exception as e:
            print(f"Error updating stats: {e}")
    
    def get_stats(self) -> MarketplaceStats:
        """Get marketplace statistics."""
        try:
            stats_data = self._read_json(self.stats_file)
            return MarketplaceStats(**stats_data)
        except Exception as e:
            print(f"Error getting stats: {e}")
            return MarketplaceStats()
    
    # ===== Search Operations =====
    
    def search_providers(
        self,
        service_type: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_price: Optional[float] = None,
        status: Optional[str] = None
    ) -> List[Provider]:
        """Search providers with filters."""
        providers = self.get_all_providers()
        
        # Filter by service type
        if service_type:
            providers = [
                p for p in providers
                if any(s.service_type == service_type for s in p.services)
            ]
        
        # Filter by rating
        if min_rating is not None:
            providers = [p for p in providers if p.rating >= min_rating]
        
        # Filter by price
        if max_price is not None:
            providers = [
                p for p in providers
                if any(s.base_price <= max_price for s in p.services)
            ]
        
        # Filter by status
        if status:
            providers = [p for p in providers if p.status == status]
        
        return providers
