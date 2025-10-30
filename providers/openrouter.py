import httpx
from typing import List
from . import LLMProvider, ModelInfo, CompletionResponse

class OpenRouterProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.AsyncClient()
        
        self.pricing = {
            "openai/gpt-3.5-turbo": (0.50, 1.50),
            "openai/gpt-4-turbo": (10.00, 30.00),
            "openai/gpt-4": (30.00, 60.00),
            "anthropic/claude-3-sonnet": (3.00, 15.00),
            "anthropic/claude-3-opus": (15.00, 75.00),
            "google/gemini-flash-1.5": (0.35, 1.05),
            "google/gemini-pro-1.5": (3.50, 10.50),
        }
    
    async def complete(self, model: str, prompt: str, max_tokens: int, **kwargs) -> CompletionResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": kwargs.get("temperature", 0.7)
        }
        
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        usage = data['usage']
        cost = self.calculate_cost(model, usage['prompt_tokens'], usage['completion_tokens'])
        
        return CompletionResponse(
            content=data['choices'][0]['message']['content'],
            model=model,
            provider="openrouter",
            input_tokens=usage['prompt_tokens'],
            output_tokens=usage['completion_tokens'],
            cost=cost
        )
    
    async def get_available_models(self) -> List[ModelInfo]:
        models = []
        for model_id, (input_price, output_price) in self.pricing.items():
            models.append(ModelInfo(
                id=model_id,
                provider="openrouter",
                input_price=input_price,
                output_price=output_price,
                context_window=128000
            ))
        return models
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        if model not in self.pricing:
            return 0.0
        
        input_price, output_price = self.pricing[model]
        return (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)
