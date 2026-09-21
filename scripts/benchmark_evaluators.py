import argparse
import csv
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sokoban.map import SokobanMap
from sokoban.competitive.state import initial_state, resolve_with_turn
from sokoban.agents import AStarAgent, GBFSAgent
from sokoban.heuristic import ReversePushHeuristic

root = Path(__file__).resolve().parents[1]
results_dir = root / 'experiments/results'
results_dir.mkdir(parents=True, exist_ok=True)

PRIMARY_MAPS = [
    'competitive_01.txt',
    'competitive_02.txt',
    'competitive_03.txt',
    'competitive_04.txt',
]

ROBUSTNESS_MAPS = [
    'easy_01.txt',
    'medium_01.txt',
    'hard_01.txt',
    'example_map.txt',
]

HORIZONS = (10, 25, 50)
ALGORITHMS = ('astar', 'gbfs')

def run_single_match(board: SokobanMap, map_name: str, algo_name: str, p1_eval: str, p2_eval: str, limit: int) -> dict:
    heur = ReversePushHeuristic(board)
    agent_cls = AStarAgent if algo_name == 'astar' else GBFSAgent

    agent1 = agent_cls(player_id=1, evaluator_type=p1_eval)
    agent2 = agent_cls(player_id=2, evaluator_type=p2_eval)
    state = initial_state(board)

    lat = [[], []]
    fallbacks = [0, 0]
    useful_pushes = [0, 0]
    ineffective_actions = [0, 0]

    for _ in range(limit):
        actions = []
        for i, agent in enumerate((agent1, agent2)):
            t0 = time.perf_counter_ns()
            act = agent.choose_action(state, board, time_limit_ms=1000, step_limit=limit)
            el_ms = (time.perf_counter_ns() - t0) / 1e6
            lat[i].append(el_ms)
            if el_ms >= 950:
                fallbacks[i] += 1
            actions.append(act)

        old_boxes = state.boxes
        old_cost = heur.for_boxes(old_boxes)
        old_owners = state.owner_map()

        nxt_state, turn_rec = resolve_with_turn(
            state, actions[0], actions[1], board, lat[0][-1], lat[1][-1]
        )

        for i, (outc, act) in enumerate(((turn_rec.a1_outcome, turn_rec.a1_action),
                                         (turn_rec.a2_outcome, turn_rec.a2_action))):
            if outc in ("BLOCKED", "CONFLICT"):
                ineffective_actions[i] += 1
            elif outc == "PUSH":
                new_cost = heur.for_boxes(nxt_state.boxes)
                aid = i + 1
                opp_id = 2 if aid == 1 else 1
                new_owners = nxt_state.owner_map()
                improved_cost = (new_cost < old_cost and new_cost != float('inf'))
                scored = any(b in board.goals and new_owners.get(b) == aid for b in nxt_state.boxes - old_boxes)
                disrupted = any(b in board.goals and old_owners.get(b) == opp_id and new_owners.get(b) != opp_id for b in old_boxes)
                if improved_cost or scored or disrupted:
                    useful_pushes[i] += 1
                else:
                    ineffective_actions[i] += 1

        state = nxt_state

    scores = state.scores(board.goals)
    p1_score, p2_score = scores
    boxes_on_goals = sum(1 for b in state.boxes if b in board.goals)

    if p1_eval == 'new':
        role = 'new_as_p1'
        new_score = p1_score
        old_score = p2_score
        new_useful = useful_pushes[0]
        old_useful = useful_pushes[1]
        new_ineff = ineffective_actions[0]
        old_ineff = ineffective_actions[1]
        new_lat = lat[0]
        old_lat = lat[1]
        new_fb = fallbacks[0]
        old_fb = fallbacks[1]
    else:
        role = 'new_as_p2'
        new_score = p2_score
        old_score = p1_score
        new_useful = useful_pushes[1]
        old_useful = useful_pushes[0]
        new_ineff = ineffective_actions[1]
        old_ineff = ineffective_actions[0]
        new_lat = lat[1]
        old_lat = lat[0]
        new_fb = fallbacks[1]
        old_fb = fallbacks[0]

    score_diff = new_score - old_score
    if score_diff > 0:
        winner = 'new'
    elif score_diff < 0:
        winner = 'old'
    else:
        winner = 'tie'

    return {
        'map': map_name,
        'step_limit': limit,
        'algorithm': algo_name,
        'p1_evaluator': p1_eval,
        'p2_evaluator': p2_eval,
        'role_assignment': role,
        'p1_score': p1_score,
        'p2_score': p2_score,
        'winner': winner,
        'new_score': new_score,
        'old_score': old_score,
        'score_diff_new_minus_old': score_diff,
        'boxes_on_goals': boxes_on_goals,
        'new_useful_pushes': new_useful,
        'old_useful_pushes': old_useful,
        'new_ineffective_actions': new_ineff,
        'old_ineffective_actions': old_ineff,
        'new_avg_latency_ms': round(statistics.mean(new_lat), 3),
        'new_med_latency_ms': round(statistics.median(new_lat), 3),
        'new_max_latency_ms': round(max(new_lat), 3),
        'old_avg_latency_ms': round(statistics.mean(old_lat), 3),
        'old_med_latency_ms': round(statistics.median(old_lat), 3),
        'old_max_latency_ms': round(max(old_lat), 3),
        'new_deadline_fallbacks': new_fb,
        'old_deadline_fallbacks': old_fb,
    }

