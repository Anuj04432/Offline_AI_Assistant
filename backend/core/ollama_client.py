"""Client for communicating with the local Ollama daemon."""

from typing import Tuple, Optional, List, Dict, Any, AsyncGenerator
import os
import shutil
import json
import httpx

DEFAULT_OLLAMA_URL = "http://localhost:11434"


def check_ollama_installation() -> Tuple[bool, Optional[str]]:
    """
    Check if the Ollama executable exists in PATH or standard installation locations.
    Returns (is_installed, binary_path).
    """
    # 1. Check system PATH
    which_path = shutil.which("ollama")
    if which_path:
        return True, which_path

    # 2. Check standard Windows locations
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe"),
        r"C:\Program Files\Ollama\ollama.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Ollama\ollama.exe"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return True, path

    return False, None


async def check_ollama_service(base_url: str = DEFAULT_OLLAMA_URL) -> Tuple[bool, Optional[str]]:
    """
    Check if the Ollama background daemon is reachable and responding.
    Returns (is_running, version).
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{base_url}/api/version")
            if resp.status_code == 200:
                data = resp.json()
                return True, data.get("version", "running")
            # Fallback check
            resp = await client.get(f"{base_url}/api/tags")
            return resp.status_code == 200, "running"
    except Exception:
        return False, None


async def get_installed_models(base_url: str = DEFAULT_OLLAMA_URL) -> List[Dict[str, Any]]:
    """Fetch all locally downloaded models from Ollama."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{base_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = []
                for m in data.get("models", []):
                    details = m.get("details", {})
                    size_bytes = m.get("size", 0)
                    size_gb = round(size_bytes / (1024 ** 3), 2) if size_bytes else 0.0
                    models.append({
                        "name": m.get("name"),
                        "size_gb": size_gb,
                        "parameter_size": details.get("parameter_size", "unknown"),
                        "quantization_level": details.get("quantization_level", "unknown"),
                        "family": details.get("family", "unknown"),
                        "modified_at": m.get("modified_at", ""),
                    })
                return models
    except Exception:
        pass
    return []


async def stream_chat_tokens(
    model: str,
    messages: List[Dict[str, str]],
    base_url: str = DEFAULT_OLLAMA_URL,
) -> AsyncGenerator[str, None]:
    """
    Send chat request to Ollama and yield token text as it streams in.
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "num_predict": 1024,
        },
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        async with client.stream("POST", f"{base_url}/api/chat", json=payload) as response:
            if response.status_code != 200:
                err_text = await response.aread()
                yield f"[Error from Ollama ({response.status_code}): {err_text.decode('utf-8', errors='ignore')}]"
                return

            async for line in response.aiter_lines():
                if not line or not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                    msg = chunk.get("message", {})
                    content = msg.get("content", "")
                    if content:
                        yield content
                    if chunk.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue


async def stream_model_pull(
    model_name: str,
    base_url: str = DEFAULT_OLLAMA_URL,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Trigger Ollama model download and yield progress dictionaries.
    Yields: {"status": "...", "completed": ..., "total": ..., "percent": ...}
    """
    payload = {"name": model_name, "stream": True}

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", f"{base_url}/api/pull", json=payload) as response:
            if response.status_code != 200:
                err_text = await response.aread()
                yield {
                    "status": "error",
                    "error": f"Failed to pull model ({response.status_code}): {err_text.decode('utf-8', errors='ignore')}",
                }
                return

            async for line in response.aiter_lines():
                if not line or not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    status = data.get("status", "")
                    completed = data.get("completed", 0)
                    total = data.get("total", 0)
                    percent = round((completed / total) * 100, 1) if total and total > 0 else 0.0

                    yield {
                        "status": status,
                        "completed": completed,
                        "total": total,
                        "percent": percent,
                        "done": status == "success",
                    }
                except json.JSONDecodeError:
                    continue
