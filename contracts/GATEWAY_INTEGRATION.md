# Phase 2.2: Sanctum Gateway Integration Guide

## Overview
Sanctum Gateway provides optimized transaction routing for Solana, ensuring maximum reliability and cost savings for agent payments.

## Prerequisites
- ✅ Phase 2.1 completed (escrow contract deployed)
- ✅ Solana wallet with devnet SOL
- ✅ Gateway API access

## Step 1: Sign Up for Gateway Access

### 1. Visit Gateway Platform
```
https://gateway.sanctum.so/
```

### 2. Create Account
- Sign up with your email
- Verify your account
- Access the dashboard

### 3. Get API Key
- Navigate to API Keys section
- Generate a new API key
- Copy and save securely

### 4. Update Environment
```bash
# Add to .env
GATEWAY_API_KEY=your_gateway_api_key_here
```

## Step 2: Install Gateway SDK

### Python Client
```bash
pip install sanctum-gateway-sdk
# or
pip install httpx  # For direct API calls
```

### JavaScript/TypeScript
```bash
npm install @sanctum/gateway-sdk
```

## Step 3: Gateway Client Implementation

### Basic Gateway Client (Python)
```python
import httpx
import os
from typing import Dict, Any

class GatewayClient:
    """Client for Sanctum Gateway API."""
    
    BASE_URL = "https://gateway.sanctum.so/api/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"}
        )
    
    async def build_gateway_transaction(
        self,
        transaction: bytes,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Build an optimized transaction using Gateway.
        
        Args:
            transaction: Serialized Solana transaction
            options: Gateway options (routing, priority, etc.)
        
        Returns:
            Gateway transaction response
        """
        payload = {
            "transaction": transaction.hex(),
            "options": options or {
                "routing": "dual-path",  # RPC + Jito
                "priority": "medium",
                "max_retries": 3,
            }
        }
        
        response = await self.client.post(
            "/transactions/build",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_transaction(
        self,
        gateway_tx_id: str
    ) -> Dict[str, Any]:
        """
        Send a Gateway-optimized transaction.
        
        Args:
            gateway_tx_id: ID from buildGatewayTransaction
        
        Returns:
            Transaction result
        """
        response = await self.client.post(
            f"/transactions/{gateway_tx_id}/send"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_transaction_status(
        self,
        gateway_tx_id: str
    ) -> Dict[str, Any]:
        """Get status of a Gateway transaction."""
        response = await self.client.get(
            f"/transactions/{gateway_tx_id}/status"
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
```

## Step 4: Integration with Escrow Client

### Updated Escrow Client with Gateway
```python
from escrow_client import EscrowClient
from gateway_client import GatewayClient

class GatewayEscrowClient(EscrowClient):
    """Escrow client with Gateway integration."""
    
    def __init__(self, *args, gateway_api_key: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.gateway = GatewayClient(
            gateway_api_key or os.getenv("GATEWAY_API_KEY")
        )
    
    async def initialize_escrow_with_gateway(
        self,
        provider_pubkey: Pubkey,
        amount: int,
        service_id: str,
        task_data: str
    ) -> str:
        """
        Initialize escrow using Gateway for optimized routing.
        """
        # 1. Build Solana transaction
        tx = await self._build_initialize_tx(
            provider_pubkey, amount, service_id, task_data
        )
        
        # 2. Send to Gateway for optimization
        gateway_tx = await self.gateway.build_gateway_transaction(
            transaction=tx.serialize(),
            options={
                "routing": "dual-path",
                "priority": "high",  # Escrow init is critical
                "max_retries": 5,
            }
        )
        
        # 3. Send optimized transaction
        result = await self.gateway.send_transaction(
            gateway_tx["transaction_id"]
        )
        
        # 4. Monitor status
        status = await self.gateway.get_transaction_status(
            gateway_tx["transaction_id"]
        )
        
        return result["signature"]
```

## Step 5: Configure Dual-Path Routing

