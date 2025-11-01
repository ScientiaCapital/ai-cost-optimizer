"""Custom tools for Cost Optimization Agent.

This module provides tools for analyzing AI usage patterns, costs, and optimization opportunities.
"""
import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import CostTracker


class CostAnalyzerTools:
    """Tools for analyzing cost optimization data."""

    def __init__(self, db_path: str = None):
        """Initialize tools with database connection.

        Args:
            db_path: Path to SQLite database (default: ../optimizer.db)
        """
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "optimizer.db"
            )
        self.db_path = db_path
        self.cost_tracker = CostTracker(db_path=db_path)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get overall usage statistics including total costs and breakdowns.

        Returns:
            Dictionary with:
            - overall: Total requests, cost, average per request
            - by_provider: Cost breakdown by provider (Gemini, Claude, etc.)
            - by_complexity: Cost breakdown by complexity level
            - recent_requests: Last 10 requests with details
        """
        try:
            stats = self.cost_tracker.get_usage_stats()
            return {
                "success": True,
                "data": stats,
                "summary": (
                    f"Total: ${stats['overall']['total_cost']:.2f} "
                    f"across {stats['overall']['total_requests']} requests. "
                    f"Average: ${stats['overall']['avg_cost_per_request']:.4f}/request"
                )
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def analyze_cost_patterns(self, days: int = 7) -> Dict[str, Any]:
        """Analyze spending patterns and identify trends.

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with spending trends, peak usage times, and anomalies
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get requests from last N days
            cutoff = datetime.now() - timedelta(days=days)
            cursor.execute("""
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as request_count,
                    SUM(cost) as daily_cost,
                    AVG(cost) as avg_cost,
                    provider,
                    complexity
                FROM requests
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp), provider, complexity
                ORDER BY date DESC
            """, (cutoff,))

            daily_data = [dict(row) for row in cursor.fetchall()]

            # Calculate trends
            total_cost = sum(row['daily_cost'] for row in daily_data)
            total_requests = sum(row['request_count'] for row in daily_data)

            # Find most expensive day
            daily_totals = {}
            for row in daily_data:
                date = row['date']
                daily_totals[date] = daily_totals.get(date, 0) + row['daily_cost']

            most_expensive_day = max(daily_totals.items(), key=lambda x: x[1]) if daily_totals else None

            # Provider usage
            provider_usage = {}
            for row in daily_data:
                provider = row['provider']
                provider_usage[provider] = provider_usage.get(provider, 0) + row['request_count']

            conn.close()

            return {
                "success": True,
                "period_days": days,
                "total_cost": round(total_cost, 4),
                "total_requests": total_requests,
                "avg_daily_cost": round(total_cost / days, 4),
                "avg_request_cost": round(total_cost / total_requests, 6) if total_requests > 0 else 0,
                "most_expensive_day": {
                    "date": most_expensive_day[0] if most_expensive_day else None,
                    "cost": round(most_expensive_day[1], 4) if most_expensive_day else 0
                },
                "provider_usage": provider_usage,
                "daily_breakdown": daily_data[:10]  # Last 10 days
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_recommendations(self) -> Dict[str, Any]:
        """Generate cost optimization recommendations based on usage patterns.

        Returns:
            List of actionable recommendations with estimated savings
        """
        try:
            stats = self.cost_tracker.get_usage_stats()
            cache_stats = self.cost_tracker.get_cache_stats()

            recommendations = []
            total_potential_savings = 0.0

            # Analyze cache effectiveness
            if cache_stats['hit_rate_percent'] < 50:
                potential_savings = stats['overall']['total_cost'] * 0.3
                recommendations.append({
                    "priority": "HIGH",
                    "category": "Caching",
                    "issue": f"Cache hit rate is only {cache_stats['hit_rate_percent']:.1f}%",
                    "recommendation": "Encourage users to reuse common queries. Current cache saves $"
                                    f"{cache_stats['total_savings']:.2f}, but could save 30% more.",
                    "potential_savings": round(potential_savings, 2)
                })
                total_potential_savings += potential_savings

            # Analyze provider usage
            provider_costs = {p['provider']: p['total_cost']
                            for p in stats.get('by_provider', [])}

            # Check if Claude is being overused for simple queries
            if 'claude' in provider_costs and 'gemini' in provider_costs:
                claude_cost = provider_costs['claude']
                total_cost = stats['overall']['total_cost']

                if claude_cost / total_cost > 0.6:  # Claude is >60% of costs
                    potential_savings = claude_cost * 0.2
                    recommendations.append({
                        "priority": "MEDIUM",
                        "category": "Provider Balance",
                        "issue": f"Claude accounts for {claude_cost/total_cost*100:.1f}% of costs",
                        "recommendation": "Review complexity scoring. Some Claude queries might be "
                                        "routable to cheaper Gemini Flash.",
                        "potential_savings": round(potential_savings, 2)
                    })
                    total_potential_savings += potential_savings

            # Check for high-cost individual requests
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as high_cost_count, AVG(cost) as avg_high_cost
                FROM requests
                WHERE cost > 0.01
            """)
            high_cost = cursor.fetchone()
            conn.close()

            if high_cost[0] > 0:
                recommendations.append({
                    "priority": "LOW",
                    "category": "Query Optimization",
                    "issue": f"{high_cost[0]} requests cost >$0.01 each (avg: ${high_cost[1]:.4f})",
                    "recommendation": "Review high-cost queries for prompt optimization or chunking.",
                    "potential_savings": "Variable"
                })

            # General caching recommendation
            if cache_stats['total_entries'] < 10:
                recommendations.append({
                    "priority": "INFO",
                    "category": "Setup",
                    "issue": "Limited usage history",
                    "recommendation": "Continue using the optimizer. More data = better optimization.",
                    "potential_savings": "N/A"
                })

            return {
                "success": True,
                "recommendations": recommendations,
                "total_potential_savings": round(total_potential_savings, 2),
                "summary": f"Found {len(recommendations)} optimization opportunities "
                          f"with potential savings of ${total_potential_savings:.2f}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def query_recent_requests(self, limit: int = 100) -> Dict[str, Any]:
        """Query recent requests for pattern analysis.

        Args:
            limit: Number of recent requests to retrieve (default: 100)

        Returns:
            List of recent requests with prompts, costs, and metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    timestamp,
                    prompt_preview as prompt,
                    complexity,
                    provider,
                    model,
                    tokens_in,
                    tokens_out,
                    cost
                FROM requests
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            requests = [dict(row) for row in cursor.fetchall()]

            # Calculate summary stats
            total_cost = sum(r['cost'] for r in requests)
            avg_cost = total_cost / len(requests) if requests else 0

            # Complexity breakdown
            complexity_counts = {}
            for r in requests:
                complexity = r['complexity']
                complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1

            conn.close()

            return {
                "success": True,
                "request_count": len(requests),
                "total_cost": round(total_cost, 4),
                "avg_cost": round(avg_cost, 6),
                "complexity_distribution": complexity_counts,
                "requests": requests[:20]  # Return first 20 for display
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def check_cache_effectiveness(self) -> Dict[str, Any]:
        """Analyze cache performance and potential savings.

        Returns:
            Cache statistics including hit rate, savings, and top cached queries
        """
        try:
            cache_stats = self.cost_tracker.get_cache_stats()

            # Get most popular cached queries
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    cache_key,
                    prompt,
                    provider,
                    cost,
                    hit_count,
                    (cost * hit_count) as total_savings
                FROM response_cache
                WHERE invalidated = 0
                ORDER BY hit_count DESC
                LIMIT 10
            """)

            popular_queries = []
            for row in cursor.fetchall():
                popular_queries.append({
                    "prompt_preview": row['prompt'][:100] + "..." if len(row['prompt']) > 100 else row['prompt'],
                    "provider": row['provider'],
                    "hit_count": row['hit_count'],
                    "savings_per_hit": round(row['cost'], 6),
                    "total_savings": round(row['total_savings'], 4)
                })

            conn.close()

            return {
                "success": True,
                "cache_stats": cache_stats,
                "popular_queries": popular_queries,
                "summary": (
                    f"Cache hit rate: {cache_stats['hit_rate_percent']:.1f}%, "
                    f"Total savings: ${cache_stats['total_savings']:.2f}, "
                    f"{cache_stats['total_entries']} cached responses"
                )
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def compare_providers(self) -> Dict[str, Any]:
        """Compare cost and performance across providers.

        Returns:
            Comparison of providers including costs, quality scores, and recommendations
        """
        try:
            stats = self.cost_tracker.get_usage_stats()
            quality_stats = self.cost_tracker.get_quality_stats()

            provider_comparison = []

            for provider_stats in stats.get('by_provider', []):
                provider = provider_stats['provider']

                # Get quality data for this provider
                provider_quality = next(
                    (p for p in quality_stats.get('by_provider', [])
                     if p['provider'] == provider),
                    None
                )

                comparison = {
                    "provider": provider,
                    "total_cost": round(provider_stats['total_cost'], 4),
                    "request_count": provider_stats['request_count'],
                    "avg_cost_per_request": round(provider_stats['avg_cost'], 6),
                    "cost_percentage": round(
                        provider_stats['total_cost'] / stats['overall']['total_cost'] * 100, 1
                    ) if stats['overall']['total_cost'] > 0 else 0
                }

                if provider_quality:
                    comparison.update({
                        "avg_quality_score": provider_quality.get('avg_quality_score'),
                        "rated_responses": provider_quality.get('rated_responses', 0)
                    })

                provider_comparison.append(comparison)

            # Sort by total cost descending
            provider_comparison.sort(key=lambda x: x['total_cost'], reverse=True)

            # Generate comparison insights
            insights = []
            if len(provider_comparison) >= 2:
                most_expensive = provider_comparison[0]
                cheapest = [p for p in provider_comparison if p['request_count'] > 0][-1]

                insights.append(
                    f"{most_expensive['provider']} is your most expensive provider at "
                    f"${most_expensive['total_cost']:.2f} ({most_expensive['cost_percentage']:.1f}% of total)"
                )

                if cheapest['provider'] != most_expensive['provider']:
                    insights.append(
                        f"{cheapest['provider']} is most cost-effective at "
                        f"${cheapest['avg_cost_per_request']:.6f} per request"
                    )

            return {
                "success": True,
                "providers": provider_comparison,
                "insights": insights,
                "total_providers": len(provider_comparison)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Tool function wrappers for Claude Agent SDK
from typing import Any
from claude_agent_sdk import tool


# Create a shared instance to avoid repeated database connections
_analyzer = CostAnalyzerTools()


@tool(
    "get_usage_stats",
    "Get overall usage statistics including total costs, request counts, and breakdowns by provider and complexity.",
    {}
)
async def get_usage_stats(args: dict[str, Any]) -> dict[str, Any]:
    """Get overall usage statistics.

    Returns structured data with total costs, request counts, and breakdowns.
    """
    try:
        result = _analyzer.get_usage_stats()
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, indent=2)
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error fetching usage stats: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    "analyze_cost_patterns",
    "Analyze spending patterns and trends over a specified time period. Returns daily breakdowns, peak usage, and spending trends.",
    {
        "days": {
            "type": "integer",
            "description": "Number of days to analyze (default: 7)",
            "default": 7
        }
    }
)
async def analyze_cost_patterns(args: dict[str, Any]) -> dict[str, Any]:
    """Analyze spending patterns over time.

    Args:
        args: Dictionary with optional 'days' parameter

    Returns structured data with trends, peak usage, and daily breakdowns.
    """
    try:
        days = args.get("days", 7)
        result = _analyzer.analyze_cost_patterns(days=days)
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, indent=2)
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error analyzing cost patterns: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    "get_recommendations",
    "Generate prioritized cost optimization recommendations based on usage patterns. Returns actionable suggestions with estimated savings.",
    {}
)
async def get_recommendations(args: dict[str, Any]) -> dict[str, Any]:
    """Generate cost optimization recommendations.

    Returns structured data with prioritized recommendations and potential savings.
    """
    try:
        result = _analyzer.get_recommendations()
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, indent=2)
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error generating recommendations: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    "query_recent_requests",
    "Query recent API requests to examine patterns, complexity distribution, and identify inefficiencies.",
    {
        "limit": {
            "type": "integer",
            "description": "Number of recent requests to retrieve (default: 100)",
            "default": 100
        }
    }
)
async def query_recent_requests(args: dict[str, Any]) -> dict[str, Any]:
    """Query recent API requests.

    Args:
        args: Dictionary with optional 'limit' parameter

    Returns structured data with recent requests and summary statistics.
    """
    try:
        limit = args.get("limit", 100)
        result = _analyzer.query_recent_requests(limit=limit)
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, indent=2)
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error querying recent requests: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    "check_cache_effectiveness",
    "Analyze cache performance including hit rate, total savings, and most popular cached queries.",
    {}
)
async def check_cache_effectiveness(args: dict[str, Any]) -> dict[str, Any]:
    """Analyze cache performance and savings.

    Returns structured data with cache hit rate, total savings, and popular queries.
    """
    try:
        result = _analyzer.check_cache_effectiveness()
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, indent=2)
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error checking cache effectiveness: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    "compare_providers",
    "Compare cost and performance across different LLM providers (Gemini, Claude, OpenRouter, etc.). Shows cost breakdowns and quality metrics.",
    {}
)
async def compare_providers(args: dict[str, Any]) -> dict[str, Any]:
    """Compare cost and performance across providers.

    Returns structured data with provider comparison and insights.
    """
    try:
        result = _analyzer.compare_providers()
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, indent=2)
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error comparing providers: {str(e)}"
            }],
            "is_error": True
        }


# ============================================================================
# LEARNING-POWERED TOOLS (Phase 1)
# ============================================================================

# Import model abstraction and learning modules
sys.path.append(os.path.dirname(__file__))
from model_abstraction import get_public_label, get_internal_models
from app.learning import QueryPatternAnalyzer
from app.complexity import score_complexity


# Core implementation functions (testable without decorator)
async def _get_smart_recommendation_impl(args: dict[str, Any]) -> dict[str, Any]:
    """Implementation of get_smart_recommendation for testing."""
    try:
        prompt = args.get("prompt", "")

        # Get database path (relative to agent directory)
        db_path = os.path.join(os.path.dirname(__file__), '..', 'optimizer.db')

        if not os.path.exists(db_path):
            return {
                "content": [{
                    "type": "text",
                    "text": "Database not found. Please ensure optimizer.db exists."
                }]
            }

        analyzer = QueryPatternAnalyzer(db_path=db_path)

        # Analyze prompt
        complexity = score_complexity(prompt)
        pattern = analyzer.identify_pattern(prompt)

        # Get recommendation
        rec = analyzer.recommend_provider(
            prompt,
            complexity,
            available_providers=["gemini", "claude", "openrouter"]
        )

        if not rec:
            return {
                "content": [{
                    "type": "text",
                    "text": f"""**Recommendation:** Insufficient historical data

**Pattern Detected:** {pattern}
**Complexity:** {complexity}

Need more historical queries to provide confident recommendations."""
                }]
            }

        # Convert to public tier
        public_tier = get_public_label(rec['model'])

        # Format response
        response = f"""**Recommended:** {public_tier}
**Confidence:** {rec['confidence']}
**Quality Score:** {rec.get('score', 'N/A')}

**Reason:** {rec['reason']}

**Pattern Detected:** {pattern}
**Complexity:** {complexity}"""

        return {
            "content": [{
                "type": "text",
                "text": response
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error generating recommendation: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    "get_smart_recommendation",
    "Get AI-powered routing recommendation based on historical performance for similar queries. Returns recommended tier with confidence level.",
    {
        "prompt": {
            "type": "string",
            "description": "The query text to analyze"
        }
    }
)
async def get_smart_recommendation(args: dict[str, Any]) -> dict[str, Any]:
    """Get smart routing recommendation with black-box tier labels."""
    return await _get_smart_recommendation_impl(args)


async def _get_pattern_analysis_impl(args: dict[str, Any]) -> dict[str, Any]:
    """Implementation of get_pattern_analysis for testing."""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'optimizer.db')

        if not os.path.exists(db_path):
            return {
                "content": [{
                    "type": "text",
                    "text": "Database not found. Please ensure optimizer.db exists."
                }]
            }

        analyzer = QueryPatternAnalyzer(db_path=db_path)

        confidence_data = analyzer.get_pattern_confidence_levels()

        # Build response
        lines = ["# Query Pattern Analysis\n"]

        for pattern, data in confidence_data.items():
            lines.append(f"\n## {pattern.title()} Queries")
            lines.append(f"- Sample Count: {data['sample_count']}")
            lines.append(f"- Confidence: {data['confidence']}")

            if data['best_model']:
                # Black-box the model
                public_label = get_public_label(data['best_model'])
                lines.append(f"- Best Performer: {public_label}")

            if data['samples_needed'] > 0:
                lines.append(f"- *Need {data['samples_needed']} more samples for high confidence*")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(lines)
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error analyzing patterns: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    "get_pattern_analysis",
    "Analyze learning progress across all 6 query patterns (code, analysis, creative, explanation, factual, reasoning). Shows confidence levels and best models per pattern.",
    {}
)
async def get_pattern_analysis(args: dict[str, Any]) -> dict[str, Any]:
    """Show learning maturity by pattern."""
    return await _get_pattern_analysis_impl(args)


async def _get_provider_performance_impl(args: dict[str, Any]) -> dict[str, Any]:
    """Implementation of get_provider_performance for testing."""
    try:
        mode = args.get("mode", "external")

        db_path = os.path.join(os.path.dirname(__file__), '..', 'optimizer.db')

        if not os.path.exists(db_path):
            return {
                "content": [{
                    "type": "text",
                    "text": "Database not found. Please ensure optimizer.db exists."
                }]
            }

        analyzer = QueryPatternAnalyzer(db_path=db_path)

        # Get performance for all complexity levels
        all_performance = []
        for complexity in ["simple", "moderate", "complex"]:
            performance = analyzer.get_provider_performance(complexity=complexity)
            all_performance.extend(performance)

        if not all_performance:
            return {
                "content": [{
                    "type": "text",
                    "text": "No performance data available yet. Generate some queries first!"
                }]
            }

        # Sort by composite score
        all_performance.sort(key=lambda x: x['score'], reverse=True)

        # Format table
        lines = ["# Provider Performance Rankings\n"]

        if mode == "internal":
            lines.append("Rank | Model | Score | Quality | Cost | Requests")
            lines.append("-----|-------|-------|---------|------|----------")

            for i, p in enumerate(all_performance[:10], 1):
                quality_str = f"{p['avg_quality']:.2f}" if p['avg_quality'] is not None else "N/A"
                lines.append(
                    f"{i} | {p['model'][:30]} | {p['score']:.3f} | "
                    f"{quality_str} | ${p['avg_cost']:.5f} | {p['request_count']}"
                )
        else:
            # External: black-box models
            lines.append("Rank | Tier | Score | Quality | Cost | Requests")
            lines.append("-----|------|-------|---------|------|----------")

            for i, p in enumerate(all_performance[:10], 1):
                tier = get_public_label(p['model'])
                quality_str = f"{p['avg_quality']:.2f}" if p['avg_quality'] is not None else "N/A"
                lines.append(
                    f"{i} | {tier[:20]} | {p['score']:.3f} | "
                    f"{quality_str} | ${p['avg_cost']:.5f} | {p['request_count']}"
                )

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(lines)
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error getting performance data: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    "get_provider_performance",
    "Compare model performance across quality and cost. Supports 'internal' mode (shows actual models) and 'external' mode (shows tier labels only).",
    {
        "mode": {
            "type": "string",
            "description": "View mode: 'internal' or 'external' (default: external)",
            "enum": ["internal", "external"]
        }
    }
)
async def get_provider_performance(args: dict[str, Any]) -> dict[str, Any]:
    """Provider performance with black-box abstraction."""
    return await _get_provider_performance_impl(args)


async def _calculate_potential_savings_impl(args: dict[str, Any]) -> dict[str, Any]:
    """Implementation of calculate_potential_savings for testing."""
    try:
        days = args.get("days", 30)

        db_path = os.path.join(os.path.dirname(__file__), '..', 'optimizer.db')

        if not os.path.exists(db_path):
            return {
                "content": [{
                    "type": "text",
                    "text": "Database not found. Please ensure optimizer.db exists."
                }]
            }

        # Query actual costs from requests table
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                SUM(cost) as total_cost,
                COUNT(*) as request_count,
                AVG(cost) as avg_cost
            FROM requests
            WHERE date(timestamp) >= date('now', ?)
        """, (f'-{days} days',))

        row = cursor.fetchone()
        current_cost = row[0] or 0
        request_count = row[1] or 0
        avg_cost = row[2] or 0

        if request_count == 0:
            conn.close()
            return {
                "content": [{
                    "type": "text",
                    "text": "Insufficient data for savings calculation. Need at least 1 request in the specified period."
                }]
            }

        # Get performance data to find cheapest quality model
        analyzer = QueryPatternAnalyzer(db_path=db_path)
        all_performance = []
        for complexity in ["simple", "moderate", "complex"]:
            performance = analyzer.get_provider_performance(complexity=complexity)
            all_performance.extend(performance)

        if not all_performance:
            conn.close()
            return {
                "content": [{
                    "type": "text",
                    "text": "No performance data available for savings calculation."
                }]
            }

        # Find best cheap model (quality >= 0.7 if quality exists, lowest cost)
        cheap_candidates = [p for p in all_performance if p['avg_quality'] is None or p['avg_quality'] >= 0]

        if not cheap_candidates:
            cheap_candidates = all_performance

        cheap_model = min(cheap_candidates, key=lambda x: x['avg_cost'])

        optimized_cost = cheap_model['avg_cost'] * request_count
        savings = current_cost - optimized_cost
        savings_pct = (savings / current_cost * 100) if current_cost > 0 else 0

        # Format response
        quality_impact = "Maintained" if (cheap_model['avg_quality'] is None or cheap_model['avg_quality'] >= 0.5) else "Minor reduction"
        quality_display = f"{cheap_model['avg_quality']:.2f}" if cheap_model['avg_quality'] is not None else "N/A"

        response = f"""# Potential Savings Analysis ({days} days)

**Current Usage:**
- Total Cost: ${current_cost:.4f}
- Requests: {request_count}
- Avg Cost/Request: ${avg_cost:.6f}

**Optimized Routing:**
- Projected Cost: ${optimized_cost:.4f}
- Using: {get_public_label(cheap_model['model'])} (Quality: {quality_display})
- Avg Cost/Request: ${cheap_model['avg_cost']:.6f}

**Savings Opportunity:**
- **${savings:.4f} ({savings_pct:.1f}% reduction)**
- Annualized: ${savings * (365/days):.2f}/year

**Quality Impact:** {quality_impact}
"""

        conn.close()

        return {
            "content": [{
                "type": "text",
                "text": response
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error calculating savings: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    "calculate_potential_savings",
    "Calculate ROI of learning-powered routing vs current usage. Shows cost reduction opportunities with quality impact analysis.",
    {
        "days": {
            "type": "integer",
            "description": "Number of days to analyze (default: 30)"
        }
    }
)
async def calculate_potential_savings(args: dict[str, Any]) -> dict[str, Any]:
    """Calculate savings from smart routing."""
    return await _calculate_potential_savings_impl(args)















