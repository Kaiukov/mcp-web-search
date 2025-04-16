Below is the comprehensive project documentation translated into English:

---

# Project Documentation  
**RAG Perplexity Clone with MCP Support**  
*A minimal prototype of a search-based AI server using free APIs, SearXNG, RAG via Mistral API, and MCP protocol support.*

---

## 1. Introduction

### 1.1. Project Goal
This project is designed to develop a flexible search solution similar to Perplexity, but implemented using free APIs. The main tasks of the project include:
- Accepting a user query
- Searching for relevant links through SearXNG
- Scraping selected links to extract textual content
- Performing semantic analysis (RAG) using the free Mistral API through OpenRouter
- Handling requests and responses in the MCP protocol format, which enables integration with external systems through bidirectional data exchange

### 1.2. Key System Components
- **FastAPI Server:** The main web server that receives queries and returns answers.
- **SearXNG Search Engine:** An open-source metasearch engine used to retrieve relevant links.
- **Scraper:** A module to fetch textual content from web pages.
- **RAG Module (Retrieval-Augmented Generation):** Generates answers using the Mistral-7B-Instruct model via OpenRouter API.
- **MCP Endpoint:** Provides support for the Model Context Protocol, enabling integration with external systems.

---

## 2. Project Architecture

### 2.1. Overall Diagram
```plaintext
                    +------------------------+
                    |   User Query           |
                    +-----------+------------+
                                │
                                ▼
                    +------------------------+
                    |  FastAPI (/ask)        |
                    +-----------+------------+
                                │
         +----------------------+----------------------+
         │                                             │
         ▼                                             ▼
+-------------------+                       +-------------------+
|   SearXNG Search  |                       |   MCP Endpoint    |
|( /search request )|                       |   (/mcp)          |
+-------------------+                       +-------------------+
         │
         ▼
+-------------------+
| URL Scraping      |
+-------------------+
         │
         ▼
+-----------------------------+
|      RAG Module             |
| (Mistral API via OpenRouter)|
+-----------------------------+
         │
         ▼
+-----------------------------+
|    Response to User         |
+-----------------------------+
```

### 2.2. Components
1. **FastAPI Server**  
   - Receives HTTP requests.
   - Handles the main endpoint `/ask` for generating answers.
   - Provides a separate endpoint `/mcp` for MCP format queries.

2. **SearXNG**  
   - Runs as a separate service (Docker container).
   - Used to find relevant links for the user’s query.

3. **Scraper**  
   - Based on the libraries `requests` and `BeautifulSoup`.
   - Extracts textual content from web pages (with a character limit for faster processing).

4. **RAG Module**  
   - Combines extracted text fragments into a unified context.
   - Sends requests to the Mistral API (via OpenRouter API) to generate a final answer.

5. **MCP Module**  
   - Processes requests in the MCP format.
   - Enables bidirectional communication between external systems and the main server.

---

## 3. Technology Stack

- **Programming Language:** Python 3.10
- **Web Framework:** FastAPI
- **Scraping:** `requests` and `BeautifulSoup` (beautifulsoup4)
- **LLM (RAG) Calls:** Requests to call the Mistral API via OpenRouter.
- **Search Engine:** SearXNG (Docker image)
- **Containerization:** Docker, docker-compose

---

## 4. Project Structure

```
rag-perplexity-clone/
├── app/
│   ├── main.py       # Main server module with endpoints /ask and /mcp
│   ├── rag.py        # Module for handling RAG (calling Mistral API)
│   └── mcp.py        # Module for processing MCP-formatted requests
├── docker-compose.yml  # Describes services (rag-api and searxng)
├── Dockerfile        # Dockerfile for building the FastAPI server
├── requirements.txt  # Python dependencies
└── .gitignore        # Excludes unnecessary files (pycache, local databases, etc.)
```

---

## 5. Detailed File Descriptions

### 5.1. `requirements.txt`

```txt
fastapi
uvicorn
requests
beautifulsoup4
```

### 5.2. `Dockerfile`

```dockerfile
FROM python:3.10

WORKDIR /app
COPY ./app ./app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.3. `docker-compose.yml`

```yaml
version: '3.8'

services:
  rag-api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - searxng

  searxng:
    image: searxng/searxng:latest
    ports:
      - "8080:8080"
    environment:
      - BASE_URL=http://localhost:8080/
      - INSTANCE_NAME=RAG-Search
