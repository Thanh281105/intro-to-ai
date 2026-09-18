#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from sokoban.map import SokobanMap
from sokoban.problem import SokobanProblem
from sokoban.search.ucs import solve as ucs
from sokoban.search.astar import solve as astar

p=argparse.ArgumentParser(); p.add_argument('--map',required=True); p.add_argument('--algorithm',choices=['ucs','astar'],default='astar'); a=p.parse_args()
result=(ucs if a.algorithm=='ucs' else astar)(SokobanProblem(SokobanMap.from_file(a.map)))
print('Actions:', result.actions); print('Total cost:', result.total_cost); print('Search statistics:'); print(json.dumps(result.as_dict(),default=str,indent=2))
