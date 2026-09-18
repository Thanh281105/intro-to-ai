# Optimization and Engineering Report

## 1. Search Engineering Audit

The engineering audit inspected the complete software stack:
- Map parsing with ragged row void isolation (`valid_cells` and `floor_cells`).
- Immutable state representation (`State`, `CompetitiveState`).
- Successor generation and legal push verification.
- Closed list duplicate handling and priority queue stale-entry pruning (`best_g`).
- Reverse-push goal distance precomputation and box-target bipartite matching.
- Deadlock detection with sound static reverse-reachability.
- Two-phase benchmark architecture (timing runs with tracemalloc OFF; isolated memory runs with tracemalloc ON).
- Competitive multi-agent simultaneous move resolution, conflict handling, and TurnRecord telemetry.
- Procedural Pygame GUI rendering with cached sprite surfaces and dynamic state overlays.

## 2. Key Performance Optimizations

1. **Heuristic Layout Caching**:
   - In single-agent search, player-only movements preserve identical box configurations while changing player coordinates.
   - By caching the minimum-weight bipartite matching result indexed by sorted box positions, A* achieves high cache hit rates (e.g., 7,046 hits to 1,143 misses on `example_map.txt`).
2. **Priority Queue Stale-Entry Pruning**:
   - `OPEN` entries carry the node cost $g(n)$. When popped, if $g > \text{best\_g}[s]$, the node is discarded immediately without generating successors.
3. **Static Wall-Aware BFS Distance in Competitive Agents**:
   - Competitive agents (`AStarAgent`, `GBFSAgent`) require fast sub-second decisions.
   - All Manhattan and Euclidean distance calculations were removed. In their place, static BFS shortest paths over traversable floor cells (`board.floor_cells`) are precomputed and cached per board.
   - This provides accurate wall-aware distance estimates in $<0.1$ ms without full dynamic state expansion.
4. **Decoupled Two-Phase Benchmarking**:
   - Disabling `tracemalloc` during timing eliminates CPython memory tracing overhead, yielding accurate hardware execution runtimes.
   - Peak allocation is measured in a dedicated memory run.

## 3. Benchmark Comparison Across All Benchmark Maps

Based on the official 48-row benchmark dataset (`experiments/results/benchmark.csv`, 5 runs per algorithm):

| Map | Algorithm | Optimal Cost | Mean Expanded | Max Frontier | Mean Runtime (ms) | Peak Memory (KB) |
|---|---|:---:|:---:|:---:|:---:|:---:|
| `easy_01.txt` | UCS | 3 | 12 | 9 | 0.133 ms | 5.56 KB |
| `easy_01.txt` | A* | 3 | 10 | 9 | 0.168 ms | 8.60 KB |
| `medium_01.txt` | UCS | 7 | 101 | 48 | 1.667 ms | 26.96 KB |
| `medium_01.txt` | A* | 7 | 55 | 34 | 1.162 ms | 30.84 KB |
| `hard_01.txt` | UCS | 10 | 811 | 397 | 12.056 ms | 238.81 KB |
| `hard_01.txt` | A* | 10 | 204 | 130 | 3.787 ms | 96.71 KB |
| **`example_map.txt`** | **UCS** | **34** | **38,405** | **8,280** | **955.313 ms** | **19,546.01 KB** |
| **`example_map.txt`** | **A\*** | **34** | **6,616** | **1,572** | **421.720 ms** | **3,350.12 KB** |

## 4. Performance Interpretation

- **Pruning Power on Large State Spaces**:
  - On the authoritative assignment `example_map.txt` (7 boxes, 7 targets, 8x9 grid), A* reduces expanded nodes by **82.8%** (from 38,405 down to 6,616).
  - Peak memory is reduced by **82.9%** (from 19.55 MB to 3.35 MB).
  - Runtime drops by **2.26x** (from 955.31 ms to 421.72 ms).
- **Overhead on Trivial Maps**:
  - On `easy_01.txt` (1 box, 3 steps), heuristic evaluation adds slight constant overhead (0.168 ms vs 0.133 ms), which is standard behavior for informed search on trivial search spaces.
- **Correctness Guarantees**:
  - On every map, UCS and A* find identical optimal path costs.
  - Every returned plan is verified step-by-step to be 100% legal under Sokoban mechanics.
