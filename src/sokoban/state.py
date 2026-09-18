from dataclasses import dataclass
from .map import Pos, SokobanMap

DIRECTIONS = {"North":(-1,0), "East":(0,1), "South":(1,0), "West":(0,-1)}

@dataclass(frozen=True)
class State:
    player: Pos
    boxes: frozenset[Pos]

    def successors(self, board: SokobanMap):
        for action, (dr, dc) in DIRECTIONS.items():
            nxt=(self.player[0]+dr,self.player[1]+dc)
            if not board.free(nxt): continue
            boxes=set(self.boxes)
            if nxt in boxes:
                beyond=(nxt[0]+dr,nxt[1]+dc)
                if not board.free(beyond) or beyond in boxes: continue
                boxes.remove(nxt); boxes.add(beyond); yield action, State(nxt,frozenset(boxes))
            else:
                yield action, State(nxt,self.boxes)
