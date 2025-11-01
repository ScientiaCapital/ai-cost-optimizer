#!/usr/bin/env python3
"""CLI Dashboard for Learning Intelligence Visualization - ADMIN VERSION.

⚠️  INTERNAL USE ONLY - DO NOT DISTRIBUTE TO CUSTOMERS
    - Shows actual model names (competitive intelligence)
    - Exposes internal routing logic
    - For development and internal analysis ONLY

For customer-facing dashboards, use customer_dashboard.py instead.

Usage:
    python admin_dashboard.py                   # Interactive mode (default to Admin View)
    python admin_dashboard.py --mode internal   # Show actual models
    python admin_dashboard.py --mode external   # Show tier labels
"""
import argparse
import sys
import os
from typing import Dict, List, Any

# Add parent to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.learning import QueryPatternAnalyzer
from model_abstraction import get_public_label


def render_progress_bar(value: float, max_value: float, width: int = 40) -> str:
    """Render ASCII progress bar.

    Args:
        value: Current value
        max_value: Maximum value
        width: Bar width in characters

    Returns:
        ASCII progress bar string
    """
    if max_value == 0:
        pct = 0
    else:
        pct = min(value / max_value, 1.0)

    filled = int(pct * width)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {pct*100:.0f}%"


def render_training_overview(analyzer: QueryPatternAnalyzer) -> str:
    """Render training data overview section."""
    import sqlite3
    conn = sqlite3.connect(analyzer.db_path)
    cursor = conn.cursor()

    # Count from requests table
    cursor.execute("SELECT COUNT(*) FROM requests")
    requests_count = cursor.fetchone()[0]

    # Count from response_cache table
    cursor.execute("SELECT COUNT(*) FROM response_cache")
    cache_count = cursor.fetchone()[0]

    total_requests = requests_count + cache_count

    # Count unique models from both tables
    cursor.execute("""
        SELECT COUNT(DISTINCT model) FROM (
            SELECT model FROM requests WHERE model IS NOT NULL AND model != ''
            UNION
            SELECT model FROM response_cache WHERE model IS NOT NULL AND model != ''
        )
    """)
    unique_models = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM response_feedback")
    feedback_count = cursor.fetchone()[0]

    conn.close()

    confidence_data = analyzer.get_pattern_confidence_levels()
    high_confidence = sum(1 for d in confidence_data.values() if d['confidence'] == 'high')

    return f"""
╔══════════════════════════════════════════════════════════════╗
║                   TRAINING DATA OVERVIEW                     ║
╚══════════════════════════════════════════════════════════════╝

Total Queries: {total_requests}
Unique Models: {unique_models}
User Feedback: {feedback_count}
High-Confidence Patterns: {high_confidence}/6

Status: {'✓ Ready for smart routing' if high_confidence >= 3 else '⚠ Needs more training data'}
"""


def render_pattern_distribution(analyzer: QueryPatternAnalyzer) -> str:
    """Render pattern distribution section."""
    confidence_data = analyzer.get_pattern_confidence_levels()

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║                  PATTERN DISTRIBUTION                        ║",
        "╚══════════════════════════════════════════════════════════════╝",
        ""
    ]

    max_count = max((d['sample_count'] for d in confidence_data.values()), default=1)

    for pattern, data in sorted(confidence_data.items()):
        bar = render_progress_bar(data['sample_count'], max(max_count, 20), width=30)
        confidence_icon = {
            'high': '✓',
            'medium': '~',
            'low': '✗'
        }[data['confidence']]

        lines.append(f"{confidence_icon} {pattern.ljust(12)} {bar} {data['sample_count']} samples")

    return "\n".join(lines)


