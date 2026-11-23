import os
import sys
import uuid
import json
import io
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
import PyPDF2

# Add parent directory to sys.path if running directly
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from core.system_info import get_system_hardware
from core.recommender import get_recommendations
from core.ollama_client import (
    check_ollama_installation,
    check_ollama_service,
    get_installed_models,
    stream_chat_tokens,
    stream_model_pull,
    DEFAULT_OLLAMA_URL,
)

app = FastAPI(title="LocalMind Offline AI Assistant")

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store
# sessions = { "session_id": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}] }
sessions: Dict[str, List[dict]] = {}

DEFAULT_MODEL = "qwen2.5-coder:7b"
SYSTEM_PROMPT = (
    "You are a helpful, knowledgeable, and concise offline AI assistant. "
    "Provide direct, clear, and well-structured answers."
)


class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = DEFAULT_MODEL
    session_id: Optional[str] = None
    stream: Optional[bool] = True


class PullRequest(BaseModel):
    model: str


# =====================================================================
# SYSTEM & PROVIDER DIAGNOSTICS
# =====================================================================

@app.get("/api/status")
async def get_provider_status():
    """
    Check if Ollama binary is installed on the host and if daemon is running.
    """
    installed, path = check_ollama_installation()
    running, version = await check_ollama_service()
    return {
        "ollama_installed": installed,
        "ollama_path": path,
        "service_running": running,
        "version": version,
    }


@app.get("/api/hardware")
def get_hardware_info():
    """
    Return detected hardware specs (RAM, CPU cores/threads, GPU, hardware tier).
    """
    return get_system_hardware()


@app.get("/api/recommendations")
def get_model_recommendations():
    """
    Return curated models scored against the host hardware capacity.
    """
    hw = get_system_hardware()
    return get_recommendations(hw)


# =====================================================================
# MODELS & PULLING
# =====================================================================

@app.get("/api/models")
@app.get("/models")
async def get_models():
    """
    Return list of locally downloaded models from Ollama.
    """
    models = await get_installed_models()
    model_names = [m["name"] for m in models]
    return {
        "models": model_names,
        "detailed_models": models,
        "default_model": DEFAULT_MODEL if DEFAULT_MODEL in model_names else (model_names[0] if model_names else None),
    }


@app.post("/api/pull")
async def pull_model_endpoint(request: PullRequest):
    """
    Stream Ollama model download progress as NDJSON chunks.
    """
    model_name = request.model.strip()
    if not model_name:
        raise HTTPException(status_code=400, detail="Model name is required")

    async def event_generator():
        async for chunk in stream_model_pull(model_name):
            yield json.dumps(chunk) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


# =====================================================================
# CHAT SESSIONS & STREAMING
# =====================================================================

@app.get("/api/sessions")
@app.get("/sessions")
async def get_sessions():
    """Return active chat sessions (newest first)."""
    session_list = []
    for sid, messages in sessions.items():
        if messages:
            first_user_msg = next((m["content"] for m in messages if m["role"] == "user"), "Conversation")
            title = first_user_msg[:32] + ("..." if len(first_user_msg) > 32 else "")
            session_list.append({"session_id": sid, "title": title})
    return {"sessions": list(reversed(session_list))}


@app.get("/api/sessions/{session_id}")
@app.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    """Return full message history for a given session."""
    if session_id in sessions:
        return {"history": sessions[session_id]}
    raise HTTPException(status_code=404, detail="Session not found")


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session from in-memory history."""
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


@app.post("/api/chat")
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Send a message to the selected local model with conversation context.
    Streams token chunks via Server-Sent Events (SSE).
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    model = request.model or DEFAULT_MODEL
    session_id = request.session_id

    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []

    # Append user turn
    sessions[session_id].append({"role": "user", "content": request.message.strip()})

    # Prepare context
    history_payload = [{"role": "system", "content": SYSTEM_PROMPT}] + sessions[session_id]

    # Non-streaming fallback
    if request.stream is False:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{DEFAULT_OLLAMA_URL}/api/chat",
                json={"model": model, "messages": history_payload, "stream": False},
            )
            data = resp.json()
            reply = data.get("message", {}).get("content", "")
            sessions[session_id].append({"role": "assistant", "content": reply})
            return {"response": reply, "session_id": session_id}

    # Streaming token generator (SSE format)
    async def sse_stream():
        full_reply = []
        # First send session_id event
        yield f"data: {json.dumps({'type': 'meta', 'session_id': session_id})}\n\n"

        async for token in stream_chat_tokens(model, history_payload):
            full_reply.append(token)
            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"

        # Record assistant reply in history
        assistant_text = "".join(full_reply)
        sessions[session_id].append({"role": "assistant", "content": assistant_text})
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_stream(), media_type="text/event-stream")


# =====================================================================
# DOCUMENT ATTACHMENT
# =====================================================================

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    model: Optional[str] = Form(DEFAULT_MODEL),
):
    """Extract text from uploaded PDF/TXT and send to model."""
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    content = await file.read()
    extracted_text = ""

    if file.filename.lower().endswith(".pdf"):
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to extract PDF text: {str(e)}")
    else:
        extracted_text = content.decode("utf-8", errors="ignore")

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="File is empty or contains no readable text")

    # Truncate if excessively long for context
    extracted_text = extracted_text[:8000]

    system_instruction = (
        f"The user attached document '{file.filename}'. Summarize it briefly and ask how to assist with it.\n\n"
        f"--- Document Content ---\n{extracted_text}"
    )

    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []

    sessions[session_id].append({"role": "user", "content": f"[Attached document: {file.filename}]"})

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{DEFAULT_OLLAMA_URL}/api/chat",
            json={
                "model": model or DEFAULT_MODEL,
                "messages": [{"role": "system", "content": system_instruction}],
                "stream": False,
            },
        )
        data = resp.json()
        reply = data.get("message", {}).get("content", "Document processed.")
        sessions[session_id].append({"role": "assistant", "content": reply})
        return {"response": reply, "session_id": session_id}


# =====================================================================
# STATIC FRONTEND SERVING
# =====================================================================

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists() and frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
