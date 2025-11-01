"""Model abstraction layer for black-box competitive protection.

Maps internal model names (e.g., openrouter/deepseek-chat) to public tier labels
(e.g., Economy Tier) to hide implementation details from external users.
"""
from typing import List, Dict


# Tier mapping: internal model -> public label
MODEL_TIERS: Dict[str, str] = {
    # Premium Tier: High quality, established providers
    "claude/claude-3-haiku": "Premium Tier",
    "openrouter/qwen-2-72b": "Premium Tier",

    # Economy Tier: Cost-effective alternatives
    "openrouter/deepseek-chat": "Economy Tier",
    "openrouter/deepseek-coder": "Economy Tier",

    # Standard Tier: Balanced quality/cost
    "google/gemini-flash": "Standard Tier",

    # Specialty Tier: Domain-specific models
    "openrouter/qwen-2.5-math": "Specialty Tier",
}


def get_public_label(internal_model: str) -> str:
    """Convert internal model name to public tier label.

    Args:
        internal_model: Provider/model string (e.g., "openrouter/deepseek-chat")

    Returns:
        Public tier label (e.g., "Economy Tier")
    """
    return MODEL_TIERS.get(internal_model, "Unknown Tier")


def get_internal_models(public_label: str) -> List[str]:
    """Reverse lookup: get all internal models for a tier.

    Args:
        public_label: Tier label (e.g., "Economy Tier")

    Returns:
        List of internal model names matching the tier
    """
    return [model for model, tier in MODEL_TIERS.items() if tier == public_label]
