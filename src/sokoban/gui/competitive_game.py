try:
    import pygame
except ImportError:
    pygame = None
from .renderer import competitive_scene
from ..competitive.game import CompetitiveGame

class CompetitiveGameGUI:
    def __init__(self, board, game):
        self.board = board
        self.game = game
        self.state = game.state
        self.paused = False
        self.step_delay_ms = 400
        self.last_step_time = 0

    def render(self, surface):
        names = tuple(getattr(a, 'name', f'Agent {i+1}') for i, a in enumerate(self.game.agents))
        last_turn = None
        if hasattr(self.game, 'turn_history') and self.game.turn_history:
            step_idx = self.state.step
            if 0 < step_idx <= len(self.game.turn_history):
                last_turn = self.game.turn_history[step_idx - 1]

        competitive_scene(
            surface,
            self.board,
            self.state,
            self.game.step_limit,
            agent_names=names,
            last_turn=last_turn,
            paused=self.paused,
        )

    def step_forward(self):
        if self.state.step < self.game.step_limit:
            self.state = self.game.step()

    def reset_match(self):
        agent1, agent2 = self.game.agents
        self.game = CompetitiveGame(self.board, agent1, agent2, self.game.step_limit)
        self.state = self.game.state
        self.paused = True

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
                        self.reset_match()

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
