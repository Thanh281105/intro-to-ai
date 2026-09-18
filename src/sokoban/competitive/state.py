from dataclasses import dataclass
from ..map import Pos, SokobanMap
from ..state import DIRECTIONS
from ..agents.base import static_distance

@dataclass(frozen=True)
class CompetitiveState:
    p1: Pos
    p2: Pos
    boxes: frozenset[Pos]
    owners: tuple[tuple[Pos, int], ...] = ()
    step: int = 0

    def owner_map(self) -> dict[Pos, int]:
        return dict(self.owners)

    def scores(self, goals) -> tuple[int, int]:
        o = self.owner_map()
        return (
            sum(1 for b in self.boxes if b in goals and o.get(b) == 1),
            sum(1 for b in self.boxes if b in goals and o.get(b) == 2),
        )

@dataclass(frozen=True)
class TurnRecord:
    step: int
    a1_action: str
    a1_outcome: str        # "MOVE", "PUSH", "BLOCKED", "CONFLICT"
    a1_latency_ms: float
    a2_action: str
    a2_outcome: str        # "MOVE", "PUSH", "BLOCKED", "CONFLICT"
    a2_latency_ms: float
    resolution_summary: str

@dataclass(frozen=True)
class AgentIntent:
    agent_id: int
    player_from: Pos
    player_to: Pos
    push_box_from: Pos | None = None
    push_box_to: Pos | None = None
    is_push: bool = False
    is_valid: bool = True

def get_deterministic_p2(board: SokobanMap, p1: Pos | None = None) -> Pos:
    """Deterministically choose a valid start position for Agent 2 on playable floor.
    Uses wall-aware static shortest-path distance (no Manhattan distance).
    """
    if p1 is None:
        p1 = board.initial_player

    # If the map explicitly defines a valid initial_player2, use it
    if board.initial_player2 is not None:
        p2 = board.initial_player2
        if (
            board.free(p2)
            and p2 not in board.walls
            and p2 not in board.initial_boxes
            and p2 != p1
        ):
            return p2

    candidates = [
        p
        for p in board.floor_cells
        if p not in board.walls
        and p not in board.initial_boxes
        and p != p1
    ]
    if not candidates:
        raise ValueError("No valid playable floor cell available for Agent 2 start position")

    # Deterministic strategy: select candidate with maximum wall-aware static path distance from p1,
    # breaking ties deterministically by bottom-right preference (-r, -c)
    def key_fn(pos: Pos):
        d = static_distance(board, pos, p1)
        d_val = d if d != float('inf') else 0
        return (d_val, -pos[0], -pos[1])

    return max(candidates, key=key_fn)

def initial_state(board: SokobanMap, p2: Pos | None = None) -> CompetitiveState:
    p1 = board.initial_player
    if p2 is not None:
        if (
            not board.free(p2)
            or p2 in board.walls
            or p2 in board.initial_boxes
            or p2 == p1
        ):
            raise ValueError(f"Invalid Agent 2 start position: {p2}")
    else:
        p2 = get_deterministic_p2(board, p1)

    return CompetitiveState(p1, p2, board.initial_boxes, (), 0)

def get_intent(agent_id: int, pos: Pos, action: str, board: SokobanMap, boxes: frozenset[Pos]) -> AgentIntent:
    if action not in DIRECTIONS:
        return AgentIntent(agent_id, pos, pos, None, None, False, False)
    dr, dc = DIRECTIONS[action]
    nxt = (pos[0] + dr, pos[1] + dc)
    if not board.free(nxt):
        return AgentIntent(agent_id, pos, pos, None, None, False, False)
    if nxt in boxes:
        beyond = (nxt[0] + dr, nxt[1] + dc)
        if not board.free(beyond) or beyond in boxes:
            return AgentIntent(agent_id, pos, pos, None, None, False, False)
        # Legal push: player moves into nxt (old box position), box moves to beyond
        return AgentIntent(agent_id, pos, nxt, nxt, beyond, True, True)
    # Legal move: player moves into nxt
    return AgentIntent(agent_id, pos, nxt, None, None, False, True)

