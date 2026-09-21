import time
from .state import initial_state, resolve_with_turn, TurnRecord

class CompetitiveGame:
    def __init__(self, board, agent1, agent2, step_limit=20):
        self.board = board
        self.agents = (agent1, agent2)
        self.step_limit = step_limit
        self.state = initial_state(board)
        self.history = [self.state]
        self.turn_history: list[TurnRecord] = []

    def step(self):
        """Execute one simultaneous turn with precise performance timing."""
        if self.state.step >= self.step_limit:
            return self.state

        t0 = time.perf_counter_ns()
        try:
            a1 = self.agents[0].choose_action(self.state, self.board, 1000, step_limit=self.step_limit)
        except TypeError:
            a1 = self.agents[0].choose_action(self.state, self.board, 1000)
        lat1 = (time.perf_counter_ns() - t0) / 1e6

        t0 = time.perf_counter_ns()
        try:
            a2 = self.agents[1].choose_action(self.state, self.board, 1000, step_limit=self.step_limit)
        except TypeError:
            a2 = self.agents[1].choose_action(self.state, self.board, 1000)
        lat2 = (time.perf_counter_ns() - t0) / 1e6

        self.state, turn_rec = resolve_with_turn(self.state, a1, a2, self.board, lat1, lat2)
        self.history.append(self.state)
        self.turn_history.append(turn_rec)
        return self.state

    def run(self):
        while self.state.step < self.step_limit:
            self.step()
        return self.state
