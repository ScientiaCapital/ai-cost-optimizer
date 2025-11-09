"""Tests for FeedbackTrainer learning pipeline."""
import pytest
from datetime import datetime, timedelta
from app.learning.feedback_trainer import FeedbackTrainer


@pytest.fixture
def trainer(tmp_path):
    """Create FeedbackTrainer with test database."""
    # Setup test database connection
    return FeedbackTrainer(db_url="postgresql://test:test@localhost:5432/test_optimizer")


def test_confidence_calculation_high(trainer):
    """Test high confidence requires 10+ samples with good quality."""
    confidence = trainer._calculate_confidence(
        sample_count=12,
        avg_quality=4.2,
        correctness_rate=0.85
    )

    assert confidence == "high"


def test_confidence_calculation_medium(trainer):
    """Test medium confidence requires 5+ samples."""
    confidence = trainer._calculate_confidence(
        sample_count=7,
        avg_quality=3.8,
        correctness_rate=0.75
    )

    assert confidence == "medium"


def test_confidence_calculation_low(trainer):
    """Test low confidence for insufficient samples."""
    confidence = trainer._calculate_confidence(
        sample_count=3,
        avg_quality=4.5,
        correctness_rate=0.9
    )

    assert confidence == "low"


def test_low_quality_gives_low_confidence(trainer):
    """Test poor quality gives low confidence even with samples."""
    confidence = trainer._calculate_confidence(
        sample_count=15,
        avg_quality=2.5,
        correctness_rate=0.5
    )

    assert confidence == "low"


def test_aggregate_feedback_by_pattern(trainer):
    """Test aggregating feedback by pattern and model."""
    # Requires test data in database
    performance_data = trainer._aggregate_feedback()

    assert isinstance(performance_data, dict)
    # Each pattern should have model stats
    for pattern, models in performance_data.items():
        assert isinstance(models, dict)
        for model, stats in models.items():
            assert 'count' in stats
            assert 'avg_quality' in stats
            assert 'correctness' in stats


def test_retrain_only_updates_confident_patterns(trainer):
    """Test retraining only changes high/medium confidence patterns."""
    # Get initial weights
    initial_weights = trainer._get_current_weights()

    # Run retraining
    changes = trainer.retrain(dry_run=True)

    # Verify only confident patterns in changes
    for change in changes['changes']:
        assert change['confidence'] in ['high', 'medium']
        assert change['sample_count'] >= 5


def test_retrain_logs_run_metadata(trainer):
    """Test retraining logs metadata to database."""
    result = trainer.retrain(dry_run=False)

    assert 'run_id' in result
    assert 'timestamp' in result
    assert 'patterns_updated' in result
    assert 'total_changes' in result
