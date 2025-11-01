"""FastAPI service for AI Cost Optimizer."""
import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .providers import init_providers
from .database import CostTracker
from app.services.routing_service import RoutingService
from .router import RoutingError  # Keep for exception handling

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Cost Optimizer",
    description="Smart multi-LLM routing for cost optimization",
    version="1.0.0"
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
        "providers_available": list(providers.keys()),
        "version": "1.0.0"
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
        stats = cost_tracker.get_usage_stats()
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
        stats = cost_tracker.get_cache_stats()
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
        cost_tracker.add_feedback(
            cache_key=request.cache_key,
            rating=request.rating,
            comment=request.comment,
            user_agent=user_agent
        )

        # Update quality score (may trigger invalidation)
        quality_score = cost_tracker.update_quality_score(request.cache_key)

        # Check if entry was invalidated
        conn = cost_tracker._CostTracker__get_connection() if hasattr(cost_tracker, '_CostTracker__get_connection') else None
        if not conn:
            import sqlite3
            conn = sqlite3.connect(cost_tracker.db_path)

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
        stats = cost_tracker.get_quality_stats()
        return stats

    except Exception as e:
        logger.error(f"Error fetching quality stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/insights")
async def get_learning_insights():
    """
    Get intelligent routing insights from learning module.

    Returns:
        Learning statistics including:
        - overall: Total queries, cache hits, rated responses
        - by_provider: Provider performance with quality and cost metrics
        - by_complexity: Performance breakdown by complexity level
        - learning_active: Whether intelligent routing has sufficient data
    """
    try:
        if not router.enable_learning or not router.analyzer:
            return {
                "learning_active": False,
                "message": "Intelligent routing not enabled. Need more historical data.",
                "overall": {
                    "unique_queries": 0,
                    "total_requests": 0,
                    "total_cache_hits": 0,
                    "rated_responses": 0,
                    "avg_quality": None
                },
                "by_provider": [],
                "by_complexity": []
            }

        insights = router.analyzer.get_insights()
        return insights

    except Exception as e:
        logger.error(f"Error fetching learning insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