def resolve_with_turn(
    state: CompetitiveState,
    a1: str,
    a2: str,
    board: SokobanMap,
    lat1_ms: float = 0.0,
    lat2_ms: float = 0.0
) -> tuple[CompetitiveState, TurnRecord]:
    """Resolve simultaneous actions and construct a rich TurnRecord containing real decision data."""
    i1 = get_intent(1, state.p1, a1, board, state.boxes)
    i2 = get_intent(2, state.p2, a2, board, state.boxes)

    p1_to = i1.player_to
    push1 = (i1.push_box_from, i1.push_box_to) if i1.is_push else None
    p2_to = i2.player_to
    push2 = (i2.push_box_from, i2.push_box_to) if i2.is_push else None

    out1 = "PUSH" if i1.is_push else ("MOVE" if i1.is_valid else "BLOCKED")
    out2 = "PUSH" if i2.is_push else ("MOVE" if i2.is_valid else "BLOCKED")

    conf1 = False
    conf2 = False

    # 1. Same player destination: both blocked
    if p1_to == p2_to:
        p1_to, p2_to = state.p1, state.p2
        push1 = push2 = None
        conf1 = conf2 = True

    # 2. Direct swap (head-on collision): both blocked
    if p1_to == state.p2 and p2_to == state.p1:
        p1_to, p2_to = state.p1, state.p2
        push1 = push2 = None
        conf1 = conf2 = True

    # 3. Entering opponent's current cell: blocked conservatively
    if p1_to == state.p2:
        p1_to = state.p1
        push1 = None
        conf1 = True
    if p2_to == state.p1:
        p2_to = state.p2
        push2 = None
        conf2 = True

    # 4. Same box push conflict
    if push1 and push2 and push1[0] == push2[0]:
        p1_to, p2_to = state.p1, state.p2
        push1 = push2 = None
        conf1 = conf2 = True

    # 5. Two pushed boxes having the same destination
    if push1 and push2 and push1[1] == push2[1]:
        p1_to, p2_to = state.p1, state.p2
        push1 = push2 = None
        conf1 = conf2 = True

    # 6. Player destination conflicts with pushed box destination
    if push2 and p1_to == push2[1]:
        p1_to, p2_to = state.p1, state.p2
        push1 = push2 = None
        conf1 = conf2 = True
    if push1 and p2_to == push1[1]:
        p1_to, p2_to = state.p1, state.p2
        push1 = push2 = None
        conf1 = conf2 = True

    # 7. Push into opponent location
    if push1 and (push1[1] == state.p2 or push1[1] == p2_to):
        p1_to = state.p1
        push1 = None
        conf1 = True
    if push2 and (push2[1] == state.p1 or push2[1] == p1_to):
        p2_to = state.p2
        push2 = None
        conf2 = True

    if conf1:
        out1 = "CONFLICT"
    if conf2:
        out2 = "CONFLICT"

    # Apply resolved pushes
    boxes = set(state.boxes)
    owners = state.owner_map()

    if push1:
        old1, new1 = push1
        boxes.remove(old1)
        boxes.add(new1)
        owners.pop(old1, None)
        if new1 in board.goals:
            owners[new1] = 1

    if push2:
        old2, new2 = push2
        boxes.remove(old2)
        boxes.add(new2)
        owners.pop(old2, None)
        if new2 in board.goals:
            owners[new2] = 2

    # Invariant assertions
    assert p1_to != p2_to, "Invariant failed: agents must never share the same cell"
    assert p1_to not in boxes, "Invariant failed: Agent 1 must never be inside a box"
    assert p2_to not in boxes, "Invariant failed: Agent 2 must never be inside a box"
    assert len(boxes) == len(state.boxes), "Invariant failed: box count must remain constant"

    owners_tuple = tuple(
        sorted((p, o) for p, o in owners.items() if p in boxes and p in board.goals and o in (1, 2))
    )
    new_state = CompetitiveState(p1_to, p2_to, frozenset(boxes), owners_tuple, state.step + 1)

    if conf1 or conf2:
        res_summary = "CONFLICT RESOLVED"
    elif out1 == "PUSH" and out2 == "PUSH":
        res_summary = "DUAL PUSH SUCCESS"
    elif out1 == "PUSH" or out2 == "PUSH":
        res_summary = "LEGAL PUSH"
    elif out1 == "MOVE" and out2 == "MOVE":
        res_summary = "BOTH MOVED"
    elif out1 == "BLOCKED" and out2 == "BLOCKED":
        res_summary = "BOTH BLOCKED"
    else:
        res_summary = "RESOLVED"

    turn_rec = TurnRecord(
        step=state.step + 1,
        a1_action=a1,
        a1_outcome=out1,
        a1_latency_ms=round(lat1_ms, 2),
        a2_action=a2,
        a2_outcome=out2,
        a2_latency_ms=round(lat2_ms, 2),
        resolution_summary=res_summary,
    )
    return new_state, turn_rec

def resolve(state: CompetitiveState, a1: str, a2: str, board: SokobanMap) -> CompetitiveState:
    """Convenience resolution wrapper returning CompetitiveState."""
    new_state, _ = resolve_with_turn(state, a1, a2, board)
    return new_state
