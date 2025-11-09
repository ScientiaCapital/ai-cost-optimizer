"""Database operations for feedback storage."""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from app.database.postgres import get_connection, get_cursor

logger = logging.getLogger(__name__)


def _is_sqlite(conn) -> bool:
    """Check if connection is SQLite."""
    return hasattr(conn, 'row_factory')


class FeedbackStore:
    """Stores and retrieves feedback data."""

    def __init__(self):
        """Initialize and verify database schema."""
        try:
            with get_connection() as conn:
                cursor = get_cursor(conn, dict_cursor=False)

                # Check if using SQLite or PostgreSQL
                if hasattr(conn, 'row_factory'):
                    # SQLite query
                    cursor.execute("""
                        SELECT name FROM sqlite_master
                        WHERE type='table' AND name IN ('routing_metrics', 'response_feedback')
                    """)
                else:
                    # PostgreSQL query
                    cursor.execute("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_name IN ('routing_metrics', 'response_feedback')
                    """)

                tables = {row[0] for row in cursor.fetchall()}

                if 'response_feedback' not in tables:
                    logger.warning(
                        "response_feedback table not found. "
                        "Run migrations: alembic upgrade head"
                    )
        except Exception as e:
            logger.warning(f"Schema verification failed: {e}")

    def store_feedback(
        self,
        request_id: str,
        quality_score: int,
        is_correct: bool,
        is_helpful: Optional[bool] = None,
        comment: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> int:
        """Store feedback in database.

        Args:
            request_id: Request ID from routing decision
            quality_score: Quality rating 1-5
            is_correct: Was response correct
            is_helpful: Was response helpful
            comment: Optional user comment
            user_id: Optional user identifier
            session_id: Optional session identifier

        Returns:
            Feedback ID
        """
        with get_connection() as conn:
            cursor = get_cursor(conn, dict_cursor=False)
            is_sqlite = _is_sqlite(conn)
            placeholder = '?' if is_sqlite else '%s'

            # Get context from routing_metrics
            query = f"""
                SELECT
                    selected_provider,
                    selected_model,
                    pattern_detected,
                    complexity_score
                FROM routing_metrics
                WHERE request_id = {placeholder}
            """
            cursor.execute(query, (request_id,))

            context = cursor.fetchone()

            if context:
                provider, model, pattern, complexity = context
            else:
                provider = model = pattern = None
                complexity = None

            # Insert feedback
            if is_sqlite:
                # SQLite doesn't support RETURNING, use last_insert_rowid
                query = f"""
                    INSERT INTO response_feedback (
                        request_id, timestamp, quality_score, is_correct, is_helpful,
                        prompt_pattern, selected_provider, selected_model,
                        complexity_score, user_id, session_id, comment
                    ) VALUES (
                        {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                        {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                        {placeholder}, {placeholder}
                    )
                """
                cursor.execute(query, (
                    request_id,
                    datetime.now(),
                    quality_score,
                    is_correct,
                    is_helpful,
                    pattern,
                    provider,
                    model,
                    complexity,
                    user_id,
                    session_id,
                    comment
                ))
                feedback_id = cursor.lastrowid
            else:
                # PostgreSQL supports RETURNING
                query = f"""
                    INSERT INTO response_feedback (
                        request_id, timestamp, quality_score, is_correct, is_helpful,
                        prompt_pattern, selected_provider, selected_model,
                        complexity_score, user_id, session_id, comment
                    ) VALUES (
                        {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                        {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                        {placeholder}, {placeholder}
                    ) RETURNING id
                """
                cursor.execute(query, (
                    request_id,
                    datetime.now(),
                    quality_score,
                    is_correct,
                    is_helpful,
                    pattern,
                    provider,
                    model,
                    complexity,
                    user_id,
                    session_id,
                    comment
                ))
                feedback_id = cursor.fetchone()[0]

            logger.info(f"Stored feedback {feedback_id} for request {request_id}")

            return feedback_id

    def get_by_id(self, feedback_id: int) -> Optional[Dict[str, Any]]:
        """Get feedback by ID.

        Args:
            feedback_id: Feedback ID

        Returns:
            Feedback dict or None
        """
        with get_connection() as conn:
            cursor = get_cursor(conn, dict_cursor=True)
            is_sqlite = _is_sqlite(conn)
            placeholder = '?' if is_sqlite else '%s'

            query = f"SELECT * FROM response_feedback WHERE id = {placeholder}"
            cursor.execute(query, (feedback_id,))

            result = cursor.fetchone()

            # Convert sqlite3.Row to dict if needed
            if result and is_sqlite:
                result = dict(result)
                # Convert SQLite integer booleans to actual booleans
                if 'is_correct' in result and result['is_correct'] is not None:
                    result['is_correct'] = bool(result['is_correct'])
                if 'is_helpful' in result and result['is_helpful'] is not None:
                    result['is_helpful'] = bool(result['is_helpful'])

            return result
