import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API keys with proper error handling
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Debug logging for API keys
if not MISTRAL_API_KEY:
    logger.warning("MISTRAL_API_KEY not found in environment variables")
    print("Warning: MISTRAL_API_KEY not found in environment variables")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not found in environment variables")
    print("Warning: GEMINI_API_KEY not found in environment variables")
else:
    # Log that we have a key (without showing the full key)
    key_preview = GEMINI_API_KEY[:4] + "..." if GEMINI_API_KEY else "None"
    logger.info(f"Loaded Gemini API key starting with: {key_preview}")
