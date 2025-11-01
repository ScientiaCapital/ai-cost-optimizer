"""Example usage of the Cost Optimization Agent.

This script demonstrates various ways to interact with the agent.
"""
import asyncio
from cost_optimizer_agent import run_agent


async def example_single_queries():
    """Demonstrate single query mode with various questions."""
    print("=" * 80)
    print("EXAMPLE 1: Single Query Mode")
    print("=" * 80)
    print("\n")

    queries = [
        "What are my total costs?",
        "How much did I spend this week?",
        "Where can I save money?",
    ]

    for query in queries:
        print(f"\n{'─' * 80}")
        print(f"Query: {query}")
        print(f"{'─' * 80}\n")
        await run_agent(query, session_mode=False)
        print("\n")


async def example_session_mode():
    """Demonstrate interactive session mode."""
    print("\n\n")
    print("=" * 80)
    print("EXAMPLE 2: Interactive Session Mode")
    print("=" * 80)
    print("\nStarting interactive session...\n")

    # In a real session, you'd interact manually
    # This example shows how to start a session programmatically
    initial_prompt = "Hi! Can you give me a quick overview of my AI spending?"
    await run_agent(initial_prompt, session_mode=True)


async def example_programmatic_usage():
    """Demonstrate using the agent in your own code."""
    print("\n\n")
    print("=" * 80)
    print("EXAMPLE 3: Programmatic Usage")
    print("=" * 80)
    print("\n")

    # You can import and use individual tools directly
    from tools import (
        get_usage_stats,
        get_recommendations,
        check_cache_effectiveness
    )

    print("📊 Direct Tool Usage (without agent):\n")

    print("1. Usage Stats:")
    print(get_usage_stats())
    print("\n")

    print("2. Recommendations:")
    print(get_recommendations())
    print("\n")

    print("3. Cache Effectiveness:")
    print(check_cache_effectiveness())
    print("\n")


async def example_targeted_analysis():
    """Demonstrate targeted analysis queries."""
    print("\n\n")
    print("=" * 80)
    print("EXAMPLE 4: Targeted Analysis")
    print("=" * 80)
    print("\n")

    queries = [
        "Compare provider costs",
        "Analyze my last 50 queries",
        "Is my cache hit rate good?",
        "What's the most expensive type of query I'm making?",
    ]

    for query in queries:
        print(f"\n{'─' * 80}")
        print(f"Query: {query}")
        print(f"{'─' * 80}\n")
        await run_agent(query, session_mode=False)
        print("\n")


async def main():
    """Run all examples."""
    import os

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not set!")
        print("\nPlease set your API key:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        return

    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "COST OPTIMIZATION AGENT EXAMPLES" + " " * 26 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")

    # Choose which examples to run
    print("Select example to run:")
    print("1. Single Query Mode (quick demos)")
    print("2. Interactive Session Mode (conversational)")
    print("3. Programmatic Usage (direct tool access)")
    print("4. Targeted Analysis (specific questions)")
    print("5. Run All Examples")
    print("\nOr press Ctrl+C to exit")

    try:
        choice = input("\nEnter choice (1-5): ").strip()

        if choice == "1":
            await example_single_queries()
        elif choice == "2":
            await example_session_mode()
        elif choice == "3":
            await example_programmatic_usage()
        elif choice == "4":
            await example_targeted_analysis()
        elif choice == "5":
            await example_single_queries()
            await example_programmatic_usage()
            await example_targeted_analysis()
            # Skip session mode when running all (it's interactive)
        else:
            print("Invalid choice. Running Example 1...")
            await example_single_queries()

    except KeyboardInterrupt:
        print("\n\n👋 Examples interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
