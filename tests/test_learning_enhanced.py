"""Tests for enhanced learning.py with model-level tracking."""
import pytest
import sqlite3
import os
from app.learning import QueryPatternAnalyzer


@pytest.fixture
def test_db():
    """Create temporary test database."""
    db_path = "test_learning.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create schema
    cursor.execute("""
        CREATE TABLE requests (
            id INTEGER PRIMARY KEY,
            prompt_preview TEXT,
            complexity TEXT,
            provider TEXT,
            model TEXT,
            tokens_in INTEGER,
            tokens_out INTEGER,
            cost REAL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE response_feedback (
            id INTEGER PRIMARY KEY,
            request_id INTEGER,
            rating INTEGER,
            FOREIGN KEY (request_id) REFERENCES requests(id)
        )
    """)

    # Insert test data
    test_requests = [
        ("Debug Python code", "complex", "openrouter", "openrouter/deepseek-coder", 100, 300, 0.00024, "2025-01-01 10:00:00"),
        ("Explain microservices", "simple", "claude", "claude/claude-3-haiku", 50, 200, 0.00095, "2025-01-01 10:05:00"),
        ("Write a function", "complex", "openrouter", "openrouter/deepseek-coder", 80, 250, 0.00020, "2025-01-01 10:10:00"),
        ("What is Docker?", "simple", "google", "google/gemini-flash", 30, 150, 0.00008, "2025-01-01 10:15:00"),
    ]

    for req in test_requests:
        cursor.execute(
            "INSERT INTO requests (prompt_preview, complexity, provider, model, tokens_in, tokens_out, cost, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            req
        )

    # Add feedback
    cursor.execute("INSERT INTO response_feedback (request_id, rating) VALUES (1, 5)")
    cursor.execute("INSERT INTO response_feedback (request_id, rating) VALUES (2, 4)")
    cursor.execute("INSERT INTO response_feedback (request_id, rating) VALUES (3, 5)")

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


def test_get_provider_performance_model_level(test_db):
    """Provider performance tracks model-level granularity."""
    analyzer = QueryPatternAnalyzer(db_path=test_db)

    performance = analyzer.get_provider_performance()

    # Should have model-level entries
    models = [p['model'] for p in performance]
    assert "openrouter/deepseek-coder" in models
    assert "claude/claude-3-haiku" in models
    assert "google/gemini-flash" in models


def test_recommend_provider_with_confidence(test_db):
    """Recommendations include confidence levels."""
    analyzer = QueryPatternAnalyzer(db_path=test_db)

    recommendation = analyzer.recommend_provider(
        "Debug my Python code",
        "complex",
        ["openrouter", "claude", "google"]
    )

    assert 'model' in recommendation
    assert 'confidence' in recommendation
    assert recommendation['confidence'] in ['high', 'medium', 'low']


def test_pattern_confidence_levels(test_db):
    """Pattern confidence levels based on sample count."""
    analyzer = QueryPatternAnalyzer(db_path=test_db)

    confidence = analyzer.get_pattern_confidence_levels()

    assert 'code' in confidence
    assert confidence['code']['sample_count'] >= 0
    assert confidence['code']['confidence'] in ['high', 'medium', 'low']
