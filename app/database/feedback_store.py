"""Database operations for feedback storage."""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from app.database.postgres import get_connection, get_cursor

logger = logging.getLogger(__name__)


class FeedbackStore:
    """Stores and retrieves feedback data."""

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

            # Get context from routing_metrics
            cursor.execute("""
                SELECT
                    selected_provider,
                    selected_model,
                    pattern_detected,
                    complexity_score
                FROM routing_metrics
                WHERE request_id = %s
            """, (request_id,))

            context = cursor.fetchone()

            if context:
                provider, model, pattern, complexity = context
            else:
                provider = model = pattern = None
                complexity = None

            # Insert feedback
            cursor.execute("""
                INSERT INTO response_feedback (
                    request_id, timestamp, quality_score, is_correct, is_helpful,
                    prompt_pattern, selected_provider, selected_model,
                    complexity_score, user_id, session_id, comment
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
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

            cursor.execute("""
                SELECT * FROM response_feedback WHERE id = %s
            """, (feedback_id,))

            return cursor.fetchone()
