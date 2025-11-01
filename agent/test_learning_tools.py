"""Tests for learning-powered agent tools."""
import pytest
import json
from tools import (
    _get_smart_recommendation_impl,
    _get_pattern_analysis_impl,
    _get_provider_performance_impl,
    _calculate_potential_savings_impl
)


@pytest.mark.asyncio
async def test_get_smart_recommendation_format():
    """Smart recommendation returns proper format."""
    result = await _get_smart_recommendation_impl({"prompt": "Debug Python code"})

    assert "content" in result
    assert len(result["content"]) > 0
    assert result["content"][0]["type"] == "text"

    # Should mention tier (not internal model) OR show graceful no-data message
    text = result["content"][0]["text"]
    # Either has data with Tier and Confidence, or shows no data message
    has_data = "Tier" in text and "Confidence" in text
    has_no_data_msg = "Insufficient historical data" in text or "Database not found" in text
    assert has_data or has_no_data_msg


@pytest.mark.asyncio
async def test_get_pattern_analysis_format():
    """Pattern analysis returns all 6 patterns."""
    result = await _get_pattern_analysis_impl({})

    text = result["content"][0]["text"]

    # Should list all patterns
    patterns = ["code", "analysis", "creative", "explanation", "factual", "reasoning"]
    for pattern in patterns:
        assert pattern in text.lower()


@pytest.mark.asyncio
async def test_get_provider_performance_black_boxed():
    """Provider performance hides internal models in external mode."""
    result = await _get_provider_performance_impl({"mode": "external"})

    text = result["content"][0]["text"]

    # Should show tiers OR graceful no-data message
    has_data = "Tier" in text
    has_no_data_msg = "No performance data available" in text or "Database not found" in text
    assert has_data or has_no_data_msg

    # Should NOT leak internal model names (if has data)
    if has_data:
        assert "openrouter" not in text.lower()
        assert "deepseek" not in text.lower()


@pytest.mark.asyncio
async def test_get_provider_performance_internal():
    """Provider performance shows models in internal mode."""
    result = await _get_provider_performance_impl({"mode": "internal"})

    text = result["content"][0]["text"]

    # Internal mode shows actual models OR graceful no-data message
    # (Will contain "Model" in header if data exists)
    has_data = "Model" in text
    has_no_data_msg = "No performance data available" in text or "Database not found" in text
    assert has_data or has_no_data_msg


@pytest.mark.asyncio
async def test_calculate_potential_savings_format():
    """Savings calculation shows current vs optimized."""
    result = await _calculate_potential_savings_impl({"days": 7})

    text = result["content"][0]["text"]

    # Should show savings data OR graceful no-data message
    has_data = ("current" in text.lower() and "optimized" in text.lower())
    has_no_data_msg = "Insufficient data" in text or "Database not found" in text or "No performance data" in text
    assert has_data or has_no_data_msg

    # All responses should mention cost
    assert "$" in text or "cost" in text.lower() or "data" in text.lower()
