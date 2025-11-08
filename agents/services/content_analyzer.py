"""
Content Analyzer Service

AI-powered content analysis using Gemini API.
Analyzes articles, blog posts, documents for summary, topics, sentiment, etc.
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


class ContentAnalyzer:
    """
    Content analysis service powered by Gemini AI.
    
    Provides real content analysis with verifiable proof of work.
    """
    
    SERVICE_NAME = "Content Analysis"
    SERVICE_DESCRIPTION = "AI-powered analysis of articles, documents, and text content"
    BASE_PRICE = 5  # Tokens (medium complexity)
    CATEGORY = "analysis"
    
    def __init__(self):
        """Initialize content analyzer with Gemini client."""
        self.gemini = get_gemini_client()
        logger.info(f"✅ {self.SERVICE_NAME} service initialized")
    
    async def analyze(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze content using Gemini AI.
        
        Args:
            content: Text content to analyze
            metadata: Optional metadata (title, author, etc.)
            
        Returns:
            Analysis results with proof
        """
        try:
            logger.info(f"📊 Analyzing content ({len(content)} characters)...")
            
            # Call Gemini for analysis
            analysis = await self.gemini.analyze_content(content)
            
            logger.info("✅ Analysis complete")
            logger.info(f"   Summary: {analysis['summary'][:50]}...")
            logger.info(f"   Topics: {', '.join(analysis['topics'])}")
            logger.info(f"   Sentiment: {analysis['sentiment']}")
            
            # Create proof of work
            input_data = {
                "content": content,
                "metadata": metadata or {}
            }
            output_data = analysis
            
            proof = ProofOfWork.create_service_proof(
                service_type="content_analysis",
                input_data=input_data,
                output_data=output_data,
                metadata={
                    "service": self.SERVICE_NAME,
                    "content_length": len(content)
                }
            )
            
            logger.info(f"🔐 Proof generated: {proof['proof'][:16]}...")
            
            # Return complete result
            return {
                "service": self.SERVICE_NAME,
                "input": input_data,  # Full input for verification
                "input_preview": {
                    "content_preview": content[:100] + "..." if len(content) > 100 else content,
                    "content_length": len(content),
                    "metadata": metadata
                },
                "output": analysis,
                "proof": proof
            }
            
        except Exception as e:
            logger.error(f"❌ Content analysis failed: {e}")
            raise
    
    async def get_pricing(self, content: str) -> Dict[str, Any]:
        """
        Get AI-powered pricing for content analysis.
        
        Args:
            content: Content to analyze
            
        Returns:
            Pricing decision
        """
        try:
            # Use AI to decide pricing based on complexity
            pricing = await self.gemini.decide_pricing(
                service_type=self.SERVICE_NAME,
                task_description=f"Analyze {len(content)} characters of content",
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
                "estimated_time_minutes": 1
            }
    
    @staticmethod
    def verify_proof(
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        proof_package: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Verify proof of work for content analysis.
        
        Args:
            input_data: Original input
            output_data: Analysis output
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
                "AI-powered content analysis",
                "Summary generation",
                "Topic extraction",
                "Sentiment analysis",
                "Key points identification",
                "Reading time estimation"
            ],
            "pricing_model": "Dynamic (AI-based on complexity)",
            "typical_price_range": "0.02-0.1 SOL"
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    async def test_content_analyzer():
        """Test content analyzer service."""
        analyzer = ContentAnalyzer()
        
        # Test content
        content = """
        Blockchain technology is revolutionizing the way we think about digital transactions.
        By creating a decentralized ledger that is transparent and immutable, blockchain enables
        trustless interactions between parties who may not know each other. This has profound
        implications for finance, supply chain management, and many other industries.
        
        The key innovation of blockchain is its consensus mechanism, which allows multiple
        parties to agree on the state of the ledger without requiring a central authority.
        This is achieved through cryptographic techniques and game theory, ensuring that
        the system remains secure even in the presence of malicious actors.
        """
        
        # Get pricing
        print("\n" + "="*70)
        print("TESTING CONTENT ANALYZER")
        print("="*70)
        
        pricing = await analyzer.get_pricing(content)
        print(f"\n💰 Price: {pricing['price']} SOL")
        print(f"   Complexity: {pricing['complexity']}")
        print(f"   Estimated time: {pricing['estimated_time_minutes']} minutes")
        print(f"   Reasoning: {pricing['reasoning']}")
        
        # Analyze content
        result = await analyzer.analyze(content)
        
        print(f"\n📊 Analysis Results:")
        print(f"   Summary: {result['output']['summary']}")
        print(f"   Topics: {', '.join(result['output']['topics'])}")
        print(f"   Sentiment: {result['output']['sentiment']}")
        print(f"   Key Points:")
        for i, point in enumerate(result['output']['key_points'], 1):
            print(f"      {i}. {point}")
        
        # Verify proof
        is_valid, message = ContentAnalyzer.verify_proof(
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
    asyncio.run(test_content_analyzer())
