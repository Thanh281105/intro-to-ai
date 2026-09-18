import time
from collections import deque
from ..state import DIRECTIONS

def legal_intent(pos, action, board, boxes):
    dr,dc=DIRECTIONS[action]; nxt=(pos[0]+dr,pos[1]+dc)
    if not board.free(nxt): return pos,None
    if nxt in boxes:
        beyond=(nxt[0]+dr,nxt[1]+dc)
        if not board.free(beyond) or beyond in boxes: return pos,None
        return nxt, (nxt, beyond)
    return nxt, None

def route_to_push(pos, boxes, board, goals):
    """Small BFS to reach a useful support square; returns the first safe move."""
    q=deque([(pos,())]); seen={pos}
    while q:
        cur,path=q.popleft()
        if path and len(path)>12: continue
        for action,(dr,dc) in DIRECTIONS.items():
            nxt=(cur[0]+dr,cur[1]+dc)
            if not board.free(nxt) or nxt in boxes: continue
            newpath=path+(action,)
            for b in boxes:
                if (b[0]-dr,b[1]-dc)==nxt and board.free((b[0]+dr,b[1]+dc)) and (b[0]+dr,b[1]+dc) not in boxes:
                    return path[0] if path else action
            if nxt not in seen: seen.add(nxt); q.append((nxt,newpath))
    return None

class Agent:
    name='Agent'
    def choose_action(self,state,board,time_limit_ms=1000): raise NotImplementedError
