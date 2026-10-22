from dataclasses import dataclass
from typing import Any
import time

@dataclass
class SearchResult:
    solved: bool
    actions: list[str]
    total_cost: int | None
    expanded_nodes: int
    generated_nodes: int
    max_frontier_size: int
    elapsed_ms: float
    solution_states: list[Any]
    heuristic_calls: int = 0
    heuristic_cache_hits: int = 0
    heuristic_cache_misses: int = 0
    def as_dict(self): return self.__dict__.copy()

def graph_search(problem, use_heuristic=False, prune_deadlocks=True):
    import heapq
    from itertools import count
    from ..deadlock import state_has_deadlock
    start_time = time.perf_counter_ns(); start = problem.initial_state
    heuristic = problem.heuristic_model
    frontier = []
    explored = set()
    serial = count()
    g_n = {start: 0}
    parent = {start: (None, None)}
    initial_h = heuristic(start) if use_heuristic else 0
    heapq.heappush(frontier, (initial_h, 0, next(serial), start))
    expanded = generated = max_frontier = 0
    while frontier:
        _, popped_g, _, state = heapq.heappop(frontier)
        if state in explored:
            continue
        if problem.is_goal(state):
            actions = []; states = []; cur = state
            while cur is not None:
                states.append(cur); prev, action = parent[cur]
                if action is not None: actions.append(action)
                cur = prev
            states.reverse(); actions.reverse()
            return SearchResult(True, actions, popped_g, expanded, generated, max_frontier,
                (time.perf_counter_ns() - start_time) / 1e6, states,
                heuristic.cache_hits + heuristic.cache_misses, heuristic.cache_hits, heuristic.cache_misses)
        explored.add(state)
        expanded += 1
        for action, nxt in problem.get_successors(state):
            generated += 1
            if nxt in explored:
                continue
            if prune_deadlocks and state_has_deadlock(nxt, heuristic):
                continue
            new_g = popped_g + 1
            if new_g < g_n.get(nxt, float('inf')):
                g_n[nxt] = new_g
                parent[nxt] = (state, action)
                h_n = heuristic(nxt) if use_heuristic else 0
                f_n = new_g + h_n
                heapq.heappush(frontier, (f_n, new_g, next(serial), nxt))
                max_frontier = max(max_frontier, len(frontier))
    return SearchResult(False, [], None, expanded, generated, max_frontier,
        (time.perf_counter_ns() - start_time) / 1e6, [],
        heuristic.cache_hits + heuristic.cache_misses, heuristic.cache_hits, heuristic.cache_misses)
