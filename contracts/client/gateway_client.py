import os
import httpx
from typing import Dict, Any, Optional
import base64


class GatewayClient:
    """Client for Sanctum Gateway Transaction Processing Gateway (TPG)."""

    # TPG endpoint base; full URL is https://tpg.sanctum.so/v1/{cluster}?apiKey={apiKey}
    # Per line 411: "We've recently introduced a v1 set of APIs"
    BASE_URL = "https://tpg.sanctum.so/v1"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("GATEWAY_API_KEY")
        if not self.api_key:
            raise ValueError("GATEWAY_API_KEY not provided or set in environment")
        self.base_url = base_url or self.BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def optimize_transaction(
        self,
        transaction: bytes,
        cluster: str = "devnet",
        request_id: str = "aep-escrow-init",
    ) -> Dict[str, Any]:
        """Call Gateway optimizeTransaction over JSON-RPC.

        Endpoint format: https://tpg.sanctum.so/v1/{cluster}?apiKey={apiKey}
        Body:
          {
            "jsonrpc":"2.0",
            "id":"...",
            "method":"optimizeTransaction",
            "params":{ "transactions": [ { "params": [ base64_tx ] } ] }
          }
        """
        url = f"{self.base_url}/{cluster}?apiKey={self.api_key}"
        b64_tx = base64.b64encode(transaction).decode()
        body: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "optimizeTransaction",
            "params": {
                "transactions": [
                    {"params": [b64_tx]}
                ]
            },
        }
        resp = await self.client.post(url, json=body, headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        return resp.json()

    async def build_gateway_transaction(
        self,
        unsigned_transaction: bytes,
        cluster: str = "devnet",
        request_id: str = "aep-build",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call Gateway buildGatewayTransaction to set blockhash, fees, and tip routing.

        Per docs: https://gateway.sanctum.so/docs/concepts/builder
        Returns JSON with result.transaction (base64) and result.latestBlockhash.
        """
        url = f"{self.base_url}/{cluster}?apiKey={self.api_key}"
        b64_tx = base64.b64encode(unsigned_transaction).decode()
        body: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "buildGatewayTransaction",
            "params": [
                b64_tx,
                options or {},
            ],
        }
        resp = await self.client.post(url, json=body, headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        return resp.json()

    async def send_transaction(
        self,
        signed_transaction: bytes,
        cluster: str = "devnet",
        request_id: str = "aep-send",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call Gateway sendTransaction with base64-encoded signed wire transaction.
        
        Per docs: https://gateway.sanctum.so/docs/concepts/delivery
        Params can be:
        - [base64_tx] - just the transaction
        - [base64_tx, {encoding: "base64", startSlot: 123}] - with options
        """
        url = f"{self.base_url}/{cluster}?apiKey={self.api_key}"
        b64_tx = base64.b64encode(signed_transaction).decode()
        
        # Build params array - ONLY the base64 transaction, nothing else
        # Per Sanctum docs: params should be [base64_tx] or [base64_tx, {options}]
        params = [b64_tx]
        if options is not None:
            params.append(options)
        
        body: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "sendTransaction",
            "params": params,
        }
        
        resp = await self.client.post(url, json=body, headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()
