"""SQLite database for cost tracking and usage statistics."""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class CostTracker:
    """Tracks LLM request costs in SQLite database."""

    def __init__(self, db_path: str = "optimizer.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Create database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                prompt_preview TEXT NOT NULL,
                complexity TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                tokens_in INTEGER NOT NULL,
                tokens_out INTEGER NOT NULL,
                cost REAL NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def log_request(
        self,
        prompt: str,
        complexity: str,
        provider: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cost: float
    ):
        """
        Log a completed request to the database.

        Args:
            prompt: User's prompt (will be truncated for storage)
            complexity: Classification (simple/complex)
            provider: Provider name (gemini/claude/openrouter)
            model: Model identifier
            tokens_in: Input token count
            tokens_out: Output token count
            cost: Total cost in USD
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Truncate prompt for preview (first 100 chars)
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt

        cursor.execute("""
            INSERT INTO requests (
                timestamp, prompt_preview, complexity, provider,
                model, tokens_in, tokens_out, cost
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            prompt_preview,
            complexity,
            provider,
            model,
            tokens_in,
            tokens_out,
            cost
        ))

        conn.commit()
        conn.close()

    def get_total_cost(self) -> float:
        """Get total cost across all requests."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT SUM(cost) FROM requests")
        result = cursor.fetchone()[0]

        conn.close()
        return result if result is not None else 0.0

    def get_usage_stats(self) -> Dict:
        """
        Get comprehensive usage statistics.

        Returns:
            Dictionary with request counts, costs, and breakdowns
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_requests,
                SUM(cost) as total_cost,
                SUM(tokens_in) as total_tokens_in,
                SUM(tokens_out) as total_tokens_out,
                AVG(cost) as avg_cost_per_request
            FROM requests
        """)
        overall = dict(cursor.fetchone())

        # Provider breakdown
        cursor.execute("""
            SELECT
                provider,
                COUNT(*) as request_count,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost
            FROM requests
            GROUP BY provider
        """)
        providers = [dict(row) for row in cursor.fetchall()]

        # Complexity breakdown
        cursor.execute("""
            SELECT
                complexity,
                COUNT(*) as request_count,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost
            FROM requests
            GROUP BY complexity
        """)
        complexity_breakdown = [dict(row) for row in cursor.fetchall()]

        # Recent requests (last 10)
        cursor.execute("""
            SELECT
                timestamp,
                prompt_preview,
                complexity,
                provider,
                model,
                cost
            FROM requests
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        recent_requests = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            "overall": overall,
            "by_provider": providers,
            "by_complexity": complexity_breakdown,
            "recent_requests": recent_requests
        }

    def get_request_history(self, limit: int = 50) -> List[Dict]:
        """
        Get recent request history.

        Args:
            limit: Maximum number of requests to return

        Returns:
            List of request dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                timestamp,
                prompt_preview,
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
        conn.close()

        return requests

    def clear_history(self):
        """Clear all request history (use with caution!)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM requests")
        conn.commit()
        conn.close()
