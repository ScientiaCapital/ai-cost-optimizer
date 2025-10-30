from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime
import uvicorn
import logging
import time
import sys
import os

from router import LLMRouter
from cost_tracker import CostTracker
from budget import BudgetManager
from provider_manager import ProviderManager

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # Log to file if /data directory exists (production)
        *([logging.FileHandler('/data/app.log')] if os.path.exists('/data') else [])
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Cost Optimizer",
    version="1.0.0",
    description="Multi-LLM routing with cost optimization and budget management"
)

# Add CORS middleware for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"Status: {response.status_code} Duration: {duration:.3f}s"
        )

        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Error: {request.method} {request.url.path} "
            f"Error: {str(e)} Duration: {duration:.3f}s"
        )
        raise

# Initialize components
provider_manager = ProviderManager()
router = LLMRouter(provider_manager)
cost_tracker = CostTracker()
budget_manager = BudgetManager()

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 1000
    budget_limit: Optional[float] = None
    user_id: Optional[str] = "default"
    provider: Optional[str] = None  # Force specific provider
    model: Optional[str] = None  # Force specific model

class CompletionResponse(BaseModel):
    response: str
    provider: str
    model_used: str
    cost: float
    complexity_score: float
    prompt_tokens: int
    completion_tokens: int

class BudgetRequest(BaseModel):
    monthly_limit: float
    alert_thresholds: Optional[list[float]] = None
    user_id: Optional[str] = "default"

@app.post("/v1/complete", response_model=CompletionResponse)
async def complete(request: CompletionRequest):
    """Route and complete LLM request across multiple providers"""
    try:
        # Route request or use forced provider/model
        if request.model and request.provider:
            provider, model, complexity = request.provider, request.model, 0.5
        else:
            provider, model, complexity = await router.route_request(
                request.prompt, request.budget_limit
            )
        
        # Check budget (estimate)
        input_tokens = cost_tracker.count_tokens(request.prompt)
        provider_obj = provider_manager.providers[provider]
        estimated_cost = Decimal(str(provider_obj.calculate_cost(model, input_tokens, request.max_tokens)))
        
        if not budget_manager.check_budget(request.user_id, estimated_cost):
            raise HTTPException(status_code=402, detail=f"Budget exceeded: ${estimated_cost}")
        
        # Send request
        result = await provider_manager.complete(
            provider, model, request.prompt, request.max_tokens
        )
        
        # Track and record
        cost_tracker.track_request({
            "user_id": request.user_id,
            "provider": provider,
            "model": model,
            "prompt_tokens": result.input_tokens,
            "completion_tokens": result.output_tokens,
            "cost": result.cost,
            "complexity": complexity
        })
        
        budget_manager.record_spend(request.user_id, Decimal(str(result.cost)))
        
        return CompletionResponse(
            response=result.content,
            provider=result.provider,
            model_used=result.model,
            cost=result.cost,
            complexity_score=complexity,
            prompt_tokens=result.input_tokens,
            completion_tokens=result.output_tokens
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/usage")
async def get_usage(user_id: str = "default", days: int = 30):
    """Get usage statistics"""
    usage = cost_tracker.get_usage(user_id, days)
    remaining = budget_manager.get_remaining_budget(user_id)
    
    return {
        **usage,
        "remaining_budget": float(remaining)
    }

@app.post("/v1/budget")
async def set_budget(request: BudgetRequest):
    """Set budget and alerts"""
    budget_manager.set_budget(
        request.user_id,
        Decimal(str(request.monthly_limit)),
        request.alert_thresholds
    )
    return {"status": "success", "user_id": request.user_id}

@app.get("/v1/models")
async def list_models():
    """List all available models across providers"""
    models = await provider_manager.get_all_models()
    return {
        "models": [
            {
                "id": m.id,
                "provider": m.provider,
                "input_price": m.input_price,
                "output_price": m.output_price,
                "context_window": m.context_window
            } for m in models
        ]
    }

@app.get("/v1/providers")
async def list_providers():
    """List enabled providers"""
    return {
        "providers": list(provider_manager.providers.keys()),
        "count": len(provider_manager.providers)
    }

@app.get("/")
async def root():
    return {
        "name": "AI Cost Optimizer - Multi-LLM Router",
        "version": "1.0.0",
        "providers": list(provider_manager.providers.keys()),
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    try:
        # Check if we have at least one provider available
        if not provider_manager.providers:
            return {
                "status": "unhealthy",
                "error": "No providers configured",
                "timestamp": datetime.now().isoformat()
            }

        return {
            "status": "healthy",
            "version": "1.0.0",
            "providers": list(provider_manager.providers.keys()),
            "provider_count": len(provider_manager.providers),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    try:
        # Get basic stats from cost tracker
        total_requests = getattr(cost_tracker, 'total_requests', 0)
        total_cost = getattr(cost_tracker, 'total_cost', 0.0)

        return {
            "requests_total": total_requests,
            "cost_total_usd": float(total_cost),
            "providers_active": len(provider_manager.providers),
            "providers_list": list(provider_manager.providers.keys()),
            "uptime_seconds": time.time() - getattr(app.state, 'start_time', time.time()),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Metrics error: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    app.state.start_time = time.time()
    logger.info("AI Cost Optimizer started")
    logger.info(f"Providers enabled: {list(provider_manager.providers.keys())}")
    logger.info(f"Total providers: {len(provider_manager.providers)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("AI Cost Optimizer shutting down")

if __name__ == "__main__":
    logger.info("Starting AI Cost Optimizer in development mode")
    uvicorn.run(app, host="0.0.0.0", port=8000)
