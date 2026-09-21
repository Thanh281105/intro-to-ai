from abc import ABC, abstractmethod
from typing import Any
from ..map import Pos, SokobanMap

class BaseCompetitiveEvaluator(ABC):
    """Abstract base class for competitive Sokoban state evaluators."""

    @abstractmethod
    def evaluate_h(
        self,
        player_pos: Pos,
        opp_pos: Pos,
        boxes: frozenset[Pos],
        owners: tuple[tuple[Pos, int], ...],
        step: int,
        player_id: int,
        step_limit: int,
        **kwargs: Any,
    ) -> float:
        """Compute search heuristic cost h(s) where lower priority indicates better state."""
        pass
