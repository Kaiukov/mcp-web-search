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
