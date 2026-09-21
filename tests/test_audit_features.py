import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import pygame
from sokoban.map import SokobanMap
from sokoban.problem import SokobanProblem
from sokoban.search.astar import solve
from sokoban.search.common import SearchResult
from sokoban.gui.single_game import SingleGame
from sokoban.competitive.game import CompetitiveGame
from sokoban.agents import AStarAgent, GBFSAgent
from sokoban.gui.competitive_game import CompetitiveGameGUI

def test_gui_playback_state_machine_and_ticks():
    root = Path(__file__).resolve().parents[1]
    b = SokobanMap.from_file(root / 'maps/easy_01.txt')
    r = solve(SokobanProblem(b))
    assert r.solved is True
    game = SingleGame(b, r, 'astar')

    # Initial state
    assert game.index == 0
    assert game.paused is True
    assert game.status == "READY"

    # Space unpauses -> PLAYING
    game.handle_key('space')
    assert game.paused is False
    assert game.status == "PLAYING"

    # Tick before step_delay_ms elapsed does not advance
    advanced = game.tick(now_ms=100)
    assert advanced is False
    assert game.index == 0

    # Tick after step_delay_ms advances index
    advanced = game.tick(now_ms=400)
    assert advanced is True
    assert game.index == 1

    # Step forward key
    game.handle_key('right')
    assert game.paused is True
    assert game.index == 2
    assert game.status == "PAUSED"

    # Step backward key
    game.handle_key('left')
    assert game.paused is True
    assert game.index == 1

    # Reset key
    game.handle_key('r')
    assert game.index == 0
    assert game.paused is True
    assert game.status == "READY"

    # Advance to end
    game.index = game.max_steps
    assert game.status == "FINISHED"

def test_unsolvable_game_status_and_rendering():
    pygame.init()
    root = Path(__file__).resolve().parents[1]
    b = SokobanMap.from_file(root / 'maps/easy_01.txt')
    unsolved_res = SearchResult(False, [], None, 50, 100, 10, 5.0, [])
    game = SingleGame(b, unsolved_res, 'astar')
    assert game.status == "UNSOLVABLE"

    surf = pygame.Surface((1280, 760))
    # Must render gracefully with initial player and boxes on board, without crashing
    game.render(surf)
    assert surf.get_size() == (1280, 760)
    pygame.quit()
    from sokoban.gui.renderer import clear_caches
    clear_caches()

def test_offscreen_competitive_renderer_with_real_history():
    from sokoban.gui.renderer import clear_caches
    clear_caches()
    pygame.init()
    root = Path(__file__).resolve().parents[1]
    b = SokobanMap.from_file(root / 'maps/competitive_01.txt')
    comp_game = CompetitiveGame(b, AStarAgent(1), GBFSAgent(2), step_limit=15)
    comp_game.run()

    assert len(comp_game.history) == 16
    gui_comp = CompetitiveGameGUI(b, comp_game)
    # Render from a real history state
    gui_comp.state = comp_game.history[10]
    surf = pygame.Surface((1280, 760))
    gui_comp.render(surf)
    assert surf.get_size() == (1280, 760)
    pygame.quit()
    clear_caches()

