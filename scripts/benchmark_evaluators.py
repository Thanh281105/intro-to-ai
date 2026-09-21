"""Controlled Head-to-Head Benchmark for Sokoban Competitive Evaluator.

Rigorous 4-Way Factorial Experimental Protocol:
1. Search algorithm held strictly fixed:
   - A* NEW vs A* OLD
   - GBFS NEW vs GBFS OLD
2. 4-Way Debiasing per condition:
   - Orientation A (Original Spawns):
     * Match 1: P1(Spawn A)=NEW, P2(Spawn B)=OLD
     * Match 2: P1(Spawn A)=OLD, P2(Spawn B)=NEW
   - Orientation B (Mirrored Spawns):
     * Match 3: P1(Spawn B)=NEW, P2(Spawn A)=OLD
     * Match 4: P1(Spawn B)=OLD, P2(Spawn A)=NEW
   Neutralizes 100% of player-turn index bias AND spawn-location advantage.
3. Partitioned Map Suites:
   - Tuning & Validation: competitive_01 to competitive_05 (5 maps)
   - Final Unseen Test Set: competitive_06 to competitive_15 (10 maps)
   - Secondary Stress Test: single-agent maps (easy_01, medium_01, hard_01, example_map)
4. Comprehensive Metrics:
   - Win / Loss / Tie counts and win rates
   - Total scores and score differences
   - Useful pushes and ineffective actions
   - Average, median, and max latencies
   - 95% Bootstrap Confidence Intervals (1000 resamples)
   - Git commit SHA and execution timestamp metadata
"""

import argparse
import csv
import datetime
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sokoban.map import SokobanMap
from sokoban.competitive.state import CompetitiveState, initial_state, resolve_with_turn
from sokoban.agents import AStarAgent, GBFSAgent
from sokoban.heuristic import ReversePushHeuristic
from sokoban.competitive.evaluator import SAFETY_DEADLINE_MS

root = Path(__file__).resolve().parents[1]
results_dir = root / 'experiments/results'
results_dir.mkdir(parents=True, exist_ok=True)

TUNING_VAL_MAPS = [f'competitive_{i:02d}.txt' for i in range(1, 6)]
UNSEEN_TEST_MAPS = [f'competitive_{i:02d}.txt' for i in range(6, 16)]
SECONDARY_STRESS_MAPS = ['easy_01.txt', 'medium_01.txt', 'hard_01.txt', 'example_map.txt']

HORIZONS = (10, 25, 50)
ALGORITHMS = ('astar', 'gbfs')

def get_commit_sha() -> str:
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).strip()
    except Exception:
        return 'unknown'

def compute_bootstrap_ci(data: list[float], num_samples: int = 1000, alpha: float = 0.05) -> tuple[float, float]:
    if not data:
        return (0.0, 0.0)
    random.seed(42)
    n = len(data)
    means = []
    for _ in range(num_samples):
        resample = [random.choice(data) for _ in range(n)]
        means.append(statistics.mean(resample))
    means.sort()
    low_idx = int((alpha / 2.0) * num_samples)
    high_idx = int((1.0 - alpha / 2.0) * num_samples)
    return round(means[low_idx], 3), round(means[high_idx], 3)

def run_single_match(
    board: SokobanMap,
    map_name: str,
    algo_name: str,
    p1_eval: str,
    p2_eval: str,
    limit: int,
    spawn_mirror: bool = False,
) -> dict:
    from sokoban.competitive.state import get_deterministic_p2
    heur = ReversePushHeuristic(board)
    agent_cls = AStarAgent if algo_name == 'astar' else GBFSAgent

    agent1 = agent_cls(player_id=1, evaluator_type=p1_eval)
    agent2 = agent_cls(player_id=2, evaluator_type=p2_eval)

    p1_orig = board.initial_player
    p2_orig = get_deterministic_p2(board, p1_orig)

    if not spawn_mirror:
        p1_pos, p2_pos = p1_orig, p2_orig
    else:
        p1_pos, p2_pos = p2_orig, p1_orig

    state = CompetitiveState(p1=p1_pos, p2=p2_pos, boxes=board.initial_boxes, owners=(), step=0)

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
            if el_ms >= SAFETY_DEADLINE_MS:
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
    p1_score, p2_score = scores[0], scores[1]

    if p1_eval == 'new':
        new_score, old_score = p1_score, p2_score
        new_idx, old_idx = 0, 1
        role = 'new_as_p1'
    else:
        new_score, old_score = p2_score, p1_score
        new_idx, old_idx = 1, 0
        role = 'new_as_p2'

    if new_score > old_score:
        winner = 'new'
    elif old_score > new_score:
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
        'spawn_mirror': spawn_mirror,
        'p1_score': p1_score,
        'p2_score': p2_score,
        'winner': winner,
        'new_score': new_score,
        'old_score': old_score,
        'score_diff_new_minus_old': new_score - old_score,
        'boxes_on_goals': sum(scores),
        'new_useful_pushes': useful_pushes[new_idx],
        'old_useful_pushes': useful_pushes[old_idx],
        'new_ineffective_actions': ineffective_actions[new_idx],
        'old_ineffective_actions': ineffective_actions[old_idx],
        'new_avg_latency_ms': round(statistics.mean(lat[new_idx]), 3),
        'new_med_latency_ms': round(statistics.median(lat[new_idx]), 3),
        'new_max_latency_ms': round(max(lat[new_idx]), 3),
        'old_avg_latency_ms': round(statistics.mean(lat[old_idx]), 3),
        'old_med_latency_ms': round(statistics.median(lat[old_idx]), 3),
        'old_max_latency_ms': round(max(lat[old_idx]), 3),
        'new_deadline_fallbacks': fallbacks[new_idx],
        'old_deadline_fallbacks': fallbacks[old_idx],
    }

