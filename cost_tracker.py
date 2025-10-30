import tiktoken
from decimal import Decimal
from datetime import datetime
from typing import Dict, Optional
import json

# Simplified pricing (per 1M tokens)
MODEL_PRICING = {
    "openai/gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "openai/gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "openai/gpt-4": {"input": 30.00, "output": 60.00},
    "anthropic/claude-instant-1.2": {"input": 0.80, "output": 2.40},
    "anthropic/claude-3-sonnet": {"input": 3.00, "output": 15.00},
    "anthropic/claude-3-opus": {"input": 15.00, "output": 75.00},
    "google/gemini-flash-1.5": {"input": 0.35, "output": 1.05},
    "google/gemini-pro-1.5": {"input": 3.50, "output": 10.50},
    "openai/o1-mini": {"input": 3.00, "output": 12.00}
}

class CostTracker:
    def __init__(self, db_path: str = "optimizer.db"):
        self.db_path = db_path
        self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoder.encode(text))
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> Decimal:
        """Calculate cost for a request"""
        if model not in MODEL_PRICING:
            # Default fallback pricing
            pricing = {"input": 5.00, "output": 15.00}
        else:
            pricing = MODEL_PRICING[model]
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return Decimal(str(input_cost + output_cost)).quantize(Decimal('0.000001'))
    
    def track_request(self, request_data: Dict) -> str:
        """Log request to database (simplified for MVP)"""
        # TODO: Implement actual database logging
        request_id = f"req_{datetime.now().timestamp()}"
        print(f"[COST] {request_id}: ${request_data['cost']} ({request_data['model']})")
        return request_id
    
    def get_usage(self, user_id: str = "default", days: int = 30) -> Dict:
        """Get usage statistics (simplified)"""
        # TODO: Implement actual database query
        return {
            "total_cost": Decimal("12.45"),
            "total_requests": 156,
            "period_days": days,
            "models_used": {"gpt-3.5-turbo": 120, "gpt-4-turbo": 36}
        }
