"""
Transaction logging and metrics collection for agent payment flow.
Tracks all escrow operations, success rates, and routing decisions.
"""
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path


class TransactionType(Enum):
    """Types of escrow transactions."""
    INITIALIZE_ESCROW = "initialize_escrow"
    SUBMIT_PROOF = "submit_proof"
    RELEASE_PAYMENT = "release_payment"
    CANCEL_ESCROW = "cancel_escrow"


class TransactionStatus(Enum):
    """Transaction execution status."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class RoutingMethod(Enum):
    """Transaction routing method."""
    GATEWAY = "gateway"
    RPC_FALLBACK = "rpc_fallback"
    RPC_DIRECT = "rpc_direct"


@dataclass
class TransactionLog:
    """Log entry for a single transaction."""
    transaction_id: str
    transaction_type: TransactionType
    status: TransactionStatus
    routing_method: RoutingMethod
    signature: Optional[str]
    timestamp: str
    agent_name: Optional[str]
    client_address: Optional[str]
    provider_address: Optional[str]
    amount_sol: Optional[float]
    escrow_pda: Optional[str]
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert enums to strings
        data['transaction_type'] = self.transaction_type.value
        data['status'] = self.status.value
        data['routing_method'] = self.routing_method.value
        return data


class TransactionLogger:
    """Centralized transaction logging system."""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize logger with log directory."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"transactions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        self.metrics_file = self.log_dir / "metrics.json"
        
    def log_transaction(self, log_entry: TransactionLog) -> None:
        """Log a transaction to the JSONL file."""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry.to_dict()) + '\n')
    
    def log_escrow_init(
        self,
        signature: str,
        status: TransactionStatus,
        routing_method: RoutingMethod,
        agent_name: str,
        client_address: str,
        provider_address: str,
        amount_sol: float,
        escrow_pda: str,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Log an escrow initialization transaction."""
        log_entry = TransactionLog(
            transaction_id=signature or f"failed_{datetime.now().timestamp()}",
            transaction_type=TransactionType.INITIALIZE_ESCROW,
            status=status,
            routing_method=routing_method,
            signature=signature,
            timestamp=datetime.now().isoformat(),
            agent_name=agent_name,
            client_address=client_address,
            provider_address=provider_address,
            amount_sol=amount_sol,
            escrow_pda=escrow_pda,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )
        self.log_transaction(log_entry)
    
    def log_proof_submission(
        self,
        signature: str,
        status: TransactionStatus,
        routing_method: RoutingMethod,
        agent_name: str,
        provider_address: str,
        escrow_pda: str,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Log a proof submission transaction."""
        log_entry = TransactionLog(
            transaction_id=signature or f"failed_{datetime.now().timestamp()}",
            transaction_type=TransactionType.SUBMIT_PROOF,
            status=status,
            routing_method=routing_method,
            signature=signature,
            timestamp=datetime.now().isoformat(),
            agent_name=agent_name,
            client_address=None,
            provider_address=provider_address,
            amount_sol=None,
            escrow_pda=escrow_pda,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )
        self.log_transaction(log_entry)
    
    def log_payment_release(
        self,
        signature: str,
        status: TransactionStatus,
        routing_method: RoutingMethod,
        agent_name: str,
        client_address: str,
        provider_address: str,
        amount_sol: float,
        escrow_pda: str,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Log a payment release transaction."""
        log_entry = TransactionLog(
            transaction_id=signature or f"failed_{datetime.now().timestamp()}",
            transaction_type=TransactionType.RELEASE_PAYMENT,
            status=status,
            routing_method=routing_method,
            signature=signature,
            timestamp=datetime.now().isoformat(),
            agent_name=agent_name,
            client_address=client_address,
            provider_address=provider_address,
            amount_sol=amount_sol,
            escrow_pda=escrow_pda,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )
        self.log_transaction(log_entry)
    
    def get_recent_transactions(self, limit: int = 100) -> list[Dict[str, Any]]:
        """Get recent transactions from log file."""
        if not self.log_file.exists():
            return []
        
        transactions = []
        with open(self.log_file, 'r') as f:
            for line in f:
                transactions.append(json.loads(line))
        
        # Return most recent first
        return transactions[-limit:][::-1]
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate metrics from transaction logs."""
        transactions = self.get_recent_transactions(limit=1000)
        
        if not transactions:
            return {
                "total_transactions": 0,
                "success_rate": 0.0,
                "gateway_usage_rate": 0.0,
                "avg_execution_time_ms": 0.0,
                "transactions_by_type": {},
                "total_volume_sol": 0.0,
            }
        
        total = len(transactions)
        successful = sum(1 for t in transactions if t['status'] == 'success')
        gateway_used = sum(1 for t in transactions if t['routing_method'] == 'gateway')
        
        # Execution times
        exec_times = [t['execution_time_ms'] for t in transactions if t.get('execution_time_ms')]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
        
        # Transactions by type
        by_type = {}
        for t in transactions:
            tx_type = t['transaction_type']
            by_type[tx_type] = by_type.get(tx_type, 0) + 1
        
        # Total volume
        total_volume = sum(t.get('amount_sol', 0) or 0 for t in transactions)
        
        metrics = {
            "total_transactions": total,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "gateway_usage_rate": (gateway_used / total * 100) if total > 0 else 0,
            "avg_execution_time_ms": avg_exec_time,
            "transactions_by_type": by_type,
            "total_volume_sol": total_volume,
            "last_updated": datetime.now().isoformat(),
        }
        
        # Save metrics to file
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        return metrics
    
    def get_failed_transactions(self, limit: int = 50) -> list[Dict[str, Any]]:
        """Get recent failed transactions for debugging."""
        transactions = self.get_recent_transactions(limit=1000)
        failed = [t for t in transactions if t['status'] == 'failed']
        return failed[-limit:][::-1]


# Global logger instance
_logger: Optional[TransactionLogger] = None


def get_logger() -> TransactionLogger:
    """Get or create global transaction logger."""
    global _logger
    if _logger is None:
        log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
        _logger = TransactionLogger(log_dir=log_dir)
    return _logger
