import heapq
import time
from itertools import count
from .base import Agent, static_distance
from ..state import DIRECTIONS
from ..heuristic import ReversePushHeuristic

class AStarAgent(Agent):
    name = 'A*'

    def __init__(self, player_id: int = 1):
        self.player_id = player_id

    def _eval_h(self, state, board, heuristic: ReversePushHeuristic) -> float:
        pos, boxes = state
        box_cost = heuristic.for_boxes(boxes)
        if box_cost == float('inf'):
            return float('inf')
        # Proximity to nearest box using wall-aware static floor distance (non-Manhattan)
        if boxes:
            min_dist = min(static_distance(board, pos, b) for b in boxes)
            if min_dist == float('inf'):
                return float('inf')
        else:
            min_dist = 0
        return float(10 * box_cost + min_dist)


    def choose_action(self, state, board, time_limit_ms=1000):
        # Enforce strict internal deadline <= 950ms
        deadline = time.perf_counter_ns() + int(min(time_limit_ms, 950) * 1e6)
        my_pos = state.p1 if self.player_id == 1 else state.p2
        opp_pos = state.p2 if self.player_id == 1 else state.p1
        heuristic = ReversePushHeuristic(board)

        serial = count()
        start_state = (my_pos, state.boxes)
        initial_h = self._eval_h(start_state, board, heuristic)

        # OPEN priority queue: (f(n), g(n), serial, state, first_action, depth)
        open_pq = [(initial_h, 0, next(serial), start_state, None, 0)]
        best_g = {start_state: 0}

        best_plan_first_action = None
        best_h_seen = initial_h

        # Default fallback: first safe legal move
        fallback_action = 'North'
        for act, (dr, dc) in DIRECTIONS.items():
            nxt = (my_pos[0] + dr, my_pos[1] + dc)
            if board.free(nxt) and nxt != opp_pos:
                fallback_action = act
                break

        max_depth = 14
        max_expansions = 1200
        expanded = 0

        while open_pq:
            if time.perf_counter_ns() >= deadline:
                break
            if expanded >= max_expansions:
                break

            f, g, _, (cur_pos, cur_boxes), first_action, depth = heapq.heappop(open_pq)
            if g > best_g.get((cur_pos, cur_boxes), float('inf')):
                continue

            expanded += 1
            cur_h = self._eval_h((cur_pos, cur_boxes), board, heuristic)

            if cur_h < best_h_seen and first_action is not None:
                best_h_seen = cur_h
                best_plan_first_action = first_action
                if cur_h == 0:
                    break

            if depth >= max_depth:
                continue

            for action, (dr, dc) in DIRECTIONS.items():
                nxt = (cur_pos[0] + dr, cur_pos[1] + dc)
                if not board.free(nxt) or nxt == opp_pos:
                    continue

                if nxt in cur_boxes:
                    beyond = (nxt[0] + dr, nxt[1] + dc)
                    if not board.free(beyond) or beyond in cur_boxes or beyond == opp_pos:
                        continue
                    nxt_boxes = frozenset((cur_boxes - {nxt}) | {beyond})
                    nxt_pos = nxt
                else:
                    nxt_boxes = cur_boxes
                    nxt_pos = nxt

                nxt_state = (nxt_pos, nxt_boxes)
                ng = g + 1
                if ng < best_g.get(nxt_state, float('inf')):
                    best_g[nxt_state] = ng
                    nh = self._eval_h(nxt_state, board, heuristic)
                    if nh < float('inf'):
                        fa = first_action if first_action is not None else action
                        heapq.heappush(open_pq, (ng + nh, ng, next(serial), nxt_state, fa, depth + 1))

        return best_plan_first_action or fallback_action
