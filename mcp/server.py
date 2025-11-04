#!/usr/bin/env python3
"""MCP server for AI Cost Optimizer - Claude Desktop integration."""
import os
import json
import asyncio
from typing import Any
import httpx
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types


# Configuration
API_BASE_URL = os.getenv("COST_OPTIMIZER_API_URL", "http://localhost:8000")

# Initialize MCP server
server = Server("ai-cost-optimizer")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    
    Returns single tool: complete_prompt for routing and executing prompts.
    """
    return [
        types.Tool(
            name="complete_prompt",
            description=(
                "Route and complete a prompt using the optimal LLM based on complexity. "
                "Automatically selects between Gemini Flash (simple queries) and Claude Haiku (complex queries). "
                "Returns response with cost breakdown and usage statistics."
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
                        "description": "Maximum tokens in response (default: 1000)",
                        "default": 1000
                    }
                },
                "required": ["prompt"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    """
    Handle tool execution requests.
    
    Args:
        name: Tool name to execute
        arguments: Tool arguments
    
    Returns:
        Tool execution result
    """
    if name != "complete_prompt":
        raise ValueError(f"Unknown tool: {name}")
    
    # Extract arguments
    prompt = arguments.get("prompt")
    max_tokens = arguments.get("max_tokens", 1000)
    
    if not prompt:
        raise ValueError("Prompt is required")
    
    # Call FastAPI service
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/complete",
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens
                }
            )
            
            if response.status_code == 503:
                # Service unavailable (no providers)
                error_detail = response.json().get("detail", "Service unavailable")
                return [
                    types.TextContent(
                        type="text",
                        text=f"❌ **Service Unavailable**\n\n{error_detail}\n\n"
                             "Please ensure:\n"
                             "1. FastAPI service is running (`python app/main.py`)\n"
                             "2. At least one API key is configured in .env file\n"
                             "3. Service is accessible at {API_BASE_URL}"
                    )
                ]
            
            response.raise_for_status()
            data = response.json()
            
            # Format response with cost breakdown
            complexity_meta = data["complexity_metadata"]
            
            result = (
                f"**Response:**\n\n{data['response']}\n\n"
                f"---\n\n"
                f"**Cost Analysis:**\n"
                f"- Provider: {data['provider']}\n"
                f"- Model: {data['model']}\n"
                f"- Complexity: {data['complexity']} "
                f"({complexity_meta['token_count']} tokens"
            )
            
            if complexity_meta['keywords_found']:
                result += f", keywords: {', '.join(complexity_meta['keywords_found'][:3])}"
            
            result += ")\n"
            result += (
                f"- Tokens: {data['tokens_in']} in / {data['tokens_out']} out\n"
                f"- Cost: ${data['cost']:.6f}\n"
                f"- Total cost (all time): ${data['total_cost_today']:.2f}\n"
            )
            
            return [types.TextContent(type="text", text=result)]
    
    except httpx.ConnectError:
        return [
            types.TextContent(
                type="text",
                text=(
                    f"❌ **Cannot Connect to Cost Optimizer**\n\n"
                    f"Service URL: {API_BASE_URL}\n\n"
                    f"Please ensure the FastAPI service is running:\n"
                    f"```bash\n"
                    f"cd /path/to/ai-cost-optimizer\n"
                    f"python app/main.py\n"
                    f"```"
                )
            )
        ]
    
    except httpx.HTTPError as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **API Error:** {str(e)}"
            )
        ]
    
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **Unexpected Error:** {str(e)}"
            )
        ]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ai-cost-optimizer",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
