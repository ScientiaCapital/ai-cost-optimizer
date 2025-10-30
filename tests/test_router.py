import pytest
from app.router import Router
from app.providers import init_providers

@pytest.fixture
def router():
    providers = init_providers()
    return Router(providers, enable_learning=False)

def test_select_provider_simple_query(router):
    """Test that simple queries route to cheap models."""
    provider_name, model_name, provider = router.select_provider(
        complexity="simple",
        prompt="What is Python?"
    )

    # Validate correct provider-model pairings (not just any combination)
    valid_combinations = [
        ("cerebras", "llama3.1-8b"),
        ("gemini", "gemini-1.5-flash"),
        ("gemini", "gemini-2.0-flash-exp"),
        ("openrouter", "google/gemini-flash-1.5")
    ]
    assert (provider_name, model_name) in valid_combinations, f"Invalid combination: {provider_name}/{model_name}"
    assert provider is not None

def test_select_provider_complex_query(router):
    """Test that complex queries route to premium models."""
    provider_name, model_name, provider = router.select_provider(
        complexity="complex",
        prompt="Design a distributed system architecture for..."
    )

    # Validate correct provider-model pairings (not just any combination)
    valid_combinations = [
        ("claude", "claude-3-haiku-20240307"),
        ("claude", "claude-3-5-haiku-20241022"),
        ("cerebras", "llama3.1-70b"),
        ("openrouter", "anthropic/claude-3-haiku"),
        ("openrouter", "anthropic/claude-3.5-haiku")
    ]
    assert (provider_name, model_name) in valid_combinations, f"Invalid combination: {provider_name}/{model_name}"
    assert provider is not None
