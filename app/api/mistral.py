import logging
from mistralai import Mistral
from fastapi import HTTPException
from app.config.config import MISTRAL_API_KEY

logger = logging.getLogger(__name__)

# Initialize Mistral client
api_key = MISTRAL_API_KEY
model = "mistral-small-latest"
client = Mistral(api_key=api_key)

def call_mistral_api(prompt: str) -> str:
    """
    Call the Mistral API to generate a response to the given prompt
    
    Args:
        prompt: The text prompt to send to the AI
        
    Returns:
        The generated text response
    """
    try:
        # Check if API key is available
        if not MISTRAL_API_KEY:
            logger.warning("Mistral API key is not set in configuration")
            raise ValueError("Mistral API key is missing")
            
        chat_response = client.chat.complete(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )
        return chat_response.choices[0].message.content
    except ValueError as e:
        # Re-raise value errors (like missing API key) to be handled by the caller
        raise e
    except Exception as e:
        logger.error(f"Error calling Mistral API: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))