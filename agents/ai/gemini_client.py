"""
Gemini AI Client

Wrapper for Google Gemini API to provide AI-powered services.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Client for interacting with Google Gemini API.
    
    Provides methods for content analysis, code review, translation, and decision making.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Use Gemini 2.0 Flash for fast responses
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        logger.info("✅ Gemini client initialized")
    
    async def generate_content(self, prompt: str) -> str:
        """
        Generate content using Gemini.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated text response
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        Generate JSON response using Gemini.
        
        Args:
            prompt: Input prompt (should request JSON output)
            
        Returns:
            Parsed JSON response
        """
        try:
            response = await self.generate_content(prompt)
            
            # Extract JSON from response (handle markdown code blocks)
            text = response.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini: {e}")
            logger.error(f"Response: {response}")
            raise
    
    async def analyze_content(self, content: str) -> Dict[str, Any]:
        """
        Analyze content using Gemini.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Analysis results with summary, topics, sentiment, key points
        """
        prompt = f"""Analyze the following content and return a JSON response:

Content:
{content}

Return JSON with this structure:
{{
    "summary": "Brief summary of the content",
    "topics": ["topic1", "topic2", "topic3"],
    "sentiment": "positive/neutral/negative",
    "key_points": ["point1", "point2", "point3"],
    "word_count": number,
    "reading_time_minutes": number
}}

Only return valid JSON, no additional text."""
        
        return await self.generate_json(prompt)
    
    async def review_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Review code using Gemini.
        
        Args:
            code: Code to review
            language: Programming language
            
        Returns:
            Code review with quality, issues, suggestions, security
        """
        prompt = f"""Review the following {language} code and return a JSON response:

Code:
```{language}
{code}
```

Return JSON with this structure:
{{
    "quality_score": 1-10,
    "issues": [
        {{"severity": "high/medium/low", "description": "issue description", "line": number}}
    ],
    "suggestions": ["suggestion1", "suggestion2"],
    "security_concerns": ["concern1", "concern2"],
    "best_practices": ["practice1", "practice2"],
    "overall_assessment": "Brief overall assessment"
}}

Only return valid JSON, no additional text."""
        
        return await self.generate_json(prompt)
    
    async def translate_text(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> Dict[str, Any]:
        """
        Translate text using Gemini.
        
        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language
            
        Returns:
            Translation with original, translated, confidence
        """
        prompt = f"""Translate the following text from {source_lang} to {target_lang}:

Text:
{text}

Return JSON with this structure:
{{
    "original": "original text",
    "translated": "translated text",
    "source_language": "{source_lang}",
    "target_language": "{target_lang}",
    "confidence": 0.0-1.0,
    "notes": "Any translation notes or context"
}}

Only return valid JSON, no additional text."""
        
        return await self.generate_json(prompt)
    
    async def decide_pricing(
        self, 
        service_type: str, 
        task_description: str,
        base_price: float = 0.1
    ) -> Dict[str, Any]:
        """
        AI-powered pricing decision.
        
        Args:
            service_type: Type of service
            task_description: Description of the task
            base_price: Base price in SOL
            
        Returns:
            Pricing decision with price, reasoning
        """
        prompt = f"""You are an AI agent pricing your services. Decide the price for this task:

Service Type: {service_type}
Task Description: {task_description}
Base Price: {base_price} SOL
Market Rate: 0.05-0.5 SOL depending on complexity

Consider:
- Task complexity
- Time required
- Value provided
- Market rates

Return JSON with this structure:
{{
    "price": number (in SOL),
    "reasoning": "Why this price is fair",
    "complexity": "low/medium/high",
    "estimated_time_minutes": number
}}

Only return valid JSON, no additional text."""
        
        return await self.generate_json(prompt)
    
    async def select_provider(
        self, 
        providers: list, 
        service_needed: str,
        budget: float
    ) -> Dict[str, Any]:
        """
        AI-powered provider selection.
        
        Args:
            providers: List of available providers
            service_needed: Service type needed
            budget: Maximum budget in SOL
            
        Returns:
            Selection decision with chosen provider, reasoning
        """
        prompt = f"""You are an AI agent selecting a service provider. Choose the best option:

Service Needed: {service_needed}
Budget: {budget} SOL
Available Providers:
{json.dumps(providers, indent=2)}

Consider:
- Price vs budget
- Provider rating
- Number of reviews
- Service quality

Return JSON with this structure:
{{
    "selected_provider": "provider_address",
    "reasoning": "Why this provider is best",
    "confidence": 0.0-1.0,
    "backup_provider": "alternative_address or null"
}}

Only return valid JSON, no additional text."""
        
        return await self.generate_json(prompt)


# Singleton instance
_gemini_client = None

def get_gemini_client() -> GeminiClient:
    """Get or create Gemini client singleton."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
