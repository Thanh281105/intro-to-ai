try:
    import pygame
except ImportError:
    pygame = None
from .renderer import single_scene

class SingleGame:
    def __init__(self, board, result, algorithm):
        self.board = board
        self.result = result
        self.algorithm = algorithm
        self.index = 0
        self.paused = True
        self.last_step_time = 0
        self.step_delay_ms = 350  # Controlled 350ms auto-replay interval

    @property
    def max_steps(self) -> int:
        return len(self.result.actions) if (self.result and self.result.actions) else 0

    @property
    def status(self) -> str:
        if not self.result or not getattr(self.result, 'solved', False):
            return "UNSOLVABLE"
        if self.index >= self.max_steps and self.max_steps > 0:
            return "FINISHED"
        if self.paused:
            return "PAUSED" if self.index > 0 else "READY"
        return "PLAYING"

    def tick(self, now_ms: int) -> bool:
        """Advance solution index when unpaused. Returns True if index advanced."""
        if not self.paused and self.result and getattr(self.result, 'solved', False) and self.index < self.max_steps:
            if now_ms - self.last_step_time >= self.step_delay_ms:
                self.index += 1
                self.last_step_time = now_ms
                if self.index >= self.max_steps:
                    self.paused = True
                return True
        return False

    def handle_key(self, key: str):
        if key == 'space':
            if self.result and getattr(self.result, 'solved', False):
                if self.index >= self.max_steps and self.max_steps > 0:
                    self.index = 0
                    self.paused = False
                else:
                    self.paused = not self.paused
        elif key == 'right':
            self.paused = True
            if self.index < self.max_steps:
                self.index += 1
        elif key == 'left':
            self.paused = True
            if self.index > 0:
                self.index -= 1
        elif key == 'r':
            self.index = 0
            self.paused = True

    def render(self, surface):
        single_scene(
            surface,
            self.board,
            self.result,
            self.algorithm,
            self.index,
            paused=self.paused,
            status_override=self.status,
        )

    def run(self):
        if pygame is None:
            raise RuntimeError('pygame is required for GUI')
        pygame.init()
        screen = pygame.display.set_mode((1280, 760))
        pygame.display.set_caption('Sokoban AI Lab - Search Visualization')
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
                        self.handle_key('space')
                    elif event.key in (pygame.K_RIGHT, pygame.K_l):
                        self.handle_key('right')
                    elif event.key in (pygame.K_LEFT, pygame.K_h):
                        self.handle_key('left')
                    elif event.key == pygame.K_r:
                        self.handle_key('r')

            self.tick(now)
            self.render(screen)
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()
