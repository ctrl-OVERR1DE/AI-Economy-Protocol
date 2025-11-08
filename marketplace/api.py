"""
Marketplace API

FastAPI endpoints for marketplace operations.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn

from .service import MarketplaceService
from .models import ProviderStatus


# Initialize FastAPI app
app = FastAPI(
    title="AI Agent Marketplace API",
    description="API for discovering and managing AI service providers",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize marketplace service
marketplace = MarketplaceService()


# ===== Request/Response Models =====

class ServiceOfferingModel(BaseModel):
    service_type: str
    base_price: float
    description: str
    features: List[str]
    avg_completion_time: int
    success_rate: float = 1.0


class RegisterProviderRequest(BaseModel):
    agent_address: str
    agent_name: str
    solana_address: str
    port: int
    endpoint: str
    services: List[Dict]


class UpdateStatusRequest(BaseModel):
    agent_address: str
    status: str  # online, offline, busy


class CreateRequestModel(BaseModel):
    client_address: str
    service_type: str
    provider_address: Optional[str] = None


class UpdateRequestModel(BaseModel):
    request_id: str
    status: str
    escrow_pda: Optional[str] = None
    amount: Optional[float] = None


class AddReviewRequest(BaseModel):
    provider_address: str
    client_address: str
    service_type: str
    rating: float
    comment: str
    transaction_signature: str


class RecordJobRequest(BaseModel):
    provider_address: str
    success: bool
    amount: float


# ===== API Endpoints =====

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "AI Agent Marketplace API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ===== Provider Endpoints =====

@app.post("/providers/register")
async def register_provider(request: RegisterProviderRequest):
    """Register a new provider or update existing one."""
    success = marketplace.register_provider(
        agent_address=request.agent_address,
        agent_name=request.agent_name,
        solana_address=request.solana_address,
        port=request.port,
        endpoint=request.endpoint,
        services=request.services
    )
    
    if success:
        return {"success": True, "message": "Provider registered successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to register provider")


@app.post("/providers/unregister")
async def unregister_provider(agent_address: str):
    """Unregister a provider (set status to offline)."""
    success = marketplace.unregister_provider(agent_address)
    
    if success:
        return {"success": True, "message": "Provider unregistered successfully"}
    else:
        raise HTTPException(status_code=404, detail="Provider not found")


@app.post("/providers/status")
async def update_provider_status(request: UpdateStatusRequest):
    """Update provider status."""
    try:
        status = ProviderStatus(request.status)
        success = marketplace.update_provider_status(request.agent_address, status)
        
        if success:
            return {"success": True, "message": "Status updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Provider not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status value")


@app.get("/providers")
async def get_all_providers():
    """Get all providers."""
    providers = marketplace.get_all_providers()
    return {"providers": [p.to_dict() for p in providers]}


@app.get("/providers/online")
async def get_online_providers():
    """Get all online providers."""
    providers = marketplace.get_online_providers()
    return {"providers": [p.to_dict() for p in providers]}


@app.get("/providers/{agent_address}")
async def get_provider(agent_address: str):
    """Get provider details."""
    provider = marketplace.get_provider(agent_address)
    
    if provider:
        return {"provider": provider.to_dict()}
    else:
        raise HTTPException(status_code=404, detail="Provider not found")


@app.get("/providers/{agent_address}/stats")
async def get_provider_stats(agent_address: str):
    """Get provider statistics."""
    stats = marketplace.get_provider_stats(agent_address)
    
    if stats:
        return {"stats": stats}
    else:
        raise HTTPException(status_code=404, detail="Provider not found")


@app.get("/providers/{agent_address}/reviews")
async def get_provider_reviews(agent_address: str):
    """Get provider reviews."""
    reviews = marketplace.get_provider_reviews(agent_address)
    return {"reviews": [r.to_dict() for r in reviews]}


@app.get("/providers/{agent_address}/requests")
async def get_provider_requests(agent_address: str, limit: Optional[int] = 10):
    """Get recent service requests (job history) for a provider."""
    reqs = marketplace.get_provider_requests(agent_address)
    # Sort by created_at desc (ISO8601 strings sort lexicographically)
    try:
        reqs_sorted = sorted(reqs, key=lambda r: r.created_at, reverse=True)
    except Exception:
        reqs_sorted = reqs
    if limit is not None and limit > 0:
        reqs_sorted = reqs_sorted[:limit]
    return {"requests": [r.to_dict() for r in reqs_sorted]}


@app.get("/providers/{agent_address}/balance")
async def get_provider_balance(agent_address: str, mint: str, rpc_url: Optional[str] = None):
    """Get SPL token balance for a provider's wallet for the given mint."""
    data = marketplace.get_provider_balance(agent_address, mint, rpc_url)
    return {"balance": data}


