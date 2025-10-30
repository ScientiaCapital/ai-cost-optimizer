"""Routing logic for selecting optimal model based on complexity."""
from typing import Tuple, Dict, Any
from .providers import (
    GeminiProvider, ClaudeProvider, OpenRouterProvider,
    CerebrasProvider, OllamaProvider
)


class RoutingError(Exception):
    """Error during routing or execution."""
    pass


class Router:
    """Routes prompts to optimal provider based on complexity."""

    def __init__(self, providers: Dict[str, Any]):
        """
        Initialize router with available providers.

        Args:
            providers: Dictionary of {provider_name: provider_instance}
        """
        self.providers = providers

    def select_provider(self, complexity: str) -> Tuple[str, str, Any]:
        """
        Select optimal provider and model based on complexity.

        Priority for simple queries:
        1. Ollama (free, local)
        2. Cerebras (ultra-fast, cheap)
        3. Gemini (free tier, good quality)
        4. OpenRouter (fallback)

        Priority for complex queries:
        1. Claude Haiku (best quality/cost)
        2. Cerebras 70B (fast, decent quality)
        3. OpenRouter (fallback)

        Args:
            complexity: Classification from complexity scorer (simple/complex)

        Returns:
            Tuple of (provider_name, model_name, provider_instance)

        Raises:
            RoutingError: If no suitable provider is available
        """
        # Simple queries: Prioritize free/cheap
        if complexity == "simple":
            # 1. Ollama - FREE and local
            if "ollama" in self.providers:
                return ("ollama", "llama3", self.providers["ollama"])

            # 2. Cerebras - Ultra-fast and cheap
            if "cerebras" in self.providers:
                return ("cerebras", "llama3.1-8b", self.providers["cerebras"])

            # 3. Gemini - Free tier
            if "gemini" in self.providers:
                return ("gemini", "gemini-1.5-flash", self.providers["gemini"])

            # 4. OpenRouter fallback
            if "openrouter" in self.providers:
                return ("openrouter", "google/gemini-flash-1.5", self.providers["openrouter"])

        # Complex queries: Prioritize quality
        if complexity == "complex":
            # 1. Claude Haiku - Best quality/cost balance
            if "claude" in self.providers:
                return ("claude", "claude-3-haiku-20240307", self.providers["claude"])

            # 2. Cerebras 70B - Fast with decent quality
            if "cerebras" in self.providers:
                return ("cerebras", "llama3.1-70b", self.providers["cerebras"])

            # 3. OpenRouter fallback
            if "openrouter" in self.providers:
                return ("openrouter", "anthropic/claude-3-haiku", self.providers["openrouter"])

        # No suitable provider available
        available = list(self.providers.keys())
        raise RoutingError(
            f"No suitable provider available for complexity '{complexity}'. "
            f"Available providers: {available}"
        )

    async def route_and_complete(
        self,
        prompt: str,
        complexity: str,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Route prompt to provider and execute completion.

        Args:
            prompt: User's prompt
            complexity: Complexity classification
            max_tokens: Maximum response tokens

        Returns:
            Dictionary with response data and metadata

        Raises:
            RoutingError: If routing or execution fails
        """
        try:
            # Select provider
            provider_name, model_name, provider = self.select_provider(complexity)

            # Execute completion
            if provider_name == "openrouter":
                # OpenRouter needs model parameter
                response, tokens_in, tokens_out, cost = await provider.complete(
                    model=model_name,
                    prompt=prompt,
                    max_tokens=max_tokens
                )
            else:
                # Direct providers (Gemini, Claude)
                response, tokens_in, tokens_out, cost = await provider.complete(
                    prompt=prompt,
                    max_tokens=max_tokens
                )

            return {
                "response": response,
                "provider": provider_name,
                "model": model_name,
                "complexity": complexity,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost": cost
            }

        except Exception as e:
            raise RoutingError(f"Failed to complete request: {str(e)}")

    def get_routing_info(self, complexity: str) -> Dict[str, Any]:
        """
        Get routing information without executing request.

        Useful for previewing which model would be selected.

        Args:
            complexity: Complexity classification

        Returns:
            Dictionary with provider, model, and reasoning
        """
        try:
            provider_name, model_name, provider = self.select_provider(complexity)

            # Get cost estimates (per 1M tokens)
            cost_map = {
                "ollama": {"input_per_1m": "FREE (local)", "output_per_1m": "FREE (local)"},
                "cerebras": {"input_per_1m": "$0.10", "output_per_1m": "$0.10"},
                "gemini": {"input_per_1m": "$0.075", "output_per_1m": "$0.30"},
                "claude": {"input_per_1m": "$0.25", "output_per_1m": "$1.25"},
                "openrouter": {"input_per_1m": "Varies by model", "output_per_1m": "Varies by model"}
            }
            cost_info = cost_map.get(provider_name, {"input_per_1m": "Unknown", "output_per_1m": "Unknown"})

            return {
                "provider": provider_name,
                "model": model_name,
                "complexity": complexity,
                "reasoning": self._get_routing_reasoning(complexity),
                "pricing": cost_info
            }

        except RoutingError as e:
            return {
                "error": str(e),
                "complexity": complexity
            }

    def _get_routing_reasoning(self, complexity: str) -> str:
        """Get human-readable explanation for routing decision."""
        if complexity == "simple":
            # Check which provider is actually available
            if "ollama" in self.providers:
                return (
                    "Simple query detected (< 100 tokens, no complexity keywords). "
                    "Using Ollama for FREE local inference."
                )
            elif "cerebras" in self.providers:
                return (
                    "Simple query detected (< 100 tokens, no complexity keywords). "
                    "Using Cerebras for ultra-fast, cheap inference."
                )
            else:
                return (
                    "Simple query detected (< 100 tokens, no complexity keywords). "
                    "Using Gemini Flash for cost efficiency (free tier available)."
                )
        else:
            # Complex queries
            if "claude" in self.providers:
                return (
                    "Complex query detected (long prompt or complexity keywords). "
                    "Using Claude Haiku for best quality/cost balance."
                )
            elif "cerebras" in self.providers:
                return (
                    "Complex query detected (long prompt or complexity keywords). "
                    "Using Cerebras Llama 70B for fast, decent quality."
                )
            else:
                return (
                    "Complex query detected (long prompt or complexity keywords). "
                    "Using available provider for better reasoning."
                )
