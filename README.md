# Sokoban AI Project: Single-Agent Search & Competitive Multi-Agent Arena

An end-to-end, release-candidate implementation of classical heuristic search (Uniform Cost Search and A* Search) and a simultaneous two-player competitive arena for the Sokoban puzzle.

---

## 1. Available Maps

The project includes five verified map configurations:
- `maps/easy_01.txt`: Minimal 1-box baseline puzzle (optimal cost: 3).
- `maps/medium_01.txt`: 2-box corridor puzzle (optimal cost: 7).
- `maps/hard_01.txt`: Multi-box bottleneck puzzle (optimal cost: 10).
- `maps/example_map.txt`: **Authoritative assignment benchmark map** restored character-by-character from PDF Page 2 (8x9 grid, 7 boxes, 7 targets; optimal cost: 34).
- `maps/competitive_01.txt`: Balanced 11x9 two-player competitive arena with symmetrical start positions and contested target zones.

### Recommended Demonstrations:
- **Single-Agent GUI Replay**: `maps/example_map.txt` with `astar`.
- **Competitive Multi-Agent GUI**: `maps/competitive_01.txt` with `25` steps.

---

## 2. Complete Run-Mode Commands (Modes A – P)

Below are copy-pasteable execution instructions formatted separately for **Windows PowerShell** and **macOS / Linux (Bash/Zsh)**.

### A. Environment Setup

#### Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH="src"
```

#### macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
```

---

### B. Run All Unit & Integration Tests

Executes the complete test suite (32 tests covering void isolation, push semantics, A* equivalence, non-geometric heuristics, conflict resolution, deadlines, GUI state machine, and turn telemetry):

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
pytest -v
```

#### macOS / Linux:
```bash
PYTHONPATH=src pytest -v
```

---

### C. Single Solver CLI with UCS

Runs Uniform Cost Search on the authoritative assignment map:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/solve.py --map maps/example_map.txt --algorithm ucs
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/solve.py --map maps/example_map.txt --algorithm ucs
```

---

### D. Single Solver CLI with A*

Runs A* search with reverse-push matching heuristic:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/solve.py --map maps/example_map.txt --algorithm astar
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/solve.py --map maps/example_map.txt --algorithm astar
```

---

### E. Single-Agent GUI with UCS

Visualizes UCS solution playback on the desktop:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/run_gui.py --map maps/example_map.txt --algorithm ucs
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/run_gui.py --map maps/example_map.txt --algorithm ucs
```

---

### F. Single-Agent GUI with A* (Recommended Demo)

Visualizes A* search solution playback with real-time telemetry:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/run_gui.py --map maps/example_map.txt --algorithm astar
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/run_gui.py --map maps/example_map.txt --algorithm astar
```

**Single-Agent GUI Controls**:
- `SPACE`: Play / Pause auto-replay playback.
- `RIGHT ARROW` / `L`: Step 1 action forward.
- `LEFT ARROW` / `H`: Step 1 action backward.
- `R`: Reset replay to initial state.
- `ESC`: Exit application.

---

### G. Competitive CLI

Runs headless simulation between Agent 1 (A*) and Agent 2 (GBFS) and prints final scores and winner:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/run_competitive.py --map maps/competitive_01.txt --steps 25
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/run_competitive.py --map maps/competitive_01.txt --steps 25
```

---

### H. Competitive GUI (Recommended Demo)

Launches the multi-agent arena GUI featuring live box ownership, real LAST TURN telemetry (latencies, actions, resolver outcomes), and a match complete modal:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/run_competitive_gui.py --map maps/competitive_01.txt --steps 25
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/run_competitive_gui.py --map maps/competitive_01.txt --steps 25
```

**Competitive GUI Controls**:
- `SPACE`: Play / Pause live simulation.
- `RIGHT ARROW` / `L`: Advance 1 turn.
- `R`: Reset match to start.
- `ESC`: Exit application.

---

### I. Choose Game Horizon ($n$)

You can customize the game horizon $n$ via the `--steps` flag:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
# 10-step blitz
python scripts/run_competitive.py --map maps/competitive_01.txt --steps 10

# 50-step endurance match in GUI
python scripts/run_competitive_gui.py --map maps/competitive_01.txt --steps 50
```

