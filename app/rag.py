import os
from mistralai import Mistral
from fastapi import HTTPException

api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-small-latest"

client = Mistral(api_key=api_key)

def call_mistral_api(prompt: str) -> str:
    try:
        chat_response = client.chat.complete(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )
        return chat_response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
