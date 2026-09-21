from typing import Optional
from ..map import Pos, SokobanMap
from ..heuristic import ReversePushHeuristic
from ..agents.base import static_distance
from .evaluator_base import BaseCompetitiveEvaluator

class OldEvaluator(BaseCompetitiveEvaluator):
    """Legacy baseline competitive evaluator.
    
    Computes heuristic cost using:
        h(s) = 10 * reverse_push_box_matching_cost + min_static_distance_to_box
    
    Notable characteristics & limitations:
    - Agnostic to goal ownership and score difference.
    - Measures distance to box cells, not the support cell required to push.
    - No horizon-dependent dynamic scaling.
    - No static deadlock detection.
    """
    _instances: dict[int, 'OldEvaluator'] = {}

    @classmethod
    def get(cls, board: SokobanMap) -> 'OldEvaluator':
        bid = id(board)
        if bid not in cls._instances:
            cls._instances[bid] = cls(board)
        return cls._instances[bid]

    def __init__(self, board: SokobanMap):
        self.board = board
        self.heuristic = ReversePushHeuristic(board)

    def evaluate_h_state(self, pos: Pos, boxes: frozenset[Pos]) -> float:
        """Legacy helper matching the original _eval_h_old signature."""
        box_cost = self.heuristic.for_boxes(boxes)
        if box_cost == float('inf'):
            return float('inf')
        if boxes:
            min_dist = min(static_distance(self.board, pos, b) for b in boxes)
            if min_dist == float('inf'):
                return float('inf')
        else:
            min_dist = 0.0
        return float(10 * box_cost + min_dist)

    def evaluate_h(
        self,
        player_pos: Pos,
        opp_pos: Pos,
        boxes: frozenset[Pos],
        owners: tuple[tuple[Pos, int], ...],
        step: int,
        player_id: int,
        step_limit: int,
        **kwargs,
    ) -> float:
        return self.evaluate_h_state(player_pos, boxes)
