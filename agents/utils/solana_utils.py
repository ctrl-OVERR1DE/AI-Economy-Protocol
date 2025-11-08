"""
Solana utilities for agent payment flow.
Handles wallet loading, escrow operations, and transaction management.
"""
import os
import hashlib
import json
import asyncio
import time
from typing import Optional, Tuple
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from dotenv import load_dotenv

from .transaction_logger import (
    get_logger,
    TransactionStatus,
    RoutingMethod,
)

# Add contracts to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "contracts"))

from client.gateway_escrow_client import GatewayEscrowClient


# Load environment variables
load_dotenv()


def load_agent_wallet(agent_name: str) -> Keypair:
    """
    Load Solana wallet for an agent.
    
    Args:
        agent_name: Name of the agent (e.g., "DataAnalystAgent", "ClientAgent")
    
    Returns:
        Keypair for the agent's wallet
    """
    # Try agent-specific wallet first
    wallet_path = os.path.expanduser(f"~/.config/solana/{agent_name.lower()}_id.json")
    
    # Fall back to default wallet
    if not os.path.exists(wallet_path):
        wallet_path = os.path.expanduser(os.getenv("SOLANA_WALLET_PATH", "~/.config/solana/id.json"))
    
    if not os.path.exists(wallet_path):
        raise FileNotFoundError(
            f"Solana wallet not found at {wallet_path}. "
            "Please create a wallet with: solana-keygen new"
        )
    
    with open(wallet_path, 'r') as f:
        secret_key = json.load(f)
    
    return Keypair.from_bytes(bytes(secret_key))


def get_escrow_client(wallet_keypair: Optional[Keypair] = None) -> GatewayEscrowClient:
    """
    Get an initialized escrow client.
    
    Args:
        wallet_keypair: Optional wallet keypair (loads from env if not provided)
    
    Returns:
        GatewayEscrowClient instance
    """
    rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    
    if wallet_keypair is None:
        wallet_keypair = load_agent_wallet("default")
    
    return GatewayEscrowClient(rpc_url=rpc_url, wallet_keypair=wallet_keypair)


