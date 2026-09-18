from .map import SokobanMap
from .state import State
from .heuristic import ReversePushHeuristic

class SokobanProblem:
    def __init__(self, board: SokobanMap):
        self.board=board
        self.initial_state=State(board.initial_player, board.initial_boxes)
        self.heuristic_model=ReversePushHeuristic(board)
    def get_successors(self, state): return state.successors(self.board)
    def is_goal(self, state): return state.boxes == self.board.goals
    def step_cost(self, *_): return 1
    def heuristic(self, state): return self.heuristic_model(state)
