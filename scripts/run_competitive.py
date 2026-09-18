import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from sokoban.map import SokobanMap
from sokoban.competitive.game import CompetitiveGame
from sokoban.agents import AStarAgent,GBFSAgent
p=argparse.ArgumentParser(); p.add_argument('--map',default='maps/medium_01.txt'); p.add_argument('--steps',type=int,default=20); a=p.parse_args(); b=SokobanMap.from_file(a.map); g=CompetitiveGame(b,AStarAgent(),GBFSAgent(),a.steps); s=g.run(); print('scores',s.scores(b.goals),'winner', 'tie' if s.scores(b.goals)[0]==s.scores(b.goals)[1] else 'agent_1' if s.scores(b.goals)[0]>s.scores(b.goals)[1] else 'agent_2')
