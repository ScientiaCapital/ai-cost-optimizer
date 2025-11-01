"""Abstract base class for routing strategies."""
from abc import ABC, abstractmethod
from app.routing.models import RoutingDecision, RoutingContext


class RoutingStrategy(ABC):
    """Abstract base for routing strategies.

    All routing strategies must implement:
    - route(): Make routing decision for a prompt
    - get_name(): Return strategy identifier for logging
    """

    @abstractmethod
    def route(self, prompt: str, context: RoutingContext) -> RoutingDecision:
        """Route prompt to optimal provider/model.

        Args:
            prompt: User's query text
            context: Additional routing context

        Returns:
            RoutingDecision with provider, model, and metadata

        Raises:
            RoutingError: If strategy cannot make decision
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return strategy identifier for logging.

        Returns:
            Strategy name (e.g., "complexity", "learning", "hybrid")
        """
        pass
