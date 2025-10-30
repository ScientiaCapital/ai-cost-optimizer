from typing import Tuple
import config

class LLMRouter:
    def __init__(self, provider_manager):
        self.provider_manager = provider_manager
        
    def analyze_complexity(self, prompt: str) -> float:
        """Analyze prompt complexity (0.0 - 1.0)"""
        score = 0.0
        
        # Length factor
        word_count = len(prompt.split())
        length_score = min(word_count / 500, 1.0)
        score += length_score * 0.3
        
        # Technical keywords
        technical_keywords = [
            'analyze', 'explain', 'compare', 'evaluate', 'design',
            'implement', 'optimize', 'algorithm', 'architecture', 'debug'
        ]
        keyword_matches = sum(1 for kw in technical_keywords if kw in prompt.lower())
        keyword_score = min(keyword_matches / 5, 1.0)
        score += keyword_score * 0.3
        
        # Structure complexity
        structure_score = 0.0
        if '?' in prompt:
            structure_score += prompt.count('?') * 0.1
        if any(char in prompt for char in ['\n', '•', '-', '*']):
            structure_score += 0.2
        structure_score = min(structure_score, 1.0)
        score += structure_score * 0.2
        
        # Specificity
        sentences = prompt.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        specificity_score = min(avg_sentence_length / 30, 1.0)
        score += specificity_score * 0.2
        
        return min(score, 1.0)
    
    def get_tier(self, complexity: float) -> str:
        """Map complexity score to cost tier"""
        for (low, high), tier in config.COMPLEXITY_TO_TIER.items():
            if low <= complexity < high:
                return tier
        return "premium"
    
    def select_model(self, complexity: float, budget_limit: float = None) -> Tuple[str, str]:
        """Select optimal provider and model based on complexity
        
        Returns: (provider, model_id)
        """
        tier = self.get_tier(complexity)
        available_models = config.MODEL_TIERS.get(tier, [])
        
        if not available_models:
            available_models = config.MODEL_TIERS["medium"]
        
        # Filter by enabled providers
        enabled_models = [
            (provider, model) for provider, model in available_models
            if provider in self.provider_manager.providers
        ]
        
        if not enabled_models:
            # Fallback to any available provider
            if self.provider_manager.providers:
                provider = list(self.provider_manager.providers.keys())[0]
                models = config.PROVIDER_MODELS.get(provider, [])
                if models:
                    return provider, models[0]
            raise ValueError("No providers available")
        
        # Return first available model in tier
        return enabled_models[0]
    
    async def route_request(self, prompt: str, budget_limit: float = None) -> Tuple[str, str, float]:
        """Route request and return (provider, model, complexity)"""
        complexity = self.analyze_complexity(prompt)
        provider, model = self.select_model(complexity, budget_limit)
        return provider, model, complexity