async def initialize_escrow_for_service(
    client_wallet: Keypair,
    provider_address: str,
    service_id: str,
    task_data: str,
    amount_lamports: int,
    client_token_account: Optional[Pubkey] = None,
    escrow_token_account: Optional[Pubkey] = None,
    agent_name: str = "unknown",
) -> Tuple[str, Pubkey]:
    """
    Initialize an escrow for a service request.
    
    Args:
        client_wallet: Client's Solana wallet keypair
        provider_address: Provider's Solana address (Pubkey string)
        service_id: Service identifier
        task_data: Task description/data
        amount_lamports: Amount to lock in escrow (in lamports)
        client_token_account: Optional client token account (uses env if not provided)
        escrow_token_account: Optional escrow token account (uses env if not provided)
        agent_name: Name of the agent initiating the transaction
    
    Returns:
        Tuple of (transaction_signature, escrow_pda)
    """
    logger = get_logger()
    start_time = time.time()
    
    # Get token accounts from env if not provided
    # Initialize escrow client first
    escrow_client = GatewayEscrowClient(wallet_keypair=client_wallet)
    
    # Convert provider address to Pubkey
    provider_pubkey = Pubkey.from_string(provider_address)
    
    # Derive escrow PDA using task_hash (matches on-chain seeds)
    task_hash = hashlib.sha256(task_data.encode()).digest()
    escrow_pda, _ = escrow_client.derive_escrow_pda(
        client_wallet.pubkey(), 
        provider_pubkey,
        service_id=None,
        task_hash=task_hash,
    )
    
    # Get client token account - derive from wallet if not provided
    if client_token_account is None:
        from spl.token.instructions import get_associated_token_address
        
        mint_str = os.getenv("TEST_MINT")
        if not mint_str:
            raise ValueError("TEST_MINT not set in environment")
        mint = Pubkey.from_string(mint_str)
        
        # Derive client's ATA for the token mint
        client_token_account = get_associated_token_address(client_wallet.pubkey(), mint)
    
    # Calculate escrow token account dynamically based on escrow PDA
    if escrow_token_account is None:
        from spl.token.instructions import get_associated_token_address, create_associated_token_account
        from solana.rpc.async_api import AsyncClient
        
        mint_str = os.getenv("TEST_MINT")
        if not mint_str:
            raise ValueError("TEST_MINT not set in environment")
        mint = Pubkey.from_string(mint_str)
        
        # Each unique escrow PDA has its own ATA
        escrow_token_account = get_associated_token_address(escrow_pda, mint)
        
        # Check if escrow ATA exists, create if not
        rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
        rpc = AsyncClient(rpc_url)
        ata_info = await rpc.get_account_info(escrow_token_account)
        
        if ata_info.value is None:
            # Create the ATA
            create_ata_ix = create_associated_token_account(
                payer=client_wallet.pubkey(),
                owner=escrow_pda,
                mint=mint
            )
            from solders.message import MessageV0
            from solders.transaction import VersionedTransaction
            from solana.rpc.types import TxOpts
            
            recent_blockhash = await rpc.get_latest_blockhash()
            msg = MessageV0.try_compile(
                payer=client_wallet.pubkey(),
                instructions=[create_ata_ix],
                address_lookup_table_accounts=[],
                recent_blockhash=recent_blockhash.value.blockhash,
            )
            tx = VersionedTransaction(msg, [client_wallet])
            resp = await rpc.send_raw_transaction(bytes(tx), opts=TxOpts(skip_preflight=False))
        
        await rpc.close()
    
    try:
        # Initialize escrow via Gateway (with RPC fallback)
        signature, used_gateway = await escrow_client.initialize_escrow_via_gateway(
            provider_pubkey=provider_pubkey,
            amount=amount_lamports,
            service_id=service_id,
            task_data=task_data,
            client_token_account=client_token_account,
            escrow_token_account=escrow_token_account,
        )
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Check if escrow was reused (no transaction sent)
        if signature == "ESCROW_ALREADY_EXISTS":
            await escrow_client.close()
            return signature, escrow_pda
        
        # Determine routing method based on whether Gateway was used
        routing_method = RoutingMethod.GATEWAY if used_gateway else RoutingMethod.RPC_FALLBACK
        
        # Log successful transaction
        logger.log_escrow_init(
            signature=signature,
            status=TransactionStatus.SUCCESS,
            routing_method=routing_method,
            agent_name=agent_name,
            client_address=str(client_wallet.pubkey()),
            provider_address=provider_address,
            amount_sol=lamports_to_sol(amount_lamports),
            escrow_pda=str(escrow_pda),
            execution_time_ms=execution_time_ms,
        )
        
        await escrow_client.close()
        return signature, escrow_pda
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Log failed transaction
        logger.log_escrow_init(
            signature=None,
            status=TransactionStatus.FAILED,
            routing_method=RoutingMethod.RPC_FALLBACK,
            agent_name=agent_name,
            client_address=str(client_wallet.pubkey()),
            provider_address=provider_address,
            amount_sol=lamports_to_sol(amount_lamports),
            escrow_pda=str(escrow_pda),
            execution_time_ms=execution_time_ms,
            error_message=str(e),
        )
        
        await escrow_client.close()
        raise


async def submit_proof_for_task(
    provider_wallet: Keypair,
    escrow_pda: str,
    proof_data: str,
) -> str:
    """
    Submit proof of task completion.
    
    Args:
        provider_wallet: Provider's Solana wallet keypair
        client_address: Client's Solana address (Pubkey string)
        proof_data: Proof of completion data
    
    Returns:
        Transaction signature
    """
    escrow_client = GatewayEscrowClient(wallet_keypair=provider_wallet)
    escrow_pda_pk = Pubkey.from_string(escrow_pda)
    # Submit proof to explicit escrow PDA
    signature = await escrow_client.submit_proof_with_pda(
        escrow_pda=escrow_pda_pk,
        provider_pubkey=provider_wallet.pubkey(),
        proof_data=proof_data,
    )
    
    await escrow_client.close()
    
    return signature


async def release_payment_for_task(
    authority_wallet: Keypair,
    client_address: str,
    provider_address: str,
) -> str:
    """
    Release payment to provider after verification.
    
    Args:
        authority_wallet: Authority wallet (client or verifier)
        client_address: Client's Solana address
        provider_address: Provider's Solana address
    
    Returns:
        Transaction signature
    """
    escrow_client = GatewayEscrowClient(wallet_keypair=authority_wallet)
    
    client_pubkey = Pubkey.from_string(client_address)
    provider_pubkey = Pubkey.from_string(provider_address)
    
    # Release payment (to be implemented in escrow_client)
    signature = await escrow_client.release_payment(
        client_pubkey=client_pubkey,
        provider_pubkey=provider_pubkey,
    )
    
    await escrow_client.close()
    
    return signature


def sol_to_lamports(sol: float) -> int:
    """Convert SOL to lamports (1 SOL = 1,000,000,000 lamports)."""
    return int(sol * 1_000_000_000)


