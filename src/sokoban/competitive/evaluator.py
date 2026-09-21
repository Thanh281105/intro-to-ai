from collections import deque
from dataclasses import dataclass
from typing import Optional
from ..map import Pos, SokobanMap
from ..state import DIRECTIONS
from ..heuristic import ReversePushHeuristic
from ..deadlock import is_static_deadlock
from ..agents.base import static_distance

@dataclass(frozen=True)
class CompetitiveWeights:
    w_score: float = 30.0
    w_push: float = 3.0
    w_route: float = 2.0
    step_penalty: float = -1.0
    terminal_win: float = 1000.0
    terminal_loss: float = -1000.0
    terminal_draw: float = 0.0
    horizon_alpha: float = 0.5

DEFAULT_WEIGHTS = CompetitiveWeights()

class CompetitiveEvaluator:
    """RL-inspired value-function state evaluator for competitive Sokoban.
    Computes potential Phi_i(s), support-cell distances, and reward shaping terms.
    Precomputes and caches static board structures for sub-millisecond execution.
    """
    _instances: dict[int, 'CompetitiveEvaluator'] = {}

    @classmethod
    def get(cls, board: SokobanMap) -> 'CompetitiveEvaluator':
        bid = id(board)
        if bid not in cls._instances:
            cls._instances[bid] = cls(board)
        return cls._instances[bid]

    def __init__(self, board: SokobanMap):
        self.board = board
        self.heuristic = ReversePushHeuristic(board)
        self.goals = frozenset(board.goals)
        # Precompute static dead squares (unpushable cells that cannot reach any goal)
        self.dead_squares = frozenset(
            p for p in board.floor_cells
            if p not in self.goals and is_static_deadlock(p, self.heuristic)
        )
        self._useful_cache: dict[tuple, list[tuple[Pos, Pos]]] = {}
        self._support_cache: dict[tuple, float] = {}
        self._cache: dict[tuple, float] = {}

    def is_deadlock_square(self, pos: Pos) -> bool:
        """Sound check if a cell is an unpushable static dead square."""
        return pos in self.dead_squares

    def has_static_deadlock(self, boxes: frozenset[Pos]) -> bool:
        """Check if any box not on a goal is permanently deadlocked."""
        return any(b in self.dead_squares for b in boxes)

    def find_useful_pushes(
        self,
        player_pos: Pos,
        opp_pos: Pos,
        boxes: frozenset[Pos],
        owner_map: dict[Pos, int],
        player_id: int,
    ) -> list[tuple[Pos, Pos]]:
        """Identify all legal pushes that improve goal progress or score difference.
        Returns list of (support_pos, push_dest).

        Key competitive behaviors:
        1. Protect own completed boxes: never push an owned box off a goal.
        2. Disrupt opponent completed boxes: pushing opponent's box off a goal is HIGH value.
        3. Score goals: pushing any box into an empty goal is HIGH value.
        4. Progress: pushing uncompleted boxes closer to goals under reverse-push distance.
        """
        cache_key = (boxes, tuple(sorted(owner_map.items())), player_id, opp_pos)
        if cache_key in self._useful_cache:
            return self._useful_cache[cache_key]

        useful_pushes = []
        opp_id = 2 if player_id == 1 else 1
        cur_matching_cost = self.heuristic.for_boxes(boxes)

        for b in boxes:
            b_owner = owner_map.get(b, 0)
            is_own_completed = (b in self.goals and b_owner == player_id)

            for action, (dr, dc) in DIRECTIONS.items():
                dest = (b[0] + dr, b[1] + dc)
                supp = (b[0] - dr, b[1] - dc)

                # Physical feasibility check
                if not self.board.free(dest) or dest in boxes or dest == opp_pos:
                    continue
                if not self.board.free(supp) or supp in boxes or supp == opp_pos:
                    continue

                # Sound deadlock pruning: discard pushes into non-goal static dead squares
                if dest not in self.goals and dest in self.dead_squares:
                    continue

                # Situation 2: Disrupt opponent completed box
                if b in self.goals and b_owner == opp_id:
                    useful_pushes.append((supp, dest))
                    continue

                # Situation 3: Completing a goal (or repositioning onto another goal)
                if dest in self.goals:
                    useful_pushes.append((supp, dest))
                    continue

                # For own completed box: moving off goal drops score (evaluated softly via score_diff)
                if is_own_completed:
                    continue

                # Situation 4: Advancing uncompleted box closer to goals
                cur_dist = min((self.heuristic.distance(b, g) for g in self.goals), default=float('inf'))
                nxt_dist = min((self.heuristic.distance(dest, g) for g in self.goals), default=float('inf'))
                if nxt_dist < cur_dist and nxt_dist != float('inf'):
                    useful_pushes.append((supp, dest))
                    continue

                # Or check if full bipartite matching cost improves
                new_boxes = frozenset((boxes - {b}) | {dest})
                new_matching_cost = self.heuristic.for_boxes(new_boxes)
                if new_matching_cost < cur_matching_cost and new_matching_cost != float('inf'):
                    useful_pushes.append((supp, dest))

        self._useful_cache[cache_key] = useful_pushes
        return useful_pushes

    def compute_support_distance(
        self,
        player_pos: Pos,
        opp_pos: Pos,
        boxes: frozenset[Pos],
        owner_map: dict[Pos, int],
        player_id: int,
    ) -> float:
        """Compute wall-aware, obstacle-avoiding shortest-path distance to a useful push support cell.
        Avoids Manhattan and Euclidean distance entirely.
        """
        # If all goals completed by me, support distance is zero
        my_completed = sum(1 for b in boxes if b in self.goals and owner_map.get(b) == player_id)
        if my_completed == len(self.goals):
            return 0.0

        cache_key = (player_pos, opp_pos, boxes, tuple(sorted(owner_map.items())), player_id)
        if cache_key in self._support_cache:
            return self._support_cache[cache_key]

        useful = self.find_useful_pushes(player_pos, opp_pos, boxes, owner_map, player_id)
        if not useful:
            # No useful pushes currently feasible; return neutral baseline
            self._support_cache[cache_key] = 0.0
            return 0.0

        support_cells = {supp for supp, _ in useful}
        if player_pos in support_cells:
            self._support_cache[cache_key] = 0.0
            return 0.0

        # Wall-aware dynamic BFS avoiding walls, boxes, and opponent
        dist: dict[Pos, int] = {player_pos: 0}
        q = deque([player_pos])
        found_dist: Optional[int] = None

        while q:
            cur = q.popleft()
            d = dist[cur]
            if cur in support_cells:
                found_dist = d
                break
            for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
                nxt = (cur[0] + dr, cur[1] + dc)
                if (
                    self.board.free(nxt)
                    and nxt not in boxes
                    and nxt != opp_pos
                    and nxt not in dist
                ):
                    dist[nxt] = d + 1
                    q.append(nxt)

        if found_dist is not None:
            res = float(found_dist)
            self._support_cache[cache_key] = res
            return res

        # Fallback if useful support cells are dynamically blocked:
        # use static shortest path distance plus detour penalty
        min_static = min(
            (static_distance(self.board, player_pos, s) for s in support_cells),
            default=float('inf'),
        )
        if min_static != float('inf'):
            res = float(min_static + 10.0)
        else:
            res = 20.0
        self._support_cache[cache_key] = res
        return res

    def evaluate_phi(
        self,
        player_pos: Pos,
        opp_pos: Pos,
        boxes: frozenset[Pos],
        owners: tuple[tuple[Pos, int], ...],
        step: int,
        player_id: int,
        step_limit: int,
        weights: CompetitiveWeights = DEFAULT_WEIGHTS,
    ) -> float:
        """Compute state potential Phi_i(s) from perspective of Agent i."""
        owner_map = dict(owners)
        my_score = sum(1 for b in boxes if b in self.goals and owner_map.get(b) == player_id)
        opp_id = 2 if player_id == 1 else 1
        opp_score = sum(1 for b in boxes if b in self.goals and owner_map.get(b) == opp_id)
        score_diff = my_score - opp_score

        # Situation 3: Terminal Evaluation at horizon (step >= step_limit)
        if step_limit > 0 and step >= step_limit:
            if score_diff > 0:
                return weights.terminal_win + weights.w_score * score_diff
            elif score_diff < 0:
                return weights.terminal_loss + weights.w_score * score_diff
            else:
                return weights.terminal_draw

        # Non-terminal state evaluation
        push_cost = self.heuristic.for_boxes(boxes)
        if push_cost == float('inf'):
            return -float('inf')

        support_dist = self.compute_support_distance(
            player_pos, opp_pos, boxes, owner_map, player_id
        )

        # Horizon awareness: score diff matters more near the end
        u = min(1.0, max(0.0, step / step_limit)) if step_limit > 0 else 0.0
        w_score_eff = weights.w_score * (1.0 + weights.horizon_alpha * u)

        # When leading late in the game, focus on defending score rather than risky push progress
        if score_diff > 0 and u > 0.7:
            w_push_eff = weights.w_push * (1.0 - 0.25 * u)
        else:
            w_push_eff = weights.w_push

        phi = (
            w_score_eff * score_diff
            - w_push_eff * push_cost
            - weights.w_route * support_dist
        )
        return float(phi)

    def evaluate_h(
        self,
        player_pos: Pos,
        opp_pos: Pos,
        boxes: frozenset[Pos],
        owners: tuple[tuple[Pos, int], ...],
        step: int,
        player_id: int,
        step_limit: int,
        weights: CompetitiveWeights = DEFAULT_WEIGHTS,
    ) -> float:
        """Search heuristic cost h_comp(s) = -Phi_i(s).
        Minimizing h_comp directly maximizes state potential Phi_i(s).
        """
        phi = self.evaluate_phi(
            player_pos, opp_pos, boxes, owners, step, player_id, step_limit, weights
        )
        if phi == -float('inf'):
            return float('inf')
        return -phi

    def transition_reward(
        self,
        s_old: tuple[Pos, frozenset[Pos], tuple[tuple[Pos, int], ...], int],
        s_new: tuple[Pos, frozenset[Pos], tuple[tuple[Pos, int], ...], int],
        opp_pos: Pos,
        player_id: int,
        step_limit: int,
        weights: CompetitiveWeights = DEFAULT_WEIGHTS,
    ) -> float:
        """Compute conceptual transition reward R_i(s, a, s') = STEP_PENALTY + Phi(s') - Phi(s)."""
        pos_old, boxes_old, owners_old, step_old = s_old
        pos_new, boxes_new, owners_new, step_new = s_new
        phi_old = self.evaluate_phi(
            pos_old, opp_pos, boxes_old, owners_old, step_old, player_id, step_limit, weights
        )
        phi_new = self.evaluate_phi(
            pos_new, opp_pos, boxes_new, owners_new, step_new, player_id, step_limit, weights
        )
        return weights.step_penalty + (phi_new - phi_old)

    def breakdown(
        self,
        player_pos: Pos,
        opp_pos: Pos,
        boxes: frozenset[Pos],
        owners: tuple[tuple[Pos, int], ...],
        step: int,
        player_id: int,
        step_limit: int,
        weights: CompetitiveWeights = DEFAULT_WEIGHTS,
    ) -> dict:
        """Provide detailed per-component breakdown for CLI/debug inspection."""
        owner_map = dict(owners)
        my_score = sum(1 for b in boxes if b in self.goals and owner_map.get(b) == player_id)
        opp_id = 2 if player_id == 1 else 1
        opp_score = sum(1 for b in boxes if b in self.goals and owner_map.get(b) == opp_id)
        score_diff = my_score - opp_score

        push_cost = self.heuristic.for_boxes(boxes)
        support_dist = self.compute_support_distance(
            player_pos, opp_pos, boxes, owner_map, player_id
        )
        u = min(1.0, max(0.0, step / step_limit)) if step_limit > 0 else 0.0
        w_score_eff = weights.w_score * (1.0 + weights.horizon_alpha * u)
        if score_diff > 0 and u > 0.7:
            w_push_eff = weights.w_push * (1.0 - 0.25 * u)
        else:
            w_push_eff = weights.w_push

        phi = self.evaluate_phi(
            player_pos, opp_pos, boxes, owners, step, player_id, step_limit, weights
        )

        return {
            'player_id': player_id,
            'step': step,
            'step_limit': step_limit,
            'my_score': my_score,
            'opp_score': opp_score,
            'score_diff': score_diff,
            'score_contrib': round(w_score_eff * score_diff, 2),
            'push_cost': round(push_cost, 2),
            'push_contrib': round(-w_push_eff * push_cost, 2),
            'support_dist': round(support_dist, 2),
            'route_contrib': round(-weights.w_route * support_dist, 2),
            'phi': round(phi, 2),
            'h_comp': round(-phi, 2),
        }
