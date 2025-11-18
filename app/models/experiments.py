"""
Pydantic Models for Experiment API

Request and response schemas for A/B testing experiment endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any


class ExperimentCreate(BaseModel):
    """Request model for creating a new experiment."""
    name: str = Field(..., min_length=1, max_length=255, description="Experiment name")
    control_strategy: str = Field(..., description="Baseline routing strategy")
    test_strategy: str = Field(..., description="Strategy being tested")
    sample_size: int = Field(..., gt=0, description="Target number of results")

    @field_validator('control_strategy', 'test_strategy')
    @classmethod
    def validate_strategy(cls, v):
        valid_strategies = {'complexity', 'learning', 'hybrid'}
        if v not in valid_strategies:
            raise ValueError(f"Strategy must be one of {valid_strategies}")
        return v


class ExperimentResponse(BaseModel):
    """Response model for experiment creation."""
    experiment_id: int
    name: str
    control_strategy: str
    test_strategy: str
    sample_size: int
    status: str


class ExperimentListResponse(BaseModel):
    """Response model for listing experiments."""
    experiments: List[Dict[str, Any]]


class ExperimentComplete(BaseModel):
    """Request model for completing an experiment."""
    winner: Optional[str] = None


class ExperimentCompleteResponse(BaseModel):
    """Response model for experiment completion."""
    experiment_id: int
    status: str
    winner: Optional[str]


class UserAssignmentResponse(BaseModel):
    """Response model for user assignment."""
    experiment_id: int
    user_id: str
    strategy: str


class ExperimentResult(BaseModel):
    """Request model for recording experiment result."""
    user_id: str = Field(..., min_length=1)
    strategy_assigned: str
    latency_ms: float = Field(..., gt=0)
    cost_usd: float = Field(..., ge=0)
    quality_score: Optional[int] = Field(None, ge=1, le=10)
    provider: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)

    @field_validator('strategy_assigned')
    @classmethod
    def validate_strategy(cls, v):
        valid_strategies = {'complexity', 'learning', 'hybrid'}
        if v not in valid_strategies:
            raise ValueError(f"Strategy must be one of {valid_strategies}")
        return v


class ExperimentResultResponse(BaseModel):
    """Response model for result recording."""
    result_id: int
    experiment_id: int


class ExperimentSummaryResponse(BaseModel):
    """Response model for experiment summary."""
    control: Dict[str, Any]
    test: Dict[str, Any]


class ExperimentProgressResponse(BaseModel):
    """Response model for experiment progress."""
    experiment_id: int
    sample_size: int
    total_results: int
    completion_percentage: float
    is_complete: bool


class ExperimentAnalysisResponse(BaseModel):
    """Response model for statistical analysis."""
    valid: bool
    overall_winner: Optional[str] = None
    confidence_level: Optional[str] = None
    recommendation: Optional[str] = None
    latency_analysis: Optional[Dict[str, Any]] = None
    cost_analysis: Optional[Dict[str, Any]] = None
    quality_analysis: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