# ===== Service Discovery Endpoints =====

@app.get("/services")
async def discover_services(service_type: Optional[str] = None):
    """Discover available services."""
    services = marketplace.discover_services(service_type)
    return {"services": services}


@app.get("/services/{service_type}/providers")
async def get_providers_by_service(service_type: str):
    """Get providers offering a specific service."""
    providers = marketplace.get_providers_by_service(service_type)
    return {"providers": [p.to_dict() for p in providers]}


@app.get("/services/{service_type}/best")
async def find_best_provider(
    service_type: str,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None
):
    """Find the best provider for a service."""
    provider = marketplace.find_best_provider(service_type, max_price, min_rating)
    
    if provider:
        return {"provider": provider}
    else:
        raise HTTPException(status_code=404, detail="No suitable provider found")


# ===== Service Request Endpoints =====

@app.post("/requests")
async def create_request(request: CreateRequestModel):
    """Create a new service request."""
    service_request = marketplace.create_request(
        client_address=request.client_address,
        service_type=request.service_type,
        provider_address=request.provider_address
    )
    
    return {"request": service_request.to_dict()}


@app.put("/requests")
async def update_request(request: UpdateRequestModel):
    """Update service request status."""
    success = marketplace.update_request_status(
        request_id=request.request_id,
        status=request.status,
        escrow_pda=request.escrow_pda,
        amount=request.amount
    )
    
    if success:
        return {"success": True, "message": "Request updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Request not found")


@app.post("/jobs/complete")
async def record_job_completion(request: RecordJobRequest):
    """Record a completed job."""
    success = marketplace.record_job_completion(
        provider_address=request.provider_address,
        success=request.success,
        amount=request.amount
    )
    
    if success:
        return {"success": True, "message": "Job recorded successfully"}
    else:
        raise HTTPException(status_code=404, detail="Provider not found")


# ===== Review Endpoints =====

@app.post("/reviews")
async def add_review(request: AddReviewRequest):
    """Add a review for a provider."""
    success = marketplace.add_review(
        provider_address=request.provider_address,
        client_address=request.client_address,
        service_type=request.service_type,
        rating=request.rating,
        comment=request.comment,
        transaction_signature=request.transaction_signature
    )
    
    if success:
        return {"success": True, "message": "Review added successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to add review")


# ===== Statistics Endpoints =====

@app.get("/stats")
async def get_marketplace_stats():
    """Get marketplace statistics."""
    stats = marketplace.get_marketplace_stats()
    return {"stats": stats.to_dict()}


# ===== Search Endpoints =====

@app.get("/search")
async def search_providers(
    service_type: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_price: Optional[float] = None,
    status: str = "online"
):
    """Search providers with filters."""
    providers = marketplace.search_providers(
        service_type=service_type,
        min_rating=min_rating,
        max_price=max_price,
        status=status
    )
    
    return {"providers": [p.to_dict() for p in providers]}


# ===== Run Server =====

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the marketplace API server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    print("Starting AI Agent Marketplace API...")
    print("API Documentation: http://localhost:8000/docs")
    start_server()
