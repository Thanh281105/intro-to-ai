from __future__ import annotations
import time
from typing import Optional, TYPE_CHECKING
from ..map import Pos, SokobanMap
from ..state import DIRECTIONS
from ..agents.base import static_distance
from .evaluator_potential import CompetitiveEvaluator
from .weights import CompetitiveWeights, DEFAULT_WEIGHTS

if TYPE_CHECKING:
    from .state import CompetitiveState

def is_tactical_close_contact(state: CompetitiveState, board: SokobanMap) -> bool:
    """Check if agents are in close tactical proximity or contesting the same box.
    Uses wall-aware static distance. Zero Manhattan / Euclidean distance.
    """
    p1 = getattr(state, 'p1', None)
    p2 = getattr(state, 'p2', None)
    if p1 is None or p2 is None:
        return False
    # Wall-aware static distance between agents <= 3
    if static_distance(board, p1, p2) <= 3:
        return True
    # Proximity to any shared contested box (both within static distance 2)
    for b in state.boxes:
        if static_distance(board, p1, b) <= 2 and static_distance(board, p2, b) <= 2:
            return True
    return False

def get_legal_actions(pos: Pos, boxes: frozenset[Pos], board: SokobanMap) -> list[str]:
    """Get legal actions (moves and pushes) for an agent, ignoring dynamic opponent."""
    legal = []
    for action, (dr, dc) in DIRECTIONS.items():
        nxt = (pos[0] + dr, pos[1] + dc)
        if not board.free(nxt):
            continue
        if nxt in boxes:
            beyond = (nxt[0] + dr, nxt[1] + dc)
            if board.free(beyond) and beyond not in boxes:
                legal.append(action)
        else:
            legal.append(action)
    return legal or ['North']

def select_robust_tactical_action(
    state: CompetitiveState,
    board: SokobanMap,
    search_action: str,
    player_id: int,
    step_limit: int,
    weights: CompetitiveWeights = DEFAULT_WEIGHTS,
    evaluator: Optional[CompetitiveEvaluator] = None,
    robust_threshold: float = 1.0,
    deadline_ns: Optional[int] = None,
) -> str:
    """Evaluate 1-step joint conflict robustness when in close tactical proximity.
    For each candidate action a_i:
        J(a_i) = min_{a_j} Phi_i(resolve(s, a_i, a_j))
    Protects against simultaneous-action collisions, swaps, and box-stealing.
    Enforces strict real-time deadline limit.
    """
    if deadline_ns is not None and time.perf_counter_ns() >= deadline_ns:
        return search_action
    from .state import resolve_with_turn
    if evaluator is None:
        evaluator = CompetitiveEvaluator.get(board)

    my_pos = state.p1 if player_id == 1 else state.p2
    opp_pos = state.p2 if player_id == 1 else state.p1
    opp_id = 2 if player_id == 1 else 1

    my_legal = get_legal_actions(my_pos, state.boxes, board)
    opp_legal = get_legal_actions(opp_pos, state.boxes, board)

    if not my_legal:
        return search_action

    # Check if search_action has a direct conflict risk with any legal opponent move
    has_conflict_risk = False
    for a_opp in opp_legal:
        a1 = search_action if player_id == 1 else a_opp
        a2 = a_opp if player_id == 1 else search_action
        _, turn = resolve_with_turn(state, a1, a2, board)
        my_outcome = turn.a1_outcome if player_id == 1 else turn.a2_outcome
        if my_outcome == "CONFLICT":
            has_conflict_risk = True
            break

    # If search_action has no conflict risk, preserve the multi-step search plan
    if not has_conflict_risk:
        return search_action

    j_scores: dict[str, float] = {}
    for a_my in my_legal:
        if deadline_ns is not None and time.perf_counter_ns() >= deadline_ns:
            return search_action
        worst_phi = float('inf')
        for a_opp in opp_legal:
            a1 = a_my if player_id == 1 else a_opp
            a2 = a_opp if player_id == 1 else a_my
            s_next, _ = resolve_with_turn(state, a1, a2, board)
            if player_id == 1:
                phi = evaluator.evaluate_phi(
                    s_next.p1, s_next.p2, s_next.boxes, s_next.owners,
                    s_next.step, 1, step_limit, weights
                )
            else:
                phi = evaluator.evaluate_phi(
                    s_next.p2, s_next.p1, s_next.boxes, s_next.owners,
                    s_next.step, 2, step_limit, weights
                )
            if phi < worst_phi:
                worst_phi = phi
        j_scores[a_my] = worst_phi

    if not j_scores:
        return search_action

    best_action = max(j_scores, key=lambda a: j_scores[a])
    best_j = j_scores[best_action]
    search_j = j_scores.get(search_action, -float('inf'))

    # If search_action is sufficiently robust (within robust_threshold of best_j), preserve search plan
    if search_action in j_scores and search_j >= best_j - robust_threshold:
        return search_action

    return best_action
