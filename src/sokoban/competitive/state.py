from dataclasses import dataclass
from ..map import Pos, SokobanMap
from ..state import DIRECTIONS

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
class AgentIntent:
    agent_id: int
    player_from: Pos
    player_to: Pos
    push_box_from: Pos | None = None
    push_box_to: Pos | None = None
    is_push: bool = False
    is_valid: bool = True

def get_deterministic_p2(board: SokobanMap, p1: Pos | None = None) -> Pos:
    """Deterministically choose a valid start position for Agent 2 on playable floor."""
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

    # Deterministic strategy: select candidate with maximum Manhattan distance from p1,
    # breaking ties deterministically by bottom-right preference (-r, -c)
    def key_fn(pos: Pos):
        dist = abs(pos[0] - p1[0]) + abs(pos[1] - p1[1])
        return (dist, -pos[0], -pos[1])

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

def resolve(state: CompetitiveState, a1: str, a2: str, board: SokobanMap) -> CompetitiveState:
    """Carefully resolve simultaneous actions with explicit conflict detection."""
    i1 = get_intent(1, state.p1, a1, board, state.boxes)
    i2 = get_intent(2, state.p2, a2, board, state.boxes)

    p1_to = i1.player_to
    push1 = (i1.push_box_from, i1.push_box_to) if i1.is_push else None
    p2_to = i2.player_to
    push2 = (i2.push_box_from, i2.push_box_to) if i2.is_push else None

    # 1. Same player destination: both blocked
    if p1_to == p2_to:
        p1_to = state.p1
        p2_to = state.p2
        push1 = push2 = None

    # 2. Direct swap (head-on collision): both blocked
    if p1_to == state.p2 and p2_to == state.p1:
        p1_to = state.p1
        p2_to = state.p2
        push1 = push2 = None

    # 3. Entering opponent's current cell: blocked conservatively
    if p1_to == state.p2:
        p1_to = state.p1
        push1 = None
    if p2_to == state.p1:
        p2_to = state.p2
        push2 = None

    # 4. Same box push conflict
    if push1 and push2 and push1[0] == push2[0]:
        p1_to = state.p1
        p2_to = state.p2
        push1 = push2 = None

    # 5. Two pushed boxes having the same destination
    if push1 and push2 and push1[1] == push2[1]:
        p1_to = state.p1
        p2_to = state.p2
        push1 = push2 = None

    # 6. Player destination conflicts with pushed box destination
    if push2 and p1_to == push2[1]:
        p1_to = state.p1
        push1 = None
        p2_to = state.p2
        push2 = None
    if push1 and p2_to == push1[1]:
        p1_to = state.p1
        push1 = None
        p2_to = state.p2
        push2 = None

    # 7. Push into opponent location
    if push1 and (push1[1] == state.p2 or push1[1] == p2_to):
        p1_to = state.p1
        push1 = None
    if push2 and (push2[1] == state.p1 or push2[1] == p1_to):
        p2_to = state.p2
        push2 = None

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
    return CompetitiveState(p1_to, p2_to, frozenset(boxes), owners_tuple, state.step + 1)
