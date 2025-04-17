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
        if 'content' not in request:
            raise HTTPException(status_code=400, detail="Missing content in MCP request")

        query = request['content']
        
        # Use RAG pipeline with better error handling
        try:
            logger.info(f"Processing query: {query}")
            links = search_duckduckgo(query)
            logger.info(f"Found {len(links)} links")
            
            # Increase to top 5 sources instead of 3
            contents = [scrape(url) for url in links[:5]] if links else []
            answer = generate_answer(query, contents) if contents else f"I couldn't find relevant information about '{query}'."
            
            response = {
                "type": "response",
                "content": answer,
                "sources": links[:5] if links else []  # Also update sources to show 5
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

# search_searxng function removed

def scrape(url):
    """Scrape content from URL with improved content extraction"""
    try:
        res = requests.get(
            url, 
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
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

def generate_answer(question, texts):
    """Generate answer using Mistral API"""
    context = "\n\n".join(texts)
    prompt = f"Answer the question: {question}\n\nHere is the information found:\n{context}"
    try:
        return call_mistral_api(prompt)
    except Exception as e:
        print(f"Error calling Mistral API: {e}")
        return f"I found some information but couldn't generate a response. Error: {str(e)}"
