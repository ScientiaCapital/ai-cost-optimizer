#!/usr/bin/env python3
"""
MCP Server for AI Cost Optimizer
Wraps FastAPI service to expose tools for Claude Desktop
"""

import os
import json
import httpx
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import asyncio
import sys

# MCP SDK imports
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from mcp.server.stdio import stdio_server


@dataclass
class ServerConfig:
    """Configuration for the MCP server"""
    api_url: str
    api_key: Optional[str] = None

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls(
            api_url=os.getenv("COST_OPTIMIZER_API_URL", "http://localhost:8000"),
            api_key=os.getenv("COST_OPTIMIZER_API_KEY")
        )


class CostOptimizerMCP:
    """MCP Server for AI Cost Optimizer"""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.api_url,
            timeout=30.0
        )
        self.server = Server("ai-cost-optimizer")
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP tool handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available tools"""
            return [
                Tool(
                    name="complete_prompt",
                    description=(
                        "Route a prompt through the AI cost optimizer. "
                        "Automatically selects the most cost-efficient model "
                        "based on prompt complexity. Returns the completion, "
                        "model used, and cost."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The prompt to complete"
                            },
                            "max_tokens": {
                                "type": "integer",
                                "description": "Maximum tokens in response",
                                "default": 1000
                            },
                            "budget_limit": {
                                "type": "number",
                                "description": "Maximum cost for this request in USD",
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User ID for tracking",
                                "default": "default"
                            },
                            "force_provider": {
                                "type": "string",
                                "description": "Force specific provider (e.g., 'anthropic', 'google')",
                            },
                            "force_model": {
                                "type": "string",
                                "description": "Force specific model (e.g., 'claude-3-5-sonnet', 'gemini-1.5-flash')",
                            }
                        },
                        "required": ["prompt"]
                    }
                ),
                Tool(
                    name="check_model_costs",
                    description=(
                        "Get comprehensive pricing information for all available "
                        "models across all providers. Returns model IDs, providers, "
                        "input/output prices per million tokens, and context windows."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_recommendation",
                    description=(
                        "Analyze a prompt and get model recommendation without "
                        "executing it. Returns complexity score, recommended model, "
                        "estimated cost, and reasoning."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The prompt to analyze"
                            },
                            "max_tokens": {
                                "type": "integer",
                                "description": "Expected response length",
                                "default": 1000
                            },
                            "budget_limit": {
                                "type": "number",
                                "description": "Budget constraint in USD",
                            }
                        },
                        "required": ["prompt"]
                    }
                ),
                Tool(
                    name="query_usage",
                    description=(
                        "Get usage statistics including total cost, request count, "
                        "remaining budget, and breakdown by model. Useful for "
                        "monitoring spending and understanding usage patterns."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID to query",
                                "default": "default"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look back",
                                "default": 30
                            }
                        }
                    }
                ),
                Tool(
                    name="set_budget",
                    description=(
                        "Set monthly budget limits and configure alert thresholds. "
                        "Alerts trigger at specified percentage thresholds "
                        "(e.g., 50%, 80%, 90%)."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "monthly_limit": {
                                "type": "number",
                                "description": "Monthly budget in USD"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User ID",
                                "default": "default"
                            },
                            "alert_thresholds": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "Alert thresholds as percentages (0.0-1.0, e.g., [0.5, 0.8, 0.9])",
                                "default": [0.5, 0.8, 0.9]
                            }
                        },
                        "required": ["monthly_limit"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""

            try:
                if name == "complete_prompt":
                    return await self._complete_prompt(arguments)
                elif name == "check_model_costs":
                    return await self._check_model_costs()
                elif name == "get_recommendation":
                    return await self._get_recommendation(arguments)
                elif name == "query_usage":
                    return await self._query_usage(arguments)
                elif name == "set_budget":
                    return await self._set_budget(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
            except httpx.HTTPStatusError as e:
                return [TextContent(
                    type="text",
                    text=f"API Error ({e.response.status_code}): {e.response.text}"
                )]
            except httpx.ConnectError:
                return [TextContent(
                    type="text",
                    text=(
                        "Cannot connect to AI Cost Optimizer service. "
                        f"Is it running at {self.config.api_url}?\n\n"
                        "To start the service:\n"
                        "1. Navigate to the ai-cost-optimizer directory\n"
                        "2. Run: python main.py\n"
                        "3. Ensure it's accessible at the configured URL"
                    )
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]

    async def _complete_prompt(self, args: Dict[str, Any]) -> List[TextContent]:
        """Execute completion through cost optimizer"""
        payload = {
            "prompt": args["prompt"],
            "max_tokens": args.get("max_tokens", 1000),
            "user_id": args.get("user_id", "default")
        }

        # Add optional parameters if provided
        if args.get("budget_limit") is not None:
            payload["budget_limit"] = args["budget_limit"]

        if args.get("force_provider") and args.get("force_model"):
            payload["provider"] = args["force_provider"]
            payload["model"] = args["force_model"]

        response = await self.client.post("/v1/complete", json=payload)
        response.raise_for_status()
        data = response.json()

        # Format response with clear sections
        result = f"""**Response:**
{data['response']}

