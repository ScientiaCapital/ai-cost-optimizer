"""Tests for model abstraction layer."""
import pytest
from model_abstraction import get_public_label, get_internal_models, MODEL_TIERS


def test_get_public_label_openrouter():
    """OpenRouter models map to correct tiers."""
    assert get_public_label("openrouter/deepseek-chat") == "Economy Tier"
    assert get_public_label("openrouter/qwen-2-72b") == "Premium Tier"


def test_get_public_label_claude():
    """Claude models map to Premium Tier."""
    assert get_public_label("claude/claude-3-haiku") == "Premium Tier"


def test_get_public_label_unknown():
    """Unknown models return Unknown Tier."""
    assert get_public_label("unknown/model") == "Unknown Tier"


def test_get_internal_models():
    """Reverse lookup from tier to models."""
    economy = get_internal_models("Economy Tier")
    assert "openrouter/deepseek-chat" in economy
    assert "openrouter/deepseek-coder" in economy


def test_tier_mapping_completeness():
    """All expected models have tier mappings."""
    required_models = [
        "claude/claude-3-haiku",
        "openrouter/qwen-2-72b",
        "openrouter/deepseek-chat",
        "openrouter/deepseek-coder",
        "google/gemini-flash",
        "openrouter/qwen-2.5-math"
    ]
    for model in required_models:
        assert model in MODEL_TIERS
