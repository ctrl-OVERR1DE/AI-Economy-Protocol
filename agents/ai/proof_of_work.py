"""
Proof of Work Module

Generates and verifies cryptographic proofs for completed work.
Uses SHA256 hashing to create verifiable proofs of input/output.
"""

import hashlib
import json
from typing import Dict, Any, Tuple


class ProofOfWork:
    """
    Generates and verifies cryptographic proofs of work.
    
    Proof is SHA256(input_hash + output_hash) to prove:
    1. Provider received specific input
    2. Provider generated specific output
    3. Work was actually performed
    """
    
    @staticmethod
    def hash_data(data: str) -> str:
        """
        Hash data using SHA256.
        
        Args:
            data: Data to hash
            
        Returns:
            Hex digest of SHA256 hash
        """
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def create_proof(input_data: str, output_data: str) -> Dict[str, str]:
        """
        Create proof of work from input and output.
        
        Args:
            input_data: Original input data
            output_data: Generated output data
            
        Returns:
            Dictionary with input_hash, output_hash, and proof
        """
        # Hash input and output separately
        input_hash = ProofOfWork.hash_data(input_data)
        output_hash = ProofOfWork.hash_data(output_data)
        
        # Create combined proof
        combined = input_hash + output_hash
        proof = ProofOfWork.hash_data(combined)
        
        return {
            "input_hash": input_hash,
            "output_hash": output_hash,
            "proof": proof
        }
    
    @staticmethod
    def verify_proof(
        input_data: str, 
        output_data: str, 
        proof: str
    ) -> Tuple[bool, str]:
        """
        Verify proof matches input and output.
        
        Args:
            input_data: Original input data
            output_data: Generated output data
            proof: Proof to verify
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Recompute proof
            computed = ProofOfWork.create_proof(input_data, output_data)
            
            # Compare
            if computed["proof"] == proof:
                return True, "Proof verified successfully"
            else:
                return False, f"Proof mismatch: expected {computed['proof']}, got {proof}"
        except Exception as e:
            return False, f"Verification error: {str(e)}"
    
    @staticmethod
    def create_service_proof(
        service_type: str,
        input_data: Any,
        output_data: Any,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create comprehensive proof for a service execution.
        
        Args:
            service_type: Type of service (e.g., "content_analysis")
            input_data: Service input (will be JSON serialized)
            output_data: Service output (will be JSON serialized)
            metadata: Additional metadata (optional)
            
        Returns:
            Complete proof package
        """
        # Serialize data
        input_str = json.dumps(input_data, sort_keys=True)
        output_str = json.dumps(output_data, sort_keys=True)
        
        # Create proof
        proof_data = ProofOfWork.create_proof(input_str, output_str)
        
        # Build complete proof package
        proof_package = {
            "service_type": service_type,
            "input_hash": proof_data["input_hash"],
            "output_hash": proof_data["output_hash"],
            "proof": proof_data["proof"],
            "metadata": metadata or {}
        }
        
        return proof_package
    
    @staticmethod
    def verify_service_proof(
        input_data: Any,
        output_data: Any,
        proof_package: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Verify service proof package.
        
        Args:
            input_data: Original service input
            output_data: Service output
            proof_package: Proof package to verify
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Serialize data
            input_str = json.dumps(input_data, sort_keys=True)
            output_str = json.dumps(output_data, sort_keys=True)
            
            # Verify proof
            return ProofOfWork.verify_proof(
                input_str,
                output_str,
                proof_package["proof"]
            )
        except Exception as e:
            return False, f"Verification error: {str(e)}"


# Example usage
if __name__ == "__main__":
    # Test proof creation and verification
    input_data = "Analyze this article about blockchain"
    output_data = json.dumps({
        "summary": "Article discusses blockchain technology",
        "topics": ["blockchain", "technology"],
        "sentiment": "neutral"
    })
    
    # Create proof
    proof = ProofOfWork.create_proof(input_data, output_data)
    print("Proof created:")
    print(f"  Input hash: {proof['input_hash'][:16]}...")
    print(f"  Output hash: {proof['output_hash'][:16]}...")
    print(f"  Proof: {proof['proof'][:16]}...")
    
    # Verify proof
    is_valid, message = ProofOfWork.verify_proof(
        input_data,
        output_data,
        proof["proof"]
    )
    print(f"\nVerification: {is_valid}")
    print(f"Message: {message}")
    
    # Test with wrong output
    wrong_output = json.dumps({"summary": "Different output"})
    is_valid, message = ProofOfWork.verify_proof(
        input_data,
        wrong_output,
        proof["proof"]
    )
    print(f"\nWrong output verification: {is_valid}")
    print(f"Message: {message}")