### Routing Options
```python
# Option 1: Dual-Path (Recommended for escrow)
routing_config = {
    "routing": "dual-path",      # RPC + Jito simultaneously
    "rpc_endpoint": "https://api.devnet.solana.com",
    "jito_tip": 0.0001,          # SOL tip for Jito
    "refund_on_rpc_success": True  # Refund tip if RPC lands first
}

# Option 2: RPC Only (Lower cost, less reliable)
routing_config = {
    "routing": "rpc-only",
    "rpc_endpoint": "https://api.devnet.solana.com",
}

# Option 3: Jito Only (Higher cost, higher reliability)
routing_config = {
    "routing": "jito-only",
    "jito_tip": 0.001,
}

# Option 4: Round Robin (Load balancing)
routing_config = {
    "routing": "round-robin",
    "endpoints": [
        {"url": "https://api.devnet.solana.com", "weight": 0.5},
        {"url": "https://rpc.helius.xyz", "weight": 0.3},
        {"url": "https://api.mainnet-beta.solana.com", "weight": 0.2},
    ]
}
```

## Step 6: Set Up Transaction Monitoring

### Dashboard Access
1. Log in to Gateway dashboard
2. Navigate to "Transactions" tab
3. View real-time transaction status
4. Monitor success rates and Jito refunds

### Programmatic Monitoring
```python
async def monitor_escrow_transaction(
    gateway_client: GatewayClient,
    tx_id: str,
    timeout: int = 60
):
    """Monitor a Gateway transaction until completion."""
    import asyncio
    
    start_time = asyncio.get_event_loop().time()
    
    while True:
        status = await gateway_client.get_transaction_status(tx_id)
        
        if status["status"] == "confirmed":
            print(f"✓ Transaction confirmed: {status['signature']}")
            if status.get("jito_tip_refunded"):
                print(f"✓ Jito tip refunded: {status['refund_amount']} SOL")
            return status
        
        elif status["status"] == "failed":
            print(f"✗ Transaction failed: {status['error']}")
            return status
        
        # Check timeout
        if asyncio.get_event_loop().time() - start_time > timeout:
            print("⚠ Transaction timeout")
            return status
        
        # Wait before next check
        await asyncio.sleep(2)
```

## Step 7: Testing

### Test Gateway Integration
```bash
# Run escrow initialization with Gateway
python -m pytest tests/test_gateway_escrow.py -v

# Monitor Gateway dashboard for transaction
# Verify dual-path routing worked
# Check if Jito tip was refunded
```

### Expected Results
- ✅ Transaction sent via both RPC and Jito
- ✅ Transaction confirmed within 2-5 seconds
- ✅ If RPC succeeded first, Jito tip refunded
- ✅ Transaction visible in Gateway dashboard
- ✅ Success rate metrics updated

## Gateway Benefits for AEP

### 1. Reliability
- Dual-path ensures escrow transactions land
- No manual retries needed
- Autonomous agents can trust payment delivery

### 2. Cost Savings
- Jito tips refunded if RPC succeeds
- Saves on high-frequency agent payments
- Optimized routing reduces failed transactions

### 3. Observability
- Real-time dashboard monitoring
- Track all agent payment transactions
- Debug failures faster
- Metrics for agent marketplace health

### 4. Developer Efficiency
- No RPC management needed
- Simple API integration
- Change parameters without redeployment
- Built-in retry logic

## Next Steps (Phase 2.3)

After Gateway integration:
1. Update Agent B to use Gateway for escrow initialization
2. Update Agent A to use Gateway for proof submission
3. Test end-to-end payment flow with Gateway
4. Monitor transaction success rates
5. Optimize routing based on metrics

## Resources

- Gateway Platform: https://gateway.sanctum.so/
- Documentation: https://gateway.sanctum.so/docs
- API Reference: https://gateway.sanctum.so/docs/api
- Dashboard: https://gateway.sanctum.so/dashboard

---

**Phase 2.2 Status**: Ready to implement
**Estimated Time**: 2-3 hours
**Blockers**: Need Gateway API key