```

### 5.4. `app/rag.py`  
Module for invoking the Mistral API (via OpenRouter).

```python
import requests

OPENROUTER_API_KEY = "org-..."  # REPLACE with your API key

def call_mistral_api(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "RAG Assistant"
    }

    body = {
        "model": "mistral/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided text."},
            {"role": "user", "content": prompt}
        ]
    }

    res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    else:
        return f"[Mistral API Error] {res.status_code}: {res.text}"
```

### 5.5. `app/mcp.py`  
Module for basic MCP protocol support.

```python
import json
from fastapi import HTTPException

def handle_mcp_request(request: dict) -> dict:
    """
    Processes requests in MCP format.
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

        message = request['content']
        # Here you can add advanced logic for processing MCP messages
        response = {
            "type": "response",
            "content": f"Answer to your request: {message}"
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 5.6. `app/main.py`  
Main FastAPI module with routes for search, RAG, and MCP.

```python
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import requests
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
```

---

## 6. Project Deployment

### 6.1. Environment Preparation
- Install [Docker](https://www.docker.com/get-started) and [docker-compose](https://docs.docker.com/compose/install/).
- Ensure that ports **8000** (FastAPI) and **8080** (SearXNG) are available on your machine.

### 6.2. Build and Run
In the root directory of the project, execute:

```bash
docker-compose up --build
```

This will start two containers:
- **rag-api** – the FastAPI server.
- **searxng** – the SearXNG search engine.

### 6.3. Testing Main Functionalities

#### 6.3.1. Testing the `/ask` Endpoint
Open a browser or use **curl** to send a query:

```bash
curl -X GET "http://localhost:8000/ask?q=Why did oil prices rise in 2024"
```

Example response:
```json
{
  "answer": "Answer generated by the Mistral API based on the aggregated data...",
  "sources": [
    "https://example.com/source1",
    "https://example.com/source2",
    "https://example.com/source3"
  ]
}
```

#### 6.3.2. Testing the `/mcp` Endpoint
Send a POST request with an MCP example:

```bash
curl -X POST "http://localhost:8000/mcp" \
  -H "Content-Type: application/json" \
  -d '{
        "type": "request",
        "content": "How will the maritime industry change in 2024?"
      }'
```

Example response:
```json
{
  "type": "response",
  "content": "Answer to your request: How will the maritime industry change in 2024?"
}
```

---

## 7. Advanced Features and Future Enhancements

### 7.1. Enhancing MCP Message Handling
- Expand the logic in `handle_mcp_request` to parse commands, manage conversation context, and maintain dialogue state.
- Implement authentication or validation of incoming messages to protect against unauthorized access.

### 7.2. Expanding RAG Functionality
- Integrate caching mechanisms to reduce load for repeated queries.
- Implement robust error handling for Mistral API responses and notify the user of error causes.
- Add pre-processing steps (cleanup, normalization) for text before sending it to the LLM.

### 7.3. User Interface and Integration
- Enhance the project with a simple web-based interface for query input.
- Explore the possibility of integrating with mobile apps via MCP.

---

## 8. Hosting on GitHub

### 8.1. Creating the Repository
1. **Initialize a Git Repository**  
   In the root of your project, run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of RAG Perplexity Clone with MCP Support"
   ```

2. **Connect to a Remote Repository**  
   Create a new repository on GitHub (for example, `rag-perplexity-clone`). Then run:
   ```bash
   git remote add origin https://github.com/your-username/rag-perplexity-clone.git
   git branch -M main
   git push -u origin main
   ```

3. **Verify Your Repository**  
   Make sure all files are uploaded and available on GitHub.

---

## 9. Conclusion

This project provides an excellent starting point for creating a flexible AI solution in the style of Perplexity, using free APIs and MCP support.  
- **Scalability:** Easily integrate new data sources and additional LLM models.
- **Modularity:** Each component (search, scraping, answer generation, MCP handling) can be improved independently.
- **Extensibility:** You can add features such as sentiment analysis, caching, or user authentication as needed.

For further questions or assistance, you may refer to the official documentation of the utilized technologies, developer communities, and open-source project examples.

---

This comprehensive documentation should assist you in deploying, further developing, and maintaining the system.