import json
import requests
from fastapi import HTTPException
from bs4 import BeautifulSoup
from .rag import call_mistral_api
import logging
from duckduckgo_search import DDGS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_mcp_request(request: dict) -> dict:
    """
    Processes requests in MCP format using DuckDuckGo search.
    Expected input JSON should contain at least:
    {
        "type": "request",
        "content": "Some request text"
    }
    Returns JSON:
    {
        "type": "response",
        "content": "Answer to your request: ..."
    }
    """
    try:
        # Check services health before processing
        services_status = check_services_health()
        if not services_status["searxng"]:
            return {
                "type": "response",
                "content": "I'm sorry, the search service is currently unavailable. Please try again later.",
                "sources": []
            }
            
        if 'content' not in request:
            raise HTTPException(status_code=400, detail="Missing content in MCP request")

        query = request['content']
        
        # Use RAG pipeline with better error handling
        try:
            logger.info(f"Processing query: {query}")
            links = search_duckduckgo(query)
            logger.info(f"Found {len(links)} links")
            
            contents = [scrape(url) for url in links[:3]] if links else []
            answer = generate_answer(query, contents) if contents else f"I couldn't find relevant information about '{query}'."
            
            response = {
                "type": "response",
                "content": answer,
                "sources": links[:3] if links else []
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

def search_duckduckgo(query):
    """Search using DuckDuckGo with error handling"""
    try:
        logger.info(f"Searching DuckDuckGo for: {query}")
        ddgs = DDGS()
        results = ddgs.text(
            keywords=query,
            region='wt-wt',
            safesearch='moderate',
            max_results=10
        )
        return [r.get("href", "") for r in results]
        
    except Exception as e:
        logger.error(f"DuckDuckGo search error: {e}")
        return []

def search_searxng(query):
    """Search using SearXNG with improved error handling"""
    try:
        logger.info(f"Searching SearXNG for: {query}")
        # Add timeout and error handling
        res = requests.get(
            f"{SEARXNG_BASE_URL}/search", 
            params={"q": query, "format": "json"},
            timeout=10,
            headers={"User-Agent": "RAG-API/1.0"}
        )
        
        logger.info(f"SearXNG response status: {res.status_code}")
        logger.info(f"SearXNG response headers: {dict(res.headers)}")
        
        # Check if response is empty
        if not res.text.strip():
            logger.warning("Empty response from SearXNG")
            return []
        
        # Log first part of response for debugging
        logger.info(f"SearXNG response preview: {res.text[:100]}...")
        
        # Try to parse JSON with better error handling
        try:
            data = res.json()
            return [r["url"] for r in data.get("results", [])]
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Response content: {res.text[:500]}")
            
            # Try to check if we're getting HTML instead of JSON
            if "<html" in res.text.lower():
                logger.error("SearXNG returned HTML instead of JSON")
                
                # Try to extract the error message if it's an HTML error page
                try:
                    soup = BeautifulSoup(res.text, "html.parser")
                    error_msg = soup.title.text if soup.title else "Unknown error"
                    logger.error(f"HTML error page title: {error_msg}")
                except Exception:
                    pass
            
            # Try direct connection to SearXNG to check if it's accessible
            try:
                logger.info("Attempting direct connection to SearXNG...")
                health_check = requests.get(SEARXNG_BASE_URL, timeout=5)
                logger.info(f"SearXNG direct connection status: {health_check.status_code}")
            except Exception as conn_err:
                logger.error(f"SearXNG connection error: {conn_err}")
            
            return []
    except requests.RequestException as e:
        logger.error(f"SearXNG request error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in search_searxng: {e}")
        return []

def scrape(url):
    """Scrape content from URL with error handling"""
    try:
        res = requests.get(
            url, 
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        # Limit the amount of text for faster processing
        return soup.get_text()[:2000]
    except Exception as e:
        print(f"Scraping error for {url}: {e}")
        return f"[Scraping Error] {e}"

def generate_answer(question, texts):
    """Generate answer using Mistral API"""
    context = "\n\n".join(texts)
    prompt = f"Answer the question: {question}\n\nHere is the information found:\n{context}"
    try:
        return call_mistral_api(prompt)
    except Exception as e:
        print(f"Error calling Mistral API: {e}")
        return f"I found some information but couldn't generate a response. Error: {str(e)}"
