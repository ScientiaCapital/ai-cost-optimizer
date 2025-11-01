"""Cost Optimization Agent - AI Spending Analyst.

This agent analyzes AI usage patterns, identifies cost-saving opportunities,
and provides actionable recommendations for optimizing LLM spending.
"""
import asyncio
import os
from typing import Optional

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server


# Import our custom tools
from tools import (
    get_usage_stats,
    analyze_cost_patterns,
    get_recommendations,
    query_recent_requests,
    check_cache_effectiveness,
    compare_providers,
    # New learning-powered tools
    get_smart_recommendation,
    get_pattern_analysis,
    get_provider_performance,
    calculate_potential_savings
)


# Agent system prompt
SYSTEM_PROMPT = """You are a Cost Optimization Agent, an expert AI spending analyst.

Your role is to help users understand and optimize their AI/LLM costs by:
1. Analyzing usage patterns and spending trends
2. Identifying cost-saving opportunities
3. Providing actionable, data-driven recommendations
4. Explaining complex cost data in clear, business-friendly language

You have access to 10 powerful tools that query the AI Cost Optimizer database:

**Analysis Tools:**
- get_usage_stats: Overall statistics (total costs, requests, breakdowns)
- analyze_cost_patterns: Spending trends over time (default: 7 days)
- query_recent_requests: Examine recent queries (up to 100)

**Optimization Tools:**
- get_recommendations: Generate prioritized optimization opportunities
- check_cache_effectiveness: Cache performance and savings analysis
- compare_providers: Cost/quality comparison across providers

**Learning Intelligence Tools (NEW):**
- get_smart_recommendation: AI-powered routing recommendations with confidence levels
- get_pattern_analysis: Learning progress across 6 query patterns (code, analysis, creative, etc.)
- get_provider_performance: Model performance rankings with internal/external view modes
- calculate_potential_savings: ROI calculator showing cost reduction opportunities

**Your Communication Style:**
- Be concise but thorough
- Use specific numbers and metrics
- Prioritize actionable insights over raw data dumps
- Highlight savings opportunities with dollar amounts
- Use business-friendly language (avoid excessive technical jargon)

**Example Interactions:**

User: "How much have I spent this week?"
You: [Use analyze_cost_patterns(days=7) and summarize key numbers]

User: "Where can I save money?"
You: [Use get_recommendations() and present top 3 opportunities with savings]

User: "Is my cache working well?"
You: [Use check_cache_effectiveness() and explain hit rate + savings]

User: "Analyze my last 50 queries"
You: [Use query_recent_requests(limit=50) and identify patterns/inefficiencies]

**Important Guidelines:**
- Always cite specific numbers when making recommendations
- Compare current state to potential optimized state
- Be honest about limitations (e.g., "Need more data for accurate analysis")
- When asked to analyze, proactively suggest next steps
- Format large numbers clearly (e.g., $1,234.56 not 1234.5678)

You are helpful, analytical, and focused on delivering ROI through cost optimization.
"""


# Create MCP server with all cost analysis tools
cost_analyzer_server = create_sdk_mcp_server(
    name="cost_analyzer",
    version="1.0.0",
    tools=[
        get_usage_stats,
        analyze_cost_patterns,
        get_recommendations,
        query_recent_requests,
        check_cache_effectiveness,
        compare_providers,
        # New learning-powered tools
        get_smart_recommendation,
        get_pattern_analysis,
        get_provider_performance,
        calculate_potential_savings
    ]
)


# Create agent configuration options
agent_options = ClaudeAgentOptions(
    system_prompt=SYSTEM_PROMPT,
    model="claude-3-5-sonnet-20241022",
    mcp_servers={"cost_analyzer": cost_analyzer_server},
    allowed_tools=[
        "get_usage_stats",
        "analyze_cost_patterns",
        "get_recommendations",
        "query_recent_requests",
        "check_cache_effectiveness",
        "compare_providers",
        # New learning-powered tools
        "get_smart_recommendation",
        "get_pattern_analysis",
        "get_provider_performance",
        "calculate_potential_savings"
    ]
)


async def run_agent(prompt: str, session_mode: bool = False):
    """Run the Cost Optimization Agent with a user prompt.

    Args:
        prompt: User's question or request
        session_mode: If True, enables interactive session mode

    Returns:
        Agent's response
    """
    # Check for ANTHROPIC_API_KEY
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found in environment variables.")
        print("Please set your API key:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\nGet your API key from: https://console.anthropic.com/")
        return

    try:
        if session_mode:
            # Interactive session mode
            async with ClaudeSDKClient(options=agent_options) as client:
                print("🤖 Cost Optimization Agent (Session Mode)")
                print("=" * 60)
                print("Type 'exit' or 'quit' to end the session\n")

                while True:
                    if not prompt:
                        user_input = input("You: ").strip()
                        if user_input.lower() in ['exit', 'quit']:
                            print("\n👋 Session ended. Happy optimizing!")
                            break
                        if not user_input:
                            continue
                        prompt = user_input

                    print(f"\n🤖 Agent: ", end="", flush=True)

                    await client.query(prompt)
                    async for message in client.receive_response():
                        print(message, end="", flush=True)

                    print("\n")
                    prompt = None  # Reset for next iteration

        else:
            # Single query mode
            from claude_agent_sdk import query

            print("🤖 Cost Optimization Agent")
            print("=" * 60)
            print(f"Query: {prompt}\n")
            print("Agent: ", end="", flush=True)

            async for message in query(
                prompt=prompt,
                options=agent_options
            ):
                print(message, end="", flush=True)

            print("\n")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if "api_key" in str(e).lower():
            print("\nMake sure your ANTHROPIC_API_KEY is set correctly.")


async def main():
    """Main entry point for the agent."""
    import sys

    if len(sys.argv) > 1:
        # Command-line query
        prompt = " ".join(sys.argv[1:])
        await run_agent(prompt, session_mode=False)
    else:
        # Interactive session mode
        prompt = "Hello! I'm ready to help you optimize your AI costs. What would you like to know?"
        await run_agent(prompt, session_mode=True)


if __name__ == "__main__":
    asyncio.run(main())
