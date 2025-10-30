"""SQLite database for cost tracking and usage statistics."""
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class CostTracker:
    """Tracks LLM request costs in SQLite database."""

    def __init__(self, db_path: str = "optimizer.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Create database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Requests table - logs all requests including cache hits
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

        # Response cache table - stores unique prompts and their responses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS response_cache (
                cache_key TEXT PRIMARY KEY,
                prompt_normalized TEXT NOT NULL,
                max_tokens INTEGER NOT NULL,
                response TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                complexity TEXT NOT NULL,
                tokens_in INTEGER NOT NULL,
                tokens_out INTEGER NOT NULL,
                cost REAL NOT NULL,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                hit_count INTEGER DEFAULT 0,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                quality_score REAL DEFAULT NULL,
                invalidated INTEGER DEFAULT 0,
                invalidation_reason TEXT DEFAULT NULL
            )
        """)

        # Response feedback table - stores user ratings for cached responses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS response_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                user_agent TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (cache_key) REFERENCES response_cache(cache_key)
            )
        """)

        # Create indexes for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_prompt
            ON response_cache(prompt_normalized)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_created
            ON response_cache(created_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_cache_key
            ON response_feedback(cache_key)
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

    # ==================== CACHE OPERATIONS ====================

    def _normalize_prompt(self, prompt: str) -> str:
        """
        Normalize prompt for consistent caching.

        Normalization rules:
        - Strip leading/trailing whitespace
        - Normalize internal whitespace (multiple spaces → single space)
        - Preserve case (case-sensitive caching)

        Args:
            prompt: Raw user prompt

        Returns:
            Normalized prompt string
        """
        # Strip and normalize whitespace
        normalized = " ".join(prompt.split())
        return normalized

    def _generate_cache_key(self, prompt: str, max_tokens: int) -> str:
        """
        Generate unique cache key for prompt + parameters.

        Cache key includes both prompt content and max_tokens because
        different token limits may produce different responses.

        Args:
            prompt: User prompt
            max_tokens: Maximum response tokens

        Returns:
            SHA-256 hash as hex string
        """
        normalized = self._normalize_prompt(prompt)
        cache_input = f"{normalized}|{max_tokens}"
        return hashlib.sha256(cache_input.encode()).hexdigest()

    def check_cache(self, prompt: str, max_tokens: int) -> Optional[Dict]:
        """
        Check if response exists in cache and is not invalidated.

        Args:
            prompt: User prompt
            max_tokens: Maximum response tokens

        Returns:
            Dictionary with cached response data if found, None otherwise
        """
        cache_key = self._generate_cache_key(prompt, max_tokens)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM response_cache
            WHERE cache_key = ? AND invalidated = 0
        """, (cache_key,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "cache_key": row["cache_key"],
                "response": row["response"],
                "provider": row["provider"],
                "model": row["model"],
                "complexity": row["complexity"],
                "tokens_in": row["tokens_in"],
                "tokens_out": row["tokens_out"],
                "cost": row["cost"],
                "created_at": row["created_at"],
                "hit_count": row["hit_count"]
            }

        return None

    def store_in_cache(
        self,
        prompt: str,
        max_tokens: int,
        response: str,
        provider: str,
        model: str,
        complexity: str,
        tokens_in: int,
        tokens_out: int,
        cost: float
    ):
        """
        Store response in cache.

        Args:
            prompt: User prompt
            max_tokens: Maximum response tokens
            response: LLM response text
            provider: Provider name
            model: Model identifier
            complexity: Complexity classification
            tokens_in: Input token count
            tokens_out: Output token count
            cost: Total cost in USD
        """
        cache_key = self._generate_cache_key(prompt, max_tokens)
        normalized_prompt = self._normalize_prompt(prompt)
        now = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO response_cache (
                cache_key, prompt_normalized, max_tokens, response,
                provider, model, complexity, tokens_in, tokens_out, cost,
                created_at, last_accessed, hit_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            cache_key, normalized_prompt, max_tokens, response,
            provider, model, complexity, tokens_in, tokens_out, cost,
            now, now
        ))

        conn.commit()
        conn.close()

    def record_cache_hit(self, cache_key: str):
        """
        Record that a cached response was used.

        Increments hit_count and updates last_accessed timestamp.

        Args:
            cache_key: Cache key of used response
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE response_cache
            SET hit_count = hit_count + 1,
                last_accessed = ?
            WHERE cache_key = ?
        """, (datetime.now().isoformat(), cache_key))

        conn.commit()
        conn.close()

    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with:
            - total_entries: Number of cached responses
            - total_hits: Sum of all hit counts
            - total_savings: Money saved from cache hits
            - hit_rate: Percentage of requests served from cache
            - popular_queries: Most frequently cached prompts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Basic cache stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_entries,
                SUM(hit_count) as total_hits,
                SUM(cost * hit_count) as total_savings
            FROM response_cache
        """)
        cache_stats = dict(cursor.fetchone())

        # Hit rate calculation (cache hits vs total requests)
        cursor.execute("SELECT COUNT(*) as total_requests FROM requests")
        total_requests = cursor.fetchone()["total_requests"]

        hit_rate = 0.0
        if total_requests > 0:
            cache_hits = cache_stats["total_hits"] or 0
            hit_rate = (cache_hits / total_requests) * 100

        # Popular cached queries (top 5 by hit count)
        cursor.execute("""
            SELECT
                prompt_normalized,
                hit_count,
                cost,
                provider,
                model,
                created_at
            FROM response_cache
            WHERE hit_count > 0
            ORDER BY hit_count DESC
            LIMIT 5
        """)
        popular_queries = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            "total_entries": cache_stats["total_entries"],
            "total_hits": cache_stats["total_hits"] or 0,
            "total_savings": cache_stats["total_savings"] or 0.0,
            "hit_rate_percent": hit_rate,
            "popular_queries": popular_queries
        }

    def clear_cache(self):
        """Clear all cached responses (use with caution!)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM response_cache")
        conn.commit()
        conn.close()

    # ==================== QUALITY TRACKING OPERATIONS ====================

    def add_feedback(
        self,
        cache_key: str,
        rating: int,
        comment: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Add user feedback for a cached response.

        Args:
            cache_key: Cache key of response being rated
            rating: 1 for upvote, -1 for downvote
            comment: Optional user comment
            user_agent: Optional user agent string

        Returns:
            True if feedback was recorded successfully
        """
        if rating not in [1, -1]:
            raise ValueError("Rating must be 1 (upvote) or -1 (downvote)")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Store feedback
            cursor.execute("""
                INSERT INTO response_feedback (
                    cache_key, rating, comment, user_agent, timestamp
                )
                VALUES (?, ?, ?, ?, ?)
            """, (cache_key, rating, comment, user_agent, datetime.now().isoformat()))

            # Update vote counts on cache entry
            if rating == 1:
                cursor.execute("""
                    UPDATE response_cache
                    SET upvotes = upvotes + 1
                    WHERE cache_key = ?
                """, (cache_key,))
            else:
                cursor.execute("""
                    UPDATE response_cache
                    SET downvotes = downvotes + 1
                    WHERE cache_key = ?
                """, (cache_key,))

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            conn.close()

    def update_quality_score(self, cache_key: str) -> Optional[float]:
        """
        Recalculate and update quality score for a cached response.

        Args:
            cache_key: Cache key to update

        Returns:
            New quality score, or None if no votes
        """
        from .quality import QualityValidator

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get current vote counts
        cursor.execute("""
            SELECT upvotes, downvotes FROM response_cache
            WHERE cache_key = ?
        """, (cache_key,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        upvotes = row["upvotes"]
        downvotes = row["downvotes"]

        # Calculate quality score
        quality_score = QualityValidator.calculate_quality_score(upvotes, downvotes)

        # Update database
        cursor.execute("""
            UPDATE response_cache
            SET quality_score = ?
            WHERE cache_key = ?
        """, (quality_score, cache_key))

        # Check if should be invalidated
        total_votes = upvotes + downvotes
        if QualityValidator.should_invalidate(quality_score, total_votes):
            # Get feedback comments for invalidation reason
            cursor.execute("""
                SELECT comment FROM response_feedback
                WHERE cache_key = ? AND comment IS NOT NULL
            """, (cache_key,))
            comments = [row["comment"] for row in cursor.fetchall() if row["comment"]]

            reason = QualityValidator.get_invalidation_reason(
                quality_score, total_votes, comments
            )

            cursor.execute("""
                UPDATE response_cache
                SET invalidated = 1, invalidation_reason = ?
                WHERE cache_key = ?
            """, (reason, cache_key))

        conn.commit()
        conn.close()

        return quality_score

    def get_feedback_for_response(self, cache_key: str) -> List[Dict]:
        """
        Get all feedback for a specific cached response.

        Args:
            cache_key: Cache key to get feedback for

        Returns:
            List of feedback dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id, rating, comment, user_agent, timestamp
            FROM response_feedback
            WHERE cache_key = ?
            ORDER BY timestamp DESC
        """, (cache_key,))

        feedback = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return feedback

    def invalidate_cache_entry(self, cache_key: str, reason: str):
        """
        Manually invalidate a cache entry.

        Args:
            cache_key: Cache key to invalidate
            reason: Reason for invalidation
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE response_cache
            SET invalidated = 1, invalidation_reason = ?
            WHERE cache_key = ?
        """, (reason, cache_key))

        conn.commit()
        conn.close()

    def get_quality_stats(self) -> Dict:
        """
        Get quality statistics across all cached responses.

        Returns:
            Dictionary with quality metrics by provider and overall
        """
        from .quality import QualityValidator

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Overall quality stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_entries,
                SUM(upvotes) as total_upvotes,
                SUM(downvotes) as total_downvotes,
                SUM(invalidated) as invalidated_count,
                AVG(quality_score) as avg_quality_score
            FROM response_cache
        """)
        overall = dict(cursor.fetchone())

        # Quality by provider
        cursor.execute("""
            SELECT
                provider,
                COUNT(*) as entry_count,
                SUM(upvotes) as total_upvotes,
                SUM(downvotes) as total_downvotes,
                AVG(quality_score) as avg_quality_score,
                SUM(upvotes + downvotes) as total_votes
            FROM response_cache
            WHERE invalidated = 0
            GROUP BY provider
        """)
        by_provider = [dict(row) for row in cursor.fetchall()]

        # Most highly rated
        cursor.execute("""
            SELECT
                prompt_normalized,
                provider,
                model,
                quality_score,
                upvotes,
                downvotes
            FROM response_cache
            WHERE quality_score IS NOT NULL AND invalidated = 0
            ORDER BY quality_score DESC
            LIMIT 5
        """)
        top_rated = [dict(row) for row in cursor.fetchall()]

        # Worst rated (excluding invalidated)
        cursor.execute("""
            SELECT
                prompt_normalized,
                provider,
                model,
                quality_score,
                upvotes,
                downvotes
            FROM response_cache
            WHERE quality_score IS NOT NULL AND invalidated = 0
            ORDER BY quality_score ASC
            LIMIT 5
        """)
        worst_rated = [dict(row) for row in cursor.fetchall()]

        # Invalidated entries
        cursor.execute("""
            SELECT
                prompt_normalized,
                provider,
                invalidation_reason,
                quality_score
            FROM response_cache
            WHERE invalidated = 1
            ORDER BY created_at DESC
        """)
        invalidated = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            "overall": overall,
            "by_provider": QualityValidator.analyze_provider_quality(by_provider),
            "top_rated": top_rated,
            "worst_rated": worst_rated,
            "invalidated_responses": invalidated
        }
