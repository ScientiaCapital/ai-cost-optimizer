"""Test script for Cost Optimization Agent."""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Import agent
from cost_optimizer_agent import run_agent


async def test_tools():
    """Test that tools work without calling the agent."""
    print("=" * 80)
    print("TESTING TOOLS (No API calls)")
    print("=" * 80)
    print()

    from tools import (
        get_usage_stats,
        get_recommendations,
        check_cache_effectiveness,
        compare_providers
    )

    print("1. Testing get_usage_stats()...")
    result = get_usage_stats()
    print(result[:200] + "..." if len(result) > 200 else result)
    print("   ✅ Success\n")

    print("2. Testing get_recommendations()...")
    result = get_recommendations()
    print(result[:200] + "..." if len(result) > 200 else result)
    print("   ✅ Success\n")

    print("3. Testing check_cache_effectiveness()...")
    result = check_cache_effectiveness()
    print(result[:200] + "..." if len(result) > 200 else result)
    print("   ✅ Success\n")

    print("4. Testing compare_providers()...")
    result = compare_providers()
    print(result[:200] + "..." if len(result) > 200 else result)
    print("   ✅ Success\n")

    print("=" * 80)
    print("ALL TOOLS WORKING! ✅")
    print("=" * 80)
    print()


async def test_agent():
    """Test the agent with a simple query."""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("=" * 80)
        print("⚠️  ANTHROPIC_API_KEY not set")
        print("=" * 80)
        print()
        print("The tools work, but the agent needs an API key to run.")
        print("To test the full agent:")
        print()
        print("  1. Set your API key:")
        print("     export ANTHROPIC_API_KEY='your-key-here'")
        print()
        print("  2. Run the agent:")
        print("     cd agent")
        print("     python3 cost_optimizer_agent.py 'What are my total costs?'")
        print()
        return

    print("=" * 80)
    print("TESTING AGENT (Will make API call)")
    print("=" * 80)
    print()

    try:
        await run_agent("What are my total costs? Give me a brief summary.", session_mode=False)
        print()
        print("=" * 80)
        print("AGENT TEST SUCCESSFUL! ✅")
        print("=" * 80)
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ Agent test failed: {str(e)}")
        print("=" * 80)


async def main():
    """Run tests."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "COST OPTIMIZATION AGENT TEST" + " " * 30 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")

    # Test tools first (no API calls)
    await test_tools()

    # Ask user if they want to test the agent (requires API key)
    print("\nTest the full agent? (requires ANTHROPIC_API_KEY and makes an API call)")
    print("Press Enter to test, or Ctrl+C to skip...")
    try:
        input()
        await test_agent()
    except KeyboardInterrupt:
        print("\n\nSkipped agent test.")
        print("\nTo test later, run:")
        print("  cd agent")
        print("  python3 cost_optimizer_agent.py 'What are my total costs?'")


if __name__ == "__main__":
    asyncio.run(main())
