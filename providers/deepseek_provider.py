import httpx
from typing import List
from . import LLMProvider, ModelInfo, CompletionResponse

class DeepseekProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"
        self.client = httpx.AsyncClient()
        
        self.pricing = {
            "deepseek-chat": (0.14, 0.28),
            "deepseek-coder": (0.14, 0.28),
        }
    
    async def complete(self, model: str, prompt: str, max_tokens: int, **kwargs) -> CompletionResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        usage = data['usage']
        return CompletionResponse(
            content=data['choices'][0]['message']['content'],
            model=model,
            provider="deepseek",
            input_tokens=usage['prompt_tokens'],
            output_tokens=usage['completion_tokens'],
            cost=self.calculate_cost(model, usage['prompt_tokens'], usage['completion_tokens'])
        )
    
    async def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(id=model, provider="deepseek", input_price=prices[0],
                     output_price=prices[1], context_window=32768)
            for model, prices in self.pricing.items()
        ]
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        if model not in self.pricing:
            return 0.0
        input_price, output_price = self.pricing[model]
        return (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)
