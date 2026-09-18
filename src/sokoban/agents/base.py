from collections import deque
from ..map import Pos, SokobanMap
from ..state import DIRECTIONS

_STATIC_DIST_CACHE: dict[tuple[int, Pos], dict[Pos, int]] = {}

def get_static_distances(board: SokobanMap, src: Pos) -> dict[Pos, int]:
    """Compute and memoize all-pairs static floor shortest-path distances using BFS.
    Ignores dynamic boxes to form a sound, wall-aware floor distance relaxation.
    Completely avoids Manhattan or Euclidean distance calculations.
    """
    key = (id(board), src)
    if key not in _STATIC_DIST_CACHE:
        dist = {src: 0}
        q = deque([src])
        while q:
            cur = q.popleft()
            d = dist[cur]
            for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
                nxt = (cur[0] + dr, cur[1] + dc)
                if board.free(nxt) and nxt not in dist:
                    dist[nxt] = d + 1
                    q.append(nxt)
        _STATIC_DIST_CACHE[key] = dist
    return _STATIC_DIST_CACHE[key]

def static_distance(board: SokobanMap, p1: Pos, p2: Pos) -> int | float:
    """Return the wall-aware static floor shortest-path distance between p1 and p2."""
    if p1 == p2:
        return 0
    d_map = get_static_distances(board, p1)
    return d_map.get(p2, float('inf'))

def legal_intent(pos, action, board, boxes):
    dr, dc = DIRECTIONS[action]
    nxt = (pos[0] + dr, pos[1] + dc)
    if not board.free(nxt):
        return pos, None
    if nxt in boxes:
        beyond = (nxt[0] + dr, nxt[1] + dc)
        if not board.free(beyond) or beyond in boxes:
            return pos, None
        return nxt, (nxt, beyond)
    return nxt, None

def route_to_push(pos, boxes, board, goals):
    """Small BFS to reach a useful support square; returns the first safe move."""
    q = deque([(pos, ())])
    seen = {pos}
    while q:
        cur, path = q.popleft()
        if path and len(path) > 12:
            continue
        for action, (dr, dc) in DIRECTIONS.items():
            nxt = (cur[0] + dr, cur[1] + dc)
            if not board.free(nxt) or nxt in boxes:
                continue
            newpath = path + (action,)
            for b in boxes:
                if (b[0] - dr, b[1] - dc) == nxt and board.free((b[0] + dr, b[1] + dc)) and (b[0] + dr, b[1] + dc) not in boxes:
                    return path[0] if path else action
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, newpath))
    return None

class Agent:
    name = 'Agent'
    def choose_action(self, state, board, time_limit_ms=1000):
        raise NotImplementedError
