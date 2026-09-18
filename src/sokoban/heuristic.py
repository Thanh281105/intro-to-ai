from collections import deque
from functools import lru_cache
from .map import Pos, SokobanMap

class ReversePushHeuristic:
    """Wall-aware relaxed push distances plus minimum-cost matching."""
    def __init__(self, board: SokobanMap):
        self.board = board
        self.distances = {g: self._reverse_distances(g) for g in sorted(board.goals)}
        self._cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def _reverse_distances(self, goal):
        dist = {goal: 0}; q = deque([goal])
        while q:
            cur = q.popleft()
            for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
                prev = (cur[0] - dr, cur[1] - dc)
                support = (prev[0] - dr, prev[1] - dc)
                if self.board.free(prev) and self.board.free(support) and prev not in dist:
                    dist[prev] = dist[cur] + 1
                    q.append(prev)
        return dist

    def distance(self, box: Pos, goal: Pos):
        return self.distances[goal].get(box, float('inf'))

    def for_boxes(self, boxes):
        key = tuple(sorted(boxes))
        if key in self._cache:
            self.cache_hits += 1
            return self._cache[key]
        self.cache_misses += 1
        goals = tuple(sorted(self.board.goals))
        if not key:
            value = 0
        else:
            costs = [[self.distance(box, goal) for goal in goals] for box in key]
            @lru_cache(None)
            def dp(i, mask):
                if i == len(key): return 0
                best = float('inf')
                for j, cost in enumerate(costs[i]):
                    if not mask >> j & 1 and cost != float('inf'):
                        best = min(best, cost + dp(i + 1, mask | (1 << j)))
                return best
            value = dp(0, 0)
        self._cache[key] = value
        return value

    def __call__(self, state):
        return self.for_boxes(state.boxes)
