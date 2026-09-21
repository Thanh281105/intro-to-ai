from collections import deque
from typing import Optional
from ..map import Pos, SokobanMap
from ..state import DIRECTIONS
from ..heuristic import ReversePushHeuristic
from ..deadlock import is_static_deadlock
from ..agents.base import static_distance
from .evaluator_base import BaseCompetitiveEvaluator
from .weights import CompetitiveWeights, DEFAULT_WEIGHTS

class CompetitiveEvaluator(BaseCompetitiveEvaluator):
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
        self._support_cache: dict[tuple, float] = {}

    def is_deadlock_square(self, p: Pos) -> bool:
        """Check if cell is a sound static deadlock square."""
        return p in self.dead_squares

    def find_useful_pushes(
        self,
        player_pos: Pos = (0, 0),
        opp_pos: Pos = (0, 0),
        boxes: frozenset[Pos] = frozenset(),
        owner_map: Optional[dict[Pos, int]] = None,
        player_id: int = 1,
        **kwargs,
    ) -> list[tuple[Pos, Pos]]:
        """Identify candidate pushes that make progress toward completing goals.
        Returns list of (support_pos, push_dest_pos).
        """
        if owner_map is None:
            owner_map = {}

        useful_pushes = []
        for b in boxes:
            b_owner = owner_map.get(b, 0)
            is_own_completed = (b in self.goals and b_owner == player_id)

            for action, (dr, dc) in DIRECTIONS.items():
                dest = (b[0] + dr, b[1] + dc)
                supp = (b[0] - dr, b[1] - dc)

                # Both dest and supp must be free valid floor cells
                if not self.board.free(dest) or not self.board.free(supp):
                    continue
                if supp in boxes or supp == opp_pos:
                    continue
                if dest in boxes:
                    continue
                # Static deadlock pruning
                if dest not in self.goals and is_static_deadlock(dest, self.heuristic):
                    continue

                # Situation 2: Disrupting opponent's completed box
                if b in self.goals and b_owner not in (0, player_id):
                    useful_pushes.append((supp, dest))
                    continue

                # Situation 3: Completing a goal (or repositioning onto another goal)
                if dest in self.goals:
                    useful_pushes.append((supp, dest))
                    continue

                # For own completed box: moving off goal drops score
                if is_own_completed:
                    continue

                # Situation 4: Advancing uncompleted box closer to goals
                cur_dist = min((self.heuristic.distance(b, g) for g in self.goals), default=float('inf'))
                nxt_dist = min((self.heuristic.distance(dest, g) for g in self.goals), default=float('inf'))
                if nxt_dist < cur_dist:
                    useful_pushes.append((supp, dest))

        return useful_pushes

    def compute_support_distance(
        self,
        player_pos: Pos,
        opp_pos: Pos,
        boxes: frozenset[Pos],
        owner_map: dict[Pos, int],
        player_id: int,
    ) -> float:
        """Compute exact wall-aware, obstacle-avoiding shortest path distance
        from player_pos to the closest useful push support cell via dynamic BFS.
        """
        cache_key = (player_pos, opp_pos, boxes, tuple(sorted(owner_map.items())), player_id)
        if cache_key in self._support_cache:
            return self._support_cache[cache_key]

        useful = self.find_useful_pushes(player_pos, opp_pos, boxes, owner_map, player_id)
        if not useful:
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
        enable_score_diff: bool = True,
        enable_support_dist: bool = True,
        enable_horizon_scaling: bool = True,
        enable_ownership: bool = True,
    ) -> float:
        """Compute state potential Phi_i(s) from perspective of Agent i."""
        owner_map = dict(owners)
        if enable_ownership:
            my_score = sum(1 for b in boxes if b in self.goals and owner_map.get(b) == player_id)
            opp_id = 2 if player_id == 1 else 1
            opp_score = sum(1 for b in boxes if b in self.goals and owner_map.get(b) == opp_id)
        else:
            my_score = sum(1 for b in boxes if b in self.goals)
            opp_score = 0

        score_diff = (my_score - opp_score) if enable_score_diff else 0

        # Terminal Evaluation at horizon (step >= step_limit)
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

        if enable_support_dist:
            support_dist = self.compute_support_distance(
                player_pos, opp_pos, boxes, owner_map, player_id
            )
        else:
            support_dist = 0.0

        # Horizon awareness: score diff matters more near the end
        if enable_horizon_scaling and step_limit > 0:
            u = min(1.0, max(0.0, step / step_limit))
            w_score_eff = weights.w_score * (1.0 + weights.horizon_alpha * u)
            if score_diff > 0 and u > 0.7:
                w_push_eff = weights.w_push * (1.0 - 0.25 * u)
            else:
                w_push_eff = weights.w_push
        else:
            w_score_eff = weights.w_score
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
        **kwargs,
    ) -> float:
        """Search heuristic cost h_comp(s) = -Phi_i(s).
        Minimizing h_comp directly maximizes state potential Phi_i(s).
        """
        phi = self.evaluate_phi(
            player_pos, opp_pos, boxes, owners, step, player_id, step_limit, weights, **kwargs
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
