"""Pydantic models for admin endpoints."""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class FeedbackSummary(BaseModel):
    """Summary of feedback statistics."""
    total_feedback: int
    avg_quality_score: float
    models: List[Dict[str, Any]]


class LearningStatus(BaseModel):
    """Status of learning pipeline."""
    last_retraining_run: Optional[str]
    next_scheduled_run: Optional[str]
    confidence_distribution: Dict[str, int]
    total_patterns: int


class RetrainingResult(BaseModel):
    """Result of retraining run."""
    run_id: str
    timestamp: str
    patterns_updated: int
    total_changes: int
    changes: List[Dict[str, Any]]
    dry_run: bool


class PerformanceTrends(BaseModel):
    """Performance trends for a pattern."""
    pattern: str
    trends: List[Dict[str, Any]]
