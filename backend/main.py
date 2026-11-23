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

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

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
from core.db import (
    init_db,
    create_or_update_conversation,
    get_all_conversations,
    get_conversation_messages,
    save_message,
    delete_conversation_by_id,
    get_all_memories,
    add_user_memory,
    delete_user_memory,
)

app = FastAPI(title="LocalMind Offline AI Assistant")

# Initialize SQLite database on startup
init_db()

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_MODEL = "qwen2.5-coder:7b"
BASE_SYSTEM_PROMPT = (
    "You are LocalMind, a knowledgeable, helpful, and concise offline AI assistant. "
    "Provide direct, clear, and well-structured answers."
)


class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = DEFAULT_MODEL
    session_id: Optional[str] = None
    stream: Optional[bool] = True


class PullRequest(BaseModel):
    model: str


class MemoryRequest(BaseModel):
    fact: str
    category: Optional[str] = "general"


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
# PERSISTENT CHAT SESSIONS & STREAMING (SQLITE)
# =====================================================================

@app.get("/api/sessions")
@app.get("/sessions")
def get_sessions():
    """Return active chat sessions from SQLite database (newest first)."""
    convs = get_all_conversations()
    return {"sessions": [{"session_id": c["id"], "title": c["title"], "model": c["model_name"]} for c in convs]}


@app.get("/api/sessions/{session_id}")
@app.get("/sessions/{session_id}")
def get_session_history(session_id: str):
    """Return full message history from SQLite for a given session."""
    msgs = get_conversation_messages(session_id)
    return {"history": [{"role": m["role"], "content": m["content"]} for m in msgs]}


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a session and all its messages from SQLite."""
    deleted = delete_conversation_by_id(session_id)
    if deleted:
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


# =====================================================================
# PERSISTENT LONG-TERM MEMORIES (FRONTIER MEMORY)
# =====================================================================

@app.get("/api/memories")
def list_memories():
    """Retrieve all persistent memories about the user."""
    return {"memories": get_all_memories()}


@app.post("/api/memories")
def create_memory(req: MemoryRequest):
    """Store a new long-term persistent fact about the user."""
    if not req.fact.strip():
        raise HTTPException(status_code=400, detail="Memory fact cannot be empty")
    created = add_user_memory(req.fact, req.category or "general")
    return {"status": "created", "memory": created}


@app.delete("/api/memories/{memory_id}")
def remove_memory(memory_id: str):
    """Delete a long-term memory."""
    success = delete_user_memory(memory_id)
    if success:
        return {"status": "deleted", "memory_id": memory_id}
    raise HTTPException(status_code=404, detail="Memory not found")


# =====================================================================
# CHAT ENDPOINT WITH CONTEXT & FRONTIER MEMORY INJECTION
# =====================================================================

@app.post("/api/chat")
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Send a message to the selected local model with conversation context and persistent frontier memories.
    Streams token chunks via Server-Sent Events (SSE).
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    model = request.model or DEFAULT_MODEL
    session_id = request.session_id

    # Create new session if none provided
    is_new_session = False
    if not session_id:
        session_id = str(uuid.uuid4())
        is_new_session = True

    # Generate a clean title for the conversation from the first message
    if is_new_session:
        clean_title = request.message.strip()[:32] + ("..." if len(request.message.strip()) > 32 else "")
        create_or_update_conversation(session_id, clean_title, model)

    # Save user message to SQLite database
    save_message(session_id, "user", request.message.strip())

    # Fetch full history for this session from SQLite
    history_records = get_conversation_messages(session_id)
    conversation_turns = [{"role": r["role"], "content": r["content"]} for r in history_records]

    # Inject persistent user memories into system prompt (Frontier-style memory)
    memories = get_all_memories()
    memory_instruction = ""
    if memories:
        memory_items = "\n".join([f"- {m['fact']}" for m in memories])
        memory_instruction = (
            f"\n\n[Persistent Long-Term Memories about the User & Context]:\n"
            f"{memory_items}\n"
            f"Use these memories to maintain context, preferences, and continuity across chats."
        )

    full_system_prompt = f"{BASE_SYSTEM_PROMPT}{memory_instruction}"
    history_payload = [{"role": "system", "content": full_system_prompt}] + conversation_turns

    # Non-streaming fallback
    if request.stream is False:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{DEFAULT_OLLAMA_URL}/api/chat",
                json={"model": model, "messages": history_payload, "stream": False},
            )
            data = resp.json()
            reply = data.get("message", {}).get("content", "")
            save_message(session_id, "assistant", reply)
            return {"response": reply, "session_id": session_id}

    # Streaming token generator (SSE format)
    async def sse_stream():
        full_reply = []
        # First send session_id event
        yield f"data: {json.dumps({'type': 'meta', 'session_id': session_id})}\n\n"

        async for token in stream_chat_tokens(model, history_payload):
            full_reply.append(token)
            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"

        # Record assistant reply in SQLite database
        assistant_text = "".join(full_reply)
        save_message(session_id, "assistant", assistant_text)
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
        if PyPDF2 is None:
            raise HTTPException(status_code=500, detail="PyPDF2 is not installed on the server. Run 'pip install PyPDF2' to process PDFs.")
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

    extracted_text = extracted_text[:8000]

    system_instruction = (
        f"The user attached document '{file.filename}'. Summarize it briefly and ask how to assist with it.\n\n"
        f"--- Document Content ---\n{extracted_text}"
    )

    if not session_id:
        session_id = str(uuid.uuid4())
        create_or_update_conversation(session_id, f"Doc: {file.filename[:20]}", model)

    save_message(session_id, "user", f"[Attached document: {file.filename}]")

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
        save_message(session_id, "assistant", reply)
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
