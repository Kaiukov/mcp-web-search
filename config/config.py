import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


MISTRAL_API_KEY=os.getenv('MISTRAL_API_KEY')
GEMINI_API_KEY=os.getenv('GEMINI_API_KEY')