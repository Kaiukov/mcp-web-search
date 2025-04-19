import os
import logging
from fastapi import HTTPException
from app.config.config import MISTRAL_API_KEY, GEMINI_API_KEY
from app.api.mistral import call_mistral_api
from app.api.gemini import call_gemini_api

logger = logging.getLogger(__name__)

def call_ai_api(prompt: str, provider: str = "gemini") -> str:
    """
    Call an AI API based on the specified provider
    
    Args:
        prompt: The text prompt to send to the AI
        provider: The AI provider to use ('mistral' or 'gemini')
        
    Returns:
        The generated text response
    """
    # Check if the requested provider's API key is available
    if provider.lower() == "gemini" and not GEMINI_API_KEY:
        logger.warning("Gemini API key is missing, falling back to Mistral")
        provider = "mistral"
    elif provider.lower() == "mistral" and not MISTRAL_API_KEY:
        logger.warning("Mistral API key is missing, falling back to Gemini")
        provider = "gemini"
        
    # If both API keys are missing, return an error
    if (provider == "gemini" and not GEMINI_API_KEY) and (provider == "mistral" and not MISTRAL_API_KEY):
        return "Unable to generate response: No valid API keys found for any provider."
        
    if provider.lower() == "mistral":
        return call_mistral_api(prompt)
    elif provider.lower() == "gemini":
        return call_gemini_api(prompt)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}. Supported providers are 'mistral' and 'gemini'")



