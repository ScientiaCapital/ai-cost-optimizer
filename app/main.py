"""FastAPI service for AI Cost Optimizer."""
import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .complexity import score_complexity, get_complexity_metadata
from .providers import init_providers
from .router import Router, RoutingError
from .database import CostTracker

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global components
providers = init_providers()
router = Router(providers)
cost_tracker = CostTracker(db_path=os.getenv("DATABASE_PATH", "optimizer.db"))

logger.info(f"AI Cost Optimizer initialized with providers: {list(providers.keys())}")


# Request/Response models
class CompleteRequest(BaseModel):
    """Request model for completion endpoint."""
    prompt: str = Field(..., min_length=1, description="User prompt")
    max_tokens: Optional[int] = Field(1000, ge=1, le=4000, description="Maximum response tokens")


class CompleteResponse(BaseModel):
    """Response model for completion endpoint."""
    response: str
    provider: str
    model: str
    complexity: str
    complexity_metadata: dict
    tokens_in: int
    tokens_out: int
    cost: float
    total_cost_today: float
    cache_hit: bool = False
    original_cost: Optional[float] = None
    savings: float = 0.0
    cache_key: Optional[str] = None


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
    2. Analyzes prompt complexity (if cache miss)
    3. Routes to appropriate model (if cache miss)
    4. Executes completion (if cache miss)
    5. Stores response in cache (if cache miss)
    6. Tracks cost in database

    Args:
        request: CompleteRequest with prompt and optional max_tokens

    Returns:
        CompleteResponse with response text, metadata, and cost

    Raises:
        HTTPException: If routing or completion fails
    """
    try:
        # ========== CACHE LOOKUP ==========
        cached = cost_tracker.check_cache(request.prompt, request.max_tokens)

        if cached:
            # Cache hit! Return instant response with $0 cost
            logger.info(f"Cache HIT: {cached['cache_key'][:16]}... (hit_count={cached['hit_count']})")

            # Record cache hit
            cost_tracker.record_cache_hit(cached["cache_key"])

            # Log as a request with cost=$0
            cost_tracker.log_request(
                prompt=request.prompt,
                complexity=cached["complexity"],
                provider="cache",
                model=cached["model"],
                tokens_in=0,
                tokens_out=0,
                cost=0.0
            )

            total_cost = cost_tracker.get_total_cost()

            return CompleteResponse(
                response=cached["response"],
                provider=cached["provider"],
                model=cached["model"],
                complexity=cached["complexity"],
                complexity_metadata={"cached": True, "original_timestamp": cached["created_at"]},
                tokens_in=cached["tokens_in"],
                tokens_out=cached["tokens_out"],
                cost=0.0,
                total_cost_today=total_cost,
                cache_hit=True,
                original_cost=cached["cost"],
                savings=cached["cost"],
                cache_key=cached["cache_key"]
            )

        # ========== CACHE MISS - NORMAL FLOW ==========
        logger.info("Cache MISS: routing to LLM provider")

        # Analyze complexity
        complexity = score_complexity(request.prompt)
        complexity_metadata = get_complexity_metadata(request.prompt)

        logger.info(
            f"Processing request: complexity={complexity}, "
            f"tokens={complexity_metadata['token_count']}"
        )

        # Route and execute
        result = await router.route_and_complete(
            prompt=request.prompt,
            complexity=complexity,
            max_tokens=request.max_tokens
        )

        # Store in cache for future use
        cost_tracker.store_in_cache(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            response=result["response"],
            provider=result["provider"],
            model=result["model"],
            complexity=complexity,
            tokens_in=result["tokens_in"],
            tokens_out=result["tokens_out"],
            cost=result["cost"]
        )

        # Log to database
        cost_tracker.log_request(
            prompt=request.prompt,
            complexity=complexity,
            provider=result["provider"],
            model=result["model"],
            tokens_in=result["tokens_in"],
            tokens_out=result["tokens_out"],
            cost=result["cost"]
        )

        # Get updated total cost
        total_cost = cost_tracker.get_total_cost()

        logger.info(
            f"Completed: provider={result['provider']}, "
            f"cost=${result['cost']:.6f}, total=${total_cost:.2f}, cached=True"
        )

        # Generate cache key for feedback
        cache_key = cost_tracker._generate_cache_key(request.prompt, request.max_tokens)

        return CompleteResponse(
            response=result["response"],
            provider=result["provider"],
            model=result["model"],
            complexity=complexity,
            complexity_metadata=complexity_metadata,
            tokens_in=result["tokens_in"],
            tokens_out=result["tokens_out"],
            cost=result["cost"],
            total_cost_today=total_cost,
            cache_hit=False,
            original_cost=None,
            savings=0.0,
            cache_key=cache_key
        )

    except RoutingError as e:
        logger.error(f"Routing error: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))

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

    Useful for previewing which model would be selected.

    Args:
        prompt: User prompt (query parameter)

    Returns:
        Routing information with provider, model, and reasoning
    """
    try:
        complexity = score_complexity(prompt)
        complexity_metadata = get_complexity_metadata(prompt)
        routing_info = router.get_routing_info(complexity)

        return {
            "complexity": complexity,
            "complexity_metadata": complexity_metadata,
            **routing_info
        }

    except Exception as e:
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
