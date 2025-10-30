import os
from dotenv import load_dotenv

load_dotenv()

# Provider API Keys
PROVIDER_CONFIGS = {
    "openrouter": {
        "enabled": bool(os.getenv("OPENROUTER_API_KEY")),
        "api_key": os.getenv("OPENROUTER_API_KEY")
    },
    "anthropic": {
        "enabled": bool(os.getenv("ANTHROPIC_API_KEY")),
        "api_key": os.getenv("ANTHROPIC_API_KEY")
    },
    "google": {
        "enabled": bool(os.getenv("GOOGLE_API_KEY")),
        "api_key": os.getenv("GOOGLE_API_KEY")
    },
    "cerebras": {
        "enabled": bool(os.getenv("CEREBRAS_API_KEY")),
        "api_key": os.getenv("CEREBRAS_API_KEY")
    },
    "deepseek": {
        "enabled": bool(os.getenv("DEEPSEEK_API_KEY")),
        "api_key": os.getenv("DEEPSEEK_API_KEY")
    },
    "huggingface": {
        "enabled": bool(os.getenv("HUGGINGFACE_API_KEY")),
        "api_key": os.getenv("HUGGINGFACE_API_KEY")
    }
}

# Database configuration - smart defaults for local vs production
# In production (Docker/RunPod), use persistent volume at /data
# In local development, use current directory
def get_database_url():
    """Get database URL with smart defaults for local vs production"""
    # If explicitly set, use that
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")

    # If /data directory exists (production), use it for persistence
    if os.path.exists("/data"):
        return "sqlite:////data/optimizer.db"

    # Otherwise, use local directory (development)
    return "sqlite:///./optimizer.db"

DATABASE_URL = get_database_url()
DEFAULT_MONTHLY_BUDGET = float(os.getenv("DEFAULT_MONTHLY_BUDGET", "100.0"))
ALERT_THRESHOLDS = [0.5, 0.8, 0.9]

# =============================================================================
# ALERT CONFIGURATION
# =============================================================================

# Email Alerts (SendGrid)
ALERT_EMAIL_ENABLED = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true"
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM", "alerts@ai-cost-optimizer.com")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

# Webhook Alerts (Slack, Discord, custom)
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL")

# Logging (always enabled, writes to budget_alerts.log)
BUDGET_ALERTS_LOG_FILE = os.getenv("BUDGET_ALERTS_LOG_FILE", "budget_alerts.log")

# Model tier mappings - organized by complexity and cost
PROVIDER_MODELS = {
    "cerebras": ["llama3.1-8b", "llama3.1-70b"],
    "deepseek": ["deepseek-chat", "deepseek-coder"],
    "google": ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"],
    "huggingface": ["mistralai/Mistral-7B-Instruct-v0.2", "meta-llama/Llama-2-70b-chat-hf"],
    "openrouter": ["openai/gpt-3.5-turbo", "openai/gpt-4-turbo", "anthropic/claude-3-sonnet"],
    "anthropic": ["claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"]
}

MODEL_TIERS = {
    "free": [
        # Free tier models
        ("google", "gemini-2.0-flash-exp"),
    ],
    "cheap": [
        # Under $1/M tokens
        ("cerebras", "llama3.1-8b"),
        ("google", "gemini-1.5-flash"),
        ("deepseek", "deepseek-chat"),
        ("anthropic", "claude-3-5-haiku-20241022"),
    ],
    "medium": [
        # $1-5/M tokens
        ("google", "gemini-1.5-pro"),
        ("anthropic", "claude-3-5-sonnet-20241022"),
        ("cerebras", "llama3.1-70b"),
    ],
    "premium": [
        # >$5/M tokens
        ("anthropic", "claude-3-opus-20240229"),
        ("openrouter", "openai/gpt-4"),
    ]
}

COMPLEXITY_TO_TIER = {
    (0.0, 0.2): "free",
    (0.2, 0.4): "cheap",
    (0.4, 0.7): "medium",
    (0.7, 1.0): "premium"
}
