"""LLM client for structured extraction and summarization."""

import json
from typing import Optional, Any, Dict

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Abstraction for LLM API calls."""
    
    def __init__(self):
        """Initialize LLM client."""
        self._api_key = settings.openai_api_key
        self._base_url = settings.openai_base_url
        self._demo_mode = settings.demo_mode
        
        # Check if we have a real API key
        self._available = (
            not self._demo_mode 
            and self._api_key 
            and self._api_key != "sk-your-api-key-here"
        )
    
    def is_available(self) -> bool:
        """Check if LLM is available."""
        return self._available
    
    async def extract_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Extract structured data from text using LLM.
        
        Args:
            prompt: The prompt to send
            schema: The expected output schema
            
        Returns:
            Extracted data as dict, or None if failed
        """
        if not self._available:
            logger.warning("LLM not available, using fallback")
            return None
        
        try:
            # In a real implementation, this would call OpenAI API
            # For now, return None to trigger fallback
            logger.info("LLM extraction called (not implemented in demo)")
            return None
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return None
    
    async def summarize_text(
        self,
        text: str,
        max_words: int = 50,
    ) -> Optional[str]:
        """
        Summarize text using LLM.
        
        Args:
            text: Text to summarize
            max_words: Maximum words in summary
            
        Returns:
            Summary string, or None if failed
        """
        if not self._available:
            return None
        
        try:
            logger.info("LLM summarization called (not implemented in demo)")
            return None
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            return None


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get the LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