def render_top_models(analyzer: QueryPatternAnalyzer, mode: str = "internal") -> str:
    """Render top models section - supports both internal and external modes."""
    # Aggregate performance across all complexities
    all_performance = []
    for complexity in ['simple', 'moderate', 'complex']:
        perf = analyzer.get_provider_performance(complexity=complexity)
        all_performance.extend(perf)

    if not all_performance:
        return "\nNo performance data available yet."

    # Aggregate by model
    model_stats = {}
    for p in all_performance:
        model = p['model']
        if model not in model_stats:
            model_stats[model] = {
                'model': model,
                'provider': p['provider'],
                'request_count': 0,
                'total_cost': 0,
                'quality_scores': [],
                'score': p.get('score', 0)
            }
        model_stats[model]['request_count'] += p['request_count']
        model_stats[model]['total_cost'] += p['avg_cost'] * p['request_count']
        if p.get('avg_quality'):
            model_stats[model]['quality_scores'].append(p['avg_quality'])

    # Calculate aggregated metrics
    performance = []
    for model, stats in model_stats.items():
        avg_cost = stats['total_cost'] / stats['request_count'] if stats['request_count'] > 0 else 0
        avg_quality = sum(stats['quality_scores']) / len(stats['quality_scores']) if stats['quality_scores'] else 0.5

        composite_score = (
            avg_quality * 0.5 +
            (1 - min(avg_cost / 0.01, 1)) * 0.3 +
            min(stats['request_count'] / 100, 1) * 0.2
        )

        performance.append({
            'model': model,
            'provider': stats['provider'],
            'request_count': stats['request_count'],
            'avg_cost': avg_cost,
            'quality_score': avg_quality,
            'composite_score': composite_score
        })

    performance.sort(key=lambda x: x['composite_score'], reverse=True)
    top_10 = performance[:10]

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║                    TOP PERFORMING MODELS                     ║",
        "╚══════════════════════════════════════════════════════════════╝",
        ""
    ]

    if mode == "internal":
        lines.append("Rank  Model                    Score   Quality  Cost       Requests")
        lines.append("────  ─────────────────────────────────────────────────────────────")

        for i, p in enumerate(top_10, 1):
            lines.append(
                f"{i:2}.   {p['model'][:24].ljust(24)} {p['composite_score']:.3f}   "
                f"{p['quality_score']:.2f}     ${p['avg_cost']:.5f}  {p['request_count']:4}"
            )
    else:
        lines.append("Rank  Tier              Score   Quality  Cost       Requests")
        lines.append("────  ──────────────────────────────────────────────────────")

        for i, p in enumerate(top_10, 1):
            tier = get_public_label(p['model'])
            lines.append(
                f"{i:2}.   {tier[:18].ljust(18)} {p['composite_score']:.3f}   "
                f"{p['quality_score']:.2f}     ${p['avg_cost']:.5f}  {p['request_count']:4}"
            )

    return "\n".join(lines)


def render_savings_projection(analyzer: QueryPatternAnalyzer) -> str:
    """Render savings projection section."""
    import sqlite3
    conn = sqlite3.connect(analyzer.db_path)
    cursor = conn.cursor()

    # Try requests table first, then response_cache
    cursor.execute("""
        SELECT SUM(cost), COUNT(*), AVG(cost)
        FROM requests
        WHERE date(timestamp) >= date('now', '-30 days')
    """)
    row = cursor.fetchone()

    if not row or row[0] is None or row[1] == 0:
        # Try response_cache table
        cursor.execute("""
            SELECT SUM(cost), COUNT(*), AVG(cost)
            FROM response_cache
            WHERE date(created_at) >= date('now', '-30 days')
        """)
        row = cursor.fetchone()

    current_cost = row[0] or 0
    request_count = row[1] or 0
    avg_cost = row[2] or 0

    conn.close()

    if request_count == 0:
        return "\n(Insufficient data for savings projection)"

    # Aggregate performance across all complexities
    all_performance = []
    for complexity in ['simple', 'moderate', 'complex']:
        perf = analyzer.get_provider_performance(complexity=complexity)
        all_performance.extend(perf)

    if not all_performance:
        return "\n(No performance data for savings projection)"

    # Aggregate by model
    model_stats = {}
    for p in all_performance:
        model = p['model']
        if model not in model_stats:
            model_stats[model] = {
                'model': model,
                'request_count': 0,
                'total_cost': 0,
                'quality_scores': []
            }
        model_stats[model]['request_count'] += p['request_count']
        model_stats[model]['total_cost'] += p['avg_cost'] * p['request_count']
        if p.get('avg_quality'):
            model_stats[model]['quality_scores'].append(p['avg_quality'])

    # Calculate final stats
    performance = []
    for model, stats in model_stats.items():
        avg_cost = stats['total_cost'] / stats['request_count'] if stats['request_count'] > 0 else 0
        avg_quality = sum(stats['quality_scores']) / len(stats['quality_scores']) if stats['quality_scores'] else 0.5

        performance.append({
            'model': model,
            'avg_cost': avg_cost,
            'quality_score': avg_quality
        })

    # Find best cheap model
    cheap_model = min(
        [p for p in performance if p['quality_score'] >= 0.7],
        key=lambda x: x['avg_cost'],
        default=min(performance, key=lambda x: x['avg_cost']) if performance else None
    )

    if not cheap_model:
        return "\n(Unable to calculate savings projection)"

    optimized_cost = cheap_model['avg_cost'] * request_count
    savings = current_cost - optimized_cost
    savings_pct = (savings / current_cost * 100) if current_cost > 0 else 0

    return f"""
╔══════════════════════════════════════════════════════════════╗
║                   SAVINGS PROJECTION (30d)                   ║
╚══════════════════════════════════════════════════════════════╝

Current Monthly Cost:    ${current_cost:.4f}
Optimized Monthly Cost:  ${optimized_cost:.4f}
────────────────────────────────────────────────────────────────
Potential Savings:       ${savings:.4f} ({savings_pct:.1f}% reduction)
Annualized Savings:      ${savings * 12:.2f}/year

Using: {get_public_label(cheap_model['model'])} (Quality: {cheap_model['quality_score']:.2f})
"""


