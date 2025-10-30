import httpx
from typing import List
from . import LLMProvider, ModelInfo, CompletionResponse

class GoogleProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.client = httpx.AsyncClient()
        
        self.pricing = {
            "gemini-1.5-pro": (1.25, 5.00),
            "gemini-1.5-flash": (0.075, 0.30),
            "gemini-2.0-flash-exp": (0.00, 0.00),  # Free tier
        }
    
    async def complete(self, model: str, prompt: str, max_tokens: int, **kwargs) -> CompletionResponse:
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": kwargs.get("temperature", 0.7)
            }
        }
        
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        content = data['candidates'][0]['content']['parts'][0]['text']
        input_tokens = data.get('usageMetadata', {}).get('promptTokenCount', 0)
        output_tokens = data.get('usageMetadata', {}).get('candidatesTokenCount', 0)
        
        return CompletionResponse(
            content=content,
            model=model,
            provider="google",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=self.calculate_cost(model, input_tokens, output_tokens)
        )
    
    async def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(id=model, provider="google", input_price=prices[0],
                     output_price=prices[1], context_window=1000000)
            for model, prices in self.pricing.items()
        ]
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        if model not in self.pricing:
            return 0.0
        input_price, output_price = self.pricing[model]
        return (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)
