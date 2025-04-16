import os
import re
from mistralai import Mistral
from fastapi import HTTPException
from typing import List

api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-small-latest"

client = Mistral(api_key=api_key)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Split text into manageable chunks with overlap"""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def summarize_content(text: str) -> str:
    """Generate summary for text chunks"""
    try:
        summary_prompt = f"Summarize this text while preserving key facts:\n{text}"
        return call_mistral_api(summary_prompt, max_tokens=500)
    except Exception as e:
        print(f"Summarization error: {e}")
        return text[:500]  # Fallback to truncation

def process_documents(content: List[str]) -> str:
    """Process and condense multiple documents"""
    processed = []
    for text in content:
        # Skip error messages
        if text.startswith("[Scraping Error]"):
            continue
            
        # Chunk and summarize
        chunks = chunk_text(text)
        summaries = [summarize_content(chunk) for chunk in chunks]
        processed.append(" ".join(summaries))
    
    return "\n\n".join(processed)

def call_mistral_api(prompt: str, max_tokens: int = 2000) -> str:
    try:
        chat_response = client.chat.complete(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return chat_response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
