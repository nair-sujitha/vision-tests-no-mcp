# gemini_proxy.py
import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow CORS if needed (Mobile-Use may call from local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini API settings
GEMINI_KEY = "AIzaSyDoiEpkt3-ffrdUSMM2pr2vsZIKmz2wHYM"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

@app.post("/v1/chat/completions")
async def proxy_openai(request: Request):
    body = await request.json()
    # Extract the last message text
    messages = body.get("messages", [])
    if not messages:
        return {"error": "No messages provided"}
    prompt = messages[-1]["content"][0]["text"]

    # Build Gemini request
    gemini_payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    headers = {"x-goog-api-key": GEMINI_KEY}

    resp = requests.post(GEMINI_URL, headers=headers, json=gemini_payload)
    gemini_resp = resp.json()

    # Extract Gemini text
    text = gemini_resp["candidates"][0]["content"]["parts"][0]["text"]
    finish_reason = gemini_resp["candidates"][0]["finishReason"]

    # Return OpenAI-compatible JSON
    return {
        "id": gemini_resp.get("responseId", "unknown"),
        "object": "chat.completion",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": text}]
                },
                "finish_reason": finish_reason
            }
        ]
    }