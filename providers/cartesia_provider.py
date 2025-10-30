# Note: Cartesia is a TTS (Text-to-Speech) provider, not a chat completion provider
# This is included for completeness but won't be used for LLM routing

import httpx
from typing import List
from . import LLMProvider, ModelInfo, CompletionResponse

class CartesiaProvider(LLMProvider):
    """Cartesia TTS provider - for voice generation, not text chat"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.cartesia.ai"
        self.client = httpx.AsyncClient()
        
        # TTS pricing (per character, converted to per-token equivalent)
        self.pricing = {
            "sonic-english": (0.15, 0.0),  # TTS has no output tokens
        }
    
    async def complete(self, model: str, prompt: str, max_tokens: int, **kwargs) -> CompletionResponse:
        """TTS doesn't do chat completion - this is a placeholder"""
        raise NotImplementedError("Cartesia is a TTS provider, not for text generation")
    
    async def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(id="sonic-english", provider="cartesia", input_price=0.15,
                     output_price=0.0, context_window=0)
        ]
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        # TTS pricing based on character count
        return input_tokens / 1_000_000 * 0.15
