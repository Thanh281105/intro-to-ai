# intro-to-ai: Sokoban AI Project

Python standard library implements the solver; optional `pygame`, `matplotlib`, and `pytest` versions are pinned in `requirements.txt`. The code avoids platform-specific solver dependencies and targets the assignment's macOS Ventura requirement.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src pytest
PYTHONPATH=src python scripts/solve.py --map maps/example_map.txt --algorithm astar
PYTHONPATH=src python scripts/benchmark.py
PYTHONPATH=src python scripts/validate_heuristic.py
PYTHONPATH=src python scripts/benchmark_agents.py
SDL_VIDEODRIVER=dummy PYTHONPATH=src python scripts/render_screenshots.py
PYTHONPATH=src python scripts/final_verify.py
PYTHONPATH=src python scripts/run_competitive.py --map maps/competitive_01.txt --steps 25
PYTHONPATH=src python scripts/run_gui.py --map maps/example_map.txt --algorithm astar
PYTHONPATH=src python scripts/run_competitive_gui.py --map maps/competitive_01.txt --steps 25
```

GUI controls: `Space` toggles auto-replay playback, `Right Arrow` steps forward, `Left Arrow` steps backward, and `R` resets the puzzle.
Packaging: `python scripts/package_submission.py --group-id GROUP --student-id ID --presentation presentation.pdf --demo-url URL`.

See `docs/requirements_matrix.md`, `docs/architecture.md`, `docs/experiment_results.md`, and `docs/final_audit.md` for comprehensive documentation and evidence mapping.