**Cost Analysis:**
• Provider: {data['provider']}
• Model: {data['model_used']}
• Cost: ${data['cost']:.6f}
• Complexity Score: {data['complexity_score']:.2f}
• Tokens: {data['prompt_tokens']} input / {data['completion_tokens']} output
"""

        return [TextContent(type="text", text=result)]

    async def _check_model_costs(self) -> List[TextContent]:
        """Get all model pricing"""
        response = await self.client.get("/v1/models")
        response.raise_for_status()
        data = response.json()

        # Group models by provider for better readability
        providers = {}
        for model in data["models"]:
            provider = model["provider"]
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(model)

        result = "# Available Models and Pricing\n\n"

        for provider, models in sorted(providers.items()):
            result += f"## {provider.upper()}\n\n"
            for model in models:
                result += (
                    f"**{model['id']}**\n"
                    f"• Input: ${model['input_price']:.2f} per 1M tokens\n"
                    f"• Output: ${model['output_price']:.2f} per 1M tokens\n"
                    f"• Context Window: {model['context_window']:,} tokens\n\n"
                )

        result += f"\n**Total Models Available:** {len(data['models'])}"

        return [TextContent(type="text", text=result)]

    async def _get_recommendation(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get recommendation by doing a dry-run analysis"""

        prompt = args["prompt"]
        max_tokens = args.get("max_tokens", 1000)

        # Use a simple heuristic-based analysis
        # In production, you might want to add a /v1/analyze endpoint to the FastAPI service

        # Calculate complexity score (simplified version of router logic)
        complexity = self._analyze_prompt_complexity(prompt)

        # Determine recommended tier and model
        if complexity < 0.2:
            tier = "Free"
            recommended_provider = "google"
            recommended_model = "gemini-2.0-flash"
            reasoning = "Very simple task - using free model"
        elif complexity < 0.4:
            tier = "Cheap"
            recommended_provider = "cerebras"
            recommended_model = "llama-3.1-8b"
            reasoning = "Simple task - using cost-efficient model"
        elif complexity < 0.7:
            tier = "Medium"
            recommended_provider = "google"
            recommended_model = "gemini-1.5-pro"
            reasoning = "Moderate complexity - balancing cost and capability"
        else:
            tier = "Premium"
            recommended_provider = "anthropic"
            recommended_model = "claude-3-5-sonnet"
            reasoning = "High complexity - using premium model for best quality"

        # Estimate cost (rough estimates - actual costs may vary)
        cost_estimates = {
            "gemini-2.0-flash": 0.0,
            "llama-3.1-8b": 0.0001,
            "gemini-1.5-pro": 0.005,
            "claude-3-5-sonnet": 0.015
        }
        estimated_cost = cost_estimates.get(recommended_model, 0.01)

        result = f"""**Recommendation Analysis**

**Complexity Assessment:**
• Complexity Score: {complexity:.2f}
• Tier: {tier}

**Recommended Model:**
• Provider: {recommended_provider}
• Model: {recommended_model}
• Estimated Cost: ${estimated_cost:.6f}

**Reasoning:**
{reasoning}

**Token Estimate:**
• Input: ~{len(prompt.split()) * 1.3:.0f} tokens
• Expected Output: {max_tokens} tokens max

**Note:** This is an estimate. Use `complete_prompt` to execute with the optimal model.
"""

        return [TextContent(type="text", text=result)]

    def _analyze_prompt_complexity(self, prompt: str) -> float:
        """
        Simple complexity analysis (mirrors router.py logic)
        Returns score between 0.0 (very simple) and 1.0 (very complex)
        """
        score = 0.0

        # Length factor
        length = len(prompt)
        if length < 100:
            score += 0.1
        elif length < 500:
            score += 0.3
        else:
            score += 0.5

        # Complexity keywords
        complex_keywords = [
            'analyze', 'design', 'architecture', 'implement', 'refactor',
            'optimize', 'algorithm', 'system', 'strategy', 'comprehensive',
            'detailed', 'technical', 'research', 'compare', 'evaluate'
        ]

        prompt_lower = prompt.lower()
        keyword_matches = sum(1 for kw in complex_keywords if kw in prompt_lower)
        score += min(keyword_matches * 0.1, 0.3)

        # Code or technical content
        if any(indicator in prompt for indicator in ['```', 'function', 'class', 'def ', 'const ', 'var ']):
            score += 0.2

        return min(score, 1.0)

    async def _query_usage(self, args: Dict[str, Any]) -> List[TextContent]:
        """Query usage statistics"""
        params = {
            "user_id": args.get("user_id", "default"),
            "days": args.get("days", 30)
        }

        response = await self.client.get("/v1/usage", params=params)
        response.raise_for_status()
        data = response.json()

        result = f"""**Usage Statistics** ({params['days']} days)

**Overview:**
• Total Cost: ${data.get('total_cost', 0):.2f}
• Total Requests: {data.get('total_requests', 0)}
• Remaining Budget: ${data.get('remaining_budget', 0):.2f}
• Budget Utilization: {((data.get('total_cost', 0) / max(data.get('remaining_budget', 0) + data.get('total_cost', 0), 1)) * 100):.1f}%
"""

        if "models_used" in data and data["models_used"]:
            result += "\n**Models Used:**\n"
            for model, count in sorted(data["models_used"].items(), key=lambda x: x[1], reverse=True):
                result += f"• {model}: {count} requests\n"

        return [TextContent(type="text", text=result)]

    async def _set_budget(self, args: Dict[str, Any]) -> List[TextContent]:
        """Set budget limits"""
        payload = {
            "monthly_limit": args["monthly_limit"],
            "user_id": args.get("user_id", "default"),
            "alert_thresholds": args.get("alert_thresholds", [0.5, 0.8, 0.9])
        }

        response = await self.client.post("/v1/budget", json=payload)
        response.raise_for_status()
        data = response.json()

        thresholds_str = ", ".join(f"{t*100:.0f}%" for t in payload["alert_thresholds"])

        result = f"""**Budget Updated Successfully**

• User: {payload['user_id']}
• Monthly Limit: ${payload['monthly_limit']:.2f}
• Alert Thresholds: {thresholds_str}

You will receive alerts when spending reaches these thresholds.
"""

        return [TextContent(type="text", text=result)]

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ai-cost-optimizer",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


def main():
    """Entry point"""
    # Load configuration from environment
    config = ServerConfig.from_env()

    # Log startup info to stderr (stdout is reserved for MCP protocol)
    print(f"Starting AI Cost Optimizer MCP Server", file=sys.stderr)
    print(f"API URL: {config.api_url}", file=sys.stderr)
    print(f"Ready to accept connections from Claude Desktop", file=sys.stderr)

    # Create and run server
    server = CostOptimizerMCP(config)

    # Run with asyncio
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