def render_learning_progress(analyzer: QueryPatternAnalyzer) -> str:
    """Render learning progress section."""
    confidence_data = analyzer.get_pattern_confidence_levels()

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║                    LEARNING PROGRESS                         ║",
        "╚══════════════════════════════════════════════════════════════╝",
        ""
    ]

    for pattern, data in sorted(confidence_data.items()):
        progress = min(data['sample_count'] / 20, 1.0)  # 20 = high confidence threshold
        bar = render_progress_bar(data['sample_count'], 20, width=25)

        lines.append(f"{pattern.ljust(12)} {bar}")

        if data['samples_needed'] > 0:
            lines.append(f"{''.ljust(12)} Need {data['samples_needed']} more for high confidence")
        lines.append("")

    return "\n".join(lines)


def get_interactive_mode() -> str:
    """Display interactive menu and get user's mode choice.

    Returns:
        str: 'internal' or 'external'
    """
    print("\n")
    print("╔══════════════════════════════════════════╗")
    print("║  Learning Intelligence Dashboard         ║")
    print("║  ⚠️  INTERNAL USE ONLY - ADMIN VERSION   ║")
    print("╚══════════════════════════════════════════╝")
    print()
    print("Select your view:")
    print()
    print("  1. Admin View (Default - INTERNAL)")
    print("     → Shows actual model names")
    print("     → Full technical details")
    print("     → DO NOT share with customers")
    print()
    print("  2. Customer View Preview")
    print("     → Shows performance tiers")
    print("     → Hides technical details")
    print()

    while True:
        try:
            choice = input("Enter choice (1-2) [1]: ").strip()

            # Default to 1 (Admin View) if empty
            if choice == "":
                choice = "1"

            if choice == "1":
                return "internal"
            elif choice == "2":
                return "external"
            else:
                print("\nInvalid choice. Please enter 1 or 2.\n")
        except (KeyboardInterrupt, EOFError):
            print("\n\nCancelled by user.")
            sys.exit(0)


def main():
    """Main dashboard entry point - ADMIN VERSION."""
    parser = argparse.ArgumentParser(
        description="Learning Intelligence Dashboard - ADMIN VERSION (INTERNAL USE ONLY)"
    )
    parser.add_argument(
        "--mode",
        choices=["internal", "external"],
        default=None,
        help="View mode: internal (show models) or external (show tiers)"
    )
    args = parser.parse_args()

    # If no mode specified, use interactive menu (defaults to admin view)
    if args.mode is None:
        mode = get_interactive_mode()
    else:
        mode = args.mode

    # Initialize analyzer
    db_path = os.path.join(os.path.dirname(__file__), '..', 'optimizer.db')

    if not os.path.exists(db_path):
        print(f"Error: Database not found: {db_path}")
        print("\nRun init_test_data.py first to create sample data.")
        sys.exit(1)

    analyzer = QueryPatternAnalyzer(db_path=db_path)

    # Render dashboard with clear mode label
    mode_label = "INTERNAL ADMIN VIEW" if mode == "internal" else "CUSTOMER VIEW PREVIEW"

    # Add security warning for internal mode
    warning = ""
    if mode == "internal":
        warning = "\n⚠️  WARNING: This view contains competitive intelligence - DO NOT share with customers\n"

    print("\n")
    print("=" * 66)
    print(f"  LEARNING INTELLIGENCE DASHBOARD - {mode_label}")
    print("=" * 66)
    if warning:
        print(warning)

    print(render_training_overview(analyzer))
    print(render_pattern_distribution(analyzer))
    print(render_top_models(analyzer, mode=mode))
    print(render_savings_projection(analyzer))
    print(render_learning_progress(analyzer))

    print("\n" + "=" * 66)
    if mode == "internal":
        print("⚠️  INTERNAL USE ONLY - Contains proprietary model information")
        print("=" * 66)
    print()


if __name__ == "__main__":
    main()
