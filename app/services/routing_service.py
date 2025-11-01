"""Service layer for intelligent routing."""
import logging
from typing import Dict, Any

from app.routing.engine import RoutingEngine
from app.routing.models import RoutingContext
from app.database import CostTracker

logger = logging.getLogger(__name__)


class RoutingService:
    """FastAPI service layer for intelligent routing.

    Bridges FastAPI endpoints and RoutingEngine, handling:
    - Cache integration
    - Provider execution
    - Cost tracking
    - Response formatting
    """

    def __init__(self, db_path: str, providers: Dict[str, Any]):
        """Initialize routing service.

        Args:
            db_path: Path to SQLite database
            providers: Dictionary of initialized provider clients
        """
        self.engine = RoutingEngine(db_path=db_path, track_metrics=True)
        self.providers = providers
        self.cost_tracker = CostTracker(db_path=db_path)

        logger.info(f"RoutingService initialized with {len(providers)} providers")
