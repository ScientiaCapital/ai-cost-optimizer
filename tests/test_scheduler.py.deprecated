"""Tests for retraining scheduler."""
import pytest
from app.scheduler import RetrainingScheduler


def test_scheduler_initialization():
    """Test scheduler can be initialized."""
    scheduler = RetrainingScheduler()

    assert scheduler is not None
    assert not scheduler.is_running()


def test_scheduler_start_stop():
    """Test starting and stopping scheduler."""
    scheduler = RetrainingScheduler()

    scheduler.start()
    assert scheduler.is_running()

    scheduler.stop()
    assert not scheduler.is_running()


def test_scheduler_has_retraining_job():
    """Test scheduler has retraining job configured."""
    scheduler = RetrainingScheduler()
    scheduler.start()

    jobs = scheduler.get_jobs()

    assert len(jobs) > 0
    assert any('retrain' in job.id for job in jobs)

    scheduler.stop()


def test_manual_trigger_while_running():
    """Test manual retraining can be triggered while scheduler running."""
    scheduler = RetrainingScheduler()
    scheduler.start()

    # Should not raise error
    result = scheduler.trigger_immediate_retraining(dry_run=True)

    assert result is not None
    assert 'run_id' in result

    scheduler.stop()
