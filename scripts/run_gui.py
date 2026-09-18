import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from sokoban.map import SokobanMap
from sokoban.problem import SokobanProblem
from sokoban.search.ucs import solve as ucs
from sokoban.search.astar import solve as astar
from sokoban.gui.single_game import SingleGame
p=argparse.ArgumentParser(); p.add_argument('--map',default='maps/easy_01.txt'); p.add_argument('--algorithm',choices=['ucs','astar'],default='astar'); a=p.parse_args(); b=SokobanMap.from_file(a.map); r=(ucs if a.algorithm=='ucs' else astar)(SokobanProblem(b)); SingleGame(b,r,a.algorithm).run()
