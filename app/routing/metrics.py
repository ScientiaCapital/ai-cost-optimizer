"""Metrics collection for routing decisions."""
import sqlite3
import hashlib
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.routing.models import RoutingDecision

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and stores routing metrics for analysis.

    Tracks routing decisions, cost savings, quality scores, and
    confidence levels for monitoring and optimization.

    Design Note:
        Cost savings are calculated by comparing auto_route=True (intelligent
        hybrid routing) vs auto_route=False (baseline complexity routing) in
        aggregate, rather than tracking per-request baseline costs. This
        simplifies implementation while still providing meaningful savings
        metrics for A/B testing and ROI analysis.
    """

    def __init__(self, db_path: str = "optimizer.db"):
        """Initialize metrics collector.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

        # Ensure table exists
        from app.database import create_routing_metrics_table
        create_routing_metrics_table(db_path)

    def track_decision(
        self,
        prompt: str,
        decision: RoutingDecision,
        auto_route: bool
    ) -> None:
        """Track a routing decision to the database.

        Args:
            prompt: The original prompt
            decision: The routing decision made
            auto_route: Whether auto_route was enabled
        """
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        timestamp = datetime.now().isoformat()

        # Extract metadata
        complexity_score = decision.metadata.get('complexity')
        pattern = decision.metadata.get('pattern')

        # Estimate cost (placeholder - would integrate with actual pricing)
        estimated_cost = self._estimate_cost(decision.provider, decision.model)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO routing_metrics (
                    timestamp, prompt_hash, strategy_used, provider, model,
                    confidence, auto_route, estimated_cost, complexity_score,
                    pattern, fallback_used, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                prompt_hash,
                decision.strategy_used,
                decision.provider,
                decision.model,
                decision.confidence,
                1 if auto_route else 0,
                estimated_cost,
                complexity_score,
                pattern,
                1 if decision.fallback_used else 0,
                json.dumps(decision.metadata)
            ))

            conn.commit()
            logger.debug(f"Tracked routing decision: {decision.provider}/{decision.model}")

        except sqlite3.Error as e:
            logger.error(f"Failed to track metrics: {e}")
        finally:
            conn.close()

    def get_cost_savings(self, days: int = 7) -> Dict[str, Any]:
        """Calculate cost savings from intelligent routing.

        Compares actual costs (auto_route=True) vs baseline costs
        (auto_route=False) to estimate savings.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with total_saved, percent_saved, intelligent_cost, baseline_cost
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get costs for auto_route=True (intelligent routing)
            cursor.execute("""
                SELECT SUM(estimated_cost)
                FROM routing_metrics
                WHERE auto_route = 1
                AND datetime(timestamp) >= datetime('now', '-' || ? || ' days')
            """, (days,))

            intelligent_cost = cursor.fetchone()[0] or 0.0

            # Get costs for auto_route=False (baseline complexity routing)
            cursor.execute("""
                SELECT SUM(estimated_cost)
                FROM routing_metrics
                WHERE auto_route = 0
                AND datetime(timestamp) >= datetime('now', '-' || ? || ' days')
            """, (days,))

            baseline_cost = cursor.fetchone()[0] or 0.0

            # Calculate savings
            total_saved = baseline_cost - intelligent_cost
            percent_saved = (total_saved / baseline_cost * 100) if baseline_cost > 0 else 0.0

            return {
                "total_saved": total_saved,
                "percent_saved": percent_saved,
                "intelligent_cost": intelligent_cost,
                "baseline_cost": baseline_cost,
                "period_days": days
            }

        except sqlite3.Error as e:
            logger.error(f"Failed to calculate cost savings: {e}")
            return {
                "total_saved": 0.0,
                "percent_saved": 0.0,
                "intelligent_cost": 0.0,
                "baseline_cost": 0.0,
                "period_days": days,
                "error": str(e)
            }

        finally:
            if conn:
                conn.close()

    def aggregate_by_strategy(self, days: int = 7) -> List[Dict[str, Any]]:
        """Aggregate metrics by strategy type.

        Args:
            days: Number of days to analyze

        Returns:
            List of dicts with strategy, count, avg_cost, avg_confidence
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    strategy_used,
                    COUNT(*) as count,
                    AVG(estimated_cost) as avg_cost,
                    SUM(CASE WHEN confidence = 'high' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as high_conf_pct
                FROM routing_metrics
                WHERE datetime(timestamp) >= datetime('now', '-' || ? || ' days')
                GROUP BY strategy_used
                ORDER BY count DESC
            """, (days,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    "strategy": row[0],
                    "count": row[1],
                    "avg_cost": row[2],
                    "high_confidence_pct": row[3] * 100
                })

            return results

        except sqlite3.Error as e:
            logger.error(f"Failed to aggregate by strategy: {e}")
            return []

        finally:
            if conn:
                conn.close()

    def aggregate_by_confidence(self, days: int = 7) -> List[Dict[str, Any]]:
        """Aggregate metrics by confidence level.

        Args:
            days: Number of days to analyze

        Returns:
            List of dicts with confidence, count, avg_cost
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    confidence,
                    COUNT(*) as count,
                    AVG(estimated_cost) as avg_cost
                FROM routing_metrics
                WHERE datetime(timestamp) >= datetime('now', '-' || ? || ' days')
                GROUP BY confidence
                ORDER BY count DESC
            """, (days,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    "confidence": row[0],
                    "count": row[1],
                    "avg_cost": row[2]
                })

            return results

        except sqlite3.Error as e:
            logger.error(f"Failed to aggregate by confidence: {e}")
            return []

        finally:
            if conn:
                conn.close()

    def _estimate_cost(self, provider: str, model: str) -> float:
        """Estimate cost for a provider/model combination.

        Placeholder implementation - would integrate with actual pricing.

        Args:
            provider: Provider name
            model: Model name

        Returns:
            Estimated cost in USD
        """
        # Simplified cost estimates (per 1K tokens)
        cost_map = {
            ("gemini", "gemini-1.5-flash"): 0.00012,
            ("claude", "claude-3-haiku-20240307"): 0.00095,
            ("claude", "claude-3-5-sonnet-20241022"): 0.0030,
            ("openrouter", "google/gemini-flash-1.5"): 0.00015,
            ("openrouter", "anthropic/claude-3-haiku"): 0.00100,
        }

        return cost_map.get((provider, model), 0.001)
