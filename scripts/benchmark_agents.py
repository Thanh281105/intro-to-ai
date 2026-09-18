import csv
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sokoban.map import SokobanMap
from sokoban.competitive.state import initial_state, resolve
from sokoban.agents import AStarAgent, GBFSAgent

root = Path(__file__).resolve().parents[1]
out = root / 'experiments/results'
out.mkdir(parents=True, exist_ok=True)

rows = []
maps = sorted((root / 'maps').glob('*.txt'))

print("Starting competitive agents benchmark (n=10, 25, 50)...")

for mp in maps:
    board = SokobanMap.from_file(mp)
    for limit in (10, 25, 50):
        agent1 = AStarAgent(player_id=1)
        agent2 = GBFSAgent(player_id=2)
        state = initial_state(board)
        lat = [[], []]
        fallbacks = [0, 0]

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

            state = resolve(state, actions[0], actions[1], board)

        scores = state.scores(board.goals)
        winner = 'tie' if scores[0] == scores[1] else ('agent_1' if scores[0] > scores[1] else 'agent_2')

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
        }
        rows.append(row)
        print(f"[{mp.name} | n={limit}] P1(A*)={scores[0]} vs P2(GBFS)={scores[1]} ({winner}) | "
              f"P1_avg={row['agent_1_avg_latency_ms']}ms, P2_avg={row['agent_2_avg_latency_ms']}ms, "
              f"P1_max={row['agent_1_max_latency_ms']}ms, P2_max={row['agent_2_max_latency_ms']}ms")

csv_path = out / 'agent_benchmark.csv'
with csv_path.open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(f"Successfully wrote {len(rows)} competitive rows to {csv_path}")
