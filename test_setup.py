"""
Quick test script to validate the AI Cost Optimizer setup
"""
import asyncio
from router import LLMRouter
from cost_tracker import CostTracker

async def test_routing():
    """Test routing logic"""
    router = LLMRouter()
    
    # Test different complexity levels
    test_prompts = [
        "What is 2+2?",
        "Explain machine learning in simple terms",
        "Design a distributed system architecture for real-time data processing with fault tolerance"
    ]
    
    for prompt in test_prompts:
        model, complexity = await router.route_request(prompt)
        print(f"\nPrompt: {prompt[:50]}...")
        print(f"Complexity: {complexity:.2f}")
        print(f"Selected Model: {model}")

def test_cost_calculation():
    """Test cost tracking"""
    tracker = CostTracker()
    
    test_text = "This is a test prompt for token counting"
    tokens = tracker.count_tokens(test_text)
    cost = tracker.calculate_cost("openai/gpt-3.5-turbo", tokens, 100)
    
    print(f"\nCost Calculation Test:")
    print(f"Input tokens: {tokens}")
    print(f"Estimated cost: ${cost}")

if __name__ == "__main__":
    print("=== AI Cost Optimizer - System Test ===\n")
    
    # Test routing
    asyncio.run(test_routing())
    
    # Test cost tracking
    test_cost_calculation()
    
    print("\n✅ Core components working!")
    print("Next: Set up .env file with your OpenRouter API key")
