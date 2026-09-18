from .state import initial_state,resolve
class CompetitiveGame:
    def __init__(self,board,agent1,agent2,step_limit=20): self.board=board; self.agents=(agent1,agent2); self.step_limit=step_limit; self.state=initial_state(board); self.history=[self.state]
    def run(self):
        while self.state.step<self.step_limit:
            actions=[a.choose_action(self.state,self.board,1000) for a in self.agents]
            self.state=resolve(self.state,actions[0],actions[1],self.board); self.history.append(self.state)
        return self.state
