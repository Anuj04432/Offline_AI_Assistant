from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx
import io
import PyPDF2
import uuid

app = FastAPI()

# Allow CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_BASE_URL = "http://localhost:11434"

# In-memory storage for sessions
# sessions = { "session_id": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}] }
sessions: Dict[str, List[dict]] = {}

DEFAULT_MODEL = "qwen2.5-coder:7b"

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = DEFAULT_MODEL
    session_id: Optional[str] = None

@app.get("/models")
async def get_models():
    """Fetch available models from local Ollama instance"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            return {"models": models, "default_model": DEFAULT_MODEL}
    except Exception as e:
        return {"models": [], "error": str(e)}

@app.get("/sessions")
async def get_sessions():
    """Return list of active sessions with their first message as title"""
    session_list = []
    for sid, messages in sessions.items():
        if messages:
            title = messages[0]["content"][:30] + "..." if len(messages[0]["content"]) > 30 else messages[0]["content"]
            session_list.append({"session_id": sid, "title": title})
    return {"sessions": list(reversed(session_list))} # newest first

@app.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    """Return full history for a session"""
    if session_id in sessions:
        return {"history": sessions[session_id]}
    raise HTTPException(status_code=404, detail="Session not found")

@app.post("/chat")
async def chat(request: ChatRequest):
    """Send chat message to Ollama with history context"""
    if not request.message:
        raise HTTPException(status_code=400, detail="Message is required")

    model = request.model or DEFAULT_MODEL

    session_id = request.session_id
    if not session_id or session_id not in sessions:
        # Create new session if none provided or invalid
        session_id = str(uuid.uuid4())
        sessions[session_id] = []
        
    # Append user message
    user_msg = {"role": "user", "content": request.message}
    sessions[session_id].append(user_msg)
    
    # System prompt to ensure brevity and speed
    system_msg = {
        "role": "system", 
        "content": "You are a helpful assistant. Keep your answers concise, direct, and brief to ensure fast response times."
    }
    
    # Build payload using full history
    payload = {
        "model": model,
        "messages": [system_msg] + sessions[session_id],
        "stream": False,
        "options": {
            "num_predict": 400  # limit output tokens for faster response
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            reply_content = data.get("message", {}).get("content", "Error parsing response")
            
            # Save assistant reply to history
            sessions[session_id].append({"role": "assistant", "content": reply_content})
            
            return {"reply": reply_content, "session_id": session_id}
            
    except httpx.HTTPStatusError as e:
        error_msg = e.response.text
        # Rollback user message on error so it doesn't break history
        if sessions[session_id]:
            sessions[session_id].pop()
        raise HTTPException(status_code=500, detail=f"Ollama error: {error_msg}")
    except httpx.ConnectError:
        if sessions[session_id]:
            sessions[session_id].pop()
        raise HTTPException(status_code=503, detail="Could not connect to Ollama. Is it running?")
    except Exception as e:
        if sessions[session_id]:
            sessions[session_id].pop()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file uploads and extract text"""
    content = ""
    try:
        if file.filename.endswith(".txt"):
            content = (await file.read()).decode("utf-8")
        elif file.filename.endswith(".pdf"):
            pdf_bytes = await file.read()
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            for page in pdf_reader.pages:
                content += page.extract_text() + "\n"
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload TXT or PDF.")
            
        return {"extracted_text": content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice")
async def process_voice(audio: UploadFile = File(...)):
    """Basic endpoint for voice input handling."""
    return {"text": f"Voice input received ({audio.filename}). Offline transcription pending integration."}