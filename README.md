# Sokoban AI Project: Single-Agent Search & Competitive Multi-Agent Arena

An end-to-end, release-candidate implementation of classical heuristic search (Uniform Cost Search and A* Search) and a simultaneous two-player competitive arena for the Sokoban puzzle.

---

## 1. Available Maps
 
### Single-Agent Benchmark Maps:
- `maps/easy_01.txt`: Minimal 1-box baseline puzzle (optimal cost: 3).
- `maps/medium_01.txt`: 2-box corridor puzzle (optimal cost: 7).
- `maps/hard_01.txt`: Multi-box bottleneck puzzle (optimal cost: 10).
- `maps/example_map.txt`: **Authoritative assignment benchmark map** restored character-by-character from PDF Page 2 (8x9 grid, 7 boxes, 7 targets; optimal cost: 34).

### Competitive Multi-Agent Maps (15 Symmetrical Arenas):
- **Tuning Set**:
  - `maps/competitive_01.txt`: Symmetrical 4-goal dual arena (mirror symmetry).
  - `maps/competitive_02.txt`: Central contested box arena featuring dynamic point disruption & theft (`Situation 1 & 2`).
  - `maps/competitive_03.txt`: Asymmetric tactical arena featuring decisive A* victory ($2 - 0$).
- **Holdout Validation Set**:
  - `maps/competitive_04.txt`: Counter-attack arena featuring decisive GBFS victory ($2 - 1$).
  - `maps/competitive_05.txt`: Dual chamber with central obstacle wall and 4 contested goals.
- **Unseen Final Test Set (Holdout)**:
  - `maps/competitive_06.txt` to `maps/competitive_15.txt`: 10 diverse unseen competitive topologies (crossroads, diamond, twin corridors, fortress, labyrinths, sprint fields). Weights were *never* adjusted on these maps.

### Recommended Demonstrations:
- **Single-Agent GUI Replay**: `maps/example_map.txt` with `astar`.
- **Competitive Multi-Agent GUI**: `maps/competitive_01.txt` with `25` steps.

---

## 2. Complete Run-Mode Commands (Modes A – T)


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

Executes the complete test suite (81 tests covering void isolation, push semantics, A* equivalence, non-geometric heuristics, conflict resolution, deadlines, GUI state machine, turn telemetry, RL reward shaping, competitive evaluation situations, and controlled head-to-head evaluator benchmarks):

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

### G. Competitive CLI with RL-Inspired Value Evaluation

Runs headless simulation between Agent 1 (A*) and Agent 2 (GBFS) using the RL-inspired state potential function $\Phi_i(s)$ and prints final scores and winner:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/run_competitive.py --map maps/competitive_01.txt --steps 25
```

#### Inspect Live Value-Function Breakdown (`--show-evaluation`):
```powershell
$env:PYTHONPATH="src"
python scripts/run_competitive.py --map maps/competitive_01.txt --steps 25 --show-evaluation
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/run_competitive.py --map maps/competitive_01.txt --steps 25 --show-evaluation
```

See [docs/competitive_evaluation.md](docs/competitive_evaluation.md) for full mathematical formulation, reward shaping interpretation, and empirical before/after analysis.

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
- Optional flag `--show-evaluation`: Displays small developer evaluation line (`Evaluation: +54.0`).

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

### J. Compare New RL-Inspired vs Old Baseline Evaluator

Both the new RL-inspired potential evaluator and the old single-agent reverse-push baseline are fully preserved and selectable via `--evaluator {new,old}`:

```powershell
# Run with NEW RL-inspired evaluator (default):
python scripts/run_competitive_gui.py --map maps/competitive_02.txt --steps 25 --evaluator new