def lamports_to_sol(lamports: int) -> float:
    """Convert lamports to SOL."""
    return lamports / 1_000_000_000


def tokens_to_smallest_unit(tokens: float, decimals: int = 6) -> int:
    """
    Convert tokens to smallest unit based on decimals.
    
    For SPL tokens with 6 decimals: 1 token = 1,000,000 smallest units
    For SOL (9 decimals): 1 SOL = 1,000,000,000 lamports
    
    Args:
        tokens: Number of tokens (e.g., 8.5)
        decimals: Token decimals (default 6 for SPL tokens)
    
    Returns:
        Amount in smallest unit (e.g., 8,500,000 for 8.5 tokens with 6 decimals)
    """
    return int(tokens * (10 ** decimals))


def smallest_unit_to_tokens(amount: int, decimals: int = 6) -> float:
    """Convert smallest unit to tokens based on decimals."""
    return amount / (10 ** decimals)


async def release_payment_from_escrow(
    client_wallet: Keypair,
    provider_address: str,
    escrow_pda: str,  # Use explicit escrow PDA to avoid derivation drift
    client_token_account: Optional[Pubkey] = None,
    provider_token_account: Optional[Pubkey] = None,
    escrow_token_account: Optional[Pubkey] = None,
    agent_name: str = "Unknown",
) -> str:
    """
    Release payment from escrow to provider.
    
    Args:
        client_wallet: Client's Solana wallet keypair
        provider_address: Provider's Solana address (Pubkey string)
        service_id: Service identifier (must match the one used during initialization)
        client_token_account: Optional client token account
        provider_token_account: Optional provider token account
        escrow_token_account: Optional escrow token account
        agent_name: Name of the agent initiating the transaction
    
    Returns:
        Transaction signature
    """
    logger = get_logger()
    start_time = time.time()
    
    # Initialize escrow client first
    escrow_client = GatewayEscrowClient(wallet_keypair=client_wallet)
    
    # Convert provider address to Pubkey and escrow PDA to Pubkey
    provider_pubkey = Pubkey.from_string(provider_address)
    escrow_pda_pk = Pubkey.from_string(escrow_pda)
    
    # Get provider token account - derive from provider address if not provided
    if provider_token_account is None:
        from spl.token.instructions import get_associated_token_address
        
        mint_str = os.getenv("TEST_MINT")
        if not mint_str:
            raise ValueError("TEST_MINT not set in environment")
        mint = Pubkey.from_string(mint_str)
        
        # Derive provider's ATA for the token mint
        provider_token_account = get_associated_token_address(provider_pubkey, mint)
    
    # Calculate escrow token account dynamically based on escrow PDA
    if escrow_token_account is None:
        from spl.token.instructions import get_associated_token_address
        from solana.rpc.async_api import AsyncClient
        
        mint_str = os.getenv("TEST_MINT")
        if not mint_str:
            raise ValueError("TEST_MINT not set in environment")
        mint = Pubkey.from_string(mint_str)
        escrow_token_account = get_associated_token_address(escrow_pda_pk, mint)
    
    try:
        # Release payment via Gateway (with RPC fallback)
        signature, used_gateway = await escrow_client.release_payment_via_gateway(
            escrow_pda=escrow_pda_pk,
            provider_pubkey=provider_pubkey,
            provider_token_account=provider_token_account,
            escrow_token_account=escrow_token_account,
        )
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Determine routing method
        routing_method = RoutingMethod.GATEWAY if used_gateway else RoutingMethod.RPC_FALLBACK
        
        # Log successful transaction
        logger.log_payment_release(
            signature=signature,
            status=TransactionStatus.SUCCESS,
            routing_method=routing_method,
            agent_name=agent_name,
            client_address=str(client_wallet.pubkey()),
            provider_address=provider_address,
            amount_sol=0.0,  # Amount not tracked in release (already logged in init)
            escrow_pda="",  # PDA not needed for logging
            execution_time_ms=execution_time_ms,
        )
        
        await escrow_client.close()
        return signature
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Log failed transaction
        logger.log_payment_release(
            signature=None,
            status=TransactionStatus.FAILED,
            routing_method=RoutingMethod.RPC_FALLBACK,
            agent_name=agent_name,
            client_address=str(client_wallet.pubkey()),
            provider_address=provider_address,
            amount_sol=0.0,
            escrow_pda="",
            execution_time_ms=execution_time_ms,
            error_message=str(e),
        )
        
        await escrow_client.close()
        raise
