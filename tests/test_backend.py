"""Unit tests for backend diagnostics, recommender, and FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.core.system_info import get_system_hardware, determine_hardware_tier
from backend.core.recommender import get_recommendations, MODEL_CATALOG
from backend.core.ollama_client import check_ollama_installation
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

    # 1B and 3B models should be optimal for 16GB
    small_model = next(m for m in result["models"] if m["id"] == "llama3.2:3b")
    assert small_model["suitability"] == "optimal"
    assert small_model["badge_color"] == "green"


def test_ollama_binary_detection():
    """Verify that Ollama binary check runs without error."""
    installed, path = check_ollama_installation()
    assert isinstance(installed, bool)
    if installed:
        assert path is not None


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
