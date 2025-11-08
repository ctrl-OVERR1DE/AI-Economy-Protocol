"""
Marketplace Service

Business logic for marketplace operations.
"""

from typing import List, Optional, Dict
from datetime import datetime
import os
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import uuid

from .database import MarketplaceDatabase
from .models import (
    Provider, ServiceOffering, Review, ServiceRequest,
    MarketplaceStats, ServiceType, ProviderStatus
)


class MarketplaceService:
    """Marketplace business logic."""
    
    def __init__(self, data_dir: str = "marketplace/data"):
        """Initialize marketplace service."""
        self.db = MarketplaceDatabase(data_dir)
    
    # ===== Provider Management =====
    
    def register_provider(
        self,
        agent_address: str,
        agent_name: str,
        solana_address: str,
        port: int,
        endpoint: str,
        services: List[Dict]
    ) -> bool:
        """Register a new provider or update existing one."""
        try:
            # Check if provider already exists
            existing = self.db.get_provider(agent_address)
            
            if existing:
                # Update existing provider
                existing.agent_name = agent_name
                existing.solana_address = solana_address
                existing.port = port
                existing.endpoint = endpoint
                existing.status = ProviderStatus.ONLINE.value
                existing.last_seen = datetime.utcnow().isoformat()
                existing.updated_at = datetime.utcnow().isoformat()
                
                # Update services
                existing.services = [ServiceOffering(**s) for s in services]
                
                return self.db.add_provider(existing)
            else:
                # Create new provider
                provider = Provider(
                    agent_address=agent_address,
                    agent_name=agent_name,
                    solana_address=solana_address,
                    port=port,
                    endpoint=endpoint,
                    services=[ServiceOffering(**s) for s in services],
                    status=ProviderStatus.ONLINE.value
                )
                
                return self.db.add_provider(provider)
        except Exception as e:
            print(f"Error registering provider: {e}")
            return False
    
    def unregister_provider(self, agent_address: str) -> bool:
        """Unregister a provider."""
        return self.db.update_provider_status(agent_address, ProviderStatus.OFFLINE.value)
    
    def update_provider_status(self, agent_address: str, status: ProviderStatus) -> bool:
        """Update provider status."""
        return self.db.update_provider_status(agent_address, status.value)
    
    def get_provider(self, agent_address: str) -> Optional[Provider]:
        """Get provider details."""
        return self.db.get_provider(agent_address)
    
    def get_all_providers(self) -> List[Provider]:
        """Get all providers."""
        return self.db.get_all_providers()
    
    def get_online_providers(self) -> List[Provider]:
        """Get all online providers."""
        return self.db.get_online_providers()
    
    def get_providers_by_service(self, service_type: str) -> List[Provider]:
        """Get providers offering a specific service."""
        return self.db.get_providers_by_service(service_type)
    
    # ===== Service Discovery =====
    
    def discover_services(self, service_type: Optional[str] = None) -> List[Dict]:
        """Discover available services (only online providers)."""
        if service_type:
            providers = self.db.get_providers_by_service(service_type)
        else:
            providers = self.db.get_all_providers()
        
        # IMPORTANT: Filter to only online providers
        providers = [p for p in providers if p.status == "online"]
        
        services = []
        for provider in providers:
            for service in provider.services:
                if not service_type or service.service_type == service_type:
                    services.append({
                        'provider_address': provider.agent_address,
                        'provider_name': provider.agent_name,
                        'solana_address': provider.solana_address,
                        'provider_rating': provider.rating,
                        'provider_jobs': provider.completed_jobs,
                        'service_type': service.service_type,
                        'base_price': service.base_price,
                        'description': service.description,
                        'features': service.features,
                        'avg_completion_time': service.avg_completion_time,
                        'success_rate': service.success_rate,
                        'port': provider.port,
                        'endpoint': provider.endpoint
                    })
        
        return services
    
    def find_best_provider(
        self,
        service_type: str,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None
    ) -> Optional[Dict]:
        """Find the best provider for a service based on criteria."""
        services = self.discover_services(service_type)
        
        # Apply filters
        if max_price:
            services = [s for s in services if s['base_price'] <= max_price]
        if min_rating:
            services = [s for s in services if s['provider_rating'] >= min_rating]
        
        if not services:
            return None
        
        # Sort by rating (desc) and price (asc)
        services.sort(key=lambda s: (-s['provider_rating'], s['base_price']))
        
        return services[0] if services else None
    
    # ===== Service Requests =====
    
    def create_request(
        self,
        client_address: str,
        service_type: str,
        provider_address: Optional[str] = None
    ) -> ServiceRequest:
        """Create a new service request."""
        request = ServiceRequest(
            request_id=str(uuid.uuid4()),
            client_address=client_address,
            service_type=service_type,
            provider_address=provider_address,
            status="pending"
        )
        
        self.db.add_request(request)
        return request
    
    def update_request_status(
        self,
        request_id: str,
        status: str,
        escrow_pda: Optional[str] = None,
        amount: Optional[float] = None
    ) -> bool:
        """Update service request status."""
        request = self.db.get_request(request_id)
        if not request:
            return False
        
        previous_status = request.status
        request.status = status
        request.updated_at = datetime.utcnow().isoformat()
        
        if escrow_pda:
            request.escrow_pda = escrow_pda
        if amount is not None:
            request.amount = amount
        if status == "completed":
            request.completed_at = datetime.utcnow().isoformat()
        
        # Persist request first
        ok = self.db.update_request(request)
        
        # If transitioning into a terminal state, update provider job stats once
        if ok and previous_status not in ("completed", "failed") and status in ("completed", "failed"):
            provider_addr = request.provider_address
            if provider_addr:
                provider = self.db.get_provider(provider_addr)
                if provider:
                    success = status == "completed"
                    amt = request.amount if (request.amount is not None) else (amount if amount is not None else 0.0)
                    provider.record_job_completion(success=success, amount=float(amt or 0.0))
                    self.db.add_provider(provider)  # triggers stats update
        
        return ok
    
    def record_job_completion(
        self,
        provider_address: str,
        success: bool,
        amount: float
    ) -> bool:
        """Record a completed job for a provider."""
        provider = self.db.get_provider(provider_address)
        if not provider:
            return False
        
        provider.record_job_completion(success, amount)
        return self.db.add_provider(provider)
    
    # ===== Reviews =====
    
    def add_review(
        self,
        provider_address: str,
        client_address: str,
        service_type: str,
        rating: float,
        comment: str,
        transaction_signature: str
    ) -> bool:
        """Add a review for a provider."""
        review = Review(
            review_id=str(uuid.uuid4()),
            provider_address=provider_address,
            client_address=client_address,
            service_type=service_type,
            rating=rating,
            comment=comment,
            transaction_signature=transaction_signature
        )
        
        return self.db.add_review(review)
    
    def get_provider_reviews(self, provider_address: str) -> List[Review]:
        """Get all reviews for a provider."""
        return self.db.get_provider_reviews(provider_address)
    
    # ===== Statistics =====
    
    def get_marketplace_stats(self) -> MarketplaceStats:
        """Get marketplace statistics."""
        return self.db.get_stats()
    
    def get_provider_stats(self, agent_address: str) -> Optional[Dict]:
        """Get statistics for a specific provider."""
        provider = self.db.get_provider(agent_address)
        if not provider:
            return None
        
        return {
            'agent_address': provider.agent_address,
            'agent_name': provider.agent_name,
            'status': provider.status,
            'rating': provider.rating,
            'review_count': provider.review_count,
            'total_jobs': provider.total_jobs,
            'completed_jobs': provider.completed_jobs,
            'failed_jobs': provider.failed_jobs,
            'success_rate': provider.completed_jobs / provider.total_jobs if provider.total_jobs > 0 else 1.0,
            'total_earned': provider.total_earned,
            'services_offered': len(provider.services),
            'last_seen': provider.last_seen
        }
    
    def get_provider_requests(self, provider_address: str):
        """Get service requests (jobs) for a provider."""
        return self.db.get_provider_requests(provider_address)
    
    # ===== Search =====
    
    def search_providers(
        self,
        service_type: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_price: Optional[float] = None,
        status: str = "online"
    ) -> List[Provider]:
        """Search providers with filters."""
        return self.db.search_providers(
            service_type=service_type,
            min_rating=min_rating,
            max_price=max_price,
            status=status
        )

    # ===== On-chain Balance (SPL Token) =====
    def get_provider_balance(self, agent_address: str, mint: str, rpc_url: Optional[str] = None) -> Dict:
        """Fetch the SPL token balance for a provider's Solana wallet for the given mint.

        Returns a dict with: address, mint, ata, raw_amount (int), decimals, amount (float tokens).
        """
        provider = self.db.get_provider(agent_address)
        if not provider:
            return {
                'address': None,
                'mint': mint,
                'ata': None,
                'raw_amount': 0,
                'decimals': 6,
                'amount': 0.0,
            }

        owner = provider.solana_address
        rpc = rpc_url or os.getenv("HELIUS_RPC_URL", "https://devnet.helius-rpc.com/?api-key=e38568c5-7dc3-4f1e-9eda-f6acbb452075")

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                owner,
                {"mint": mint},
                {"encoding": "jsonParsed"}
            ]
        }
        try:
            req = Request(rpc, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
        except (URLError, HTTPError, TimeoutError, Exception) as e:
            print(f"Error fetching token accounts: {e}")
            return {
                'address': owner,
                'mint': mint,
                'ata': None,
                'raw_amount': 0,
                'decimals': 6,
                'amount': 0.0,
            }

        try:
            value = (res.get("result") or {}).get("value") or []
            if not value:
                return {
                    'address': owner,
                    'mint': mint,
                    'ata': None,
                    'raw_amount': 0,
                    'decimals': 6,
                    'amount': 0.0,
                }
            first = value[0]
            ata = first.get("pubkey")
            token_amount = (((first.get("account") or {}).get("data") or {}).get("parsed") or {}).get("info", {}).get("tokenAmount", {})
            raw_str = token_amount.get("amount", "0")
            decimals = int(token_amount.get("decimals", 6))
            try:
                raw_amount = int(raw_str)
            except Exception:
                raw_amount = 0
            amount = raw_amount / (10 ** decimals) if decimals >= 0 else 0.0
            return {
                'address': owner,
                'mint': mint,
                'ata': ata,
                'raw_amount': raw_amount,
                'decimals': decimals,
                'amount': amount,
            }
        except Exception as e:
            print(f"Error parsing token accounts: {e}")
            return {
                'address': owner,
                'mint': mint,
                'ata': None,
                'raw_amount': 0,
                'decimals': 6,
                'amount': 0.0,
            }
