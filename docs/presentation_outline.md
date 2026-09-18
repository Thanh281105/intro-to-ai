# Oral Defense Presentation Outline (Target: 4:30 – 4:50, 4:3 Aspect Ratio)

## Slide 1: Team & Project Scope (0:25)
- Title: Multi-Agent and Heuristic Search in Sokoban.
- Presenter details: Group ID, Student Name, Student ID, Email, Role, Task Breakdown (100% Completion).
- Deliverables: Single-agent optimal search, non-geometric heuristic design, empirical memory/runtime benchmarking, simultaneous multi-agent competitive arena.

## Slide 2: State-Space Modeling & Robust Parsing (0:35)
- World Model: Static immutable board vs dynamic state tuple `State(player=(r, c), boxes=frozenset({...}))`.
- Ragged Map Safety: Void isolation preventing unpadded row characters from becoming walkable corridors.
- Transition Model: Deterministic Walk and Push mechanics, legal push precondition checking.
- Problem Instances: Standard benchmarks and the authoritative 8x9 `example_map.txt` (7 boxes, 7 targets).

## Slide 3: Search Algorithms: UCS vs A* (0:40)
- Graph Search Foundation: Explicit `OPEN` priority queue and `CLOSED` set; duplicate state pruning.
- Uniform Cost Search (UCS): Min-priority on path cost $g(n)$, ensuring admissibility and completeness.
- A* Search: Min-priority on evaluation function $f(n) = g(n) + h(n)$ with stale-entry rejection via `best_g`.
- Exact Solution Equivalence: Proving both algorithms reach identical optimal costs ($3, 7, 10, 34$) on all maps.

## Slide 4: Empirical Search Space & Memory Telemetry (0:35)
- Empirical Figures: `expanded_nodes_by_map.png`, `runtime_by_map.png`, `max_frontier_by_map.png`.
- Two-Phase Methodology: Timing runs (tracemalloc OFF) vs memory runs (tracemalloc ON in isolation).
- Benchmark Findings on `example_map.txt`:
  - **82.8% reduction in expanded nodes** (6,616 vs 38,405).
  - **82.9% reduction in peak memory** (3.35 MB vs 19.55 MB).
  - **2.26x speedup** in execution time (421.72 ms vs 955.31 ms).

## Slide 5: Non-Geometric Heuristic Formulation (0:40)
- Reverse-Push Distance: Offline BFS from goal positions with support cell validation.
- Minimum-Weight Bipartite Matching: Bitmask DP assigning each box to a distinct goal.
- Admissibility & Monotonicity Proof: Relaxed problem without inter-box interference provides a strict lower bound ($h \le h^*$).
- Validation Results: `heuristic_validation.csv` confirms 0 admissibility violations, 0 consistency violations across 90 states and 304 transition edges.
- Static Deadlock Pruning: Immediate detection of unpushable corner cells.

## Slide 6: Single-Agent Replay GUI (0:30)
- Visual Artifact: `experiments/figures/gui_single.png`.
- Key Features: Step-by-step replay timeline, play/pause (SPACE), step forward/back (RIGHT/LEFT), reset (R).
- Clean Telemetry: Node expansion, generated states, memory, live step counter.
- Status Machine: Clearly displays `IN PROGRESS` during active replay; `SOLVED` only upon goal state.

## Slide 7: Competitive Multi-Agent Arena & Semantics (0:45)
- Visual Artifacts:
  - `experiments/figures/gui_competitive.png` (Active Match: step 16/25, real LAST TURN telemetry, no emotes).
  - `experiments/figures/gui_competitive_final.png` (Match Complete: overlay, final score, crown on winner, crying on loser).
- Simultaneous Action Resolution: Intent declaration, swap conflict detection, dual-push resolution, box ownership tracking.
- Real Telemetry: Live decision latencies, action outcomes (`MOVE`, `PUSH`, `BLOCKED`, `CONFLICT`).
- Wall-Aware Static BFS Heuristic: Zero Manhattan / Euclidean distance; max decision latency 45.4 ms ($<1000$ ms deadline).

## Slide 8: Requirements Traceability & Conclusion (0:25)
- Matrix Overview: 100% PASS across all assignment specifications.
- Reproducibility: Clean copy-paste reproduction commands for Windows PowerShell and macOS/Linux.
- Q&A Preparation: Theoretical soundness of relaxation, tie-breaking, and multi-agent game-theoretic equilibrium.
