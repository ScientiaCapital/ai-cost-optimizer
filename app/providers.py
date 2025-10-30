"""LLM provider implementations for Gemini, Claude, and OpenRouter."""
import os
from typing import Tuple
import httpx


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class GeminiProvider:
    """Google Gemini provider using direct API."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    MODEL = "gemini-1.5-flash"

    # Pricing per 1M tokens (as of 2024)
    INPUT_PRICE = 0.075  # $0.075 per 1M input tokens
    OUTPUT_PRICE = 0.30  # $0.30 per 1M output tokens

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def complete(self, prompt: str, max_tokens: int = 1000) -> Tuple[str, int, int, float]:
        """
        Send completion request to Gemini.

        Returns:
            Tuple of (response_text, input_tokens, output_tokens, cost)
        """
        url = f"{self.BASE_URL}/models/{self.MODEL}:generateContent?key={self.api_key}"

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.7
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                # Extract response text
                if "candidates" not in data or not data["candidates"]:
                    raise ProviderError("No response from Gemini")

                text = data["candidates"][0]["content"]["parts"][0]["text"]

                # Extract token usage
                usage = data.get("usageMetadata", {})
                input_tokens = usage.get("promptTokenCount", 0)
                output_tokens = usage.get("candidatesTokenCount", 0)

                # Calculate cost
                cost = self.calculate_cost(input_tokens, output_tokens)

                return text, input_tokens, output_tokens, cost

            except httpx.HTTPError as e:
                raise ProviderError(f"Gemini API error: {str(e)}")

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage."""
        input_cost = (input_tokens / 1_000_000) * self.INPUT_PRICE
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_PRICE
        return input_cost + output_cost


class ClaudeProvider:
    """Anthropic Claude provider using direct API."""

    BASE_URL = "https://api.anthropic.com/v1"
    MODEL = "claude-3-haiku-20240307"

    # Pricing per 1M tokens
    INPUT_PRICE = 0.25   # $0.25 per 1M input tokens
    OUTPUT_PRICE = 1.25  # $1.25 per 1M output tokens

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def complete(self, prompt: str, max_tokens: int = 1000) -> Tuple[str, int, int, float]:
        """
        Send completion request to Claude.

        Returns:
            Tuple of (response_text, input_tokens, output_tokens, cost)
        """
        url = f"{self.BASE_URL}/messages"

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.MODEL,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                # Extract response text
                text = data["content"][0]["text"]

                # Extract token usage
                usage = data["usage"]
                input_tokens = usage["input_tokens"]
                output_tokens = usage["output_tokens"]

                # Calculate cost
                cost = self.calculate_cost(input_tokens, output_tokens)

                return text, input_tokens, output_tokens, cost

            except httpx.HTTPError as e:
                raise ProviderError(f"Claude API error: {str(e)}")

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage."""
        input_cost = (input_tokens / 1_000_000) * self.INPUT_PRICE
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_PRICE
        return input_cost + output_cost


class OpenRouterProvider:
    """OpenRouter provider for fallback and alternative models."""

    BASE_URL = "https://openrouter.ai/api/v1"

    # Model-specific pricing (per 1M tokens)
    MODEL_PRICING = {
        "google/gemini-flash-1.5": {"input": 0.075, "output": 0.30},
        "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
        "anthropic/claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    }

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def complete(self, model: str, prompt: str, max_tokens: int = 1000) -> Tuple[str, int, int, float]:
        """
        Send completion request to OpenRouter.

        Args:
            model: Model identifier (e.g., "google/gemini-flash-1.5")
            prompt: User prompt
            max_tokens: Maximum response tokens

        Returns:
            Tuple of (response_text, input_tokens, output_tokens, cost)
        """
        url = f"{self.BASE_URL}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                # Extract response text
                text = data["choices"][0]["message"]["content"]

                # Extract token usage
                usage = data["usage"]
                input_tokens = usage["prompt_tokens"]
                output_tokens = usage["completion_tokens"]

                # Calculate cost
                cost = self.calculate_cost(model, input_tokens, output_tokens)

                return text, input_tokens, output_tokens, cost

            except httpx.HTTPError as e:
                raise ProviderError(f"OpenRouter API error: {str(e)}")

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on model and token usage."""
        pricing = self.MODEL_PRICING.get(model, {"input": 0, "output": 0})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost


class CerebrasProvider:
    """Cerebras provider - fastest inference (1000+ tokens/sec)."""

    BASE_URL = "https://api.cerebras.ai/v1"
    MODEL = "llama3.1-8b"  # Default to fastest, cheapest model

    # Pricing per 1M tokens
    MODEL_PRICING = {
        "llama3.1-8b": {"input": 0.10, "output": 0.10},
        "llama3.1-70b": {"input": 0.60, "output": 0.60},
    }

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def complete(self, prompt: str, max_tokens: int = 1000, model: str = None) -> Tuple[str, int, int, float]:
        """
        Send completion request to Cerebras.

        Returns:
            Tuple of (response_text, input_tokens, output_tokens, cost)
        """
        url = f"{self.BASE_URL}/chat/completions"
        model = model or self.MODEL

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                # Extract response text
                text = data["choices"][0]["message"]["content"]

                # Extract token usage
                usage = data["usage"]
                input_tokens = usage["prompt_tokens"]
                output_tokens = usage["completion_tokens"]

                # Calculate cost
                cost = self.calculate_cost(model, input_tokens, output_tokens)

                return text, input_tokens, output_tokens, cost

            except httpx.HTTPError as e:
                raise ProviderError(f"Cerebras API error: {str(e)}")

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on model and token usage."""
        pricing = self.MODEL_PRICING.get(model, {"input": 0.10, "output": 0.10})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost


class OllamaProvider:
    """Ollama provider - local models, completely free."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    async def complete(self, prompt: str, max_tokens: int = 1000, model: str = "llama3") -> Tuple[str, int, int, float]:
        """
        Send completion request to Ollama.

        Returns:
            Tuple of (response_text, input_tokens, output_tokens, cost)
        """
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7
            }
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                # Extract response text
                text = data["response"]

                # Ollama doesn't provide exact token counts, estimate
                input_tokens = int(len(prompt.split()) * 1.3)
                output_tokens = int(len(text.split()) * 1.3)

                # Local models are free
                cost = 0.0

                return text, input_tokens, output_tokens, cost

            except httpx.HTTPError as e:
                raise ProviderError(f"Ollama API error: {str(e)}")

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Local models are always free."""
        return 0.0


def init_providers() -> dict:
    """
    Initialize available providers based on environment variables.

    Returns:
        Dictionary of {provider_name: provider_instance}
    """
    providers = {}

    # Primary providers
    if api_key := os.getenv("GOOGLE_API_KEY"):
        providers["gemini"] = GeminiProvider(api_key)

    if api_key := os.getenv("ANTHROPIC_API_KEY"):
        providers["claude"] = ClaudeProvider(api_key)

    # Ultra-fast providers
    if api_key := os.getenv("CEREBRAS_API_KEY"):
        providers["cerebras"] = CerebrasProvider(api_key)

    # Local/self-hosted (only if BASE_URL is set)
    if os.getenv("OLLAMA_BASE_URL"):
        providers["ollama"] = OllamaProvider()

    # Fallback aggregator
    if api_key := os.getenv("OPENROUTER_API_KEY"):
        providers["openrouter"] = OpenRouterProvider(api_key)

    return providers
