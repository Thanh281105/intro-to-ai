import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from sokoban.map import SokobanMap
from sokoban.competitive.game import CompetitiveGame
from sokoban.agents import AStarAgent,GBFSAgent
from sokoban.gui.competitive_game import CompetitiveGameGUI
parser = argparse.ArgumentParser(description="Run Competitive Sokoban GUI Arena")
parser.add_argument('--map', default='maps/competitive_01.txt', help="Map file path")
parser.add_argument('--steps', type=int, default=25, help="Step horizon n")
parser.add_argument('--evaluator', choices=['new', 'old'], default='new', help="Evaluator type: 'new' (RL-inspired Phi) or 'old' (single-agent reverse-push baseline)")
parser.add_argument('--show-evaluation', action='store_true', help="Show small developer evaluation line in GUI")
args = parser.parse_args()

b = SokobanMap.from_file(args.map)
a1 = AStarAgent(player_id=1, evaluator_type=args.evaluator)
a2 = GBFSAgent(player_id=2, evaluator_type=args.evaluator)
game = CompetitiveGame(b, a1, a2, args.steps)
gui = CompetitiveGameGUI(b, game, show_evaluation=args.show_evaluation)
gui.run()

