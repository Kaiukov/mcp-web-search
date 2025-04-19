import json
import httpx  # Replace requests with httpx
import asyncio
from fastapi import HTTPException
from bs4 import BeautifulSoup
from .rag import call_mistral_api
import logging
from duckduckgo_search import DDGS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_mcp_async(request: dict) -> dict:
    """
    Asynchronous version of handle_mcp_request
    """
    try:
        if 'content' not in request:
            raise HTTPException(status_code=400, detail="Missing content in MCP request")

        query = request['content']
        
        # Get the provider from the request, default to "gemini" if not specified
        provider = request.get('provider', 'gemini').lower()
        
        # Validate the provider
        from app.api import AVAILABLE_PROVIDERS
        if provider not in AVAILABLE_PROVIDERS:
            logger.warning(f"Invalid provider: {provider}. Using default provider.")
            provider = 'gemini'  # Default to gemini if invalid provider
        
        # Use RAG pipeline with better error handling
        try:
            logger.info(f"Processing query: {query} with provider: {provider}")
            links = await search_duckduckgo(query)
            logger.info(f"Found {len(links)} links")
            
            # Process links in parallel using asyncio.gather
            contents = await asyncio.gather(*[scrape_async(url) for url in links[:5]]) if links else []
            # Pass the provider to generate_answer
            answer = await generate_answer(query, contents, provider) if contents else f"I couldn't find relevant information about '{query}'."
            
            response = {
                "type": "response",
                "content": answer,
                "sources": links[:5] if links else [],
                "provider": provider  # Include the provider in the response
            }
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {str(e)}")
            # Fallback response if RAG pipeline fails
            response = {
                "type": "response",
                "content": f"I'm sorry, I encountered an error while processing your request: {str(e)}",
                "sources": []
            }

        return response

    except Exception as e:
        logger.error(f"Error handling MCP request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def search_duckduckgo(query):
    """Asynchronous search using DuckDuckGo with error handling"""
    try:
        logger.info(f"Searching DuckDuckGo for: {query}")
        # Run the synchronous DDGS operation in a thread pool to avoid blocking
        ddgs = DDGS()
        
        # Use run_in_executor to run the synchronous code in a separate thread
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None,
            lambda: ddgs.text(
                keywords=query,
                region='wt-wt',
                safesearch='moderate',
                max_results=10
            )
        )
        
        return [r.get("href", "") for r in results]
        
    except Exception as e:
        logger.error(f"DuckDuckGo search error: {e}")
        return []

async def scrape_async(url):
    """Asynchronous scraper with improved content extraction"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = await client.get(url, headers=headers)
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Try to extract main content by targeting common content containers
            main_content = ""
            
            # Look for article or main content areas first
            for tag in ['article', 'main', '[role="main"]', '.content', '#content', '.post', '.entry']:
                content = soup.select(tag)
                if content:
                    main_content = " ".join([elem.get_text(strip=True) for elem in content])
                    break
            
            # If no main content found, use the whole page but remove navigation, headers, footers
            if not main_content:
                for tag in ['nav', 'header', 'footer', 'aside', '.sidebar', '#sidebar', '.menu', '.ad', '.advertisement']:
                    for elem in soup.select(tag):
                        elem.decompose()
                main_content = soup.get_text(strip=True)
            
            # Limit to 1500 chars per source for more focused content
            return main_content[:1500]
    except Exception as e:
        logger.error(f"Scraping error for {url}: {e}")
        return f"[Scraping Error] {e}"

async def generate_answer(question, texts, provider="gemini"):  # Change default to mistral since Gemini key is missing
    """Generate answer using AI API asynchronously
    
    Args:
        question: The question to answer
        texts: List of text content from scraped sources
        provider: AI provider to use ('mistral' or 'gemini')
    """
    context = "\n\n".join(texts)
    prompt = f"Answer the question: {question}\n\nHere is the information found:\n{context}"
    try:
        from .rag import call_ai_api
        # Check if we have the necessary API keys
        from app.config.config import MISTRAL_API_KEY, GEMINI_API_KEY
        
        # If the requested provider's API key is missing, fall back to the other provider
        if provider == "gemini" and not GEMINI_API_KEY:
            logger.warning("Gemini API key is missing, falling back to Mistral")
            provider = "mistral"
        elif provider == "mistral" and not MISTRAL_API_KEY:
            logger.warning("Mistral API key is missing, falling back to Gemini")
            provider = "gemini"
            
        # If both API keys are missing, return an error
        if (provider == "gemini" and not GEMINI_API_KEY) or (provider == "mistral" and not MISTRAL_API_KEY):
            return "Unable to generate response: No valid API keys found for any provider."
            
        # Run the potentially blocking API call in a thread pool
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: call_ai_api(prompt, provider)
        )
        return result
    except Exception as e:
        logger.error(f"Error calling {provider.capitalize()} API: {e}")
        return f"I found some information but couldn't generate a response. Error: {str(e)}"

# Keep the original handle_mcp_request for backward compatibility
def handle_mcp_request(request: dict) -> dict:
    """
    Synchronous version - kept for backward compatibility
    """
    # This will run the async function in a new event loop
    return asyncio.run(handle_mcp_async(request))
