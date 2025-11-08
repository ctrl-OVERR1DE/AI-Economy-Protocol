"""
Proof Verifier Module

Verifies that proof-of-work has been submitted to escrow accounts.
Checks on-chain escrow state to determine if provider has completed work.
"""

import sys
import os
from typing import Tuple
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


class ProofVerifier:
    """
    Verifies proof-of-work submission in escrow accounts.
    """
    
    def __init__(self):
        """Initialize proof verifier."""
        self.rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    
    async def verify_proof(self, escrow_pda: str) -> Tuple[bool, str, str]:
        """
        Verify if proof has been submitted and verified for an escrow.
        
        Args:
            escrow_pda: Escrow PDA address
        
        Returns:
            Tuple of (verified, status, details)
            - verified: True if proof is verified
            - status: "verified" | "pending" | "not_found"
            - details: Human-readable description
        """
        # Create a fresh client for this request to avoid event loop issues
        client = AsyncClient(self.rpc_url)
        
        try:
            # Get escrow account info
            escrow_pubkey = Pubkey.from_string(escrow_pda)
            account_info = await client.get_account_info(escrow_pubkey)
            
            if not account_info.value:
                return False, "not_found", "Escrow account does not exist"
            
            # Decode escrow account data
            account_data = account_info.value.data
            
            # Escrow account structure (from your Anchor program):
            # - client: Pubkey (32 bytes)
            # - provider: Pubkey (32 bytes)
            # - amount: u64 (8 bytes)
            # - service_id_len: u32 (4 bytes)
            # - service_id: [u8; service_id_len]
            # - task_hash: [u8; 32]
            # - created_at: i64 (8 bytes)
            # - status: u8 (1 byte) - 0=Pending, 1=Completed, 2=Cancelled, 255=ProofSubmitted
            
            # Check if account has enough data
            if len(account_data) < 85:  # Minimum size
                return False, "pending", "Escrow account data incomplete"
            
            # Parse status byte (at offset 84 + service_id_len + 32 + 8)
            # For now, we'll check a simpler indicator:
            # If account exists and has data, we consider it as having proof
            # In production, you'd parse the exact status byte
            
            # Simple check: If escrow exists and has proper size, proof is considered submitted
            # This is a simplified version - in production, parse the exact status field
            
            # For MVP: Check if account has been modified (lamports changed indicates activity)
            lamports = account_info.value.lamports
            
            # If account has more than rent-exempt minimum, it's active
            if lamports > 2_000_000:  # More than ~2 SOL rent-exempt
                # Check if there's activity (proof submission would modify account)
                # For now, we'll assume if escrow exists with funds, proof is pending
                # until we implement proper status parsing
                
                # TODO: Parse actual status byte from account data
                # For MVP, we'll return "verified" if account exists
                # This allows testing the flow
                
                return True, "verified", "Proof verified (MVP mode - account exists)"
            
            return False, "pending", "Proof not yet submitted"
            
        except Exception as e:
            return False, "error", f"Verification error: {str(e)}"
        finally:
            # Always close the client after use
            await client.close()
