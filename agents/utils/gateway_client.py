"""
Gateway Client

Simple client for agents to interact with the x402 Payment Gateway.
Provides clean interface for claiming payments and verifying proofs.
"""

import aiohttp
import logging
from typing import Tuple, Optional, Dict, Any
import uuid

logger = logging.getLogger(__name__)

# Suppress httpx logging to prevent API key exposure
logging.getLogger("httpx").setLevel(logging.WARNING)


class GatewayClient:
    """
    Client for interacting with x402 Payment Gateway.
    
    Usage:
        client = GatewayClient()
        success, result = await client.claim_payment(escrow_pda, provider_address)
    """
    
    def __init__(self, gateway_url: str = "http://localhost:8001", marketplace_url: str = "http://localhost:8000"):
        """
        Initialize gateway client.
        
        Args:
            gateway_url: URL of the payment gateway
            marketplace_url: URL of the marketplace API
        """
        self.gateway_url = gateway_url
        self.marketplace_url = marketplace_url
    
    async def verify_proof(self, escrow_pda: str) -> Tuple[bool, str, str]:
        """
        Verify proof status for an escrow.
        
        Args:
            escrow_pda: Escrow PDA address
        
        Returns:
            Tuple of (verified, status, details)
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.gateway_url}/verify-proof",
                    json={"escrow_pda": escrow_pda}
                ) as response:
                    data = await response.json()
                    
                    if response.status == 200:
                        return (
                            data.get("verified", False),
                            data.get("status", "unknown"),
                            data.get("details", "")
                        )
                    else:
                        return False, "error", data.get("error", "Unknown error")
        
        except Exception as e:
            logger.error(f"Error verifying proof: {e}")
            return False, "error", str(e)
    
    async def claim_payment(
        self,
        escrow_pda: str,
        provider_solana_address: str,
        provider_agent_address: Optional[str] = None,
        client_address: Optional[str] = None,
        service_type: Optional[str] = None,
        amount: Optional[float] = None,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Claim payment from escrow via x402 gateway.
        
        This method handles the x402 flow:
        1. Request payment
        2. If 402, wait and retry (proof not verified yet)
        3. If 200, payment released
        4. Update marketplace request status
        
        Args:
            escrow_pda: Escrow PDA address
            provider_solana_address: Provider's Solana address (used by x402 gateway)
            provider_agent_address: Provider's uAgents address (used by marketplace DB)
            client_address: Client's address (for marketplace tracking)
            service_type: Service type (for marketplace tracking)
            amount: Payment amount (for marketplace tracking)
            max_retries: Maximum number of retries if 402
            retry_delay: Seconds to wait between retries
        
        Returns:
            Tuple of (success, result_data, error_message)
            - success: True if payment released
            - result_data: Payment details (tx, amount, etc.)
            - error_message: Error description if failed
        """
        import asyncio
        
        # Create marketplace request if we have the info
        request_id = None
        if client_address and service_type and (provider_agent_address is not None):
            request_id = await self._create_marketplace_request(
                client_address=client_address,
                service_type=service_type,
                provider_address=provider_agent_address,
                escrow_pda=escrow_pda,
                amount=amount
            )
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.gateway_url}/claim-payment",
                        json={
                            "escrow_pda": escrow_pda,
                            "provider_address": provider_solana_address
                        }
                    ) as response:
                        data = await response.json()
                        
                        if response.status == 200:
                            # Payment released!
                            logger.info(f"✅ Payment claimed successfully!")
                            logger.info(f"   Transaction: {data.get('tx_signature')}")
                            logger.info(f"   Amount: {data.get('amount')} Tokens")
                            
                            # Update marketplace request to completed
                            if request_id:
                                await self._update_marketplace_request(
                                    request_id=request_id,
                                    status="completed",
                                    amount=data.get('amount', amount)
                                )
                            
                            return True, data, None
                        
                        elif response.status == 402:
                            # x402 Paywall: Proof not verified yet
                            details = data.get("details", "Proof not verified")
                            logger.info(f"⏳ x402 Paywall: {details}")
                            
                            if attempt < max_retries - 1:
                                logger.info(f"   Retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                                await asyncio.sleep(retry_delay)
                                continue
                            else:
                                logger.warning(f"❌ Max retries reached. Proof still not verified.")
                                return False, None, details
                        
                        else:
                            # Other error
                            error = data.get("error", "Unknown error")
                            logger.error(f"❌ Payment claim failed: {error}")
                            return False, None, error
            
            except Exception as e:
                logger.error(f"Error claiming payment: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return False, None, str(e)
        
        return False, None, "Max retries exceeded"
    
    async def get_gateway_info(self) -> Optional[Dict[str, Any]]:
        """
        Get gateway information.
        
        Returns:
            Gateway info dict or None if error
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.gateway_url}/") as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Error getting gateway info: {e}")
            return None
    
    async def _create_marketplace_request(
        self,
        client_address: str,
        service_type: str,
        provider_address: str,
        escrow_pda: str,
        amount: Optional[float] = None
    ) -> Optional[str]:
        """Create a service request in the marketplace."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "client_address": client_address,
                    "service_type": service_type,
                    "provider_address": provider_address
                }
                async with session.post(
                    f"{self.marketplace_url}/requests",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        request_id = data.get("request", {}).get("request_id")
                        
                        # Immediately update with escrow and amount if available
                        if request_id:
                            await self._update_marketplace_request(
                                request_id=request_id,
                                status="in_progress",
                                escrow_pda=escrow_pda,
                                amount=amount
                            )
                        
                        return request_id
                    else:
                        logger.warning(f"Failed to create marketplace request: {response.status}")
                        return None
        except Exception as e:
            logger.warning(f"Error creating marketplace request: {e}")
            return None
    
    async def _update_marketplace_request(
        self,
        request_id: str,
        status: str,
        escrow_pda: Optional[str] = None,
        amount: Optional[float] = None
    ) -> bool:
        """Update a service request in the marketplace."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "request_id": request_id,
                    "status": status
                }
                if escrow_pda:
                    payload["escrow_pda"] = escrow_pda
                if amount is not None:
                    payload["amount"] = float(amount)
                
                async with session.put(
                    f"{self.marketplace_url}/requests",
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.debug(f"Updated marketplace request {request_id} to {status}")
                        return True
                    else:
                        logger.warning(f"Failed to update marketplace request: {response.status}")
                        return False
        except Exception as e:
            logger.warning(f"Error updating marketplace request: {e}")
            return False
