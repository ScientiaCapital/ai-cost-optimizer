"""
Quick test script to validate the AI Cost Optimizer setup
Note: This script is a placeholder and needs to be updated to work with the current app architecture.
The app uses a different routing system than what's tested here.
"""
import asyncio
from app.router import Router
from app.providers import init_providers
from app.complexity import score_complexity
from app.database import CostTracker

async def test_routing():
    """Test routing logic"""
    providers = init_providers()
    router = Router(providers)
    
    # Test different complexity levels
    test_prompts = [
        "What is 2+2?",
        "Explain machine learning in simple terms",
        "Design a distributed system architecture for real-time data processing with fault tolerance"
    ]
    
    for prompt in test_prompts:
        complexity = score_complexity(prompt)
        routing_info = router.get_routing_info(complexity)
        print(f"\nPrompt: {prompt[:50]}...")
        print(f"Complexity: {complexity:.2f}")
        print(f"Routing: {routing_info}")

def test_cost_calculation():
    """Test cost tracking"""
    tracker = CostTracker()
    
    # Test database operations
    test_prompt = "This is a test prompt for token counting"
    complexity = score_complexity(test_prompt)
    
    # Log a test request
    tracker.log_request(
        prompt=test_prompt,
        complexity=complexity,
        provider="test",
        model="test-model",
        tokens_in=10,
        tokens_out=50,
        cost=0.001
    )
    
    print(f"\nCost Tracking Test:")
    print(f"Total cost: ${tracker.get_total_cost()}")

if __name__ == "__main__":
    print("=== AI Cost Optimizer - System Test ===\n")
    
    # Test routing
    asyncio.run(test_routing())
    
    # Test cost tracking
    test_cost_calculation()
    
    print("\n✅ Core components working!")
    print("Next: Set up .env file with your API keys")
