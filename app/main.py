from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import os
import httpx  # Replace requests with httpx for async support
import asyncio
from bs4 import BeautifulSoup
from .rag import call_mistral_api
from .mcp import handle_mcp_async

app = FastAPI()

@app.get("/ask")
async def ask(q: str = Query(...)):  # Make this async
    """
    Main endpoint for user queries.
    Depending on the query:
    - Retrieves relevant links using DuckDuckGo
    - Scrapes textual content in parallel
    - Generates an answer using RAG (Mistral API)
    """
    links = search_duckduckgo(q)
    # Use asyncio.gather to process links concurrently
    contents = await asyncio.gather(*[scrape_async(url) for url in links[:3]])
    answer = generate_answer(q, contents)
    return {"answer": answer, "sources": links[:3]}

@app.post("/mcp")
async def mcp_request(request: dict):  # Make this async too
    """
    Endpoint for processing MCP-formatted requests.
    Accepts a JSON request and returns an MCP-formatted response.
    """
    response = await handle_mcp_async(request)
    return JSONResponse(content=response)

def search_duckduckgo(query):
    try:
        from duckduckgo_search import DDGS
        ddgs = DDGS()
        results = ddgs.text(
            keywords=query,
            region='wt-wt',
            safesearch='moderate',
            max_results=10
        )
        return [r.get("href", "") for r in results]
        
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
        return []

async def scrape_async(url):
    """Asynchronous version of scrape function"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = await client.get(url, headers=headers)
            # Parse the HTML with BeautifulSoup (this runs synchronously)
            soup = BeautifulSoup(response.text, "html.parser")
            # Limit the amount of text for faster processing
            return soup.get_text()[:2000]
    except Exception as e:
        return f"[Scraping Error] {e}"

def generate_answer(question, texts):
    from .rag import call_mistral_api
    context = "\n\n".join(texts)
    prompt = f"Answer the question: {question}\n\nHere is the information found:\n{context}"
    try:
        if os.environ.get("MISTRAL_API_KEY"):
            return call_mistral_api(prompt)
        else:
            return "mistral"
    except Exception as e:
        return str(e)
