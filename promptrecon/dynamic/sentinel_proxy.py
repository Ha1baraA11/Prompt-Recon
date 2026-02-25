# file: promptrecon/dynamic/sentinel_proxy.py
import subprocess
import os

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import uvicorn

app = FastAPI(title="Prompt-Recon Sentinel Proxy")

# Sentinel is designed to sit between the app and the LLM API.
# In a real deployed environment, it would intercept traffic on the network layer
# or be used as the base URL for the LLM client.

OAI_BASE_URL = "https://api.openai.com"

def analyze_payload_for_leaks(payload: dict) -> bool:
    """
    Check if the outgoing payload contains high-risk prompt patterns.
    This acts as the runtime dynamic check.
    """
    # Simplified check for demonstration of the Sentinel Architecture.
    # In a full implementation, this calls vector_analyzer.py or core scanner.
    
    dumps = str(payload).lower()
    if "admin_password" in dumps or "system_prompt: you are a highly confidential" in dumps:
        return True # Leak detected!
        
    return False

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_llm(request: Request, path: str):
    """
    Proxy request to actual LLM provider, inspecting payload first.
    """
    body = await request.body()
    
    # 1. Inspect
    try:
        payload = await request.json()
        is_leaking = analyze_payload_for_leaks(payload)
        if is_leaking:
            print(f"[SENTINEL BLOCKED] High-risk prompt detected in runtime payload to /{path}")
            raise HTTPException(status_code=403, detail="Prompt-Recon Sentinel: Request blocked due to data leak policy.")
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        pass # Not JSON or unable to parse

    # 2. Forward if safe
    url = f"{OAI_BASE_URL}/{path}"
    headers = dict(request.headers)
    headers.pop("host", None) # Let httpx handle host
    
    async with httpx.AsyncClient() as client:
        req = client.build_request(
            request.method,
            url,
            headers=headers,
            content=body
        )
        response = await client.send(req)
        
    return JSONResponse(content=response.json(), status_code=response.status_code)

def run_sentinel(port=8080):
    print(f"[*] Starting Prompt-Recon Sentinel on port {port}...")
    uvicorn.run(app, host="127.0.0.1", port=port)
