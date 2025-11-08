"""
Translator Service

AI-powered translation using Gemini API.
Translates text between multiple languages with quality assessment.
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


class Translator:
    """
    Translation service powered by Gemini AI.
    
    Provides real translation with verifiable proof of work.
    """
    
    SERVICE_NAME = "Translation"
    SERVICE_DESCRIPTION = "AI-powered translation between multiple languages"
    BASE_PRICE = 3  # Tokens (simpler task)
    CATEGORY = "language"
    
    def __init__(self):
        """Initialize translator with Gemini client."""
        self.gemini = get_gemini_client()
        logger.info(f"✅ {self.SERVICE_NAME} service initialized")
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Translate text using Gemini AI.
        
        Args:
            text: Text to translate
            source_lang: Source language (e.g., "English")
            target_lang: Target language (e.g., "Spanish")
            metadata: Optional metadata
            
        Returns:
            Translation results with proof
        """
        try:
            logger.info(f"🌐 Translating {source_lang} → {target_lang} ({len(text)} characters)...")
            
            # Call Gemini for translation
            translation = await self.gemini.translate_text(text, source_lang, target_lang)
            
            logger.info("✅ Translation complete")
            logger.info(f"   Original: {text[:50]}...")
            logger.info(f"   Translated: {translation['translated'][:50]}...")
            logger.info(f"   Confidence: {translation['confidence']}")
            
            # Create proof of work
            input_data = {
                "text": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "metadata": metadata or {}
            }
            output_data = translation
            
            proof = ProofOfWork.create_service_proof(
                service_type="translation",
                input_data=input_data,
                output_data=output_data,
                metadata={
                    "service": self.SERVICE_NAME,
                    "text_length": len(text),
                    "language_pair": f"{source_lang}-{target_lang}"
                }
            )
            
            logger.info(f"🔐 Proof generated: {proof['proof'][:16]}...")
            
            # Return complete result
            return {
                "service": self.SERVICE_NAME,
                "input": input_data,  # Full input for verification
                "input_preview": {
                    "text_preview": text[:100] + "..." if len(text) > 100 else text,
                    "text_length": len(text),
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "metadata": metadata
                },
                "output": translation,
                "proof": proof
            }
            
        except Exception as e:
            logger.error(f"❌ Translation failed: {e}")
            raise
    
    async def get_pricing(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Dict[str, Any]:
        """
        Get AI-powered pricing for translation.
        
        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language
            
        Returns:
            Pricing decision
        """
        try:
            # Use AI to decide pricing based on complexity
            pricing = await self.gemini.decide_pricing(
                service_type=self.SERVICE_NAME,
                task_description=f"Translate {len(text)} characters from {source_lang} to {target_lang}",
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
        Verify proof of work for translation.
        
        Args:
            input_data: Original input
            output_data: Translation output
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
                "AI-powered translation",
                "Multi-language support",
                "Confidence scoring",
                "Context-aware translation",
                "Translation notes",
                "Quality assessment"
            ],
            "supported_languages": [
                "English", "Spanish", "French", "German", "Italian",
                "Portuguese", "Chinese", "Japanese", "Korean", "Arabic",
                "Russian", "Hindi", "Dutch", "Swedish", "Polish"
            ],
            "pricing_model": "Dynamic (AI-based on complexity)",
            "typical_price_range": "0.01-0.05 SOL"
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    async def test_translator():
        """Test translator service."""
        translator = Translator()
        
        # Test text
        text = """
        Blockchain technology is revolutionizing digital transactions.
        It provides a decentralized and transparent way to record data.
        """
        
        # Get pricing
        print("\n" + "="*70)
        print("TESTING TRANSLATOR")
        print("="*70)
        
        pricing = await translator.get_pricing(text, "English", "Spanish")
        print(f"\n💰 Price: {pricing['price']} SOL")
        print(f"   Complexity: {pricing['complexity']}")
        print(f"   Estimated time: {pricing['estimated_time_minutes']} minutes")
        print(f"   Reasoning: {pricing['reasoning']}")
        
        # Translate text
        result = await translator.translate(text, "English", "Spanish")
        
        print(f"\n🌐 Translation Results:")
        print(f"   Source ({result['output']['source_language']}):")
        print(f"      {result['output']['original']}")
        print(f"\n   Target ({result['output']['target_language']}):")
        print(f"      {result['output']['translated']}")
        print(f"\n   Confidence: {result['output']['confidence']}")
        if result['output'].get('notes'):
            print(f"   Notes: {result['output']['notes']}")
        
        # Verify proof
        is_valid, message = Translator.verify_proof(
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
    asyncio.run(test_translator())
