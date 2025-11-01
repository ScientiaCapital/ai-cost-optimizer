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
        fallback_used = False

        # Simple prompts → Gemini (with fallback)
        if complexity_score < 0.3:
            provider, model = self._select_simple_provider(context.available_providers)
            if (provider, model) == (None, None):
                # Fallback to any available provider
                provider, model, fallback_used = self._fallback_provider(context.available_providers)

        # Moderate prompts → Claude Haiku (with fallback)
        elif complexity_score < 0.7:
            provider, model = self._select_moderate_provider(context.available_providers)
            if (provider, model) == (None, None):
                # Fallback to any available provider
                provider, model, fallback_used = self._fallback_provider(context.available_providers)

        # Complex prompts → Claude Sonnet (with fallback)
        else:
            provider, model = self._select_complex_provider(context.available_providers)
            if (provider, model) == (None, None):
                # Fallback to any available provider
                provider, model, fallback_used = self._fallback_provider(context.available_providers)

        return RoutingDecision(
            provider=provider,
            model=model,
            confidence="medium",  # Complexity has medium confidence
            strategy_used="complexity",
            reasoning=f"Complexity score: {complexity_score:.2f}",
            fallback_used=fallback_used,
            metadata={
                "complexity": complexity_score,
                "pattern": "unknown"
            }
        )

    def _select_simple_provider(self, available_providers: list) -> tuple:
        """Select provider for simple prompts with fallback chain.

        Priority: gemini → openrouter/gemini → claude
        """
        if "gemini" in available_providers:
            return "gemini", "gemini-1.5-flash"

        if "openrouter" in available_providers:
            return "openrouter", "google/gemini-flash-1.5"

        if "claude" in available_providers:
            return "claude", "claude-3-haiku-20240307"

        return None, None

    def _select_moderate_provider(self, available_providers: list) -> tuple:
        """Select provider for moderate prompts with fallback chain.

        Priority: claude → gemini → openrouter
        """
        if "claude" in available_providers:
            return "claude", "claude-3-haiku-20240307"

        if "gemini" in available_providers:
            return "gemini", "gemini-1.5-flash"

        if "openrouter" in available_providers:
            return "openrouter", "anthropic/claude-3-haiku"

        return None, None

    def _select_complex_provider(self, available_providers: list) -> tuple:
        """Select provider for complex prompts with fallback chain.

        Priority: claude → gemini → openrouter
        """
        if "claude" in available_providers:
            return "claude", "claude-3-5-sonnet-20241022"

        if "gemini" in available_providers:
            return "gemini", "gemini-1.5-flash"

        if "openrouter" in available_providers:
            return "openrouter", "anthropic/claude-3-sonnet"

        return None, None

    def _fallback_provider(self, available_providers: list) -> tuple:
        """Last resort fallback to any available provider.

        Returns: (provider, model, fallback_used)
        """
        if not available_providers:
            raise ValueError("No providers available for routing")

        # Try providers in priority order
        if "gemini" in available_providers:
            return "gemini", "gemini-1.5-flash", True

        if "claude" in available_providers:
            return "claude", "claude-3-haiku-20240307", True

        if "openrouter" in available_providers:
            return "openrouter", "google/gemini-flash-1.5", True

        # Use first available as absolute last resort
        provider = available_providers[0]
        return provider, "default", True

    def get_name(self) -> str:
        """Return strategy name."""
        return "complexity"
