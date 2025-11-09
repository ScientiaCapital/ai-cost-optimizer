"""Tests for admin monitoring endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_feedback_summary_endpoint():
    """Test /admin/feedback/summary returns stats."""
    response = client.get("/admin/feedback/summary")

    assert response.status_code == 200
    data = response.json()

    assert "total_feedback" in data
    assert "avg_quality_score" in data
    assert "models" in data
    assert isinstance(data["models"], list)


def test_learning_status_endpoint():
    """Test /admin/learning/status returns status."""
    response = client.get("/admin/learning/status")

    assert response.status_code == 200
    data = response.json()

    assert "last_retraining_run" in data
    assert "confidence_distribution" in data
    assert "high" in data["confidence_distribution"]
    assert "medium" in data["confidence_distribution"]
    assert "low" in data["confidence_distribution"]


def test_retrain_dry_run_endpoint():
    """Test /admin/learning/retrain?dry_run=true."""
    response = client.post("/admin/learning/retrain?dry_run=true")

    assert response.status_code == 200
    data = response.json()

    assert "changes" in data
    assert "total_changes" in data
    assert data["dry_run"] is True


def test_retrain_actual_endpoint():
    """Test /admin/learning/retrain without dry_run."""
    response = client.post("/admin/learning/retrain?dry_run=false")

    assert response.status_code == 200
    data = response.json()

    assert "run_id" in data
    assert data["dry_run"] is False


def test_performance_trends_endpoint():
    """Test /admin/performance/trends."""
    response = client.get("/admin/performance/trends?pattern=code")

    assert response.status_code == 200
    data = response.json()

    assert "pattern" in data
    assert "trends" in data
    assert isinstance(data["trends"], list)
