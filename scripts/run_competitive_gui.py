import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from sokoban.map import SokobanMap
from sokoban.competitive.game import CompetitiveGame
from sokoban.agents import AStarAgent,GBFSAgent
from sokoban.gui.competitive_game import CompetitiveGameGUI
p=argparse.ArgumentParser(); p.add_argument('--map',default='maps/medium_01.txt'); p.add_argument('--steps',type=int,default=25); a=p.parse_args(); b=SokobanMap.from_file(a.map); CompetitiveGameGUI(b,CompetitiveGame(b,AStarAgent(),GBFSAgent(),a.steps)).run()
