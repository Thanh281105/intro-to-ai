import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sokoban.map import SokobanMap
from sokoban.competitive.game import CompetitiveGame
from sokoban.agents import AStarAgent, GBFSAgent

parser = argparse.ArgumentParser(description="Run Competitive Sokoban Match")
parser.add_argument('--map', default='maps/competitive_01.txt', help="Map file path")
parser.add_argument('--steps', type=int, default=25, help="Step horizon n")
parser.add_argument('--evaluator', choices=['new', 'old'], default='new', help="Evaluator type: 'new' (RL-inspired Phi) or 'old' (single-agent reverse-push baseline)")
parser.add_argument('--show-evaluation', action='store_true', help="Show step-by-step evaluation breakdown")
args = parser.parse_args()

board = SokobanMap.from_file(args.map)
a1 = AStarAgent(player_id=1, evaluator_type=args.evaluator)
a2 = GBFSAgent(player_id=2, evaluator_type=args.evaluator)
game = CompetitiveGame(board, a1, a2, args.steps)

print(f"=== Competitive Sokoban Match: {args.map} (Horizon n={args.steps}, Evaluator={args.evaluator}) ===")
if args.show_evaluation:
    print(f"{'Step':>4} | {'A1 Act':>7} {'Outcome':>8} {'Lat(ms)':>7} {'Phi':>7} {'ScoreDiff':>9} {'PushCost':>8} {'SuppDist':>8} | {'A2 Act':>7} {'Outcome':>8} {'Lat(ms)':>7} {'Phi':>7}")
    print("-" * 90)

while game.state.step < game.step_limit:
    game.step()
    turn = game.turn_history[-1]
    if args.show_evaluation:
        e1 = a1.last_evaluation or {}
        e2 = a2.last_evaluation or {}
        print(f"{turn.step:4d} | {turn.a1_action:>7} {turn.a1_outcome:>8} {turn.a1_latency_ms:7.2f} {e1.get('phi', 0.0):+7.1f} {e1.get('score_diff', 0):+9d} {e1.get('push_cost', 0.0):8.1f} {e1.get('support_dist', 0.0):8.1f} | "
              f"{turn.a2_action:>7} {turn.a2_outcome:>8} {turn.a2_latency_ms:7.2f} {e2.get('phi', 0.0):+7.1f}")

scores = game.state.scores(board.goals)
winner = 'tie' if scores[0] == scores[1] else ('agent_1' if scores[0] > scores[1] else 'agent_2')
print("-" * 90 if args.show_evaluation else "")
print(f"Final Scores: Agent 1 (A*)={scores[0]} | Agent 2 (GBFS)={scores[1]} -> Winner: {winner.upper()}")
