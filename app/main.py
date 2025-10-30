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


class StatsResponse(BaseModel):
    """Response model for stats endpoint."""
    overall: dict
    by_provider: list
    by_complexity: list
    recent_requests: list


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
    Route and complete a prompt using optimal provider.

    This is the main endpoint that:
    1. Analyzes prompt complexity
    2. Routes to appropriate model
    3. Executes completion
    4. Tracks cost in database

    Args:
        request: CompleteRequest with prompt and optional max_tokens

    Returns:
        CompleteResponse with response text, metadata, and cost

    Raises:
        HTTPException: If routing or completion fails
    """
    try:
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
            f"cost=${result['cost']:.6f}, total=${total_cost:.2f}"
        )

        return CompleteResponse(
            response=result["response"],
            provider=result["provider"],
            model=result["model"],
            complexity=complexity,
            complexity_metadata=complexity_metadata,
            tokens_in=result["tokens_in"],
            tokens_out=result["tokens_out"],
            cost=result["cost"],
            total_cost_today=total_cost
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
