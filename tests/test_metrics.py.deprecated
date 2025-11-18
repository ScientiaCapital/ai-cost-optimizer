"""Tests for metrics tracking system."""
import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta

from app.routing.metrics import MetricsCollector
from app.routing.models import RoutingDecision
from app.routing.engine import RoutingEngine


class TestMetricsCollector:
    """Test MetricsCollector functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def metrics_collector(self, temp_db):
        """Create a MetricsCollector instance."""
        return MetricsCollector(db_path=temp_db)

    def test_metrics_collector_tracks_decision(self, metrics_collector, temp_db):
        """Test that MetricsCollector records routing decisions."""
        # Create a routing decision
        decision = RoutingDecision(
            provider="gemini",
            model="gemini-1.5-flash",
            reasoning="Simple prompt, use fast model",
            confidence="high",
            strategy_used="complexity",
            fallback_used=False,
            metadata={
                "complexity": 0.3,
                "pattern": "question"
            }
        )

        prompt = "What is 2+2?"

        # Track the decision
        metrics_collector.track_decision(prompt, decision, auto_route=True)

        # Verify it was stored in the database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM routing_metrics")
        count = cursor.fetchone()[0]
        assert count == 1

        cursor.execute("""
            SELECT strategy_used, provider, model, confidence, auto_route
            FROM routing_metrics
        """)
        row = cursor.fetchone()

        assert row[0] == "complexity"
        assert row[1] == "gemini"
        assert row[2] == "gemini-1.5-flash"
        assert row[3] == "high"
        assert row[4] == 1  # auto_route=True

        conn.close()

    def test_metrics_collector_calculates_cost_savings(self, metrics_collector, temp_db):
        """Test that MetricsCollector compares auto_route vs complexity costs."""
        # Simulate 5 auto_route decisions (intelligent routing)
        decision_auto = RoutingDecision(
            provider="gemini",
            model="gemini-1.5-flash",
            reasoning="Pattern-based routing",
            confidence="high",
            strategy_used="learning",
            fallback_used=False,
            metadata={"complexity": 0.3}
        )

        for i in range(5):
            metrics_collector.track_decision(f"Prompt {i}", decision_auto, auto_route=True)

        # Simulate 5 baseline decisions (complexity-only routing)
        decision_baseline = RoutingDecision(
            provider="claude",
            model="claude-3-5-sonnet-20241022",
            reasoning="Complex prompt",
            confidence="high",
            strategy_used="complexity",
            fallback_used=False,
            metadata={"complexity": 0.8}
        )

        for i in range(5):
            metrics_collector.track_decision(f"Baseline {i}", decision_baseline, auto_route=False)

        # Calculate savings
        savings = metrics_collector.get_cost_savings(days=7)

        # Verify savings structure
        assert "total_saved" in savings
        assert "percent_saved" in savings
        assert "intelligent_cost" in savings
        assert "baseline_cost" in savings

        # Intelligent routing should be cheaper than baseline
        assert savings["intelligent_cost"] < savings["baseline_cost"]
        assert savings["total_saved"] > 0
        assert savings["percent_saved"] > 0

    def test_metrics_collector_aggregates_by_strategy(self, metrics_collector, temp_db):
        """Test that MetricsCollector aggregates metrics by strategy type."""
        # Create decisions with different strategies
        strategies = [
            ("complexity", "gemini", "gemini-1.5-flash", "high"),
            ("complexity", "gemini", "gemini-1.5-flash", "high"),
            ("learning", "gemini", "gemini-1.5-flash", "high"),
            ("learning", "claude", "claude-3-haiku-20240307", "medium"),
            ("feedback", "claude", "claude-3-5-sonnet-20241022", "low"),
        ]

        for strategy, provider, model, confidence in strategies:
            decision = RoutingDecision(
                provider=provider,
                model=model,
                reasoning=f"{strategy} routing",
                confidence=confidence,
                strategy_used=strategy,
                fallback_used=False,
                metadata={"complexity": 0.5}
            )
            metrics_collector.track_decision(f"Test prompt", decision, auto_route=True)

        # Aggregate by strategy
        results = metrics_collector.aggregate_by_strategy(days=7)

        # Verify results
        assert len(results) == 3  # complexity, learning, feedback

        # Find complexity strategy
        complexity_stats = next(r for r in results if r["strategy"] == "complexity")
        assert complexity_stats["count"] == 2
        assert "avg_cost" in complexity_stats
        assert "high_confidence_pct" in complexity_stats
        assert complexity_stats["high_confidence_pct"] == 100.0  # Both were high confidence

        # Find learning strategy
        learning_stats = next(r for r in results if r["strategy"] == "learning")
        assert learning_stats["count"] == 2
        assert learning_stats["high_confidence_pct"] == 50.0  # 1 high, 1 medium

    def test_metrics_collector_aggregates_by_confidence(self, metrics_collector, temp_db):
        """Test that MetricsCollector aggregates metrics by confidence level."""
        # Create decisions with different confidence levels
        confidence_levels = ["high", "high", "high", "medium", "medium", "low"]

        for confidence in confidence_levels:
            decision = RoutingDecision(
                provider="gemini",
                model="gemini-1.5-flash",
                reasoning="Test",
                confidence=confidence,
                strategy_used="complexity",
                fallback_used=False,
                metadata={"complexity": 0.5}
            )
            metrics_collector.track_decision("Test prompt", decision, auto_route=True)

        # Aggregate by confidence
        results = metrics_collector.aggregate_by_confidence(days=7)

        # Verify results
        assert len(results) == 3  # high, medium, low

        # Find high confidence
        high_conf = next(r for r in results if r["confidence"] == "high")
        assert high_conf["count"] == 3
        assert "avg_cost" in high_conf

        # Find medium confidence
        medium_conf = next(r for r in results if r["confidence"] == "medium")
        assert medium_conf["count"] == 2

        # Find low confidence
        low_conf = next(r for r in results if r["confidence"] == "low")
        assert low_conf["count"] == 1


class TestRoutingEngineMetrics:
    """Test RoutingEngine integration with metrics."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def engine(self, temp_db):
        """Create a RoutingEngine with metrics enabled."""
        return RoutingEngine(db_path=temp_db, track_metrics=True)

    def test_routing_engine_logs_metrics(self, engine, temp_db):
        """Test that RoutingEngine automatically logs metrics."""
        # Route a simple prompt
        prompt = "What is the capital of France?"
        decision = engine.route(prompt, auto_route=False)

        # Verify metrics were logged
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM routing_metrics")
        count = cursor.fetchone()[0]
        assert count == 1

        cursor.execute("""
            SELECT strategy_used, provider, model, auto_route
            FROM routing_metrics
        """)
        row = cursor.fetchone()

        assert row[0] == decision.strategy_used
        assert row[1] == decision.provider
        assert row[2] == decision.model
        assert row[3] == 0  # auto_route=False

        conn.close()

        # Route with auto_route enabled
        decision_auto = engine.route(prompt, auto_route=True)

        # Verify second metric was logged
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM routing_metrics")
        count = cursor.fetchone()[0]
        assert count == 2

        conn.close()
