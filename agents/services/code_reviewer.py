"""
Code Reviewer Service

AI-powered code review using Gemini API.
Reviews code for quality, security, best practices, and potential issues.
"""

import sys
import os
import logging
from typing import Dict, Any, Tuple

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from agents.ai.gemini_client import get_gemini_client
from agents.ai.proof_of_work import ProofOfWork

logger = logging.getLogger(__name__)


class CodeReviewer:
    """
    Code review service powered by Gemini AI.
    
    Provides real code analysis with verifiable proof of work.
    """
    
    SERVICE_NAME = "Code Review"
    SERVICE_DESCRIPTION = "AI-powered code review for quality, security, and best practices"
    BASE_PRICE = 8  # Tokens (complex AI analysis)
    CATEGORY = "development"
    
    def __init__(self):
        """Initialize code reviewer with Gemini client."""
        self.gemini = get_gemini_client()
        logger.info(f"✅ {self.SERVICE_NAME} service initialized")
    
    async def review(
        self, 
        code: str, 
        language: str = "python",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Review code using Gemini AI.
        
        Args:
            code: Code to review
            language: Programming language
            metadata: Optional metadata (filename, author, etc.)
            
        Returns:
            Review results with proof
        """
        try:
            logger.info(f"🔍 Reviewing {language} code ({len(code)} characters)...")
            
            # Call Gemini for code review
            review = await self.gemini.review_code(code, language)
            
            logger.info("✅ Code review complete")
            logger.info(f"   Quality Score: {review['quality_score']}/10")
            logger.info(f"   Issues Found: {len(review['issues'])}")
            logger.info(f"   Security Concerns: {len(review['security_concerns'])}")
            
            # Create proof of work
            input_data = {
                "code": code,
                "language": language,
                "metadata": metadata or {}
            }
            output_data = review
            
            proof = ProofOfWork.create_service_proof(
                service_type="code_review",
                input_data=input_data,
                output_data=output_data,
                metadata={
                    "service": self.SERVICE_NAME,
                    "code_length": len(code),
                    "language": language
                }
            )
            
            logger.info(f"🔐 Proof generated: {proof['proof'][:16]}...")
            
            # Return complete result
            return {
                "service": self.SERVICE_NAME,
                "input": input_data,  # Full input for verification
                "input_preview": {
                    "code_preview": code[:100] + "..." if len(code) > 100 else code,
                    "code_length": len(code),
                    "language": language,
                    "metadata": metadata
                },
                "output": review,
                "proof": proof
            }
            
        except Exception as e:
            logger.error(f"❌ Code review failed: {e}")
            raise
    
    async def get_pricing(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Get AI-powered pricing for code review.
        
        Args:
            code: Code to review
            language: Programming language
            
        Returns:
            Pricing decision
        """
        try:
            # Use AI to decide pricing based on complexity
            pricing = await self.gemini.decide_pricing(
                service_type=self.SERVICE_NAME,
                task_description=f"Review {len(code)} characters of {language} code",
                base_price=self.BASE_PRICE
            )
            
            logger.info(f"💰 AI Pricing: {pricing['price']} SOL")
            logger.info(f"   Reasoning: {pricing['reasoning']}")
            
            return pricing
            
        except Exception as e:
            logger.error(f"❌ Pricing decision failed: {e}")
            # Fallback to base price
            return {
                "price": self.BASE_PRICE,
                "reasoning": "Using base price due to pricing error",
                "complexity": "unknown",
                "estimated_time_minutes": 2
            }
    
    @staticmethod
    def verify_proof(
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        proof_package: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Verify proof of work for code review.
        
        Args:
            input_data: Original input
            output_data: Review output
            proof_package: Proof to verify
            
        Returns:
            Tuple of (is_valid, message)
        """
        return ProofOfWork.verify_service_proof(
            input_data,
            output_data,
            proof_package
        )
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information for marketplace listing."""
        return {
            "name": self.SERVICE_NAME,
            "description": self.SERVICE_DESCRIPTION,
            "base_price": self.BASE_PRICE,
            "category": self.CATEGORY,
            "features": [
                "AI-powered code analysis",
                "Quality scoring (1-10)",
                "Security vulnerability detection",
                "Best practices suggestions",
                "Issue identification with severity",
                "Overall assessment"
            ],
            "supported_languages": [
                "Python", "JavaScript", "TypeScript", "Java", 
                "C++", "Go", "Rust", "Solidity"
            ],
            "pricing_model": "Dynamic (AI-based on complexity)",
            "typical_price_range": "0.05-0.3 SOL"
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    async def test_code_reviewer():
        """Test code reviewer service."""
        reviewer = CodeReviewer()
        
        # Test code
        code = """
def transfer_funds(from_account, to_account, amount):
    # Transfer funds between accounts
    from_account.balance -= amount
    to_account.balance += amount
    return True

def process_payment(user_input):
    # Process payment from user
    query = f"SELECT * FROM users WHERE id = {user_input}"
    execute_query(query)
"""
        
        # Get pricing
        print("\n" + "="*70)
        print("TESTING CODE REVIEWER")
        print("="*70)
        
        pricing = await reviewer.get_pricing(code, "python")
        print(f"\n💰 Price: {pricing['price']} SOL")
        print(f"   Complexity: {pricing['complexity']}")
        print(f"   Estimated time: {pricing['estimated_time_minutes']} minutes")
        print(f"   Reasoning: {pricing['reasoning']}")
        
        # Review code
        result = await reviewer.review(code, "python")
        
        print(f"\n🔍 Code Review Results:")
        print(f"   Quality Score: {result['output']['quality_score']}/10")
        print(f"   Overall: {result['output']['overall_assessment']}")
        
        print(f"\n⚠️  Issues Found ({len(result['output']['issues'])}):")
        for issue in result['output']['issues']:
            print(f"      [{issue['severity'].upper()}] {issue['description']}")
            if 'line' in issue:
                print(f"                Line {issue['line']}")
        
        print(f"\n🔒 Security Concerns ({len(result['output']['security_concerns'])}):")
        for concern in result['output']['security_concerns']:
            print(f"      - {concern}")
        
        print(f"\n💡 Suggestions ({len(result['output']['suggestions'])}):")
        for suggestion in result['output']['suggestions']:
            print(f"      - {suggestion}")
        
        print(f"\n✅ Best Practices ({len(result['output']['best_practices'])}):")
        for practice in result['output']['best_practices']:
            print(f"      - {practice}")
        
        # Verify proof
        is_valid, message = CodeReviewer.verify_proof(
            result['input'],
            result['output'],
            result['proof']
        )
        print(f"\n🔐 Proof Verification: {is_valid}")
        print(f"   {message}")
        
        print("\n" + "="*70)
        print("TEST COMPLETE")
        print("="*70)
    
    # Run test
    asyncio.run(test_code_reviewer())