def run_experiment(map_names: list[str], label: str = "primary") -> list[dict]:
    matches = []
    total_runs = len(ALGORITHMS) * len(map_names) * len(HORIZONS) * 2
    idx = 0
    print(f"\n========================================================")
    print(f"Starting {label.upper()} Head-to-Head Evaluator Benchmark ({total_runs} matches)")
    print(f"========================================================")

    for algo in ALGORITHMS:
        for mname in map_names:
            mpath = root / 'maps' / mname
            board = SokobanMap.from_file(mpath)
            for horizon in HORIZONS:
                # Match A: P1=NEW, P2=OLD
                idx += 1
                mA = run_single_match(board, mname, algo, 'new', 'old', horizon)
                matches.append(mA)
                print(f"[{idx:02d}/{total_runs}] {algo.upper():>5s} | {mname:<18s} n={horizon:2d} | Match A (P1=NEW, P2=OLD) -> NEW={mA['new_score']} OLD={mA['old_score']} ({mA['winner'].upper():<4s}) | lat_new={mA['new_avg_latency_ms']:.2f}ms lat_old={mA['old_avg_latency_ms']:.2f}ms")

                # Match B: Role Swap (P1=OLD, P2=NEW)
                idx += 1
                mB = run_single_match(board, mname, algo, 'old', 'new', horizon)
                matches.append(mB)
                print(f"[{idx:02d}/{total_runs}] {algo.upper():>5s} | {mname:<18s} n={horizon:2d} | Match B (P1=OLD, P2=NEW) -> NEW={mB['new_score']} OLD={mB['old_score']} ({mB['winner'].upper():<4s}) | lat_new={mB['new_avg_latency_ms']:.2f}ms lat_old={mB['old_avg_latency_ms']:.2f}ms")

    return matches

