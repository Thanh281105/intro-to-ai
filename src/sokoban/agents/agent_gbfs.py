import heapq
import time
from itertools import count
from typing import Optional
from .base import Agent
from ..state import DIRECTIONS
from ..competitive.evaluator import CompetitiveEvaluator, CompetitiveWeights, DEFAULT_WEIGHTS

class GBFSAgent(Agent):
    name = 'GBFS'

    def __init__(self, player_id: int = 2, weights: Optional[CompetitiveWeights] = None, evaluator_type: str = 'new'):
        self.player_id = player_id
        self.weights = weights or DEFAULT_WEIGHTS
        self.evaluator_type = evaluator_type
        self.last_evaluation: Optional[dict] = None

    def _eval_h_old(self, state, board, heuristic) -> float:
        pos, boxes = state
        box_cost = heuristic.for_boxes(boxes)
        if box_cost == float('inf'):
            return float('inf')
        if boxes:
            from .base import static_distance
            min_dist = min(static_distance(board, pos, b) for b in boxes)
            if min_dist == float('inf'):
                return float('inf')
        else:
            min_dist = 0
        return float(10 * box_cost + min_dist)

    def choose_action(self, state, board, time_limit_ms: int = 1000, step_limit: int = 25) -> str:
        # Enforce strict internal deadline <= 950ms using high-precision performance counter
        deadline = time.perf_counter_ns() + int(min(time_limit_ms, 950) * 1e6)
        my_pos = state.p2 if self.player_id == 2 else state.p1
        opp_pos = state.p1 if self.player_id == 2 else state.p2

        # Default fallback: first safe legal move
        fallback_action = 'North'
        for act, (dr, dc) in DIRECTIONS.items():
            nxt = (my_pos[0] + dr, my_pos[1] + dc)
            if board.free(nxt) and nxt != opp_pos and nxt not in state.boxes:
                fallback_action = act
                break

        # LEGACY OLD EVALUATION PATH
        if self.evaluator_type == 'old':
            from ..heuristic import ReversePushHeuristic
            heuristic = ReversePushHeuristic(board)
            serial = count()
            start_state = (my_pos, state.boxes)
            initial_h = self._eval_h_old(start_state, board, heuristic)
            open_pq = [(initial_h, next(serial), start_state, None, 0)]
            visited = {start_state}
            best_plan_first_action = None
            best_h_seen = initial_h
            max_depth = 14
            max_expansions = 600
            expanded = 0

            while open_pq:
                if time.perf_counter_ns() >= deadline or expanded >= max_expansions:
                    break
                h, _, (cur_pos, cur_boxes), first_action, depth = heapq.heappop(open_pq)
                expanded += 1
                if h < best_h_seen and first_action is not None:
                    best_h_seen = h
                    best_plan_first_action = first_action
                    if h == 0:
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
                    if nxt_state not in visited:
                        visited.add(nxt_state)
                        nh = self._eval_h_old(nxt_state, board, heuristic)
                        if nh < float('inf'):
                            fa = first_action if first_action is not None else action
                            heapq.heappush(open_pq, (nh, next(serial), nxt_state, fa, depth + 1))
            return best_plan_first_action or fallback_action

        # NEW RL-INSPIRED EVALUATION PATH
        evaluator = CompetitiveEvaluator.get(board)

        cur_step = getattr(state, 'step', 0)
        start_state = (my_pos, state.boxes, state.owners, cur_step)
        initial_h = evaluator.evaluate_h(
            my_pos, opp_pos, state.boxes, state.owners, cur_step,
            self.player_id, step_limit, self.weights
        )

        self.last_evaluation = evaluator.breakdown(
            my_pos, opp_pos, state.boxes, state.owners, cur_step,
            self.player_id, step_limit, self.weights
        )

        # OPEN priority queue ordered purely by h(n): (h(n), serial, state, first_action, depth)
        serial = count()
        open_pq = [(initial_h, next(serial), start_state, None, 0)]
        visited = {(my_pos, state.boxes, state.owners)}

        best_plan_first_action = None
        best_h_seen = initial_h

        max_depth = 14
        max_expansions = 600
        expanded = 0

        while open_pq:
            if time.perf_counter_ns() >= deadline:
                break
            if expanded >= max_expansions:
                break

            h, _, (cur_pos, cur_boxes, cur_owners, c_step), first_action, depth = heapq.heappop(open_pq)
            expanded += 1

            if h < best_h_seen and first_action is not None:
                best_h_seen = h
                best_plan_first_action = first_action
                # Terminal win achieved
                if h <= -self.weights.terminal_win:
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
                    # Sound static deadlock pruning
                    if beyond not in evaluator.goals and evaluator.is_deadlock_square(beyond):
                        continue

                    nxt_boxes = frozenset((cur_boxes - {nxt}) | {beyond})
                    # Update box ownership semantics
                    owners_dict = dict(cur_owners)
                    owners_dict.pop(nxt, None)
                    if beyond in evaluator.goals:
                        owners_dict[beyond] = self.player_id
                    nxt_owners = tuple(
                        sorted((p, o) for p, o in owners_dict.items() if p in nxt_boxes and p in evaluator.goals)
                    )
                    nxt_pos = nxt
                else:
                    nxt_boxes = cur_boxes
                    nxt_owners = cur_owners
                    nxt_pos = nxt

                nxt_step = c_step + 1
                nxt_state_key = (nxt_pos, nxt_boxes, nxt_owners)

                if nxt_state_key not in visited:
                    visited.add(nxt_state_key)
                    nh = evaluator.evaluate_h(
                        nxt_pos, opp_pos, nxt_boxes, nxt_owners, nxt_step,
                        self.player_id, step_limit, self.weights
                    )
                    if nh < float('inf'):
                        fa = first_action if first_action is not None else action
                        nxt_search_state = (nxt_pos, nxt_boxes, nxt_owners, nxt_step)
                        heapq.heappush(open_pq, (nh, next(serial), nxt_search_state, fa, depth + 1))

        return best_plan_first_action or fallback_action

