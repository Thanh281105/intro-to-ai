import csv
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sokoban.map import SokobanMap
from sokoban.competitive.state import initial_state, resolve_with_turn
from sokoban.competitive.evaluator import CompetitiveEvaluator, CompetitiveWeights
from sokoban.agents import AStarAgent, GBFSAgent

root = Path(__file__).resolve().parents[1]
out = root / 'experiments/results'
out.mkdir(parents=True, exist_ok=True)
tuning_csv = out / 'reward_weight_tuning.csv'

# Tuning maps (holdout maps: hard_01.txt, example_map.txt)
tuning_maps = [root / 'maps' / name for name in ('easy_01.txt', 'medium_01.txt', 'competitive_01.txt')]
step_limits = (10, 25)

def evaluate_configuration(weights: CompetitiveWeights):
    matches = 0
    wins = {'agent_1': 0, 'agent_2': 0, 'tie': 0}
    score_diffs = []
    completed_boxes_list = []
    useful_pushes_list = []
    wasted_moves_list = []
    latencies = []
    fallbacks = 0

    for mp in tuning_maps:
        board = SokobanMap.from_file(mp)
        heur = CompetitiveEvaluator.get(board).heuristic

        for limit in step_limits:
            matches += 1
            agent1 = AStarAgent(player_id=1, weights=weights)
            agent2 = GBFSAgent(player_id=2, weights=weights)
            state = initial_state(board)
            match_lats = [[], []]
            u_pushes = [0, 0]
            w_moves = [0, 0]

            for _ in range(limit):
                actions = []
                for i, agent in enumerate((agent1, agent2)):
                    t0 = time.perf_counter_ns()
                    act = agent.choose_action(state, board, time_limit_ms=1000, step_limit=limit)
                    el_ms = (time.perf_counter_ns() - t0) / 1e6
                    match_lats[i].append(el_ms)
                    latencies.append(el_ms)
                    if el_ms >= 950:
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
                        w_moves[i] += 1
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
                            w_moves[i] += 1

                state = nxt_state

            scores = state.scores(board.goals)
            if scores[0] > scores[1]:
                wins['agent_1'] += 1
            elif scores[1] > scores[0]:
                wins['agent_2'] += 1
            else:
                wins['tie'] += 1

            score_diffs.append(scores[0] - scores[1])
            completed_boxes_list.append(scores[0] + scores[1])
            useful_pushes_list.append(sum(u_pushes))
            wasted_moves_list.append(sum(w_moves))

    return {
        'matches': matches,
        'win_a1': wins['agent_1'],
        'win_a2': wins['agent_2'],
        'ties': wins['tie'],
        'avg_score_diff': round(statistics.mean(score_diffs), 3),
        'total_completed_boxes': sum(completed_boxes_list),
        'avg_useful_pushes': round(statistics.mean(useful_pushes_list), 3),
        'avg_wasted_moves': round(statistics.mean(wasted_moves_list), 3),
        'avg_latency_ms': round(statistics.mean(latencies), 3),
        'max_latency_ms': round(max(latencies), 3),
        'deadline_fallbacks': fallbacks,
    }

print("Starting Staged Empirical Weight Tuning...")
trials = []

# Stage 1: Search SCORE x PUSH (fix ROUTE=1.0, STEP=-1.0)
stage1_configs = [
    (30.0, 3.0), (30.0, 5.0), (30.0, 8.0),
    (50.0, 3.0), (50.0, 5.0), (50.0, 8.0),
    (80.0, 3.0), (80.0, 5.0), (80.0, 8.0),
]

trial_idx = 1
best_s1 = None
best_s1_score = -float('inf')

for w_s, w_p in stage1_configs:
    w = CompetitiveWeights(w_score=w_s, w_push=w_p, w_route=1.0, step_penalty=-1.0)
    res = evaluate_configuration(w)
    row = {
        'trial': trial_idx,
        'stage': 'Stage 1 (Score x Push)',
        'w_score': w_s,
        'w_push': w_p,
        'w_route': 1.0,
        'step_penalty': -1.0,
        **res
    }
    trials.append(row)
    print(f"[Trial {trial_idx:02d} | Stage 1] W_SCORE={w_s:4.1f}, W_PUSH={w_p:4.1f} | "
          f"A1_win={res['win_a1']}, A2_win={res['win_a2']}, Ties={res['ties']}, "
          f"Completed={res['total_completed_boxes']}, UsefulPushes={res['avg_useful_pushes']}, Wasted={res['avg_wasted_moves']}, MaxLat={res['max_latency_ms']}ms")

    # Composite quality metric: completed boxes, useful pushes, low wasted moves, safe latency
    quality = res['total_completed_boxes'] * 10 + res['avg_useful_pushes'] * 5 - res['avg_wasted_moves']
    if quality > best_s1_score and res['max_latency_ms'] < 950:
        best_s1_score = quality
        best_s1 = (w_s, w_p)
    trial_idx += 1

print(f"\nBest Stage 1 Candidate: W_SCORE={best_s1[0]}, W_PUSH={best_s1[1]}\n")

# Stage 2: Search ROUTE around best candidate
best_w_s, best_w_p = best_s1
stage2_routes = [0.5, 1.0, 2.0]
best_s2_route = 1.0
best_s2_score = -float('inf')

for r_val in stage2_routes:
    if r_val == 1.0:
        continue # Already measured in Stage 1
    w = CompetitiveWeights(w_score=best_w_s, w_push=best_w_p, w_route=r_val, step_penalty=-1.0)
    res = evaluate_configuration(w)
    row = {
        'trial': trial_idx,
        'stage': 'Stage 2 (Route)',
        'w_score': best_w_s,
        'w_push': best_w_p,
        'w_route': r_val,
        'step_penalty': -1.0,
        **res
    }
    trials.append(row)
    print(f"[Trial {trial_idx:02d} | Stage 2] W_SCORE={best_w_s:4.1f}, W_PUSH={best_w_p:4.1f}, W_ROUTE={r_val:4.1f} | "
          f"A1_win={res['win_a1']}, Completed={res['total_completed_boxes']}, Useful={res['avg_useful_pushes']}, Wasted={res['avg_wasted_moves']}, MaxLat={res['max_latency_ms']}ms")
    trial_idx += 1

# Stage 3: Test STEP_PENALTY (-0.5 vs -1.0)
for step_pen in (-0.5,):
    w = CompetitiveWeights(w_score=best_w_s, w_push=best_w_p, w_route=1.0, step_penalty=step_pen)
    res = evaluate_configuration(w)
    row = {
        'trial': trial_idx,
        'stage': 'Stage 3 (Step Penalty)',
        'w_score': best_w_s,
        'w_push': best_w_p,
        'w_route': 1.0,
        'step_penalty': step_pen,
        **res
    }
    trials.append(row)
    print(f"[Trial {trial_idx:02d} | Stage 3] STEP_PENALTY={step_pen:4.1f} | "
          f"A1_win={res['win_a1']}, Completed={res['total_completed_boxes']}, Useful={res['avg_useful_pushes']}, Wasted={res['avg_wasted_moves']}, MaxLat={res['max_latency_ms']}ms")
    trial_idx += 1

with tuning_csv.open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=list(trials[0].keys()))
    writer.writeheader()
    writer.writerows(trials)

print(f"\nSuccessfully wrote {len(trials)} tuning trials to {tuning_csv}")
