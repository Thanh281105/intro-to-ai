import csv,sys
from pathlib import Path
from collections import deque
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from sokoban.map import SokobanMap
from sokoban.problem import SokobanProblem
from sokoban.search.ucs import solve
root=Path(__file__).resolve().parents[1]; rows=[]
validation_maps = [root/'maps'/name for name in ('easy_01.txt','medium_01.txt','hard_01.txt')]
for mp in validation_maps:
 p=SokobanProblem(SokobanMap.from_file(mp)); seen={p.initial_state}; q=deque([p.initial_state]); states=[]
 while q and len(states)<30:
  s=q.popleft(); states.append(s)
  for _,n in p.get_successors(s):
   if n not in seen: seen.add(n); q.append(n)
 adm=cons=0; maxv=0; edges=0
 for s in states:
  h=p.heuristic(s); sub=SokobanProblem(p.board); sub.initial_state=s; opt=solve(sub); true=opt.total_cost
  if true is not None and h>true: adm+=1; maxv=max(maxv,h-true)
  for _,n in p.get_successors(s): edges+=1; cons+=int(h>1+p.heuristic(n)); maxv=max(maxv,h-(1+p.heuristic(n)))
 rows.append({'map':mp.name,'states_tested':len(states),'admissibility_violations':adm,'consistency_edges':edges,'consistency_violations':cons,'maximum_violation':maxv})
out=root/'experiments/results/heuristic_validation.csv'; out.parent.mkdir(exist_ok=True,parents=True)
with out.open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
print('wrote',out)
