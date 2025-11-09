"""FastAPI service for AI Cost Optimizer."""
import os
import logging
import sqlite3
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .providers import init_providers
from .database import CostTracker
from app.services.routing_service import RoutingService
from app.models.feedback import FeedbackRequest as ProductionFeedbackRequest, FeedbackResponse as ProductionFeedbackResponse
from app.database.feedback_store import FeedbackStore
from app.models.admin import (
    FeedbackSummary, LearningStatus,
    RetrainingResult, PerformanceTrends
)
from app.learning.feedback_trainer import FeedbackTrainer
from app.database.postgres import get_connection, get_cursor
from app.scheduler import RetrainingScheduler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize retraining scheduler (before lifespan)
scheduler = None

if os.getenv('ENABLE_SCHEDULER', 'true').lower() == 'true':
    scheduler = RetrainingScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup: Start scheduler
    if scheduler:
        scheduler.start()
        logger.info("Retraining scheduler started")

    yield

    # Shutdown: Stop scheduler
    if scheduler:
        scheduler.stop()
        logger.info("Retraining scheduler stopped")


# Initialize FastAPI app
app = FastAPI(
    title="AI Cost Optimizer",
    description="Smart multi-LLM routing for cost optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware (configurable via environment)
cors_origins = os.getenv("CORS_ORIGINS", "*")
# Parse comma-separated origins or use "*" for all
if cors_origins == "*":
    allow_origins = ["*"]
else:
    allow_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global components
providers = init_providers()
routing_service = RoutingService(
    db_path=os.getenv("DATABASE_PATH", "optimizer.db"),
    providers=providers
)
feedback_store = FeedbackStore()
feedback_trainer = FeedbackTrainer()

logger.info(f"AI Cost Optimizer initialized with providers: {list(providers.keys())}")


# Request/Response models
class CompleteRequest(BaseModel):
    """Request model for completion endpoint."""
    prompt: str = Field(..., min_length=1, description="User prompt")
    max_tokens: Optional[int] = Field(1000, ge=1, le=4000, description="Maximum response tokens")
    auto_route: bool = Field(False, description="Enable intelligent routing (hybrid strategy)")
    tokenizer_id: Optional[str] = Field(None, description="Optional HF repo id for tokenization metrics (e.g., 'UW/OLMo2-8B-SuperBPE-t180k')")


class CompleteResponse(BaseModel):
    """Response model for completion endpoint."""
    request_id: str     # NEW: Unique request ID for feedback tracking
    response: str
    provider: str
    model: str
    strategy_used: str  # NEW: "complexity", "learning", "hybrid", "cached"
    confidence: str     # NEW: "high", "medium", "low"
    complexity: str     # DEPRECATED but kept for compatibility
    complexity_metadata: dict
    routing_metadata: dict  # NEW: Full RoutingDecision.metadata
    tokens_in: int
    tokens_out: int
    cost: float
    total_cost_today: float
    cache_hit: bool = False
    original_cost: Optional[float] = None
    savings: float = 0.0
    cache_key: Optional[str] = None
    tokenizer_id: Optional[str] = None
    tokenizer_tokens_in: Optional[int] = None
    tokenizer_bytes_per_token: Optional[float] = None
    tokenizer_tokens_per_byte: Optional[float] = None


class StatsResponse(BaseModel):
    """Response model for stats endpoint."""
    overall: dict
    by_provider: list
    by_complexity: list
    recent_requests: list


class FeedbackRequest(BaseModel):
    """Request model for feedback endpoint."""
    cache_key: str = Field(..., min_length=1, description="Cache key of response to rate")
    rating: int = Field(..., ge=-1, le=1, description="1 for upvote, -1 for downvote")
    comment: Optional[str] = Field(None, max_length=500, description="Optional feedback comment")


class FeedbackResponse(BaseModel):
    """Response model for feedback endpoint."""
    success: bool
    cache_key: str
    quality_score: Optional[float]
    invalidated: bool
    message: str


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "providers_available": list(routing_service.providers.keys()),
        "routing_engine": "v2",  # Phase 2 Auto-Routing with RoutingEngine
        "auto_route_enabled": routing_service.engine.track_metrics,
        "version": "2.0.0"  # Phase 2 FastAPI Integration
    }