#### macOS / Linux:
```bash
# 10-step blitz
PYTHONPATH=src python3 scripts/run_competitive.py --map maps/competitive_01.txt --steps 10

# 50-step endurance match in GUI
PYTHONPATH=src python3 scripts/run_competitive_gui.py --map maps/competitive_01.txt --steps 50
```

---

### J. Benchmark UCS vs A*

Runs the rigorous two-phase benchmark (timing with `tracemalloc` OFF across 5 measured runs; memory with `tracemalloc` ON separately):

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/benchmark.py
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/benchmark.py
```
*Outputs: `experiments/results/benchmark.csv` and `experiments/results/benchmark_summary.csv`.*

---

### K. Heuristic Validation

Empirically validates admissibility ($h \le h^*$) and consistency/monotonicity ($h(s) \le 1 + h(s')$) across reachable states:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/validate_heuristic.py
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/validate_heuristic.py
```
*Outputs: `experiments/results/heuristic_validation.csv`.*

---

### L. Competitive-Agent Benchmark

Evaluates decision latencies and scores across all maps for horizons $n \in \{10, 25, 50\}$, verifying the $<1000$ ms deadline:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/benchmark_agents.py
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/benchmark_agents.py
```
*Outputs: `experiments/results/agent_benchmark.csv`.*

---

### M. Regenerate Figures

Regenerates grayscale-friendly presentation charts from `benchmark_summary.csv`:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/generate_figures.py
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/generate_figures.py
```
*Outputs:*
- `experiments/figures/expanded_nodes_by_map.png`
- `experiments/figures/runtime_by_map.png`
- `experiments/figures/max_frontier_by_map.png`

---

### N. Regenerate GUI Screenshots

Generates authentic offscreen screenshots directly from real gameplay histories:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/render_screenshots.py
```

#### macOS / Linux:
```bash
SDL_VIDEODRIVER=dummy PYTHONPATH=src python3 scripts/render_screenshots.py
```
*Outputs:*
- `experiments/figures/gui_single.png`: Replay state showing telemetry and "IN PROGRESS".
- `experiments/figures/gui_competitive.png`: Active match (step 16/25, real LAST TURN telemetry, no crown/cry emotes).
- `experiments/figures/gui_competitive_final.png`: Match complete state (step 25/25, match complete overlay, crown on winner, crying on loser).

---

### O. Final Verification

Runs end-to-end verification proving both UCS and A* solve all benchmark maps, produce identical optimal costs, and generate strictly legal replayable plans:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/final_verify.py
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/final_verify.py
```

---

### P. Submission Packaging

Generates a zip archive conforming to the assignment directory standard:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/package_submission.py --group-id "GROUP01" --student-id "22127001" --presentation "presentation.pdf" --demo-url "https://youtu.be/example"
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/package_submission.py --group-id "GROUP01" --student-id "22127001" --presentation "presentation.pdf" --demo-url "https://youtu.be/example"
```

---

## 3. Documentation Index

- [docs/requirements_matrix.md](file:///c:/Users/Admin/Desktop/AI/sokoban-midterm-second-pass/sokoban-midterm/docs/requirements_matrix.md): Traceability matrix matching all assignment specifications.
- [docs/experiment_methodology.md](file:///c:/Users/Admin/Desktop/AI/sokoban-midterm-second-pass/sokoban-midterm/docs/experiment_methodology.md): Rigorous two-phase benchmarking protocol.
- [docs/experiment_results.md](file:///c:/Users/Admin/Desktop/AI/sokoban-midterm-second-pass/sokoban-midterm/docs/experiment_results.md): Empirical data tables, metrics, and speedup analysis.
- [docs/final_audit.md](file:///c:/Users/Admin/Desktop/AI/sokoban-midterm-second-pass/sokoban-midterm/docs/final_audit.md): Complete release-candidate audit report (all milestones PASS).
- [docs/heuristic_analysis.md](file:///c:/Users/Admin/Desktop/AI/sokoban-midterm-second-pass/sokoban-midterm/docs/heuristic_analysis.md): Formal admissibility and consistency proofs and competitive static BFS.
- [docs/optimization_report.md](file:///c:/Users/Admin/Desktop/AI/sokoban-midterm-second-pass/sokoban-midterm/docs/optimization_report.md): Search engineering details and memory optimization.
- [docs/presentation_outline.md](file:///c:/Users/Admin/Desktop/AI/sokoban-midterm-second-pass/sokoban-midterm/docs/presentation_outline.md): 8-slide oral presentation blueprint.
