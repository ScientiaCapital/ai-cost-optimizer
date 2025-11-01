"""Routing strategies."""
from abc import ABC, abstractmethod
from app.routing.models import RoutingDecision, RoutingContext
from app.routing.complexity import score_complexity


class RoutingStrategy(ABC):
    """Abstract base for routing strategies.

    All routing strategies must implement:
    - route(): Make routing decision for a prompt
    - get_name(): Return strategy identifier for logging
    """

    @abstractmethod
    def route(self, prompt: str, context: RoutingContext) -> RoutingDecision:
        """Route prompt to optimal provider/model.

        Args:
            prompt: User's query text
            context: Additional routing context

        Returns:
            RoutingDecision with provider, model, and metadata

        Raises:
            RoutingError: If strategy cannot make decision
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return strategy identifier for logging.

        Returns:
            Strategy name (e.g., "complexity", "learning", "hybrid")
        """
        pass


class ComplexityStrategy(RoutingStrategy):
    """Complexity-based routing strategy (baseline).

    Routes based on prompt complexity analysis:
    - Simple (<0.3): Gemini Flash (cheap, fast)
    - Moderate (0.3-0.7): Claude Haiku (balanced)
    - Complex (>0.7): Claude Sonnet (high quality)
    """

    def route(self, prompt: str, context: RoutingContext) -> RoutingDecision:
        """Route based on prompt complexity."""
        complexity_score = score_complexity(prompt)

        # Simple prompts → Gemini
        if complexity_score < 0.3:
            provider, model = "gemini", "gemini-flash"

        # Moderate prompts → Claude Haiku
        elif complexity_score < 0.7:
            provider, model = "claude", "claude-3-haiku"

        # Complex prompts → Claude Sonnet
        else:
            provider, model = "claude", "claude-3-sonnet"

        return RoutingDecision(
            provider=provider,
            model=model,
            confidence="medium",  # Complexity has medium confidence
            strategy_used="complexity",
            reasoning=f"Complexity score: {complexity_score:.2f}",
            fallback_used=False,
            metadata={
                "complexity": complexity_score,
                "pattern": "unknown"
            }
        )

    def get_name(self) -> str:
        """Return strategy name."""
        return "complexity"
