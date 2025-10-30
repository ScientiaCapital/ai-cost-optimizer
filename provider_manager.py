from typing import Dict, List, Optional
from providers import LLMProvider, CompletionResponse, ModelInfo
from providers.openrouter import OpenRouterProvider
from providers.anthropic_provider import AnthropicProvider
from providers.google_provider import GoogleProvider
from providers.cerebras_provider import CerebrasProvider
from providers.deepseek_provider import DeepseekProvider
from providers.huggingface_provider import HuggingFaceProvider
import config

class ProviderManager:
    """Manages all LLM providers"""
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured providers"""
        provider_configs = config.PROVIDER_CONFIGS
        
        for provider_name, cfg in provider_configs.items():
            if not cfg.get("enabled", False):
                continue
            
            api_key = cfg.get("api_key")
            if not api_key:
                continue
            
            try:
                if provider_name == "openrouter":
                    self.providers[provider_name] = OpenRouterProvider(api_key)
                elif provider_name == "anthropic":
                    self.providers[provider_name] = AnthropicProvider(api_key)
                elif provider_name == "google":
                    self.providers[provider_name] = GoogleProvider(api_key)
                elif provider_name == "cerebras":
                    self.providers[provider_name] = CerebrasProvider(api_key)
                elif provider_name == "deepseek":
                    self.providers[provider_name] = DeepseekProvider(api_key)
                elif provider_name == "huggingface":
                    self.providers[provider_name] = HuggingFaceProvider(api_key)
            except Exception as e:
                print(f"Failed to initialize {provider_name}: {e}")
    
    async def complete(self, provider: str, model: str, prompt: str, 
                      max_tokens: int, **kwargs) -> CompletionResponse:
        """Route completion to specific provider"""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not available")
        
        return await self.providers[provider].complete(model, prompt, max_tokens, **kwargs)
    
    async def get_all_models(self) -> List[ModelInfo]:
        """Get all available models from all providers"""
        all_models = []
        for provider_name, provider in self.providers.items():
            try:
                models = await provider.get_available_models()
                all_models.extend(models)
            except Exception as e:
                print(f"Error fetching models from {provider_name}: {e}")
        return all_models
    
    def get_provider_for_model(self, model_id: str) -> Optional[str]:
        """Find which provider has this model"""
        for provider_name in self.providers:
            if model_id in config.PROVIDER_MODELS.get(provider_name, []):
                return provider_name
        return None
