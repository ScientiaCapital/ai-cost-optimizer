import httpx
from typing import List
from . import LLMProvider, ModelInfo, CompletionResponse

class OllamaProvider(LLMProvider):
    """Local Ollama provider - free, runs on your machine"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Local models = free
        self.pricing = {
            "llama2": (0.0, 0.0),
            "llama3": (0.0, 0.0),
            "mistral": (0.0, 0.0),
            "codellama": (0.0, 0.0),
            "phi": (0.0, 0.0),
        }
    
    async def complete(self, model: str, prompt: str, max_tokens: int, **kwargs) -> CompletionResponse:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": kwargs.get("temperature", 0.7)
            }
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        # Ollama doesn't provide exact token counts, estimate
        input_tokens = len(prompt.split()) * 1.3
        output_tokens = len(data['response'].split()) * 1.3
        
        return CompletionResponse(
            content=data['response'],
            model=model,
            provider="ollama",
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            cost=0.0  # Local = free
        )
    
    async def get_available_models(self) -> List[ModelInfo]:
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            data = response.json()
            return [
                ModelInfo(id=m['name'], provider="ollama", input_price=0.0,
                         output_price=0.0, context_window=4096)
                for m in data.get('models', [])
            ]
        except:
            return []  # Ollama not running
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        return 0.0  # Always free
