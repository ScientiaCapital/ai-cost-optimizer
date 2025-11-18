"""Tests for feedback API endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_submit_feedback_success():
    """Test submitting feedback returns success."""
    response = client.post("/production/feedback", json={
        "request_id": "test_request_123",
        "quality_score": 4,
        "is_correct": True,
        "comment": "Good answer"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert "feedback_id" in data
    assert data["message"] == "Thank you for feedback"


def test_submit_feedback_invalid_score():
    """Test invalid quality score returns 422."""
    response = client.post("/production/feedback", json={
        "request_id": "test_request",
        "quality_score": 6,  # Invalid: must be 1-5
        "is_correct": True
    })

    assert response.status_code == 422


def test_submit_feedback_missing_required():
    """Test missing required fields returns 422."""
    response = client.post("/production/feedback", json={
        "request_id": "test_request"
        # Missing quality_score and is_correct
    })

    assert response.status_code == 422


def test_submit_feedback_stores_in_database(tmp_path):
    """Test feedback is actually stored in database."""
    # Submit feedback
    response = client.post("/production/feedback", json={
        "request_id": "test_store_123",
        "quality_score": 5,
        "is_correct": True
    })

    feedback_id = response.json()["feedback_id"]

    # Verify in database
    from app.database.feedback_store import FeedbackStore
    store = FeedbackStore()
    feedback = store.get_by_id(feedback_id)

    assert feedback is not None
    assert feedback["request_id"] == "test_store_123"
    assert feedback["quality_score"] == 5
    assert feedback["is_correct"] is True
