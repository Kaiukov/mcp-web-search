from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import os
import requests  # Add this import
from bs4 import BeautifulSoup
from .rag import call_mistral_api
from .mcp import handle_mcp_request

app = FastAPI()

@app.get("/ask")
def ask(q: str = Query(...)):
    """
    Main endpoint for user queries.
    Depending on the query:
    - Retrieves relevant links using DuckDuckGo
    - Scrapes textual content
    - Generates an answer using RAG (Mistral API)
    """
    links = search_duckduckgo(q)
    contents = [scrape(url) for url in links[:3]]
    answer = generate_answer(q, contents)
    return {"answer": answer, "sources": links[:3]}

@app.post("/mcp")
def mcp_request(request: dict):
    """
    Endpoint for processing MCP-formatted requests.
    Accepts a JSON request and returns an MCP-formatted response.
    """
    response = handle_mcp_request(request)
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
def scrape(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
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
