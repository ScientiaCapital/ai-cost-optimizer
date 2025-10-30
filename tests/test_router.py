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

    # Should select cheap tier
    assert provider_name in ["gemini", "cerebras"]
    assert model_name in ["gemini-2.0-flash-exp", "gemini-1.5-flash", "llama3.1-8b"]

def test_select_provider_complex_query(router):
    """Test that complex queries route to premium models."""
    provider_name, model_name, provider = router.select_provider(
        complexity="complex",
        prompt="Design a distributed system architecture for..."
    )

    # Should select premium tier
    assert provider_name in ["anthropic", "claude", "openrouter", "cerebras"]
