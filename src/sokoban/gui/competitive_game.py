try:
    import pygame
except ImportError:
    pygame = None
from .renderer import competitive_scene

class CompetitiveGameGUI:
    def __init__(self, board, game):
        self.board = board
        self.game = game
        self.state = game.state
        self.paused = False
        self.step_delay_ms = 350
        self.last_step_time = 0

    def render(self, surface):
        names = tuple(getattr(a, 'name', f'Agent {i+1}') for i, a in enumerate(self.game.agents))
        competitive_scene(surface, self.board, self.state, self.game.step_limit, agent_names=names)

    def step_forward(self):
        if self.state.step < self.game.step_limit:
            from ..competitive.state import resolve
            actions = [agent.choose_action(self.state, self.board, 1000) for agent in self.game.agents]
            self.state = resolve(self.state, actions[0], actions[1], self.board)
            if hasattr(self.game, 'history') and self.state not in self.game.history:
                self.game.history.append(self.state)

    def run(self):
        if pygame is None:
            raise RuntimeError('pygame is required for GUI')
        pygame.init()
        screen = pygame.display.set_mode((1280, 760))
        pygame.display.set_caption('Sokoban Duel - Multi-Agent Arena')
        clock = pygame.time.Clock()
        running = True
        
        while running:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key in (pygame.K_RIGHT, pygame.K_l):
                        self.step_forward()
                    elif event.key == pygame.K_r:
                        from ..competitive.state import initial_state
                        self.state = initial_state(self.board)
                        self.paused = True
            
            # Step match automatically when unpaused
            if not self.paused and self.state.step < self.game.step_limit:
                if now - self.last_step_time >= self.step_delay_ms:
                    self.step_forward()
                    self.last_step_time = now
                    if self.state.step >= self.game.step_limit:
                        self.paused = True

            self.render(screen)
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()
