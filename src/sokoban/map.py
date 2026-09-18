from dataclasses import dataclass
from pathlib import Path

Pos = tuple[int, int]

@dataclass(frozen=True)
class SokobanMap:
    width: int
    height: int
    walls: frozenset[Pos]
    goals: frozenset[Pos]
    initial_player: Pos
    initial_boxes: frozenset[Pos]
    valid_cells: frozenset[Pos] = frozenset()
    floor_cells: frozenset[Pos] = frozenset()
    initial_player2: Pos | None = None

    def __post_init__(self):
        if not self.valid_cells:
            object.__setattr__(self, 'valid_cells', frozenset((r, c) for r in range(self.height) for c in range(self.width)))
        if not self.floor_cells:
            object.__setattr__(self, 'floor_cells', frozenset(self.valid_cells - self.walls))

    @classmethod
    def from_text(cls, text: str) -> "SokobanMap":
        lines = text.splitlines()
        if not lines:
            raise ValueError("empty map")
        width = max(len(line) for line in lines)
        walls = set()
        goals = set()
        boxes = set()
        valid = set()
        floor = set()
        player = None
        player2 = None
        for r, line in enumerate(lines):
            for c, ch in enumerate(line):
                p = (r, c)
                valid.add(p)
                if ch == '%':
                    walls.add(p)
                elif ch in 'D.':
                    goals.add(p)
                    floor.add(p)
                elif ch == 'B':
                    boxes.add(p)
                    floor.add(p)
                elif ch == 'C':
                    boxes.add(p)
                    goals.add(p)
                    floor.add(p)
                elif ch == 'A':
                    player = p
                    floor.add(p)
                elif ch in '2Ea':
                    player2 = p
                    floor.add(p)
                elif ch == ' ':
                    floor.add(p)
                else:
                    raise ValueError(f"unknown map symbol {ch!r}")
        if player is None:
            raise ValueError("map needs A")
        if len(boxes) != len(goals):
            raise ValueError("boxes and goals must match")
        return cls(
            width=width,
            height=len(lines),
            walls=frozenset(walls),
            goals=frozenset(goals),
            initial_player=player,
            initial_boxes=frozenset(boxes),
            valid_cells=frozenset(valid),
            floor_cells=frozenset(floor),
            initial_player2=player2,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "SokobanMap":
        return cls.from_text(Path(path).read_text(encoding="utf-8"))

    def inside(self, p: Pos) -> bool:
        return p in self.valid_cells

    def free(self, p: Pos) -> bool:
        return p in self.floor_cells

