"""
x402 Payment Verifier

Verifies escrow-based payments for x402 protocol.
"""

import os
import json
import base64
import hashlib
from typing import Tuple, Optional, Dict, Any
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

# Add project root to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from contracts.client.escrow_client import EscrowClient


class PaymentVerifier:
    """
    Verifies x402 payments using AEP escrow contracts.
    
    Unlike standard x402 (direct transfers), this verifies that:
    1. Payment is locked in escrow
    2. Escrow PDA matches task hash
    3. Amount is sufficient
    4. Escrow is in correct state
    """
    
    def __init__(
        self,
        rpc_url: str = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com"),
        escrow_program_id: str = os.getenv("ESCROW_PROGRAM_ID"),
    ):
        self.rpc_url = rpc_url
        self.escrow_program_id = escrow_program_id
        self.client = AsyncClient(rpc_url)
    
    async def verify_x_payment_header(
        self,
        x_payment_header: str,
        expected_amount: float,
        service_id: str,
        task_data: str,
        provider_pubkey: str,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Verify X-Payment header contains valid escrow payment.
        
        Args:
            x_payment_header: Base64 encoded X-Payment header
            expected_amount: Expected payment amount in SOL
            service_id: Service identifier
            task_data: Task data for hash verification
            provider_pubkey: Provider's public key
        
        Returns:
            Tuple of (is_valid, error_message, payment_details)
        """
        try:
            # Decode X-Payment header
            payment_json = base64.b64decode(x_payment_header).decode('utf-8')
            payment_data = json.loads(payment_json)
            
            # Validate structure
            if payment_data.get('x402Version') != 1:
                return False, "Invalid x402 version", None
            
            if payment_data.get('scheme') != 'escrow':
                return False, "Invalid payment scheme (expected 'escrow')", None
            
            if payment_data.get('network') != 'solana-devnet':
                return False, "Invalid network (expected 'solana-devnet')", None
            
            payload = payment_data.get('payload', {})
            escrow_pda = payload.get('escrowPDA')
            task_hash = payload.get('taskHash')
            serialized_tx = payload.get('serializedTransaction')
            nonce = payload.get('nonce')
            
            if not escrow_pda:
                return False, "Missing escrowPDA in payload", None
            
            if not task_hash:
                return False, "Missing taskHash in payload", None
            
            if not serialized_tx:
                return False, "Missing serializedTransaction in payload", None
            
            if not nonce:
                return False, "Missing nonce in payload", None
            
            # Verify task hash matches (including nonce)
            expected_hash = self._compute_task_hash(service_id, task_data, nonce)
            if task_hash != expected_hash:
                return False, f"Task hash mismatch (expected {expected_hash})", None
            
            # Check if escrow already exists
            print("   🔍 Checking if escrow already exists...")
            escrow_pubkey = Pubkey.from_string(escrow_pda)
            existing_account = await self.client.get_account_info(escrow_pubkey)
            
            if existing_account.value:
                print(f"   ♻️  Escrow already exists, reusing...")
                signature = "ESCROW_ALREADY_EXISTS"
            else:
                # Submit the transaction to blockchain
                print("   📤 Submitting escrow transaction to blockchain...")
                try:
                    from solders.transaction import VersionedTransaction
                    
                    # Decode transaction
                    tx_bytes = base64.b64decode(serialized_tx)
                    tx = VersionedTransaction.from_bytes(tx_bytes)
                    
                    # Submit transaction
                    from solana.rpc.types import TxOpts
                    print(f"   Transaction size: {len(bytes(tx))} bytes")
                    
                    resp = await self.client.send_raw_transaction(
                        bytes(tx),
                        opts=TxOpts(skip_preflight=False, preflight_commitment="confirmed")
                    )
                    signature = str(resp.value)
                    print(f"   ✅ Escrow initialized on-chain!")
                    print(f"   Transaction: {signature}")
                    print(f"   🔗 https://explorer.solana.com/tx/{signature}?cluster=devnet")
                    
                    # Wait for transaction to be confirmed
                    print(f"   ⏳ Waiting for confirmation...")
                    import asyncio
                    
                    # Wait and retry checking for account
                    for i in range(10):  # Try 10 times
                        await asyncio.sleep(2)  # Wait 2 seconds each time
                        check_account = await self.client.get_account_info(escrow_pubkey)
                        if check_account.value:
                            print(f"   ✅ Escrow confirmed after {(i+1)*2} seconds")
                            break
                        print(f"   ⏳ Still waiting... ({(i+1)*2}s)")
                    else:
                        print(f"   ⚠️  Escrow not confirmed after 20s, continuing anyway...")
                    
                except Exception as e:
                    print(f"   ❌ Transaction submission failed: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return False, f"Failed to submit transaction: {str(e)}", None
            
            # Verify escrow exists and is valid
            is_valid, error = await self._verify_escrow_on_chain(
                escrow_pda,
                expected_amount,
                provider_pubkey,
            )
            
            if not is_valid:
                return False, error, None
            
            # Payment verified!
            payment_details = {
                'escrowPDA': escrow_pda,
                'taskHash': task_hash,
                'serviceId': payload.get('serviceId'),
                'amount': expected_amount,
                'escrowInitTx': signature,
            }
            
            return True, None, payment_details
            
        except json.JSONDecodeError:
            return False, "Invalid JSON in X-Payment header", None
        except base64.binascii.Error:
            return False, "Invalid base64 encoding in X-Payment header", None
        except Exception as e:
            return False, f"Payment verification error: {str(e)}", None
    
    async def _verify_escrow_on_chain(
        self,
        escrow_pda: str,
        expected_amount: float,
        provider_pubkey: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify escrow account exists on-chain with correct state.
        
        Args:
            escrow_pda: Escrow PDA address
            expected_amount: Expected amount in SOL
            provider_pubkey: Provider's public key
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            print(f"   🔍 Verifying escrow account on-chain...")
            print(f"   Escrow PDA: {escrow_pda}")
            
            # Get escrow account info
            escrow_pubkey = Pubkey.from_string(escrow_pda)
            account_info = await self.client.get_account_info(escrow_pubkey)
            
            print(f"   Account info: {account_info}")
            
            if not account_info.value:
                print(f"   ❌ Escrow account does not exist yet")
                return False, "Escrow account does not exist"
            
            print(f"   ✅ Escrow account exists!")
            print(f"   Owner: {account_info.value.owner}")
            print(f"   Lamports: {account_info.value.lamports}")
            
            # TODO: Decode escrow account data and verify:
            # - Amount matches expected
            # - Provider matches
            # - Status is Pending
            # For now, just check account exists
            
            # Convert SOL to lamports for comparison
            expected_lamports = int(expected_amount * 1_000_000_000)
            
            # Account exists, assume valid for MVP
            # In production, decode and verify all fields
            return True, None
            
        except Exception as e:
            print(f"   ❌ Verification error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, f"On-chain verification failed: {str(e)}"
    
    def _compute_task_hash(self, service_id: str, task_data: str, nonce: int) -> str:
        """
        Compute SHA256 hash of task data with nonce.
        
        Args:
            service_id: Service identifier
            task_data: Task data
            nonce: Unique nonce for this request
        
        Returns:
            Hex string of SHA256 hash
        """
        combined = f"{service_id}:{task_data}:{nonce}"
        hash_bytes = hashlib.sha256(combined.encode('utf-8')).digest()
        return hash_bytes.hex()
    
    async def close(self):
        """Close the RPC client."""
        await self.client.close()
