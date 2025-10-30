import pytest
from app.router import Router
from app.complexity import score_complexity
from app.providers import init_providers

@pytest.fixture(scope="module")
def router():
    return Router(init_providers())

def test_complexity_scoring_benchmark(benchmark):
    """Benchmark complexity scoring performance."""
    prompt = "Write a Python function to implement binary search"

    result = benchmark(score_complexity, prompt)

    # Should complete in under 10ms
    assert benchmark.stats['mean'] < 0.01

def test_provider_selection_benchmark(benchmark, router):
    """Benchmark provider selection performance."""

    def select():
        return router.select_provider("complex", "Explain quantum computing")

    result = benchmark(select)

    # Should complete in under 50ms
    assert benchmark.stats['mean'] < 0.05
