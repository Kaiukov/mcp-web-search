import logging
import requests
import json
from fastapi import HTTPException
from app.config.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

def call_gemini_api(prompt: str) -> str:
    """
    Call the Gemini API to generate a response to the given prompt
    
    Args:
        prompt: The text prompt to send to the AI
        
    Returns:
        The generated text response
    """
    try:
        # Check if API key is available
        if not GEMINI_API_KEY:
            logger.warning(f"Gemini API key is not set in configuration or is empty: '{GEMINI_API_KEY}'")
            raise ValueError("Gemini API key is missing")
            
        # Log that we have a key (without showing the full key)
        key_preview = GEMINI_API_KEY[:4] + "..." if GEMINI_API_KEY else "None"
        logger.info(f"Using Gemini API key starting with: {key_preview}")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Log request (without API key)
        logger.debug(f"Sending request to Gemini API with prompt length: {len(prompt)}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        # Log response status
        logger.debug(f"Gemini API response status: {response.status_code}")
        
        response.raise_for_status()  # Raise exception for HTTP errors
        
        result = response.json()
        
        # Extract the text from the response
        if "candidates" in result and len(result["candidates"]) > 0:
            if "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                parts = result["candidates"][0]["content"]["parts"]
                if parts and "text" in parts[0]:
                    return parts[0]["text"]
        
        # If we couldn't extract text through the expected path
        logger.warning(f"Unexpected Gemini API response structure: {result}")
        return "No response generated from Gemini API"
    except ValueError as e:
        # Re-raise value errors (like missing API key) to be handled by the caller
        raise e
    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")