@app.post("/complete", response_model=CompleteResponse)
async def complete_prompt(request: CompleteRequest):
    """
    Route and complete a prompt using optimal provider with caching.

    This is the main endpoint that:
    1. Checks response cache for instant results
    2. Routes using RoutingEngine (complexity or hybrid based on auto_route)
    3. Executes completion with selected provider
    4. Stores response in cache
    5. Tracks cost and routing metrics

    Args:
        request: CompleteRequest with prompt, max_tokens, and auto_route

    Returns:
        CompleteResponse with response text, metadata, and cost

    Raises:
        HTTPException: If routing or completion fails
    """
    try:
        result = await routing_service.route_and_complete(
            prompt=request.prompt,
            auto_route=request.auto_route,
            max_tokens=request.max_tokens
        )

        # Optional tokenizer metrics
        tokenizer_id = request.tokenizer_id
        tokenizer_tokens_in = None
        tokenizer_bytes_per_token = None
        tokenizer_tokens_per_byte = None

        if tokenizer_id and not result["cache_hit"]:
            try:
                from .tokenizer_registry import estimate_tokenization_metrics
                est = estimate_tokenization_metrics(request.prompt, tokenizer_id)
                if est is not None:
                    tokenizer_tokens_in, tokenizer_bytes_per_token, tokenizer_tokens_per_byte = est
            except Exception as ex:
                logger.warning(f"Tokenizer metrics unavailable: {ex}")

        return CompleteResponse(
            request_id=result["request_id"],
            response=result["response"],
            provider=result["provider"],
            model=result["model"],
            strategy_used=result["strategy_used"],
            confidence=result["confidence"],
            complexity=result.get("strategy_used", "unknown"),  # Deprecated field
            complexity_metadata=result["complexity_metadata"],
            routing_metadata=result["routing_metadata"],
            tokens_in=result["tokens_in"],
            tokens_out=result["tokens_out"],
            cost=result["cost"],
            total_cost_today=result["total_cost_today"],
            cache_hit=result["cache_hit"],
            original_cost=result.get("original_cost"),
            savings=result.get("savings", 0.0),
            cache_key=result.get("cache_key"),
            tokenizer_id=tokenizer_id,
            tokenizer_tokens_in=tokenizer_tokens_in,
            tokenizer_bytes_per_token=tokenizer_bytes_per_token,
            tokenizer_tokens_per_byte=tokenizer_tokens_per_byte,
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/stats", response_model=StatsResponse)
async def get_usage_stats():
    """
    Get usage statistics from database.

    Returns:
        Statistics including total costs, breakdowns by provider/complexity,
        and recent request history
    """
    try:
        stats = routing_service.cost_tracker.get_usage_stats()
        return StatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/providers")
async def list_providers():
    """
    List all available providers and their models.

    Returns:
        Dictionary of enabled providers with model information
    """
    return {
        "enabled_providers": list(providers.keys()),
        "models": {
            "gemini": {
                "name": "gemini-1.5-flash",
                "pricing": {"input_per_1m": "$0.075", "output_per_1m": "$0.30"},
                "recommended_for": "Simple queries, free tier available"
            },
            "claude": {
                "name": "claude-3-haiku-20240307",
                "pricing": {"input_per_1m": "$0.25", "output_per_1m": "$1.25"},
                "recommended_for": "Complex queries, best quality/cost balance"
            },
            "openrouter": {
                "name": "multiple models",
                "pricing": {"input_per_1m": "Varies", "output_per_1m": "Varies"},
                "recommended_for": "Fallback aggregator for all models"
            }
        }
    }


@app.get("/recommendation")
async def get_recommendation(prompt: str):
    """
    Get routing recommendation without executing request.

    Always uses auto_route=true (hybrid strategy) for recommendations.
    Useful for previewing which model would be selected.

    Args:
        prompt: User prompt (query parameter)

    Returns:
        Routing information with provider, model, confidence, and reasoning
    """
    try:
        return routing_service.get_recommendation(prompt=prompt)

    except Exception as e:
        logger.error(f"Error getting recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/routing/metrics")
async def get_routing_metrics():
    """
    Get auto-routing analytics for monitoring and ROI tracking.

    Returns strategy performance, decision counts, and confidence distribution
    from the routing engine metrics collector.

    Returns:
        Dict with strategy_performance, total_decisions, confidence_distribution, provider_usage
    """
    try:
        return routing_service.get_routing_metrics()

    except Exception as e:
        logger.error(f"Error fetching routing metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/routing/decision")
async def get_routing_decision(prompt: str, auto_route: bool = True):
    """
    Get detailed routing explanation for debugging and transparency.

    Returns complete RoutingDecision with all metadata for understanding
    why a particular provider/model was selected.

    Args:
        prompt: Prompt to analyze (query parameter)
        auto_route: Use intelligent routing (default: true)

    Returns:
        Dict with decision and full metadata
    """
    try:
        recommendation = routing_service.get_recommendation(prompt=prompt)

        return {
            "decision": {
                "provider": recommendation["provider"],
                "model": recommendation["model"],
                "confidence": recommendation["confidence"],
                "strategy_used": recommendation["strategy_used"],
                "reasoning": recommendation["reasoning"]
            },
            "metadata": recommendation["metadata"]
        }

    except Exception as e:
        logger.error(f"Error getting routing decision: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get response cache statistics.

    Returns:
        Cache statistics including:
        - total_entries: Number of unique cached responses
        - total_hits: How many times cache was used
        - total_savings: Money saved from cache hits
        - hit_rate_percent: Cache hit rate percentage
        - popular_queries: Most frequently cached queries
    """
    try:
        stats = routing_service.cost_tracker.get_cache_stats()
        return stats

    except Exception as e:
        logger.error(f"Error fetching cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest, user_agent: Optional[str] = None):
    """
    Submit user feedback (thumbs up/down) for a cached response.

    This endpoint allows users to rate cached responses for quality.
    After 3+ votes, poor quality responses (score < 0.3) are automatically
    invalidated and will be regenerated on next request.

    Args:
        request: FeedbackRequest with cache_key, rating, and optional comment
        user_agent: Optional User-Agent header

    Returns:
        FeedbackResponse with updated quality score and invalidation status
    """
    try:
        # Add feedback to database
        routing_service.cost_tracker.add_feedback(
            cache_key=request.cache_key,
            rating=request.rating,
            comment=request.comment,
            user_agent=user_agent
        )

        # Update quality score (may trigger invalidation)
        quality_score = routing_service.cost_tracker.update_quality_score(request.cache_key)

        # Check if entry was invalidated
        conn = routing_service.cost_tracker._CostTracker__get_connection() if hasattr(routing_service.cost_tracker, '_CostTracker__get_connection') else None
        if not conn:
            conn = sqlite3.connect(routing_service.cost_tracker.db_path)

        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT invalidated FROM response_cache
            WHERE cache_key = ?
        """, (request.cache_key,))
        row = cursor.fetchone()
        invalidated = bool(row["invalidated"]) if row else False
        conn.close()

        logger.info(
            f"Feedback received: cache_key={request.cache_key[:16]}..., "
            f"rating={request.rating}, quality_score={quality_score}, invalidated={invalidated}"
        )

        message = "Thank you for your feedback!"
        if invalidated:
            message = "Response invalidated due to low quality. Future requests will generate a fresh response."
        elif quality_score is not None and quality_score < 0.5:
            message = "Thank you for your feedback! This response is being monitored for quality."

        return FeedbackResponse(
            success=True,
            cache_key=request.cache_key,
            quality_score=quality_score,
            invalidated=invalidated,
            message=message
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/production/feedback", response_model=ProductionFeedbackResponse)
async def submit_production_feedback(request: ProductionFeedbackRequest):
    """Submit quality feedback for a request.

    This endpoint collects user feedback on response quality for the
    production learning pipeline. Feedback is used to retrain routing
    recommendations.

    Args:
        request: Feedback submission with request_id, quality_score, correctness

    Returns:
        Feedback confirmation with feedback_id
    """
    try:
        feedback_id = feedback_store.store_feedback(
            request_id=request.request_id,
            quality_score=request.quality_score,
            is_correct=request.is_correct,
            is_helpful=request.is_helpful,
            comment=request.comment
        )

        return ProductionFeedbackResponse(
            status="recorded",
            feedback_id=feedback_id,
            message="Thank you for feedback"
        )

    except Exception as e:
        logger.error(f"Failed to store production feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to store feedback"
        )


@app.get("/quality/stats")
async def get_quality_stats():
    """
    Get quality statistics across all cached responses.

    Returns quality metrics including:
    - overall: Aggregate quality stats
    - by_provider: Quality breakdown by provider
    - top_rated: Highest quality responses
    - worst_rated: Lowest quality responses (excluding invalidated)
    - invalidated_responses: Responses that were removed due to poor quality
    """
    try:
        stats = routing_service.cost_tracker.get_quality_stats()
        return stats

    except Exception as e:
        logger.error(f"Error fetching quality stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/insights")
async def get_learning_insights():
    """Get intelligent routing insights from learning module.

    NOTE: This endpoint is being migrated to the new routing architecture.
    Use /routing/metrics for current routing analytics.
    """
    return {
        "learning_active": False,
        "message": "This endpoint is deprecated. Please use /routing/metrics instead.",
        "migration_note": "Learning insights are being integrated into the new routing engine.",
        "alternative_endpoint": "/routing/metrics"
    }


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

def _is_sqlite(conn) -> bool:
    """Check if connection is SQLite."""
    return hasattr(conn, 'row_factory')


@app.get("/admin/feedback/summary", response_model=FeedbackSummary)
async def get_feedback_summary():
    """Get feedback statistics summary."""
    with get_connection() as conn:
        cursor = get_cursor(conn, dict_cursor=True)

        try:
            # Total feedback and avg quality
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    AVG(quality_score) as avg_quality
                FROM response_feedback
            """)

            stats = cursor.fetchone()

            # Per-model stats
            cursor.execute("""
                SELECT
                    selected_model,
                    COUNT(*) as count,
                    AVG(quality_score) as avg_quality,
                    AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as correctness_rate
                FROM response_feedback
                WHERE selected_model IS NOT NULL
                GROUP BY selected_model
                ORDER BY count DESC
            """)

            models = cursor.fetchall()

            return FeedbackSummary(
                total_feedback=stats['total'],
                avg_quality_score=float(stats['avg_quality'] or 0),
                models=[dict(m) for m in models]
            )
        except Exception as e:
            # Table doesn't exist yet - return empty stats
            logger.warning(f"Feedback table not found: {e}")
            return FeedbackSummary(
                total_feedback=0,
                avg_quality_score=0.0,
                models=[]
            )


@app.get("/admin/learning/status", response_model=LearningStatus)
async def get_learning_status():
    """Get learning pipeline status."""
    with get_connection() as conn:
        cursor = get_cursor(conn, dict_cursor=True)

        try:
            # Get last run from performance history
            cursor.execute("""
                SELECT
                    retraining_run_id,
                    MAX(updated_at) as last_run
                FROM model_performance_history
                GROUP BY retraining_run_id
                ORDER BY last_run DESC
                LIMIT 1
            """)

            last_run = cursor.fetchone()

            # Get confidence distribution
            cursor.execute("""
                SELECT
                    confidence_level,
                    COUNT(DISTINCT pattern) as count
                FROM model_performance_history
                WHERE retraining_run_id = (
                    SELECT retraining_run_id
                    FROM model_performance_history
                    ORDER BY updated_at DESC
                    LIMIT 1
                )
                GROUP BY confidence_level
            """)

            conf_dist = {row['confidence_level']: row['count'] for row in cursor.fetchall()}

            return LearningStatus(
                last_retraining_run=last_run['last_run'].isoformat() if last_run else None,
                next_scheduled_run=None,  # TODO: Add scheduler info
                confidence_distribution={
                    'high': conf_dist.get('high', 0),
                    'medium': conf_dist.get('medium', 0),
                    'low': conf_dist.get('low', 0)
                },
                total_patterns=sum(conf_dist.values())
            )
        except Exception as e:
            # Table doesn't exist yet - return empty status
            logger.warning(f"Performance history table not found: {e}")
            return LearningStatus(
                last_retraining_run=None,
                next_scheduled_run=None,
                confidence_distribution={'high': 0, 'medium': 0, 'low': 0},
                total_patterns=0
            )


@app.post("/admin/learning/retrain", response_model=RetrainingResult)
async def trigger_retraining(dry_run: bool = True):
    """Manually trigger retraining.

    Args:
        dry_run: If True, preview changes without applying

    Returns:
        Retraining result summary
    """
    if scheduler:
        result = scheduler.trigger_immediate_retraining(dry_run=dry_run)
    else:
        result = feedback_trainer.retrain(dry_run=dry_run)

    return RetrainingResult(**result)


@app.get("/admin/performance/trends", response_model=PerformanceTrends)
async def get_performance_trends(pattern: str):
    """Get performance trends for a pattern.

    Args:
        pattern: Pattern to analyze (e.g., 'code', 'explanation')

    Returns:
        Performance trends over time
    """
    with get_connection() as conn:
        cursor = get_cursor(conn, dict_cursor=True)
        is_sqlite = _is_sqlite(conn)
        placeholder = '?' if is_sqlite else '%s'

        try:
            query = f"""
                SELECT
                    model,
                    avg_quality_score,
                    correctness_rate,
                    sample_count,
                    confidence_level,
                    updated_at
                FROM model_performance_history
                WHERE pattern = {placeholder}
                ORDER BY updated_at DESC
                LIMIT 20
            """
            cursor.execute(query, (pattern,))

            trends = cursor.fetchall()

            return PerformanceTrends(
                pattern=pattern,
                trends=[dict(t) for t in trends]
            )
        except Exception as e:
            # Table doesn't exist yet - return empty trends
            logger.warning(f"Performance history table not found: {e}")
            return PerformanceTrends(
                pattern=pattern,
                trends=[]
            )


# Run the application
if __name__ == "__main__":
    import uvicorn

    # Check if any providers are available
    if not providers:
        logger.error(
            "No providers configured! Please set at least one API key:\n"
            "  - GOOGLE_API_KEY for Gemini\n"
            "  - ANTHROPIC_API_KEY for Claude\n"
            "  - OPENROUTER_API_KEY for OpenRouter"
        )
        exit(1)

    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting AI Cost Optimizer on port {port}")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
