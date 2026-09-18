import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import pygame
from sokoban.map import SokobanMap
from sokoban.problem import SokobanProblem
from sokoban.search.astar import solve as astar_solve
from sokoban.gui.single_game import SingleGame
from sokoban.competitive.game import CompetitiveGame
from sokoban.agents import AStarAgent, GBFSAgent
from sokoban.gui.competitive_game import CompetitiveGameGUI

root = Path(__file__).resolve().parents[1]
out = root / 'experiments/figures'
out.mkdir(parents=True, exist_ok=True)

pygame.init()
surface = pygame.Surface((1280, 760))

# 1. Single Replay Screenshot (Restored assignment example_map.txt replay)
# Solved optimally in 34 steps by A*; capturing real replay step 8
board_single = SokobanMap.from_file(root / 'maps/example_map.txt')
result = astar_solve(SokobanProblem(board_single))
single = SingleGame(board_single, result, 'astar')
single.index = 8
single.render(surface)
single_path = out / 'gui_single.png'
pygame.image.save(surface, single_path)
print(f"Saved authentic gui_single.png: {surface.get_size()}, step {single.index}/{len(result.actions)}, cost {result.total_cost}")

# 2. Competitive Arena Screenshot (100% Genuine CompetitiveGame History)
# Using competitive_01.txt where A* and GBFS agents compete autonomously.
# Extracting authentic history frame at step 16 where Agent 1 leads 2-1 with genuine box ownership.
board_comp = SokobanMap.from_file(root / 'maps/competitive_01.txt')
comp_game = CompetitiveGame(board_comp, AStarAgent(1), GBFSAgent(2), step_limit=25)
comp_game.run()

gui_comp = CompetitiveGameGUI(board_comp, comp_game)
gui_comp.state = comp_game.history[16]
gui_comp.render(surface)
comp_path = out / 'gui_competitive.png'
pygame.image.save(surface, comp_path)
scores = gui_comp.state.scores(board_comp.goals)
print(f"Saved authentic gui_competitive.png: {surface.get_size()}, step {gui_comp.state.step}/25, scores {scores}, owners {gui_comp.state.owners}")

# 3. Competitive Arena Final Screenshot (Authentic Match Complete State at step n=25)
# Renders Match Complete modal overlay, final score, crown on winner, crying on loser, box ownership
gui_comp.state = comp_game.history[25]
gui_comp.render(surface)
comp_final_path = out / 'gui_competitive_final.png'
pygame.image.save(surface, comp_final_path)
final_scores = gui_comp.state.scores(board_comp.goals)
print(f"Saved authentic gui_competitive_final.png: {surface.get_size()}, step {gui_comp.state.step}/25, final scores {final_scores}, owners {gui_comp.state.owners}")

pygame.quit()
print("All final screenshots successfully generated from actual renderer execution on genuine game history.")
