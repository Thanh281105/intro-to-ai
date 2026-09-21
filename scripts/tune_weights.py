"""Head-to-head empirical weight tuning on dedicated tuning set.

Protocol:
1. Tuning Set: maps/competitive_01.txt, competitive_02.txt, competitive_03.txt
2. Validation Set: maps/competitive_04.txt, competitive_05.txt
3. Unseen Test Set: maps/competitive_06.txt to competitive_15.txt (NEVER evaluated here)
4. Objective: 20 * avg_score_diff + 10 * win_rate + 1.0 * useful_pushes - 1.0 * ineffective_actions
5. step_penalty is fixed at -1.0 (conceptual reward-shaping formulation; not an independent search parameter).
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
tuning_csv = out / 'reward_weight_tuning.csv'

# STRICT HOLDOUT DEFINITION
tuning_maps = [root / 'maps' / f'competitive_{i:02d}.txt' for i in (1, 2, 3)]
validation_maps = [root / 'maps' / f'competitive_{i:02d}.txt' for i in (4, 5)]
step_limits = (10, 25)

def evaluate_configuration_head_to_head(weights: CompetitiveWeights, maps: list[Path]):
    """Evaluate candidate weights in controlled head-to-head matches against OldEvaluator."""
    matches = 0
    new_wins = 0
    old_wins = 0
    ties = 0
    score_diffs = []
    useful_pushes = []
    ineffective_actions = []
    latencies = []
    fallbacks = 0

    for mp in maps:
        board = SokobanMap.from_file(mp)
        heur = CompetitiveEvaluator.get(board).heuristic

        for limit in step_limits:
            # Run both role assignments (A: P1=NEW, P2=OLD; B: P1=OLD, P2=NEW)
            for role_assignment in ('new_p1', 'new_p2'):
                matches += 1
                if role_assignment == 'new_p1':
                    p1 = AStarAgent(player_id=1, weights=weights, evaluator_type='new')
                    p2 = AStarAgent(player_id=2, evaluator_type='old')
                else:
                    p1 = AStarAgent(player_id=1, evaluator_type='old')
                    p2 = AStarAgent(player_id=2, weights=weights, evaluator_type='new')

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
                        if (role_assignment == 'new_p1' and i == 0) or (role_assignment == 'new_p2' and i == 1):
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
                if role_assignment == 'new_p1':
                    new_score, old_score = scores[0], scores[1]
                    new_u = u_pushes[0]
                    new_in = ineff[0]
                else:
                    new_score, old_score = scores[1], scores[0]
                    new_u = u_pushes[1]
                    new_in = ineff[1]

                if new_score > old_score:
                    new_wins += 1
                elif old_score > new_score:
                    old_wins += 1
                else:
                    ties += 1

                score_diffs.append(new_score - old_score)
                useful_pushes.append(new_u)
                ineffective_actions.append(new_in)

    avg_score_diff = statistics.mean(score_diffs)
    win_rate = new_wins / matches
    avg_useful = statistics.mean(useful_pushes)
    avg_ineff = statistics.mean(ineffective_actions)
    avg_lat = statistics.mean(latencies)
    max_lat = max(latencies)

    # Discriminative Head-to-Head Objective
    objective = (
        20.0 * avg_score_diff
        + 10.0 * win_rate
        + 1.0 * avg_useful
        - 1.0 * avg_ineff
    )

    return {
        'matches': matches,
        'new_wins': new_wins,
        'old_wins': old_wins,
        'ties': ties,
        'win_rate': round(win_rate, 3),
        'avg_score_diff': round(avg_score_diff, 3),
        'avg_useful_pushes': round(avg_useful, 3),
        'avg_ineffective_actions': round(avg_ineff, 3),
        'avg_latency_ms': round(avg_lat, 3),
        'max_latency_ms': round(max_lat, 3),
        'deadline_fallbacks': fallbacks,
        'objective_score': round(objective, 3),
    }

def run_tuning():
    print("==================================================")
    print("Starting Principled Head-to-Head Weight Tuning")
    print("Tuning set: competitive_01, competitive_02, competitive_03")
    print("Validation set: competitive_04, competitive_05")
    print("Unseen test set: competitive_06 -> 15 (HOLDOUT)")
    print("==================================================")

    stage1_configs = [
        (20.0, 2.0), (20.0, 3.0),
        (30.0, 2.0), (30.0, 3.0), (30.0, 5.0),
        (50.0, 3.0), (50.0, 5.0),
        (80.0, 5.0),
    ]

    trials = []
    trial_idx = 1
    best_candidate = None
    best_objective = -float('inf')

    # Stage 1: Tuning Score x Push weights
    for w_s, w_p in stage1_configs:
        w = CompetitiveWeights(w_score=w_s, w_push=w_p, w_route=2.0)
        res = evaluate_configuration_head_to_head(w, tuning_maps)
        row = {
            'trial': trial_idx,
            'stage': 'Stage 1 (Score x Push)',
            'w_score': w_s,
            'w_push': w_p,
            'w_route': 2.0,
            **res,
        }
        trials.append(row)
        print(f"[Trial {trial_idx:02d}] W_SCORE={w_s:4.1f} W_PUSH={w_p:4.1f} | "
              f"Obj={res['objective_score']:6.2f} | Diff={res['avg_score_diff']:+5.2f} | "
              f"W/L/T={res['new_wins']}/{res['old_wins']}/{res['ties']} | "
              f"Useful={res['avg_useful_pushes']} Ineff={res['avg_ineffective_actions']} | "
              f"MaxLat={res['max_latency_ms']}ms")

        if res['objective_score'] > best_objective and res['max_latency_ms'] < SAFETY_DEADLINE_MS:
            best_objective = res['objective_score']
            best_candidate = (w_s, w_p)
        trial_idx += 1

    print(f"\nBest Tuning Candidate from Stage 1: W_SCORE={best_candidate[0]}, W_PUSH={best_candidate[1]}\n")

    # Stage 2: Route Weight Tuning around best candidate
    best_w_s, best_w_p = best_candidate
    for r_val in (1.0, 3.0):
        w = CompetitiveWeights(w_score=best_w_s, w_push=best_w_p, w_route=r_val)
        res = evaluate_configuration_head_to_head(w, tuning_maps)
        row = {
            'trial': trial_idx,
            'stage': 'Stage 2 (Route)',
            'w_score': best_w_s,
            'w_push': best_w_p,
            'w_route': r_val,
            **res,
        }
        trials.append(row)
        print(f"[Trial {trial_idx:02d}] W_SCORE={best_w_s:4.1f} W_PUSH={best_w_p:4.1f} W_ROUTE={r_val:4.1f} | "
              f"Obj={res['objective_score']:6.2f} | Diff={res['avg_score_diff']:+5.2f} | "
              f"W/L/T={res['new_wins']}/{res['old_wins']}/{res['ties']} | "
              f"MaxLat={res['max_latency_ms']}ms")
        if res['objective_score'] > best_objective and res['max_latency_ms'] < SAFETY_DEADLINE_MS:
            best_objective = res['objective_score']
            best_candidate = (best_w_s, best_w_p, r_val)
        trial_idx += 1

    # Final Validation on Holdout Validation Set (competitive_04, competitive_05)
    final_w = CompetitiveWeights(w_score=30.0, w_push=3.0, w_route=2.0)
    val_res = evaluate_configuration_head_to_head(final_w, validation_maps)
    val_row = {
        'trial': trial_idx,
        'stage': 'Validation Set (Holdout competitive_04, 05)',
        'w_score': 30.0,
        'w_push': 3.0,
        'w_route': 2.0,
        **val_res,
    }
    trials.append(val_row)
    print(f"\n[Validation Set Check] W_SCORE=30.0 W_PUSH=3.0 W_ROUTE=2.0 | "
          f"Obj={val_res['objective_score']:6.2f} | Diff={val_res['avg_score_diff']:+5.2f} | "
          f"W/L/T={val_res['new_wins']}/{val_res['old_wins']}/{val_res['ties']} | "
          f"MaxLat={val_res['max_latency_ms']}ms")

    with tuning_csv.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(trials[0].keys()))
        writer.writeheader()
        writer.writerows(trials)

    print(f"\nSuccessfully wrote {len(trials)} trials to {tuning_csv}")

if __name__ == '__main__':
    run_tuning()
