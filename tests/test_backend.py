"""Unit tests for backend diagnostics, recommender, SQLite database, memory, and FastAPI endpoints."""

import pytest
import uuid
from fastapi.testclient import TestClient

from backend.core.system_info import get_system_hardware, determine_hardware_tier
from backend.core.recommender import get_recommendations, MODEL_CATALOG
from backend.core.ollama_client import check_ollama_installation
from backend.core.db import (
    create_or_update_conversation,
    get_all_conversations,
    get_conversation_messages,
    save_message,
    delete_conversation_by_id,
    add_user_memory,
    get_all_memories,
    delete_user_memory,
)
from backend.main import app


def test_determine_hardware_tier():
    """Verify hardware tier categorization logic."""
    assert determine_hardware_tier(4.0) == "LIGHT"
    assert determine_hardware_tier(7.0) == "LIGHT"
    assert determine_hardware_tier(8.0) == "MEDIUM"
    assert determine_hardware_tier(16.0) == "MEDIUM"
    assert determine_hardware_tier(32.0) == "STRONG"
    assert determine_hardware_tier(64.0) == "STRONG"


def test_get_system_hardware():
    """Verify hardware diagnostic inspection returns required fields."""
    hw = get_system_hardware()
    assert "ram_total_gb" in hw
    assert hw["ram_total_gb"] > 0
    assert "ram_available_gb" in hw
    assert "cpu_physical_cores" in hw
    assert hw["cpu_physical_cores"] >= 1
    assert "cpu_model" in hw
    assert "hardware_tier" in hw
    assert hw["hardware_tier"] in ["LIGHT", "MEDIUM", "STRONG"]


def test_recommender():
    """Verify model recommendations evaluate properly against hardware."""
    mock_hw = {
        "ram_total_gb": 16.0,
        "ram_available_gb": 10.0,
        "hardware_tier": "MEDIUM",
    }
    result = get_recommendations(mock_hw)
    assert result["tier"] == "MEDIUM"
    assert "summary" in result
    assert len(result["models"]) == len(MODEL_CATALOG)

    small_model = next(m for m in result["models"] if m["id"] == "llama3.2:3b")
    assert small_model["suitability"] == "optimal"
    assert small_model["badge_color"] == "green"


def test_ollama_binary_detection():
    """Verify that Ollama binary check runs without error."""
    installed, path = check_ollama_installation()
    assert isinstance(installed, bool)
    if installed:
        assert path is not None


def test_db_persistence_and_messages():
    """Verify SQLite persistence for conversations and messages."""
    test_id = str(uuid.uuid4())
    create_or_update_conversation(test_id, "Test Chat Session", "qwen2.5:3b")
    save_message(test_id, "user", "Hello SQLite")
    save_message(test_id, "assistant", "Hello! Stored safely.")

    convs = get_all_conversations()
    found = next((c for c in convs if c["id"] == test_id), None)
    assert found is not None
    assert found["title"] == "Test Chat Session"

    msgs = get_conversation_messages(test_id)
    assert len(msgs) == 2
    assert msgs[0]["content"] == "Hello SQLite"
    assert msgs[1]["content"] == "Hello! Stored safely."

    # Clean up
    delete_conversation_by_id(test_id)


def test_db_frontier_memories():
    """Verify long-term persistent user memories in SQLite."""
    mem = add_user_memory("User develops in Python and TypeScript", "skills")
    assert "id" in mem
    assert mem["fact"] == "User develops in Python and TypeScript"

    all_mems = get_all_memories()
    found = next((m for m in all_mems if m["id"] == mem["id"]), None)
    assert found is not None

    # Clean up
    delete_user_memory(mem["id"])
    assert not any(m["id"] == mem["id"] for m in get_all_memories())


def test_api_status_endpoint():
    """Test /api/status endpoint."""
    client = TestClient(app)
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "ollama_installed" in data
    assert "service_running" in data


def test_api_hardware_endpoint():
    """Test /api/hardware endpoint."""
    client = TestClient(app)
    response = client.get("/api/hardware")
    assert response.status_code == 200
    data = response.json()
    assert "ram_total_gb" in data
    assert "hardware_tier" in data


def test_api_recommendations_endpoint():
    """Test /api/recommendations endpoint."""
    client = TestClient(app)
    response = client.get("/api/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert "tier" in data
    assert "models" in data
    assert len(data["models"]) > 0


def test_api_models_endpoint():
    """Test /api/models endpoint."""
    client = TestClient(app)
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], list)


def test_api_memories_endpoints():
    """Test /api/memories GET, POST, DELETE endpoints."""
    client = TestClient(app)

    # 1. Create memory
    post_res = client.post("/api/memories", json={"fact": "User prefers concise answers", "category": "preferences"})
    assert post_res.status_code == 200
    created = post_res.json()["memory"]
    mem_id = created["id"]

    # 2. Get memories
    get_res = client.get("/api/memories")
    assert get_res.status_code == 200
    mems = get_res.json()["memories"]
    assert any(m["id"] == mem_id for m in mems)

    # 3. Delete memory
    del_res = client.delete(f"/api/memories/{mem_id}")
    assert del_res.status_code == 200

    # 4. Confirm deleted
    get_res2 = client.get("/api/memories")
    assert not any(m["id"] == mem_id for m in get_res2.json()["memories"])