def run_suite(suite_name: str, map_files: list[str], output_csv: Path) -> list[dict]:
    print(f"\n========================================================")
    print(f"Starting {suite_name.upper()} Suite ({len(map_files)} maps x {len(HORIZONS)} horizons x 2 algos x 4 matches = {len(map_files)*len(HORIZONS)*2*4} matches)")
    print(f"========================================================")

    rows = []
    total = len(map_files) * len(HORIZONS) * len(ALGORITHMS) * 4
    idx = 0

    for m_file in map_files:
        board_path = root / 'maps' / m_file
        if not board_path.exists():
            print(f"Skipping non-existent map: {m_file}")
            continue
        board = SokobanMap.from_file(board_path)

        for limit in HORIZONS:
            for algo in ALGORITHMS:
                # 4-Way Factorial Design
                # Orientation A (Original Spawns)
                for p1_e, p2_e in (('new', 'old'), ('old', 'new')):
                    idx += 1
                    res = run_single_match(board, m_file, algo, p1_e, p2_e, limit, spawn_mirror=False)
                    rows.append(res)
                    print(f"[{idx:03d}/{total:03d}] {algo.upper():5} | {m_file:18} n={limit:2d} | "
                          f"Sp=Orig P1={p1_e} P2={p2_e} -> NEW={res['new_score']} OLD={res['old_score']} ({res['winner'].upper():3}) | "
                          f"lat_new={res['new_avg_latency_ms']:5.2f}ms lat_old={res['old_avg_latency_ms']:5.2f}ms")

                # Orientation B (Mirrored Spawns)
                for p1_e, p2_e in (('new', 'old'), ('old', 'new')):
                    idx += 1
                    res = run_single_match(board, m_file, algo, p1_e, p2_e, limit, spawn_mirror=True)
                    rows.append(res)
                    print(f"[{idx:03d}/{total:03d}] {algo.upper():5} | {m_file:18} n={limit:2d} | "
                          f"Sp=Mirr P1={p1_e} P2={p2_e} -> NEW={res['new_score']} OLD={res['old_score']} ({res['winner'].upper():3}) | "
                          f"lat_new={res['new_avg_latency_ms']:5.2f}ms lat_old={res['old_avg_latency_ms']:5.2f}ms")

    if rows:
        with output_csv.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} match rows to {output_csv}")

    return rows

def build_summary(matches: list[dict]) -> list[dict]:
    """Aggregate individual matches by (algorithm, map, step_limit)."""
    groups = {}
    for r in matches:
        k = (r['algorithm'], r['map'], r['step_limit'])
        if k not in groups:
            groups[k] = []
        groups[k].append(r)

    out = []
    for (algo, m, limit), g in groups.items():
        out.append({
            'algorithm': algo,
            'map': m,
            'step_limit': limit,
            'role_swapped_matches': len(g),
            'new_score': sum(r['new_score'] for r in g),
            'old_score': sum(r['old_score'] for r in g),
            'score_diff': sum(r['new_score'] for r in g) - sum(r['old_score'] for r in g),
            'new_wins': sum(1 for r in g if r['winner'] == 'new'),
            'old_wins': sum(1 for r in g if r['winner'] == 'old'),
            'ties': sum(1 for r in g if r['winner'] == 'tie'),
            'new_useful_pushes': sum(r['new_useful_pushes'] for r in g),
            'old_useful_pushes': sum(r['old_useful_pushes'] for r in g),
            'new_ineffective_actions': sum(r['new_ineffective_actions'] for r in g),
            'old_ineffective_actions': sum(r['old_ineffective_actions'] for r in g),
            'new_avg_latency_ms': round(statistics.mean(r['new_avg_latency_ms'] for r in g), 3),
            'old_avg_latency_ms': round(statistics.mean(r['old_avg_latency_ms'] for r in g), 3),
            'new_max_latency_ms': round(max(r['new_max_latency_ms'] for r in g), 3),
            'old_max_latency_ms': round(max(r['old_max_latency_ms'] for r in g), 3),
            'new_fallbacks': sum(r['new_deadline_fallbacks'] for r in g),
            'old_fallbacks': sum(r['old_deadline_fallbacks'] for r in g),
        })
    return out

