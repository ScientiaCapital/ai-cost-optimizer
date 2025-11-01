"""Service layer for intelligent routing."""
import hashlib
import logging
from typing import Dict, Any

from app.routing.engine import RoutingEngine
from app.routing.models import RoutingContext
from app.database import CostTracker

logger = logging.getLogger(__name__)


class RoutingService:
    """FastAPI service layer for intelligent routing.

    Bridges FastAPI endpoints and RoutingEngine, handling:
    - Cache integration
    - Provider execution
    - Cost tracking
    - Response formatting
    """

    def __init__(self, db_path: str, providers: Dict[str, Any]):
        """Initialize routing service.

        Args:
            db_path: Path to SQLite database
            providers: Dictionary of initialized provider clients
        """
        self.engine = RoutingEngine(db_path=db_path, track_metrics=True)
        self.providers = providers
        self.cost_tracker = CostTracker(db_path=db_path)

        logger.info(f"RoutingService initialized with {len(providers)} providers")

    async def route_and_complete(
        self,
        prompt: str,
        auto_route: bool,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Route prompt and execute completion with cache check.

        Args:
            prompt: User prompt to route
            auto_route: If True, use intelligent hybrid routing
            max_tokens: Maximum response tokens

        Returns:
            Dict with response, provider, model, cost, and metadata
        """
        # Check cache first
        cached = self.cost_tracker.check_cache(prompt, max_tokens)

        if cached:
            logger.info(f"Cache HIT: {cached['cache_key'][:16]}...")

            # Record cache hit
            self.cost_tracker.record_cache_hit(cached["cache_key"])

            # Log as request with $0 cost
            self.cost_tracker.log_request(
                prompt=prompt,
                complexity=cached["complexity"],
                provider="cache",
                model=cached["model"],
                tokens_in=0,
                tokens_out=0,
                cost=0.0
            )

            total_cost = self.cost_tracker.get_total_cost()

            return {
                "response": cached["response"],
                "provider": cached["provider"],
                "model": cached["model"],
                "strategy_used": "cached",
                "confidence": "high",
                "complexity_metadata": {
                    "cached": True,
                    "original_timestamp": cached["created_at"]
                },
                "tokens_in": cached["tokens_in"],
                "tokens_out": cached["tokens_out"],
                "cost": 0.0,
                "total_cost_today": total_cost,
                "cache_hit": True,
                "original_cost": cached["cost"],
                "savings": cached["cost"],
                "cache_key": cached["cache_key"],
                "routing_metadata": {}
            }

        # Cache miss - proceed with routing
        logger.info("Cache MISS: routing to provider")

        # Get routing decision from engine
        context = RoutingContext(prompt=prompt)
        decision = self.engine.route(prompt=prompt, auto_route=auto_route, context=context)

        # Execute with selected provider
        provider = self.providers[decision.provider]
        response = await provider.send_message(prompt, max_tokens=max_tokens)

        # Extract response data
        response_text = response.get("response", response.get("text", ""))
        tokens_in = response.get("tokens_in", response.get("usage", {}).get("input_tokens", 0))
        tokens_out = response.get("tokens_out", response.get("usage", {}).get("output_tokens", 0))
        cost = response.get("cost", 0.0)

        # Store in cache
        self.cost_tracker.store_in_cache(
            prompt=prompt,
            max_tokens=max_tokens,
            response=response_text,
            provider=decision.provider,
            model=decision.model,
            complexity="unknown",  # Will be set by engine in future
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost
        )

        # Log to database
        self.cost_tracker.log_request(
            prompt=prompt,
            complexity="unknown",
            provider=decision.provider,
            model=decision.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost
        )

        total_cost = self.cost_tracker.get_total_cost()

        # Generate cache key directly (avoid private method access)
        normalized = " ".join(prompt.split())
        cache_key = hashlib.sha256(f"{normalized}|{max_tokens}".encode()).hexdigest()

        return {
            "response": response_text,
            "provider": decision.provider,
            "model": decision.model,
            "strategy_used": decision.strategy_used,
            "confidence": decision.confidence,
            "complexity_metadata": decision.metadata,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": cost,
            "total_cost_today": total_cost,
            "cache_hit": False,
            "original_cost": None,
            "savings": 0.0,
            "cache_key": cache_key,
            "routing_metadata": decision.metadata
        }

    def get_recommendation(self, prompt: str) -> Dict[str, Any]:
        """Get routing recommendation without execution.

        Args:
            prompt: User prompt to analyze

        Returns:
            Dict with provider, model, strategy, confidence, metadata
        """
        # Get routing decision using hybrid strategy
        context = RoutingContext(prompt=prompt)
        decision = self.engine.route(prompt=prompt, auto_route=True, context=context)

        return {
            "provider": decision.provider,
            "model": decision.model,
            "strategy_used": decision.strategy_used,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "metadata": decision.metadata
        }

    def get_routing_metrics(self) -> Dict[str, Any]:
        """Get routing performance metrics.

        Returns:
            Dict with strategy performance, decision counts, confidence distribution
        """
        return self.engine.metrics.get_metrics()
