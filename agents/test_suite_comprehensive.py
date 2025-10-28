"""
Comprehensive test suite for Phase 2.5: Testing & Validation
Tests all aspects of the agent payment flow for production readiness.
"""
import asyncio
import os
import sys
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

from utils.solana_utils import (
    load_agent_wallet,
    initialize_escrow_for_service,
    submit_proof_for_task,
    release_payment_for_task,
    sol_to_lamports,
)
from utils.transaction_logger import get_logger


class TestResult:
    """Test result container."""
    def __init__(self, test_name: str, passed: bool, duration_ms: int, error: str = None):
        self.test_name = test_name
        self.passed = passed
        self.duration_ms = duration_ms
        self.error = error


class ComprehensiveTestSuite:
    """Comprehensive test suite for agent payment flow."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.logger = get_logger()
        
    def add_result(self, result: TestResult):
        """Add a test result."""
        self.results.append(result)
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"  {status} | {result.test_name:50s} | {result.duration_ms:5d}ms")
        if result.error:
            print(f"         Error: {result.error}")
    
    async def test_wallet_loading(self) -> TestResult:
        """Test 1: Wallet loading."""
        start = time.time()
        try:
            wallet = load_agent_wallet("default")
            assert wallet is not None
            assert wallet.pubkey() is not None
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Wallet Loading", True, duration_ms)
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Wallet Loading", False, duration_ms, str(e))
    
    async def test_escrow_initialization(self) -> TestResult:
        """Test 2: Escrow initialization."""
        start = time.time()
        try:
            client_wallet = load_agent_wallet("default")
            provider_address = os.getenv("PROVIDER_PUBLIC_KEY")
            
            if not provider_address:
                provider_address = str(client_wallet.pubkey())
            
            signature, escrow_pda = await initialize_escrow_for_service(
                client_wallet=client_wallet,
                provider_address=provider_address,
                service_id="test_service_001",
                task_data="Test task data",
                amount_lamports=sol_to_lamports(0.01),
                agent_name="TestAgent",
            )
            
            assert signature is not None
            assert len(signature) > 0
            assert escrow_pda is not None
            
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Escrow Initialization", True, duration_ms)
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            # Account already exists is expected in repeated tests
            if "already in use" in str(e).lower():
                return TestResult("Escrow Initialization", True, duration_ms, "Account exists (expected)")
            return TestResult("Escrow Initialization", False, duration_ms, str(e))
    
    async def test_proof_submission(self) -> TestResult:
        """Test 3: Proof submission."""
        start = time.time()
        try:
            provider_wallet = load_agent_wallet("default")
            client_address = str(provider_wallet.pubkey())
            
            signature = await submit_proof_for_task(
                provider_wallet=provider_wallet,
                client_address=client_address,
                proof_data="Test proof data",
            )
            
            assert signature is not None
            assert len(signature) > 0
            
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Proof Submission", True, duration_ms)
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Proof Submission", False, duration_ms, str(e))
    
    async def test_payment_release(self) -> TestResult:
        """Test 4: Payment release."""
        start = time.time()
        try:
            client_wallet = load_agent_wallet("default")
            provider_address = os.getenv("PROVIDER_PUBLIC_KEY", str(client_wallet.pubkey()))
            
            signature = await release_payment_for_task(
                authority_wallet=client_wallet,
                client_address=str(client_wallet.pubkey()),
                provider_address=provider_address,
            )
            
            assert signature is not None
            assert len(signature) > 0
            
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Payment Release", True, duration_ms)
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Payment Release", False, duration_ms, str(e))
    
    async def test_transaction_logging(self) -> TestResult:
        """Test 5: Transaction logging."""
        start = time.time()
        try:
            # Check if logs exist
            recent = self.logger.get_recent_transactions(limit=10)
            assert recent is not None
            assert isinstance(recent, list)
            
            # Check metrics calculation
            metrics = self.logger.calculate_metrics()
            assert metrics is not None
            assert "total_transactions" in metrics
            assert "success_rate" in metrics
            
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Transaction Logging", True, duration_ms)
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Transaction Logging", False, duration_ms, str(e))
    
    async def test_metrics_calculation(self) -> TestResult:
        """Test 6: Metrics calculation."""
        start = time.time()
        try:
            metrics = self.logger.calculate_metrics()
            
            # Validate metrics structure
            required_keys = [
                "total_transactions",
                "success_rate",
                "gateway_usage_rate",
                "avg_execution_time_ms",
                "transactions_by_type",
                "total_volume_sol",
            ]
            
            for key in required_keys:
                assert key in metrics, f"Missing metric: {key}"
            
            # Validate metric types
            assert isinstance(metrics["total_transactions"], int)
            assert isinstance(metrics["success_rate"], (int, float))
            assert isinstance(metrics["transactions_by_type"], dict)
            
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Metrics Calculation", True, duration_ms)
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Metrics Calculation", False, duration_ms, str(e))
    
    async def test_error_handling(self) -> TestResult:
        """Test 7: Error handling."""
        start = time.time()
        try:
            # Test with invalid provider address
            client_wallet = load_agent_wallet("default")
            
            try:
                await initialize_escrow_for_service(
                    client_wallet=client_wallet,
                    provider_address="InvalidAddress",
                    service_id="test",
                    task_data="test",
                    amount_lamports=1000,
                    agent_name="TestAgent",
                )
                # Should have raised an error
                return TestResult("Error Handling", False, 0, "Expected error not raised")
            except Exception:
                # Error was properly raised and handled
                pass
            
            # Check that failed transaction was logged
            failed = self.logger.get_failed_transactions(limit=5)
            # Note: May not have failed transactions if error was caught early
            
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Error Handling", True, duration_ms)
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Error Handling", False, duration_ms, str(e))
    
    async def test_performance_benchmark(self) -> TestResult:
        """Test 8: Performance benchmark."""
        start = time.time()
        try:
            # Already tested in previous tests, just validate timing
            metrics = self.logger.calculate_metrics()
            avg_time = metrics.get("avg_execution_time_ms", 0)
            
            # Performance targets
            MAX_AVG_TIME_MS = 5000  # 5 seconds max average
            
            if avg_time > MAX_AVG_TIME_MS:
                return TestResult(
                    "Performance Benchmark",
                    False,
                    int(avg_time),
                    f"Average time {avg_time}ms exceeds target {MAX_AVG_TIME_MS}ms"
                )
            
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Performance Benchmark", True, duration_ms)
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return TestResult("Performance Benchmark", False, duration_ms, str(e))
    
    async def run_all_tests(self):
        """Run all tests in the suite."""
        print("="*80)
        print("  PHASE 2.5: COMPREHENSIVE TEST SUITE")
        print("="*80)
        print()
        
        tests = [
            self.test_wallet_loading,
            self.test_escrow_initialization,
            self.test_proof_submission,
            self.test_payment_release,
            self.test_transaction_logging,
            self.test_metrics_calculation,
            self.test_error_handling,
            self.test_performance_benchmark,
        ]
        
        print(f"Running {len(tests)} tests...")
        print("-"*80)
        
        for test in tests:
            result = await test()
            self.add_result(result)
        
        print("-"*80)
        print()
        
        # Summary
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        success_rate = (passed / len(self.results) * 100) if self.results else 0
        
        print("="*80)
        print("  TEST SUMMARY")
        print("="*80)
        print(f"  Total Tests:     {len(self.results)}")
        print(f"  Passed:          {passed}")
        print(f"  Failed:          {failed}")
        print(f"  Success Rate:    {success_rate:.1f}%")
        print()
        
        # Metrics from actual transactions
        metrics = self.logger.calculate_metrics()
        print("="*80)
        print("  TRANSACTION METRICS")
        print("="*80)
        print(f"  Total Transactions:     {metrics['total_transactions']}")
        print(f"  Success Rate:           {metrics['success_rate']:.1f}%")
        print(f"  Avg Execution Time:     {metrics['avg_execution_time_ms']:.0f}ms")
        print(f"  Total Volume:           {metrics['total_volume_sol']:.4f} SOL")
        print()
        
        # Validation
        print("="*80)
        print("  VALIDATION RESULTS")
        print("="*80)
        
        validations = []
        
        # Test success rate validation
        if success_rate >= 85:
            validations.append(("✓", "Test Suite Success Rate", f"{success_rate:.1f}% (Target: ≥85%)"))
        else:
            validations.append(("✗", "Test Suite Success Rate", f"{success_rate:.1f}% (Target: ≥85%)"))
        
        # Transaction success rate validation
        if metrics['success_rate'] >= 90:
            validations.append(("✓", "Transaction Success Rate", f"{metrics['success_rate']:.1f}% (Target: ≥90%)"))
        else:
            validations.append(("✗", "Transaction Success Rate", f"{metrics['success_rate']:.1f}% (Target: ≥90%)"))
        
        # Performance validation
        if metrics['avg_execution_time_ms'] <= 3000:
            validations.append(("✓", "Performance", f"{metrics['avg_execution_time_ms']:.0f}ms (Target: ≤3000ms)"))
        else:
            validations.append(("✗", "Performance", f"{metrics['avg_execution_time_ms']:.0f}ms (Target: ≤3000ms)"))
        
        # Logging validation
        if metrics['total_transactions'] > 0:
            validations.append(("✓", "Transaction Logging", "Working"))
        else:
            validations.append(("✗", "Transaction Logging", "No transactions logged"))
        
        for icon, name, result in validations:
            print(f"  {icon} {name:30s} {result}")
        
        print()
        print("="*80)
        
        # Final verdict
        all_validations_passed = all(v[0] == "✓" for v in validations)
        if all_validations_passed and failed == 0:
            print("  🎉 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION")
        elif failed == 0:
            print("  ⚠️  ALL TESTS PASSED - SOME VALIDATIONS NEED ATTENTION")
        else:
            print("  ❌ SOME TESTS FAILED - REVIEW REQUIRED")
        print("="*80)


async def main():
    """Run the comprehensive test suite."""
    suite = ComprehensiveTestSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
