import httpx
from typing import List
from . import LLMProvider, ModelInfo, CompletionResponse

class HuggingFaceProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api-inference.huggingface.co/models"
        self.client = httpx.AsyncClient()
        
        # HF pricing varies, these are estimates for serverless
        self.pricing = {
            "mistralai/Mistral-7B-Instruct-v0.2": (0.05, 0.05),
            "meta-llama/Llama-2-70b-chat-hf": (0.50, 0.50),
            "bigcode/starcoder": (0.10, 0.10),
        }
    
    async def complete(self, model: str, prompt: str, max_tokens: int, **kwargs) -> CompletionResponse:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": kwargs.get("temperature", 0.7)
            }
        }
        
        response = await self.client.post(
            f"{self.base_url}/{model}",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        content = data[0]['generated_text'] if isinstance(data, list) else data.get('generated_text', '')
        
        # Estimate tokens (HF doesn't always return counts)
        input_tokens = len(prompt.split()) * 1.3
        output_tokens = len(content.split()) * 1.3
        
        return CompletionResponse(
            content=content,
            model=model,
            provider="huggingface",
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            cost=self.calculate_cost(model, int(input_tokens), int(output_tokens))
        )
    
    async def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(id=model, provider="huggingface", input_price=prices[0],
                     output_price=prices[1], context_window=4096)
            for model, prices in self.pricing.items()
        ]
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        if model not in self.pricing:
            return (input_tokens + output_tokens) / 1_000_000 * 0.05  # Default estimate
        input_price, output_price = self.pricing[model]
        return (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)
