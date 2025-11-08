"""
AEP x402 Client

HTTP client implementing x402 protocol with escrow-based payments.
Handles 402 responses and creates escrow transactions for payment.
"""

import os
import sys
import json
import base64
import asyncio
import requests
from typing import Dict, Any, Optional, Tuple

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from agents.x402.escrow_payment import create_escrow_transaction, serialize_transaction_for_x_payment
from agents.utils.solana_utils import load_agent_wallet


class X402Client:
    """
    x402 HTTP client with escrow-based payment support.
    
    Automatically handles 402 responses by creating escrow transactions
    and retrying with X-Payment header.
    """
    
    def __init__(self, wallet_keypair=None, agent_name: str = "ClientAgent"):
        """
        Initialize x402 client.
        
        Args:
            wallet_keypair: Optional wallet keypair (loads from agent_name if not provided)
            agent_name: Name of the agent (for wallet loading)
        """
        if wallet_keypair is None:
            wallet_keypair = load_agent_wallet(agent_name)
        
        self.wallet = wallet_keypair
        self.agent_name = agent_name
    
    async def request_with_payment(
        self,
        url: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Make an HTTP request with automatic x402 payment handling.
        
        Flow:
        1. Make initial request
        2. If 402, create escrow transaction
        3. Retry with X-Payment header
        4. Return result
        
        Args:
            url: Target URL
            method: HTTP method (GET, POST)
            data: Optional request data
            headers: Optional additional headers
        
        Returns:
            Tuple of (status_code, response_json)
        """
        if headers is None:
            headers = {}
        
        # Step 1: Make initial request (expect 402)
        print(f"\n🔍 Requesting service: {url}")
        
        if method.upper() == "GET":
            resp = requests.get(url, params=data, headers=headers)
        else:
            resp = requests.post(url, json=data, headers=headers)
        
        # If not 402, return immediately
        if resp.status_code != 402:
            return resp.status_code, resp.json()
        
        # Step 2: Handle 402 Payment Required
        print("💰 Payment required (402 response)")
        
        try:
            payment_req = resp.json()
            payment_info = payment_req.get('payment', {})
            
            print(f"📋 Payment details:")
            print(f"   Recipient: {payment_info.get('recipient')}")
            print(f"   Amount: {payment_info.get('amount')} SOL")
            print(f"   Service ID: {payment_info.get('serviceId')}")
            print(f"   Network: {payment_info.get('network')}")
            
            # Extract payment requirements
            recipient = payment_info.get('recipient')
            amount = payment_info.get('amount')
            service_id = payment_info.get('serviceId')
            task_data = payment_info.get('taskData', data.get('data', '') if data else '')
            
            if not all([recipient, amount, service_id]):
                raise ValueError("Incomplete payment requirements in 402 response")
            
            # Step 3: Create escrow transaction
            print("\n🔒 Creating escrow transaction...")
            
            tx, escrow_pda, task_hash, nonce = await create_escrow_transaction(
                client_wallet=self.wallet,
                provider_address=recipient,
                service_id=service_id,
                task_data=task_data,
                amount_sol=amount,
            )
            
            print(f"✅ Escrow transaction created")
            print(f"   Escrow PDA: {escrow_pda}")
            print(f"   Task Hash: {task_hash}")
            print(f"   Nonce: {nonce}")
            
            # Step 4: Serialize transaction for X-Payment header
            serialized_tx = serialize_transaction_for_x_payment(tx)
            
            # Step 5: Create X-Payment header (x402 standard with escrow scheme)
            x_payment_data = {
                "x402Version": 1,
                "scheme": "escrow",  # Custom scheme for AEP
                "network": "solana-devnet",
                "payload": {
                    "serializedTransaction": serialized_tx,
                    "escrowPDA": str(escrow_pda),
                    "serviceId": service_id,
                    "taskHash": task_hash,
                    "nonce": nonce,  # Include nonce for server verification
                }
            }
            
            x_payment_header = base64.b64encode(
                json.dumps(x_payment_data).encode('utf-8')
            ).decode('utf-8')
            
            # Step 6: Retry request with X-Payment header
            print("\n📤 Retrying request with payment proof...")
            
            headers['X-Payment'] = x_payment_header
            
            if method.upper() == "GET":
                resp = requests.get(url, params=data, headers=headers)
            else:
                resp = requests.post(url, json=data, headers=headers)
            
            if resp.status_code == 200:
                print("✅ Payment accepted! Service completed.")
                result = resp.json()
                
                # Display payment details if available
                if 'paymentDetails' in result:
                    payment_details = result['paymentDetails']
                    print(f"\n💸 Payment details:")
                    print(f"   Escrow PDA: {payment_details.get('escrowPDA')}")
                    print(f"   Amount: {payment_details.get('amountPaid')} SOL")
                    if payment_details.get('proofSubmitTx'):
                        print(f"   Proof TX: {payment_details.get('proofSubmitTx')}")
                
                return resp.status_code, result
            else:
                print(f"❌ Payment rejected: {resp.status_code}")
                return resp.status_code, resp.json()
                
        except Exception as e:
            print(f"❌ Payment flow error: {e}")
            raise
    
    async def get_with_payment(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Convenience method for GET requests with payment.
        
        Args:
            url: Target URL
            params: Optional query parameters
        
        Returns:
            Tuple of (status_code, response_json)
        """
        return await self.request_with_payment(url, method="GET", data=params)
    
    async def post_with_payment(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Convenience method for POST requests with payment.
        
        Args:
            url: Target URL
            data: Optional request body
        
        Returns:
            Tuple of (status_code, response_json)
        """
        return await self.request_with_payment(url, method="POST", data=data)


async def main():
    """
    Example usage of x402 client.
    """
    print("="*70)
    print("AEP x402 Client - Example Usage")
    print("="*70)
    
    # Initialize client
    client = X402Client(agent_name="ClientAgent")
    
    # Make request to x402-protected endpoint
    status, response = await client.get_with_payment(
        url="http://localhost:8000/analyze",
        params={"data": "Analyze Q4 2024 sales data"}
    )
    
    print(f"\n📊 Final result:")
    print(f"   Status: {status}")
    if status == 200 and 'result' in response:
        print(f"   Analysis: {response['result']}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(main())
