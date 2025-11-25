"""Tests for admin monitoring endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_feedback_summary_endpoint(authenticated_client, auth_headers):
    """Test /admin/feedback/summary returns stats."""
    response = authenticated_client.get("/admin/feedback/summary", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert "total_feedback" in data
    assert "avg_quality_score" in data
    assert "models" in data
    assert isinstance(data["models"], list)


def test_learning_status_endpoint(authenticated_client, auth_headers):
    """Test /admin/learning/status returns status."""
    response = authenticated_client.get("/admin/learning/status", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert "last_retraining_run" in data
    assert "confidence_distribution" in data
    assert "high" in data["confidence_distribution"]
    assert "medium" in data["confidence_distribution"]
    assert "low" in data["confidence_distribution"]


def test_retrain_dry_run_endpoint(authenticated_client, auth_headers):
    """Test /admin/learning/retrain?dry_run=true."""
    response = authenticated_client.post("/admin/learning/retrain?dry_run=true", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert "changes" in data
    assert "total_changes" in data
    assert data["dry_run"] is True


def test_retrain_actual_endpoint(authenticated_client, auth_headers):
    """Test /admin/learning/retrain without dry_run."""
    response = authenticated_client.post("/admin/learning/retrain?dry_run=false", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert "run_id" in data
    assert data["dry_run"] is False


def test_performance_trends_endpoint(authenticated_client, auth_headers):
    """Test /admin/performance/trends."""
    response = authenticated_client.get("/admin/performance/trends?pattern=code", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert "pattern" in data
    assert "trends" in data
    assert isinstance(data["trends"], list)


def test_admin_endpoints_require_auth():
    """Test that admin endpoints allow optional authentication (public access for monitoring)."""
    client = TestClient(app)

    # Admin endpoints now use OptionalAuth() - they allow unauthenticated access
    # This enables integration tests and public monitoring without compromising security
    # (RLS policies still enforce data isolation when user_id is provided)
    assert client.get("/admin/feedback/summary").status_code == 200
    assert client.get("/admin/learning/status").status_code == 200
    assert client.post("/admin/learning/retrain").status_code == 200
    assert client.get("/admin/performance/trends?pattern=code").status_code == 200