# Run with OLD baseline evaluator for direct side-by-side comparison:
python scripts/run_competitive_gui.py --map maps/competitive_02.txt --steps 25 --evaluator old
```

**Available Competitive Maps**:
- `maps/competitive_01.txt`: Symmetric 4-goal dual arena (mirror symmetry).
- `maps/competitive_02.txt`: Central contested box arena featuring dynamic point disruption & theft (`Situation 1 & 2`).
- `maps/competitive_03.txt`: Asymmetric tactical arena featuring decisive A* victory ($2 - 0$).
- `maps/competitive_04.txt`: Counter-attack arena featuring decisive GBFS victory ($2 - 1$).

---

### K. Benchmark UCS vs A*

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

### L. Heuristic Validation

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

### M. Competitive-Agent Benchmark

Evaluates decision latencies and scores across all 8 maps for horizons $n \in \{10, 25, 50\}$, verifying the $<1000$ ms deadline:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
# Benchmark new evaluator:
python scripts/benchmark_agents.py

# Benchmark old baseline evaluator:
python scripts/benchmark_agents.py --evaluator old --output agent_benchmark_before.csv

# Comparative run generating both before and after CSVs cleanly:
python scripts/benchmark_agents.py --compare-evaluators
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/benchmark_agents.py --compare-evaluators
```
*Outputs: `experiments/results/agent_benchmark_before.csv`, `experiments/results/agent_benchmark_after.csv`, and `experiments/results/agent_benchmark.csv`.*

---

### N. Regenerate Figures

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

### O. Regenerate GUI Screenshots

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

### P. Final Verification

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

### Q. Submission Packaging

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

### R. 4-Way Debiased Evaluator Benchmark

Executes the strictly controlled head-to-head benchmark holding the search algorithm fixed ($A^*$ NEW vs $A^*$ OLD and GBFS NEW vs GBFS OLD) with **4-way factorial debiasing** (Role Swap $\times$ Spawn Mirror):

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
# Run complete suite (Tuning/Val 120 matches + Unseen Test 240 matches + Stress 96 matches = 456 matches):
python scripts/benchmark_evaluators.py --suite all

# Run specific suite:
python scripts/benchmark_evaluators.py --suite test  # Unseen holdout test (competitive_06 to 15)
python scripts/benchmark_evaluators.py --suite val   # Tuning & validation (competitive_01 to 05)
python scripts/benchmark_evaluators.py --suite stress# Secondary stress test on single-agent maps
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/benchmark_evaluators.py --suite all
```
*Outputs: `experiments/results/evaluator_benchmark_summary.csv`, `evaluator_benchmark_test.csv`, `evaluator_benchmark_val.csv`, `evaluator_benchmark_stress.csv`.*

---

### S. Evaluator Ablation Study

Evaluates component contributions (Score difference, Support distance, Horizon scaling, Ownership tracking) against the baseline:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/ablation_study.py
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/ablation_study.py
```
*Outputs: `experiments/results/evaluator_ablation.csv`.*

---

### T. Principled Weight Tuning

Runs discriminative head-to-head parameter tuning on the dedicated tuning set (`competitive_01` to `03`) and validates on the holdout validation set (`competitive_04` and `05`):

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
python scripts/tune_weights.py
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 scripts/tune_weights.py
```
*Outputs: `experiments/results/reward_weight_tuning.csv`.*

---


## 3. Documentation Index

- [docs/competitive_evaluation.md](docs/competitive_evaluation.md): RL-inspired state potential formulation, reward shaping interpretation, empirical weights, and controlled head-to-head benchmark.
- [docs/requirements_matrix.md](docs/requirements_matrix.md): Traceability matrix matching all assignment specifications.
- [docs/experiment_methodology.md](docs/experiment_methodology.md): Rigorous two-phase benchmarking protocol.
- [docs/experiment_results.md](docs/experiment_results.md): Empirical data tables, metrics, and speedup analysis.
- [docs/final_audit.md](docs/final_audit.md): Complete release-candidate audit report (all milestones PASS).
- [docs/heuristic_analysis.md](docs/heuristic_analysis.md): Formal admissibility and consistency proofs and competitive static BFS.
- [docs/optimization_report.md](docs/optimization_report.md): Search engineering details and memory optimization.
- [docs/presentation_outline.md](docs/presentation_outline.md): 8-slide oral presentation blueprint.
- [docs/oral_defense_notes.md](docs/oral_defense_notes.md): Oral defense speaking notes and architectural invariants.

