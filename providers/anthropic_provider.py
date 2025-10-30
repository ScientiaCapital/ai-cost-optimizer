import httpx
from typing import List
from . import LLMProvider, ModelInfo, CompletionResponse

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.client = httpx.AsyncClient()
        
        self.pricing = {
            "claude-3-5-sonnet-20241022": (3.00, 15.00),
            "claude-3-5-haiku-20241022": (1.00, 5.00),
            "claude-3-opus-20240229": (15.00, 75.00),
        }
    
    async def complete(self, model: str, prompt: str, max_tokens: int, **kwargs) -> CompletionResponse:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        
        response = await self.client.post(
            f"{self.base_url}/messages",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        input_tokens = data['usage']['input_tokens']
        output_tokens = data['usage']['output_tokens']
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        return CompletionResponse(
            content=data['content'][0]['text'],
            model=model,
            provider="anthropic",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost
        )
    
    async def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(id=model, provider="anthropic", input_price=prices[0], 
                     output_price=prices[1], context_window=200000)
            for model, prices in self.pricing.items()
        ]
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        if model not in self.pricing:
            return 0.0
        input_price, output_price = self.pricing[model]
        return (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)
