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

parser = argparse.ArgumentParser(description="Competitive Agents Benchmark")
parser.add_argument('--output', default='agent_benchmark.csv', help="Output CSV filename or path")
args = parser.parse_args()

root = Path(__file__).resolve().parents[1]
out = root / 'experiments/results'
out.mkdir(parents=True, exist_ok=True)
csv_path = Path(args.output) if Path(args.output).is_absolute() else out / args.output

rows = []
maps = sorted((root / 'maps').glob('*.txt'))

print(f"Starting competitive agents benchmark (n=10, 25, 50) -> {csv_path.name}...")

for mp in maps:
    board = SokobanMap.from_file(mp)
    heur = ReversePushHeuristic(board)
    for limit in (10, 25, 50):
        agent1 = AStarAgent(player_id=1)
        agent2 = GBFSAgent(player_id=2)
        state = initial_state(board)
        lat = [[], []]
        fallbacks = [0, 0]
        useful_pushes = [0, 0]
        wasted_moves = [0, 0]

        for _ in range(limit):
            actions = []
            for i, agent in enumerate((agent1, agent2)):
                start = time.perf_counter_ns()
                action = agent.choose_action(state, board, time_limit_ms=1000)
                elapsed_ms = (time.perf_counter_ns() - start) / 1e6
                lat[i].append(elapsed_ms)
                if elapsed_ms >= 950:
                    fallbacks[i] += 1
                actions.append(action)

            old_boxes = state.boxes
            old_cost = heur.for_boxes(old_boxes)
            old_owners = state.owner_map()

            nxt_state, turn_rec = resolve_with_turn(
                state, actions[0], actions[1], board, lat[0][-1], lat[1][-1]
            )

            # Analyze actions for useful pushes vs wasted moves
            for i, (outc, act) in enumerate(((turn_rec.a1_outcome, turn_rec.a1_action),
                                             (turn_rec.a2_outcome, turn_rec.a2_action))):
                if outc in ("BLOCKED", "CONFLICT"):
                    wasted_moves[i] += 1
                elif outc == "PUSH":
                    # Check if push improved reverse-push matching or achieved goal or removed opponent goal
                    new_cost = heur.for_boxes(nxt_state.boxes)
                    agent_id = i + 1
                    opp_id = 2 if agent_id == 1 else 1
                    new_owners = nxt_state.owner_map()
                    # Useful if: cost decreased, or completed own goal, or stripped opponent goal
                    improved_cost = (new_cost < old_cost and new_cost != float('inf'))
                    scored = any(b in board.goals and new_owners.get(b) == agent_id for b in nxt_state.boxes - old_boxes)
                    disrupted = any(b in board.goals and old_owners.get(b) == opp_id and new_owners.get(b) != opp_id for b in old_boxes)
                    if improved_cost or scored or disrupted:
                        useful_pushes[i] += 1
                    else:
                        wasted_moves[i] += 1

            state = nxt_state

        scores = state.scores(board.goals)
        winner = 'tie' if scores[0] == scores[1] else ('agent_1' if scores[0] > scores[1] else 'agent_2')
        total_boxes_completed = sum(1 for b in state.boxes if b in board.goals)

        row = {
            'map': mp.name,
            'step_limit': limit,
            'agent_1_score': scores[0],
            'agent_2_score': scores[1],
            'winner': winner,
            'agent_1_avg_latency_ms': round(statistics.mean(lat[0]), 3),
            'agent_1_med_latency_ms': round(statistics.median(lat[0]), 3),
            'agent_1_max_latency_ms': round(max(lat[0]), 3),
            'agent_2_avg_latency_ms': round(statistics.mean(lat[1]), 3),
            'agent_2_med_latency_ms': round(statistics.median(lat[1]), 3),
            'agent_2_max_latency_ms': round(max(lat[1]), 3),
            'agent_1_deadline_fallbacks': fallbacks[0],
            'agent_2_deadline_fallbacks': fallbacks[1],
            'boxes_completed': total_boxes_completed,
            'agent_1_useful_pushes': useful_pushes[0],
            'agent_2_useful_pushes': useful_pushes[1],
            'agent_1_wasted_moves': wasted_moves[0],
            'agent_2_wasted_moves': wasted_moves[1],
        }
        rows.append(row)
        print(f"[{mp.name} | n={limit}] P1(A*)={scores[0]} vs P2(GBFS)={scores[1]} ({winner}) | "
              f"completed={total_boxes_completed}, useful=({useful_pushes[0]},{useful_pushes[1]}), "
              f"wasted=({wasted_moves[0]},{wasted_moves[1]}) | P1_avg={row['agent_1_avg_latency_ms']}ms, P2_avg={row['agent_2_avg_latency_ms']}ms")

with csv_path.open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(f"Successfully wrote {len(rows)} competitive rows to {csv_path}")

