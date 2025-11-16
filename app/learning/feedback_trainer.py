"""Automated learning pipeline from user feedback."""
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.database.postgres import get_connection, get_cursor
from app.learning.query_pattern_analyzer import QueryPatternAnalyzer

logger = logging.getLogger(__name__)


def _is_sqlite(conn) -> bool:
    """Check if connection is SQLite."""
    return hasattr(conn, 'row_factory')


class FeedbackTrainer:
    """Retrains routing recommendations from user feedback.

    Uses confidence-based thresholds to only update routing when
    sufficient quality feedback has been collected.
    """

    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 10
    MEDIUM_CONFIDENCE_THRESHOLD = 5
    MIN_QUALITY_SCORE = 3.5
    MIN_CORRECTNESS_RATE = 0.7

    def __init__(self):
        """Initialize trainer with database connection."""
        self.analyzer = QueryPatternAnalyzer(db_path=None)  # Uses PostgreSQL

    def retrain(self, dry_run: bool = False) -> Dict[str, Any]:
        """Run retraining cycle.

        Args:
            dry_run: If True, preview changes without applying

        Returns:
            Retraining summary with changes made
        """
        run_id = str(uuid.uuid4())
        logger.info(f"Starting retraining run {run_id} (dry_run={dry_run})")

        # 1. Aggregate feedback by pattern + model
        performance_data = self._aggregate_feedback()

        changes = []

        # 2. Compute confidence and update routing
        for pattern, models_data in performance_data.items():
            for model, stats in models_data.items():
                confidence = self._calculate_confidence(
                    sample_count=stats['count'],
                    avg_quality=stats['avg_quality'],
                    correctness_rate=stats['correctness']
                )

                # 3. Only update if meets threshold
                if confidence in ['high', 'medium']:
                    change = {
                        'pattern': pattern,
                        'model': model,
                        'confidence': confidence,
                        'sample_count': stats['count'],
                        'avg_quality': stats['avg_quality'],
                        'correctness_rate': stats['correctness']
                    }

                    changes.append(change)

                    if not dry_run:
                        self._update_routing_weights(pattern, model, stats)
                        self._store_performance_history(
                            pattern, model, stats, confidence, run_id
                        )

        # 4. Log retraining run
        result = {
            'run_id': run_id,
            'timestamp': datetime.now().isoformat(),
            'patterns_updated': len(set(c['pattern'] for c in changes)),
            'total_changes': len(changes),
            'changes': changes,
            'dry_run': dry_run
        }

        if not dry_run:
            self._log_retraining_run(result)

        logger.info(f"Retraining complete: {result['total_changes']} changes")

        return result

    def _calculate_confidence(
        self,
        sample_count: int,
        avg_quality: float,
        correctness_rate: float
    ) -> str:
        """Calculate confidence level for pattern.

        Args:
            sample_count: Number of feedback samples
            avg_quality: Average quality score (1-5)
            correctness_rate: Correctness rate (0-1)

        Returns:
            Confidence level: 'high', 'medium', or 'low'
        """
        # Check quality thresholds
        if avg_quality < self.MIN_QUALITY_SCORE or correctness_rate < self.MIN_CORRECTNESS_RATE:
            return "low"

        # High confidence: lots of samples + excellent metrics
        if sample_count >= self.HIGH_CONFIDENCE_THRESHOLD and avg_quality >= 4.0 and correctness_rate >= 0.8:
            return "high"

        # Medium confidence: sufficient samples + good metrics
        if sample_count >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return "medium"

        # Low confidence: insufficient data
        return "low"

    def _aggregate_feedback(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Aggregate feedback by pattern and model.

        Returns:
            Nested dict: {pattern: {model: {stats}}}
        """
        with get_connection() as conn:
            cursor = get_cursor(conn, dict_cursor=True)
            is_sqlite = _is_sqlite(conn)

            if is_sqlite:
                # SQLite query
                query = """
                    SELECT
                        prompt_pattern,
                        selected_model,
                        COUNT(*) as sample_count,
                        AVG(quality_score) as avg_quality,
                        AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as correctness_rate,
                        AVG(complexity_score) as avg_complexity
                    FROM routing_feedback
                    WHERE prompt_pattern IS NOT NULL
                      AND selected_model IS NOT NULL
                      AND datetime(timestamp) > datetime('now', '-90 days')
                    GROUP BY prompt_pattern, selected_model
                    HAVING COUNT(*) >= 3
                """
                cursor.execute(query)
            else:
                # PostgreSQL query
                query = """
                    SELECT
                        prompt_pattern,
                        selected_model,
                        COUNT(*) as sample_count,
                        AVG(quality_score) as avg_quality,
                        AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as correctness_rate,
                        AVG(complexity_score) as avg_complexity
                    FROM routing_feedback
                    WHERE prompt_pattern IS NOT NULL
                      AND selected_model IS NOT NULL
                      AND timestamp > NOW() - INTERVAL '90 days'
                    GROUP BY prompt_pattern, selected_model
                    HAVING COUNT(*) >= 3
                """
                cursor.execute(query)

            rows = cursor.fetchall()

            # Organize by pattern -> model
            result = {}
            for row in rows:
                # Handle both dict-like cursor and sqlite3.Row
                if is_sqlite:
                    row = dict(row)

                pattern = row['prompt_pattern']
                model = row['selected_model']

                if pattern not in result:
                    result[pattern] = {}

                result[pattern][model] = {
                    'count': row['sample_count'],
                    'avg_quality': float(row['avg_quality']),
                    'correctness': float(row['correctness_rate']),
                    'avg_complexity': float(row['avg_complexity']) if row['avg_complexity'] else 0.5
                }

            return result

    def _update_routing_weights(
        self,
        pattern: str,
        model: str,
        stats: Dict[str, Any]
    ):
        """Update routing weights for pattern-model pair.

        Args:
            pattern: Prompt pattern
            model: Model name
            stats: Performance statistics
        """
        # Update QueryPatternAnalyzer weights
        # This is application-specific logic
        logger.info(f"Updating weights for {pattern} -> {model}: quality={stats['avg_quality']:.2f}")

        # Implementation depends on how QueryPatternAnalyzer stores recommendations
        # For now, just log the update
        pass

    def _store_performance_history(
        self,
        pattern: str,
        model: str,
        stats: Dict[str, Any],
        confidence: str,
        run_id: str
    ):
        """Store performance metrics to history table.

        Args:
            pattern: Prompt pattern
            model: Model name
            stats: Performance statistics
            confidence: Confidence level
            run_id: Retraining run ID
        """
        with get_connection() as conn:
            cursor = get_cursor(conn, dict_cursor=False)
            is_sqlite = _is_sqlite(conn)

            # Extract provider from model name
            provider = model.split('/')[0] if '/' in model else 'unknown'

            if is_sqlite:
                # SQLite doesn't have model_performance_history table in migrations
                # Skip for now - this is for PostgreSQL deployment
                logger.debug(f"Skipping performance history storage for SQLite: {pattern}/{model}")
                return
            else:
                # PostgreSQL
                cursor.execute("""
                    INSERT INTO model_performance_history (
                        pattern, provider, model,
                        avg_quality_score, correctness_rate, sample_count, confidence_level,
                        avg_cost, total_cost, updated_at, retraining_run_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    pattern,
                    provider,
                    model,
                    stats['avg_quality'],
                    stats['correctness'],
                    stats['count'],
                    confidence,
                    None,  # avg_cost - compute if needed
                    None,  # total_cost
                    datetime.now(),
                    run_id
                ))

    def _log_retraining_run(self, result: Dict[str, Any]):
        """Log retraining run metadata.

        Args:
            result: Retraining result summary
        """
        logger.info(f"Retraining run {result['run_id']}: {result['total_changes']} changes applied")

    def _get_current_weights(self) -> Dict[str, Any]:
        """Get current routing weights for comparison.

        Returns:
            Current weights
        """
        # Placeholder for getting current state
        return {}
