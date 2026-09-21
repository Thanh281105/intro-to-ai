"""Ablation study script for competitive Sokoban potential evaluator.

Evaluates:
1. Full Potential Evaluator (all features active)
2. No Score Diff (w_score = 0)
3. No Support Distance (w_route = 0)
4. No Horizon Scaling (alpha = 0)
5. No Ownership Logic (goals treated neutrally)

Outputs results to experiments/results/evaluator_ablation.csv.
"""

import csv
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sokoban.map import SokobanMap
from sokoban.competitive.state import initial_state, resolve_with_turn
from sokoban.competitive.evaluator import (
    CompetitiveEvaluator,
    CompetitiveWeights,
    OldEvaluator,
    SAFETY_DEADLINE_MS,
)
from sokoban.agents import AStarAgent, GBFSAgent

root = Path(__file__).resolve().parents[1]
out = root / 'experiments/results'
out.mkdir(parents=True, exist_ok=True)
ablation_csv = out / 'evaluator_ablation.csv'

# Evaluate across tuning and validation maps (competitive_01 to 04)
eval_maps = [root / 'maps' / f'competitive_{i:02d}.txt' for i in (1, 2, 3, 4)]
step_limits = (10, 25)

VARIANTS = [
    ('Full Potential Evaluator', {}),
    ('No Score Difference', {'enable_score_diff': False}),
    ('No Support Distance', {'enable_support_dist': False}),
    ('No Horizon Scaling', {'enable_horizon_scaling': False}),
    ('No Ownership Logic', {'enable_ownership': False}),
]

def run_ablation():
    print("==================================================")
    print("Starting Competitive Evaluator Ablation Study")
    print(f"Evaluating {len(VARIANTS)} variants across {len(eval_maps)} maps x {len(step_limits)} horizons")
    print("==================================================")

    results = []
    base_weights = CompetitiveWeights(w_score=30.0, w_push=3.0, w_route=2.0)

    for name, kwargs in VARIANTS:
        matches = 0
        new_wins = 0
        old_wins = 0
        ties = 0
        new_scores = 0
        old_scores = 0
        useful_pushes = 0
        ineffective_actions = 0
        latencies = []
        fallbacks = 0

        for mp in eval_maps:
            board = SokobanMap.from_file(mp)
            heur = CompetitiveEvaluator.get(board).heuristic

            for limit in step_limits:
                # Role swap: Match A (P1=Variant, P2=OLD), Match B (P1=OLD, P2=Variant)
                for role_assignment in ('var_p1', 'var_p2'):
                    matches += 1
                    # Configure custom agent evaluation
                    if role_assignment == 'var_p1':
                        p1 = AStarAgent(player_id=1, weights=base_weights, evaluator_type='new')
                        p2 = AStarAgent(player_id=2, evaluator_type='old')
                    else:
                        p1 = AStarAgent(player_id=1, evaluator_type='old')
                        p2 = AStarAgent(player_id=2, weights=base_weights, evaluator_type='new')

                    # Monkey-patch evaluator call with variant kwargs for the testing agent
                    target_agent = p1 if role_assignment == 'var_p1' else p2
                    orig_choose = target_agent.choose_action

                    def make_patched_choose(agent_obj, is_p1):
                        def patched_choose(state, b, time_limit_ms=1000, step_limit=limit):
                            # Temporarily override evaluate_phi within agent
                            ev = CompetitiveEvaluator.get(b)
                            orig_phi = ev.evaluate_phi
                            ev.evaluate_phi = lambda *a, **k: orig_phi(*a, **{**k, **kwargs})
                            try:
                                return orig_choose(state, b, time_limit_ms, step_limit)
                            finally:
                                ev.evaluate_phi = orig_phi
                        return patched_choose

                    target_agent.choose_action = make_patched_choose(target_agent, role_assignment == 'var_p1')

                    state = initial_state(board)
                    match_lats = [[], []]
                    u_pushes = [0, 0]
                    ineff = [0, 0]

                    for _ in range(limit):
                        actions = []
                        for i, agent in enumerate((p1, p2)):
                            t0 = time.perf_counter_ns()
                            act = agent.choose_action(state, board, time_limit_ms=1000, step_limit=limit)
                            el_ms = (time.perf_counter_ns() - t0) / 1e6
                            match_lats[i].append(el_ms)
                            if (role_assignment == 'var_p1' and i == 0) or (role_assignment == 'var_p2' and i == 1):
                                latencies.append(el_ms)
                            if el_ms >= SAFETY_DEADLINE_MS:
                                fallbacks += 1
                            actions.append(act)

                        old_boxes = state.boxes
                        old_cost = heur.for_boxes(old_boxes)
                        old_owners = state.owner_map()

                        nxt_state, turn_rec = resolve_with_turn(
                            state, actions[0], actions[1], board, match_lats[0][-1], match_lats[1][-1]
                        )

                        for i, (outc, act) in enumerate(((turn_rec.a1_outcome, turn_rec.a1_action),
                                                         (turn_rec.a2_outcome, turn_rec.a2_action))):
                            if outc in ("BLOCKED", "CONFLICT"):
                                ineff[i] += 1
                            elif outc == "PUSH":
                                new_cost = heur.for_boxes(nxt_state.boxes)
                                aid = i + 1
                                opp_id = 2 if aid == 1 else 1
                                new_owners = nxt_state.owner_map()
                                improved_cost = (new_cost < old_cost and new_cost != float('inf'))
                                scored = any(b in board.goals and new_owners.get(b) == aid for b in nxt_state.boxes - old_boxes)
                                disrupted = any(b in board.goals and old_owners.get(b) == opp_id and new_owners.get(b) != opp_id for b in old_boxes)
                                if improved_cost or scored or disrupted:
                                    u_pushes[i] += 1
                                else:
                                    ineff[i] += 1

                        state = nxt_state

                    scores = state.scores(board.goals)
                    if role_assignment == 'var_p1':
                        v_score, o_score = scores[0], scores[1]
                        v_u, v_in = u_pushes[0], ineff[0]
                    else:
                        v_score, o_score = scores[1], scores[0]
                        v_u, v_in = u_pushes[1], ineff[1]

                    new_scores += v_score
                    old_scores += o_score
                    useful_pushes += v_u
                    ineffective_actions += v_in

                    if v_score > o_score:
                        new_wins += 1
                    elif o_score > v_score:
                        old_wins += 1
                    else:
                        ties += 1

        score_diff = new_scores - old_scores
        win_rate = new_wins / matches
        avg_lat = statistics.mean(latencies)
        max_lat = max(latencies)

        row = {
            'variant': name,
            'matches': matches,
            'wins': new_wins,
            'losses': old_wins,
            'ties': ties,
            'win_rate': round(win_rate, 3),
            'variant_score': new_scores,
            'old_score': old_scores,
            'score_diff': score_diff,
            'useful_pushes': useful_pushes,
            'ineffective_actions': ineffective_actions,
            'avg_latency_ms': round(avg_lat, 3),
            'max_latency_ms': round(max_lat, 3),
            'deadline_fallbacks': fallbacks,
        }
        results.append(row)
        print(f"| {name:25} | ScoreDiff: {score_diff:+3d} | W/L/T: {new_wins:2d}/{old_wins:2d}/{ties:2d} | "
              f"Useful: {useful_pushes:3d} | Ineff: {ineffective_actions:3d} | MaxLat: {max_lat:5.2f}ms |")

    with ablation_csv.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"\nWrote ablation results to {ablation_csv}")

if __name__ == '__main__':
    run_ablation()