def generate_summary(all_rows: dict[str, list[dict]], summary_csv: Path):
    commit_sha = get_commit_sha()
    timestamp = datetime.datetime.now().isoformat()

    summary_rows = []
    for split_name, rows in all_rows.items():
        if not rows:
            continue

        for algo in ('astar', 'gbfs', 'ALL'):
            algo_rows = rows if algo == 'ALL' else [r for r in rows if r['algorithm'] == algo]
            if not algo_rows:
                continue

            matches = len(algo_rows)
            new_wins = sum(1 for r in algo_rows if r['winner'] == 'new')
            old_wins = sum(1 for r in algo_rows if r['winner'] == 'old')
            ties = sum(1 for r in algo_rows if r['winner'] == 'tie')
            new_score = sum(r['new_score'] for r in algo_rows)
            old_score = sum(r['old_score'] for r in algo_rows)
            diffs = [r['score_diff_new_minus_old'] for r in algo_rows]
            useful_new = sum(r['new_useful_pushes'] for r in algo_rows)
            useful_old = sum(r['old_useful_pushes'] for r in algo_rows)
            ineff_new = sum(r['new_ineffective_actions'] for r in algo_rows)
            ineff_old = sum(r['old_ineffective_actions'] for r in algo_rows)
            lat_new = [r['new_avg_latency_ms'] for r in algo_rows]
            lat_old = [r['old_avg_latency_ms'] for r in algo_rows]
            max_lat_new = max(r['new_max_latency_ms'] for r in algo_rows)
            max_lat_old = max(r['old_max_latency_ms'] for r in algo_rows)
            fallbacks_new = sum(r['new_deadline_fallbacks'] for r in algo_rows)
            fallbacks_old = sum(r['old_deadline_fallbacks'] for r in algo_rows)

            mean_diff = round(statistics.mean(diffs), 3)
            med_diff = round(statistics.median(diffs), 3)
            std_diff = round(statistics.stdev(diffs), 3) if len(diffs) > 1 else 0.0
            ci_low, ci_high = compute_bootstrap_ci([float(x) for x in diffs])

            summary_rows.append({
                'commit_sha': commit_sha,
                'timestamp': timestamp,
                'split': split_name,
                'algorithm': algo,
                'matches': matches,
                'new_wins': new_wins,
                'old_wins': old_wins,
                'ties': ties,
                'win_rate_new': round(new_wins / matches, 3),
                'new_score': new_score,
                'old_score': old_score,
                'score_diff_total': new_score - old_score,
                'mean_score_diff': mean_diff,
                'median_score_diff': med_diff,
                'std_score_diff': std_diff,
                'ci_95_low': ci_low,
                'ci_95_high': ci_high,
                'useful_pushes_new': useful_new,
                'useful_pushes_old': useful_old,
                'ineffective_new': ineff_new,
                'ineffective_old': ineff_old,
                'avg_latency_new_ms': round(statistics.mean(lat_new), 3),
                'avg_latency_old_ms': round(statistics.mean(lat_old), 3),
                'max_latency_new_ms': round(max_lat_new, 3),
                'max_latency_old_ms': round(max_lat_old, 3),
                'fallbacks_new': fallbacks_new,
                'fallbacks_old': fallbacks_old,
            })

    if summary_rows:
        with summary_csv.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)
        print(f"\nWrote comprehensive summary to {summary_csv}")

def main():
    parser = argparse.ArgumentParser(description="Run controlled head-to-head evaluator benchmark with 4-way debiasing.")
    parser.add_argument('--suite', choices=['all', 'val', 'test', 'stress'], default='all',
                        help="Which suite to benchmark (default: all)")
    args = parser.parse_args()

    suite_results = {}

    if args.suite in ('all', 'val'):
        csv_path = results_dir / 'evaluator_benchmark_val.csv'
        suite_results['tuning_val'] = run_suite('Tuning & Validation', TUNING_VAL_MAPS, csv_path)

    if args.suite in ('all', 'test'):
        csv_path = results_dir / 'evaluator_benchmark_test.csv'
        suite_results['unseen_test'] = run_suite('Final Unseen Test (Holdout)', UNSEEN_TEST_MAPS, csv_path)

    if args.suite in ('all', 'stress'):
        csv_path = results_dir / 'evaluator_benchmark_stress.csv'
        suite_results['secondary_stress'] = run_suite('Secondary Stress Test (Single-Agent Maps)', SECONDARY_STRESS_MAPS, csv_path)

    # Legacy output compatibility
    if 'tuning_val' in suite_results:
        # Write legacy evaluator_head_to_head.csv for older test fixtures
        leg_path = results_dir / 'evaluator_head_to_head.csv'
        with leg_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(suite_results['tuning_val'][0].keys()))
            writer.writeheader()
            writer.writerows(suite_results['tuning_val'])

    summary_csv = results_dir / 'evaluator_benchmark_summary.csv'
    generate_summary(suite_results, summary_csv)
    print("\nBenchmark completed successfully!")

if __name__ == '__main__':
    main()