def build_summary(matches: list[dict]) -> list[dict]:
    summary_rows = []
    # Group by (algorithm, map, step_limit)
    groups = {}
    for m in matches:
        key = (m['algorithm'], m['map'], m['step_limit'])
        groups.setdefault(key, []).append(m)

    for (algo, mname, horizon), pair in groups.items():
        new_score = sum(m['new_score'] for m in pair)
        old_score = sum(m['old_score'] for m in pair)
        score_diff = new_score - old_score

        new_wins = sum(1 for m in pair if m['winner'] == 'new')
        old_wins = sum(1 for m in pair if m['winner'] == 'old')
        ties = sum(1 for m in pair if m['winner'] == 'tie')

        new_useful = sum(m['new_useful_pushes'] for m in pair)
        old_useful = sum(m['old_useful_pushes'] for m in pair)
        new_ineff = sum(m['new_ineffective_actions'] for m in pair)
        old_ineff = sum(m['old_ineffective_actions'] for m in pair)

        new_avg_lats = [m['new_avg_latency_ms'] for m in pair]
        old_avg_lats = [m['old_avg_latency_ms'] for m in pair]
        new_max_lats = [m['new_max_latency_ms'] for m in pair]
        old_max_lats = [m['old_max_latency_ms'] for m in pair]

        summary_rows.append({
            'algorithm': algo,
            'map': mname,
            'step_limit': horizon,
            'role_swapped_matches': len(pair),
            'new_score': new_score,
            'old_score': old_score,
            'score_diff': score_diff,
            'new_wins': new_wins,
            'old_wins': old_wins,
            'ties': ties,
            'new_useful_pushes': new_useful,
            'old_useful_pushes': old_useful,
            'new_ineffective_actions': new_ineff,
            'old_ineffective_actions': old_ineff,
            'new_avg_latency_ms': round(statistics.mean(new_avg_lats), 3),
            'old_avg_latency_ms': round(statistics.mean(old_avg_lats), 3),
            'new_max_latency_ms': round(max(new_max_lats), 3),
            'old_max_latency_ms': round(max(old_max_lats), 3),
            'new_fallbacks': sum(m['new_deadline_fallbacks'] for m in pair),
            'old_fallbacks': sum(m['old_deadline_fallbacks'] for m in pair),
        })

    # Add Algorithm Subtotals
    for algo in ALGORITHMS:
        algo_matches = [m for m in matches if m['algorithm'] == algo]
        if not algo_matches:
            continue
        new_score = sum(m['new_score'] for m in algo_matches)
        old_score = sum(m['old_score'] for m in algo_matches)
        score_diff = new_score - old_score

        new_wins = sum(1 for m in algo_matches if m['winner'] == 'new')
        old_wins = sum(1 for m in algo_matches if m['winner'] == 'old')
        ties = sum(1 for m in algo_matches if m['winner'] == 'tie')

        new_useful = sum(m['new_useful_pushes'] for m in algo_matches)
        old_useful = sum(m['old_useful_pushes'] for m in algo_matches)
        new_ineff = sum(m['new_ineffective_actions'] for m in algo_matches)
        old_ineff = sum(m['old_ineffective_actions'] for m in algo_matches)

        new_avg_lats = [m['new_avg_latency_ms'] for m in algo_matches]
        old_avg_lats = [m['old_avg_latency_ms'] for m in algo_matches]
        new_max_lats = [m['new_max_latency_ms'] for m in algo_matches]
        old_max_lats = [m['old_max_latency_ms'] for m in algo_matches]

        summary_rows.append({
            'algorithm': f"{algo.upper()}_TOTAL",
            'map': 'ALL_PRIMARY',
            'step_limit': 'ALL',
            'role_swapped_matches': len(algo_matches),
            'new_score': new_score,
            'old_score': old_score,
            'score_diff': score_diff,
            'new_wins': new_wins,
            'old_wins': old_wins,
            'ties': ties,
            'new_useful_pushes': new_useful,
            'old_useful_pushes': old_useful,
            'new_ineffective_actions': new_ineff,
            'old_ineffective_actions': old_ineff,
            'new_avg_latency_ms': round(statistics.mean(new_avg_lats), 3),
            'old_avg_latency_ms': round(statistics.mean(old_avg_lats), 3),
            'new_max_latency_ms': round(max(new_max_lats), 3),
            'old_max_latency_ms': round(max(old_max_lats), 3),
            'new_fallbacks': sum(m['new_deadline_fallbacks'] for m in algo_matches),
            'old_fallbacks': sum(m['old_deadline_fallbacks'] for m in algo_matches),
        })

    # Overall Total
    new_score = sum(m['new_score'] for m in matches)
    old_score = sum(m['old_score'] for m in matches)
    summary_rows.append({
        'algorithm': "OVERALL_TOTAL",
        'map': 'ALL_PRIMARY',
        'step_limit': 'ALL',
        'role_swapped_matches': len(matches),
        'new_score': new_score,
        'old_score': old_score,
        'score_diff': new_score - old_score,
        'new_wins': sum(1 for m in matches if m['winner'] == 'new'),
        'old_wins': sum(1 for m in matches if m['winner'] == 'old'),
        'ties': sum(1 for m in matches if m['winner'] == 'tie'),
        'new_useful_pushes': sum(m['new_useful_pushes'] for m in matches),
        'old_useful_pushes': sum(m['old_useful_pushes'] for m in matches),
        'new_ineffective_actions': sum(m['new_ineffective_actions'] for m in matches),
        'old_ineffective_actions': sum(m['old_ineffective_actions'] for m in matches),
        'new_avg_latency_ms': round(statistics.mean([m['new_avg_latency_ms'] for m in matches]), 3),
        'old_avg_latency_ms': round(statistics.mean([m['old_avg_latency_ms'] for m in matches]), 3),
        'new_max_latency_ms': round(max([m['new_max_latency_ms'] for m in matches]), 3),
        'old_max_latency_ms': round(max([m['old_max_latency_ms'] for m in matches]), 3),
        'new_fallbacks': sum(m['new_deadline_fallbacks'] for m in matches),
        'old_fallbacks': sum(m['old_deadline_fallbacks'] for m in matches),
    })

    return summary_rows

def write_csv(path: Path, data: list[dict]):
    if not data:
        return
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)
    print(f"Wrote {len(data)} rows to {path}")

def main():
    parser = argparse.ArgumentParser(description="Head-to-Head Evaluator Benchmark (holding search fixed)")
    parser.add_argument('--include-robustness', action='store_true', help="Also run secondary robustness matches on single-agent maps")
    args = parser.parse_args()

    primary_matches = run_experiment(PRIMARY_MAPS, label="primary")
    primary_csv = results_dir / 'evaluator_head_to_head.csv'
    write_csv(primary_csv, primary_matches)

    summary_rows = build_summary(primary_matches)
    summary_csv = results_dir / 'evaluator_head_to_head_summary.csv'
    write_csv(summary_csv, summary_rows)

    if args.include_robustness:
        robustness_matches = run_experiment(ROBUSTNESS_MAPS, label="robustness")
        robustness_csv = results_dir / 'evaluator_head_to_head_robustness.csv'
        write_csv(robustness_csv, robustness_matches)

    print("\nBenchmark completed successfully!")

if __name__ == '__main__':
    main()
