from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ModelInfo:
    id: str
    provider: str
    input_price: float  # per 1M tokens
    output_price: float  # per 1M tokens
    context_window: int
    
@dataclass
class CompletionResponse:
    content: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost: float

class LLMProvider(ABC):
    """Base class for all LLM providers"""
    
    @abstractmethod
    async def complete(self, model: str, prompt: str, max_tokens: int, **kwargs) -> CompletionResponse:
        """Send completion request"""
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models with pricing"""
        pass
    
    @abstractmethod
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a request"""
        pass
