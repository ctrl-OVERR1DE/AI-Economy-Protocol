"""
Simple monitoring dashboard for agent payment flow.
Displays transaction metrics, recent activity, and failed transactions.
"""
import time
import os
import sys
from datetime import datetime

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from utils.transaction_logger import get_logger


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_timestamp


def display_dashboard():
    """Display the monitoring dashboard."""
    logger = get_logger()
    
    clear_screen()
    
    print("="*80)
    print("  AI ECONOMY PROTOCOL - PAYMENT FLOW MONITORING DASHBOARD")
    print("="*80)
    print()
    
    # Calculate and display metrics
    metrics = logger.calculate_metrics()
    
    print("📊 OVERALL METRICS")
    print("-"*80)
    print(f"  Total Transactions:     {metrics['total_transactions']}")
    print(f"  Success Rate:           {metrics['success_rate']:.1f}%")
    print(f"  Gateway Usage:          {metrics['gateway_usage_rate']:.1f}%")
    print(f"  Avg Execution Time:     {metrics['avg_execution_time_ms']:.0f} ms")
    print(f"  Total Volume:           {metrics['total_volume_sol']:.2f} SOL")
    print()
    
    # Transactions by type
    print("📈 TRANSACTIONS BY TYPE")
    print("-"*80)
    for tx_type, count in metrics['transactions_by_type'].items():
        print(f"  {tx_type:25s} {count:5d}")
    print()
    
    # Recent transactions
    print("🔄 RECENT TRANSACTIONS (Last 10)")
    print("-"*80)
    recent = logger.get_recent_transactions(limit=10)
    
    if recent:
        for tx in recent:
            status_icon = "✓" if tx['status'] == 'success' else "✗"
            routing = "GW" if tx['routing_method'] == 'gateway' else "RPC"
            timestamp = format_timestamp(tx['timestamp'])
            tx_type = tx['transaction_type'].replace('_', ' ').title()
            
            print(f"  {status_icon} [{routing:3s}] {timestamp} | {tx_type:20s}", end="")
            if tx.get('amount_sol'):
                print(f" | {tx['amount_sol']:.2f} SOL", end="")
            if tx.get('signature'):
                print(f" | {tx['signature'][:16]}...")
            else:
                print()
    else:
        print("  No transactions yet.")
    print()
    
    # Failed transactions
    failed = logger.get_failed_transactions(limit=5)
    if failed:
        print("❌ RECENT FAILURES (Last 5)")
        print("-"*80)
        for tx in failed:
            timestamp = format_timestamp(tx['timestamp'])
            tx_type = tx['transaction_type'].replace('_', ' ').title()
            error = tx.get('error_message', 'Unknown error')[:50]
            print(f"  {timestamp} | {tx_type:20s} | {error}")
        print()
    
    # Gateway dashboard link
    print("🔗 EXTERNAL DASHBOARDS")
    print("-"*80)
    print("  Sanctum Gateway: https://gateway.sanctum.so/dashboard")
    print("  Solana Explorer: https://explorer.solana.com/?cluster=devnet")
    print()
    
    print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Press Ctrl+C to exit | Refreshing every 5 seconds...")
    print("="*80)


def main():
    """Run the monitoring dashboard."""
    print("Starting AI Economy Protocol Monitoring Dashboard...")
    print("Loading transaction logs...")
    time.sleep(1)
    
    try:
        while True:
            display_dashboard()
            time.sleep(5)  # Refresh every 5 seconds
    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")


if __name__ == "__main__":
    main()
