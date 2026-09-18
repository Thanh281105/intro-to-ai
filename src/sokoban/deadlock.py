from .heuristic import ReversePushHeuristic
from .map import Pos

def is_static_deadlock(box: Pos, heuristic: ReversePushHeuristic) -> bool:
    return all(box not in distances for distances in heuristic.distances.values())

def state_has_deadlock(state, heuristic: ReversePushHeuristic) -> bool:
    return any(is_static_deadlock(box, heuristic) for box in state.boxes if box not in heuristic.board.goals)
