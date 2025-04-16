from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from .rag import call_mistral_api
from bs4 import BeautifulSoup
from .rag import call_mistral_api
from .mcp import handle_mcp_request

app = FastAPI()

@app.get("/ask")
def ask(q: str = Query(...)):
    """
    Main endpoint for user queries.
    Depending on the query:
    - Retrieves relevant links using SearXNG
    - Scrapes textual content
    - Generates an answer using RAG (Mistral API)
    """
    links = search_searxng(q)
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

def search_searxng(query):
    res = requests.get("http://searxng:8080/search", params={"q": query, "format": "json"})
    data = res.json()
    return [r["url"] for r in data.get("results", [])]

def scrape(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        # Limit the amount of text for faster processing
        return soup.get_text()[:2000]
    except Exception as e:
        return f"[Scraping Error] {e}"

def generate_answer(question, texts):
    context = "\n\n".join(texts)
    prompt = f"Answer the question: {question}\n\nHere is the information found:\n{context}"
    return call_mistral_api(prompt)
