"""
Async ExperimentTracker - A/B Testing Framework with Supabase

Manages A/B test experiments for routing strategy comparison:
- Deterministic user assignment (control vs test group)
- Result recording and aggregation
- Progress tracking toward sample size goals
- Statistical readiness detection
- Multi-tenant support via RLS
"""

import hashlib
import logging
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any

from app.database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class AsyncExperimentTracker:
    """
    Async A/B testing tracker with Supabase backend.

    Provides deterministic user assignment and result aggregation
    to enable scientific comparison of routing strategies.

    Key Features:
    - Async database operations
    - Multi-tenant RLS support
    - SHA256-based deterministic user assignment
    - Real-time progress tracking
    """

    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize async experiment tracker.

        Args:
            user_id: Optional user ID for RLS context (UUID string)
                    If None, operates in admin mode (bypasses RLS)
        """
        self.user_id = user_id
        self.db = get_supabase_client()

        logger.info(f"AsyncExperimentTracker initialized (user_id={user_id})")

    def set_user_context(self, user_id: str) -> None:
        """
        Set user context for RLS.

        Args:
            user_id: User ID (UUID string)
        """
        self.user_id = user_id
        logger.debug(f"User context set to {user_id}")

    async def create_experiment(
        self,
        name: str,
        control_strategy: str,
        test_strategy: str,
        sample_size: int = 100,
        status: str = 'active',
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new A/B test experiment.

        Args:
            name: Human-readable experiment name (must be unique)
            control_strategy: Baseline routing strategy
            test_strategy: Strategy being tested against control
            sample_size: Target number of results to collect (default: 100)
            status: Experiment status (default: 'active')
            description: Optional experiment description

        Returns:
            Created experiment row

        Raises:
            ValueError: If validation fails
        """
        # Input validation
        if not name or not name.strip():
            raise ValueError("Experiment name cannot be empty")

        if control_strategy == test_strategy:
            raise ValueError(
                f"Control and test strategies must be different, "
                f"both set to '{control_strategy}'"
            )

        valid_strategies = {'complexity', 'learning', 'hybrid'}
        if control_strategy not in valid_strategies:
            raise ValueError(
                f"Invalid control strategy '{control_strategy}', "
                f"must be one of {valid_strategies}"
            )

        if test_strategy not in valid_strategies:
            raise ValueError(
                f"Invalid test strategy '{test_strategy}', "
                f"must be one of {valid_strategies}"
            )

        valid_statuses = {'active', 'completed', 'paused'}
        if status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{status}', must be one of {valid_statuses}"
            )

        logger.info(f"Creating experiment: {name} ({control_strategy} vs {test_strategy})")

        data = {
            "name": name,
            "description": description,
            "control_strategy": control_strategy,
            "test_strategy": test_strategy,
            "status": status,
            "created_by": self.user_id,  # RLS
            "created_at": datetime.now(UTC).isoformat()
        }

        use_admin = self.user_id is None

        result = await self.db.insert("experiments", data, use_admin=use_admin)

        logger.info(f"Created experiment: {result.get('id')} - {name}")

        return result

    async def get_active_experiments(self) -> List[Dict[str, Any]]:
        """
        Retrieve all active experiments for current user.

        Returns:
            List of experiment dicts with id, name, strategies, etc.
        """
        filters = {"status": "active"}
        if self.user_id:
            filters["created_by"] = self.user_id

        use_admin = self.user_id is None

        experiments = await self.db.select(
            "experiments",
            columns="id,name,description,control_strategy,test_strategy,status,created_at",
            filters=filters,
            order_by="created_at",
            use_admin=use_admin
        )

        logger.debug(f"Found {len(experiments)} active experiments")

        return experiments

    async def get_experiment(self, experiment_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single experiment by ID.

        Args:
            experiment_id: Experiment ID

        Returns:
            Experiment dict or None if not found
        """
        filters = {"id": experiment_id}
        if self.user_id:
            filters["created_by"] = self.user_id

        use_admin = self.user_id is None

        experiments = await self.db.select(
            "experiments",
            columns="*",
            filters=filters,
            use_admin=use_admin
        )

        return experiments[0] if experiments else None

    async def complete_experiment(
        self,
        experiment_id: int,
        winner: Optional[str] = None
    ) -> None:
        """
        Mark experiment as completed.

        Args:
            experiment_id: ID of experiment to complete
            winner: Optional winning strategy name
        """
        data = {
            "status": "completed",
            "completed_at": datetime.now(UTC).isoformat()
        }

        filters = {"id": experiment_id}
        if self.user_id:
            filters["created_by"] = self.user_id

        use_admin = self.user_id is None

        await self.db.update(
            "experiments",
            data=data,
            filters=filters,
            use_admin=use_admin
        )

        logger.info(f"Completed experiment {experiment_id} with winner: {winner}")

    def assign_user(self, experiment_id: int, user_id: str) -> str:
        """
        Assign user to control or test group using deterministic hashing.

        Same user_id will always get same assignment for given experiment.
        Uses SHA256(experiment_id + user_id) % 2 for 50/50 distribution.

        Args:
            experiment_id: ID of experiment
            user_id: User identifier

        Returns:
            "control" or "test" group assignment

        Note: This is NOT async because it's pure computation (no I/O)
        """
        # Deterministic hash-based assignment
        hash_input = f"{experiment_id}:{user_id}".encode('utf-8')
        hash_digest = hashlib.sha256(hash_input).hexdigest()
        assignment = int(hash_digest, 16) % 2

        group = "control" if assignment == 0 else "test"

        logger.debug(f"Assigned user {user_id} to {group} group for experiment {experiment_id}")

        return group

    async def record_result(
        self,
        experiment_id: int,
        user_id: str,
        strategy_assigned: str,
        latency_ms: Optional[float] = None,
        cost_usd: Optional[float] = None,
        quality_score: Optional[float] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record an experiment result (routing decision outcome).

        Args:
            experiment_id: ID of experiment
            user_id: User identifier
            strategy_assigned: Which strategy was used (control or test)
            latency_ms: Optional response latency in milliseconds
            cost_usd: Optional API cost in USD
            quality_score: Optional quality rating (0.0-1.0)
            provider: Optional AI provider used
            model: Optional model name used

        Returns:
            Inserted result row
        """
        logger.debug(f"Recording result for experiment {experiment_id}, user {user_id}")

        data = {
            "experiment_id": experiment_id,
            "user_id": user_id,
            "assigned_strategy": strategy_assigned,
            "timestamp": datetime.now(UTC).isoformat(),
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "quality_score": quality_score,
            "provider": provider,
            "model": model
        }

        use_admin = self.user_id is None

        result = await self.db.insert("experiment_results", data, use_admin=use_admin)

        logger.debug(f"Recorded result: {result.get('id')}")

        return result

    async def get_experiment_progress(self, experiment_id: int) -> Dict[str, Any]:
        """
        Get progress toward sample_size goal.

        Args:
            experiment_id: ID of experiment

        Returns:
            Dict with experiment_id, total_results, control_count, test_count
        """
        # Get experiment details
        experiment = await self.get_experiment(experiment_id)

        if not experiment:
            return {
                'experiment_id': experiment_id,
                'total_results': 0,
                'control_count': 0,
                'test_count': 0,
                'error': 'Experiment not found'
            }

        # Count total results
        filters = {"experiment_id": experiment_id}

        use_admin = self.user_id is None

        results = await self.db.select(
            "experiment_results",
            columns="assigned_strategy",
            filters=filters,
            use_admin=use_admin
        )

        total_results = len(results)
        control_count = sum(1 for r in results if r.get("assigned_strategy") == "control")
        test_count = sum(1 for r in results if r.get("assigned_strategy") == "test")

        return {
            'experiment_id': experiment_id,
            'experiment_name': experiment.get('name'),
            'total_results': total_results,
            'control_count': control_count,
            'test_count': test_count,
            'control_strategy': experiment.get('control_strategy'),
            'test_strategy': experiment.get('test_strategy')
        }

    async def get_experiment_summary(self, experiment_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Get aggregated statistics by strategy (control vs test).

        Args:
            experiment_id: ID of experiment

        Returns:
            Dict with 'control' and 'test' keys, each containing:
            - strategy: strategy name
            - count: number of results
            - avg_latency_ms: average latency
            - avg_cost_usd: average cost
            - avg_quality_score: average quality
        """
        # Get experiment details
        experiment = await self.get_experiment(experiment_id)

        if not experiment:
            return {'control': {}, 'test': {}}

        control_strategy = experiment.get('control_strategy')
        test_strategy = experiment.get('test_strategy')

        # Fetch all results for this experiment
        filters = {"experiment_id": experiment_id}

        use_admin = self.user_id is None

        results = await self.db.select(
            "experiment_results",
            columns="assigned_strategy,latency_ms,cost_usd,quality_score",
            filters=filters,
            use_admin=use_admin
        )

        # Separate control and test results
        control_results = [r for r in results if r.get("assigned_strategy") == "control"]
        test_results = [r for r in results if r.get("assigned_strategy") == "test"]

        def calculate_stats(results_list: List[Dict]) -> Dict[str, Any]:
            """Calculate aggregate statistics for a group."""
            if not results_list:
                return {
                    'count': 0,
                    'avg_latency_ms': 0.0,
                    'avg_cost_usd': 0.0,
                    'avg_quality_score': 0.0
                }

            latencies = [r.get('latency_ms', 0) for r in results_list if r.get('latency_ms') is not None]
            costs = [r.get('cost_usd', 0) for r in results_list if r.get('cost_usd') is not None]
            scores = [r.get('quality_score', 0) for r in results_list if r.get('quality_score') is not None]

            return {
                'count': len(results_list),
                'avg_latency_ms': sum(latencies) / len(latencies) if latencies else 0.0,
                'avg_cost_usd': sum(costs) / len(costs) if costs else 0.0,
                'avg_quality_score': sum(scores) / len(scores) if scores else 0.0
            }

        summary = {
            'control': {
                'strategy': control_strategy,
                **calculate_stats(control_results)
            },
            'test': {
                'strategy': test_strategy,
                **calculate_stats(test_results)
            }
        }

        return summary
