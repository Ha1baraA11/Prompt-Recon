# file: promptrecon/dynamic/sentinel_proxy.py
import subprocess
import os
import json

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import uvicorn

app = FastAPI(title="Prompt-Recon Sentinel Proxy")

# Sentinel is designed to sit between the app and the LLM API.
# In a real deployed environment, it would intercept traffic on the network layer
# or be used as the base URL for the LLM client.

OAI_BASE_URL = "https://api.openai.com"

# Lazy-load vector detector when first needed
_vector_detector = None

def get_vector_detector():
    """Lazily initialize the vector detector."""
    global _vector_detector
    if _vector_detector is None:
        try:
            from ..ml.vector_analyzer import VectorAnomalyDetector
            _vector_detector = VectorAnomalyDetector()
        except Exception as e:
            print(f"[WARNING] Failed to load VectorAnomalyDetector: {e}")
            _vector_detector = False
    return _vector_detector if _vector_detector else None

def analyze_payload_for_leaks(payload: dict) -> bool:
    """
    Check if the outgoing payload contains high-risk prompt patterns.
    Uses both keyword matching and vector anomaly detection.
    """
    # Keyword-based detection
    dumps = str(payload).lower()
    if "admin_password" in dumps or "system_prompt: you are a highly confidential" in dumps:
        return True

    # Try vector-based detection
    detector = get_vector_detector()
    if detector:
        try:
            # Extract message content from common payload formats
            messages = payload.get("messages", [])
            if isinstance(messages, list):
                for msg in messages:
                    content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
                    if detector.is_anomalous_prompt(content):
                        return True
        except Exception:
            pass

    return False

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_llm(request: Request, path: str):
    """
    Proxy request to actual LLM provider, inspecting payload first.
    """
    body = await request.body()

    # 1. Inspect
    try:
        payload = json.loads(body)
        is_leaking = analyze_payload_for_leaks(payload)
        if is_leaking:
            print(f"[SENTINEL BLOCKED] High-risk prompt detected in runtime payload to /{path}")
            raise HTTPException(status_code=403, detail="Prompt-Recon Sentinel: Request blocked due to data leak policy.")
    except HTTPException:
        raise
    except Exception:
        pass  # Not JSON or unable to parse - let it pass through

    # 2. Forward if safe
    url = f"{OAI_BASE_URL}/{path}"
    headers = dict(request.headers)
    headers.pop("host", None)  # Let httpx handle host

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body
        )

    # Handle streaming responses
    content_type = response.headers.get("content-type", "")
    if "text/event-stream" in content_type or "stream" in content_type:
        return StreamingResponse(
            response.iter_bytes(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )

    # Handle JSON responses
    try:
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception:
        # Fallback for non-JSON responses
        return JSONResponse(
            content={"error": "Failed to parse response", "status": response.status_code},
            status_code=response.status_code
        )

def run_sentinel(port=8080):
    print(f"[*] Starting Prompt-Recon Sentinel on port {port}...")
    print(f"[*] Configure your app to use http://127.0.0.1:{port} as the API base URL")
    uvicorn.run(app, host="127.0.0.1", port=port)
