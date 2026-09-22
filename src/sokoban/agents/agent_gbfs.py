import heapq
import time
from itertools import count
from typing import Optional
from .base import Agent
from ..state import DIRECTIONS
from ..competitive.evaluator import (
    CompetitiveEvaluator,
    CompetitiveWeights,
    DEFAULT_WEIGHTS,
    OldEvaluator,
    SAFETY_DEADLINE_MS,
    MAX_SEARCH_DEPTH,
    MAX_SEARCH_EXPANSIONS,
)

class GBFSAgent(Agent):
    name = 'GBFS'

    def __init__(self, player_id: int = 2, weights: Optional[CompetitiveWeights] = None, evaluator_type: str = 'new'):
        self.player_id = player_id
        self.weights = weights or DEFAULT_WEIGHTS
        self.evaluator_type = evaluator_type
        self.last_evaluation: Optional[dict] = None

    def choose_action(self, state, board, time_limit_ms: int = 1000, step_limit: int = 25) -> str:
        # Enforce strict internal safety deadline using high-precision performance counter
        deadline = time.perf_counter_ns() + int(min(time_limit_ms, SAFETY_DEADLINE_MS) * 1e6)
        my_pos = state.p2 if self.player_id == 2 else state.p1
        opp_pos = state.p1 if self.player_id == 2 else state.p2

        # Fallback action: prioritize legal walk moves, then legal push moves
        fallback_action = 'North'
        legal_walks = []
        legal_pushes = []
        for act, (dr, dc) in DIRECTIONS.items():
            nxt = (my_pos[0] + dr, my_pos[1] + dc)
            if not board.free(nxt) or nxt == opp_pos:
                continue
            if nxt in state.boxes:
                beyond = (nxt[0] + dr, nxt[1] + dc)
                if board.free(beyond) and beyond not in state.boxes and beyond != opp_pos:
                    legal_pushes.append(act)
            else:
                legal_walks.append(act)

        if legal_walks:
            fallback_action = legal_walks[0]
        elif legal_pushes:
            fallback_action = legal_pushes[0]

        # LEGACY OLD EVALUATION PATH
        if self.evaluator_type == 'old':
            old_eval = OldEvaluator.get(board)
            serial = count()
            start_state = (my_pos, state.boxes)
            initial_h = old_eval.evaluate_h_state(my_pos, state.boxes)
            open_pq = [(initial_h, next(serial), start_state, None, 0)]
            visited = {start_state}
            best_plan_first_action = None
            best_h_seen = initial_h
            max_depth = MAX_SEARCH_DEPTH
            max_expansions = MAX_SEARCH_EXPANSIONS
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
                        nh = old_eval.evaluate_h_state(nxt_pos, nxt_boxes)
                        if nh < float('inf'):
                            fa = first_action if first_action is not None else action
                            heapq.heappush(open_pq, (nh, next(serial), nxt_state, fa, depth + 1))
            return best_plan_first_action or fallback_action

        # NEW RL-INSPIRED EVALUATION PATH
        evaluator = CompetitiveEvaluator.get(board)

        cur_step = getattr(state, 'step', 0)
        # Search state tuple: (cur_pos, cur_boxes, cur_owners, c_step, last_action, last_was_push)
        start_state = (my_pos, state.boxes, state.owners, cur_step, None, False)
        initial_h = evaluator.evaluate_h(
            my_pos, opp_pos, state.boxes, state.owners, cur_step,
            self.player_id, step_limit, self.weights
        )

        self.last_evaluation = evaluator.breakdown(
            my_pos, opp_pos, state.boxes, state.owners, cur_step,
            self.player_id, step_limit, self.weights
        )

        # OPEN priority queue ordered purely by h(n): (h(n), rank, serial, state, first_action, depth)
        serial = count()
        open_pq = [(initial_h, 3, next(serial), start_state, None, 0)]
        visited = {(my_pos, state.boxes, state.owners, cur_step)}

        best_plan_first_action = None
        best_h_seen = initial_h

        max_depth = MAX_SEARCH_DEPTH
        max_expansions = MAX_SEARCH_EXPANSIONS
        expanded = 0
        opposite_dirs = {'North': 'South', 'South': 'North', 'East': 'West', 'West': 'East'}

        while open_pq:
            if time.perf_counter_ns() >= deadline:
                break
            if expanded >= max_expansions:
                break

            h, rank, _, (cur_pos, cur_boxes, cur_owners, c_step, last_action, last_was_push), first_action, depth = heapq.heappop(open_pq)
            expanded += 1

            if h < best_h_seen and first_action is not None:
                best_h_seen = h
                best_plan_first_action = first_action
                # Terminal win achieved
                if h <= -self.weights.terminal_win:
                    break

            if depth >= max_depth:
                continue

            opp_id = 2 if self.player_id == 1 else 1
            candidates = []
            for action, (dr, dc) in DIRECTIONS.items():
                # Acyclic walk-reversal pruning: do not immediately reverse pure walk steps
                if last_action is not None and not last_was_push and action == opposite_dirs[last_action]:
                    continue

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
                    old_owner = owners_dict.pop(nxt, None)
                    if beyond in evaluator.goals:
                        owners_dict[beyond] = self.player_id
                    nxt_owners = tuple(
                        sorted((p, o) for p, o in owners_dict.items() if p in nxt_boxes and p in evaluator.goals)
                    )
                    nxt_pos = nxt
                    is_push = True
                    if beyond in evaluator.goals:
                        move_rank = 0
                    elif nxt in evaluator.goals and old_owner == opp_id:
                        move_rank = 1
                    else:
                        move_rank = 2
                else:
                    nxt_boxes = cur_boxes
                    nxt_owners = cur_owners
                    nxt_pos = nxt
                    is_push = False
                    move_rank = 3

                candidates.append((move_rank, action, is_push, nxt_pos, nxt_boxes, nxt_owners))

            candidates.sort(key=lambda c: c[0])

            for move_rank, action, is_push, nxt_pos, nxt_boxes, nxt_owners in candidates:
                nxt_step = c_step + 1
                nxt_state_key = (nxt_pos, nxt_boxes, nxt_owners, nxt_step)

                if nxt_state_key not in visited:
                    visited.add(nxt_state_key)
                    nh = evaluator.evaluate_h(
                        nxt_pos, opp_pos, nxt_boxes, nxt_owners, nxt_step,
                        self.player_id, step_limit, self.weights
                    )
                    if nh < float('inf'):
                        fa = first_action if first_action is not None else action
                        nxt_search_state = (nxt_pos, nxt_boxes, nxt_owners, nxt_step, action, is_push)
                        heapq.heappush(open_pq, (nh, move_rank, next(serial), nxt_search_state, fa, depth + 1))

        return best_plan_first_action or fallback_action

