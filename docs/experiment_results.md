# Experiment Results

The benchmark evaluates duplicate-aware Uniform Cost Search (UCS) and A* Search with Reverse-Push Matching Heuristic across four benchmark maps, including the fully restored assignment map (`example_map.txt`). Timing experiments were conducted with `tracemalloc` completely disabled across 5 measured runs (after 1 warm-up run), reporting both mean and median runtimes. Memory consumption was measured in isolated runs with `tracemalloc` enabled.

## 1. Single-Agent Search Benchmark Summary

| Map | Algorithm | Solved | Cost | Mean Expanded | Generated | Max Frontier | Mean Runtime (ms) | Median Runtime (ms) | Peak Memory (KB) | Heuristic Cache Hits |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| easy_01.txt | UCS | Yes | 3 | 12 | 41 | 9 | 0.133 | 0.132 | 5.56 | 0 |
| easy_01.txt | A* | Yes | 3 | 10 | 35 | 9 | 0.168 | 0.153 | 8.60 | 15 |
| medium_01.txt | UCS | Yes | 7 | 101 | 344 | 48 | 1.667 | 1.615 | 26.96 | 0 |
| medium_01.txt | A* | Yes | 7 | 55 | 193 | 34 | 1.162 | 1.194 | 30.84 | 80 |
| hard_01.txt | UCS | Yes | 10 | 811 | 2,829 | 397 | 12.056 | 12.035 | 238.81 | 0 |
| hard_01.txt | A* | Yes | 10 | 204 | 724 | 130 | 3.787 | 3.515 | 96.71 | 299 |
| **example_map.txt** | **UCS** | **Yes** | **34** | **38,405** | **102,368** | **8,280** | **955.313** | **948.202** | **19,546.01** | **0** |
| **example_map.txt** | **A\*** | **Yes** | **34** | **6,616** | **17,700** | **1,572** | **421.720** | **425.246** | **3,350.12** | **7,046** |

### Key Findings
1. **Assignment Map Solvability**: When restored character-by-character from the assignment PDF (8 `%` in final row, 8 columns wide, enclosed perimeter) and parsed with proper void isolation, `example_map.txt` is **100% solvable**. Both UCS and A* find the optimal path of 34 steps.
2. **Search Efficiency**: On `example_map.txt`, A* achieves an **82.8% reduction in expanded nodes** (6,616 vs 38,405), a **2.26x speedup** in execution runtime (421.72 ms vs 955.31 ms), and reduces peak memory from 19.55 MB down to 3.35 MB (**82.9% reduction**).
3. **Optimality Verification**: On all four maps, UCS and A* return identical optimal costs ($3, 7, 10, 34$). Every returned action sequence was verified by step-by-step state simulation.

## 2. Heuristic Validation

Empirical validation checked admissibility ($h(s) \le h^*(s)$ using optimal UCS cost) and monotonicity/consistency ($h(s) \le 1 + h(s')$) across 90 reachable states and 304 successor edges.
- Admissibility violations: **0 / 90 (0.0%)**
- Consistency violations: **0 / 304 (0.0%)**
- Maximum violation: **0.0**

## 3. Competitive Multi-Agent Benchmark

Two autonomous planners were benchmarked across all five repository maps for horizons $n \in \{10, 25, 50\}$:
- **Agent 1 (A*)**: Time-bounded A* graph search minimizing $f(n) = g(n) + h(n)$ with OPEN priority queue and `best_g` pruning.
- **Agent 2 (GBFS)**: Greedy Best-First Search prioritizing minimal $h(n)$ with OPEN priority queue.

Both agents use static wall-aware BFS shortest-path distance heuristics (no Manhattan, no Euclidean) and enforce an internal deadline $\le 950$ ms using high-resolution hardware timers (`time.perf_counter_ns()`).

| Map | Horizon ($n$) | Score (A1 / A2) | Winner | A1 Avg (ms) | A1 Max (ms) | A2 Avg (ms) | A2 Max (ms) | Deadline Fallbacks |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| competitive_01.txt | 10 | 1 - 1 | Tie | 22.00 | 25.78 | 14.97 | 16.38 | 0 / 0 |
| competitive_01.txt | 25 | 2 - 1 | Agent 1 (A*) | 13.67 | 23.28 | 9.04 | 15.54 | 0 / 0 |
| competitive_01.txt | 50 | 2 - 1 | Agent 1 (A*) | 7.86 | 42.63 | 4.96 | 21.39 | 0 / 0 |
| easy_01.txt | 10 | 0 - 0 | Tie | 0.90 | 1.17 | 0.51 | 0.60 | 0 / 0 |
| easy_01.txt | 25 | 0 - 0 | Tie | 0.89 | 1.37 | 0.51 | 0.64 | 0 / 0 |
| easy_01.txt | 50 | 0 - 0 | Tie | 0.90 | 1.39 | 0.51 | 0.85 | 0 / 0 |
| example_map.txt | 10 | 2 - 0 | Agent 1 (A*) | 29.02 | 44.10 | 0.82 | 1.17 | 0 / 0 |
| example_map.txt | 25 | 3 - 0 | Agent 1 (A*) | 16.17 | 44.90 | 0.66 | 0.84 | 0 / 0 |
| example_map.txt | 50 | 3 - 0 | Agent 1 (A*) | 10.24 | 45.43 | 0.58 | 0.93 | 0 / 0 |
| hard_01.txt | 10 | 0 - 1 | Agent 2 (GBFS) | 12.06 | 14.55 | 7.67 | 11.14 | 0 / 0 |
| hard_01.txt | 25 | 0 - 1 | Agent 2 (GBFS) | 13.71 | 25.59 | 7.04 | 11.06 | 0 / 0 |
| hard_01.txt | 50 | 0 - 1 | Agent 2 (GBFS) | 13.11 | 15.67 | 6.54 | 9.07 | 0 / 0 |
| medium_01.txt | 10 | 0 - 0 | Tie | 8.68 | 14.16 | 3.67 | 5.83 | 0 / 0 |
| medium_01.txt | 25 | 0 - 0 | Tie | 7.29 | 13.16 | 3.91 | 8.27 | 0 / 0 |
| medium_01.txt | 50 | 0 - 0 | Tie | 6.95 | 13.52 | 3.90 | 6.17 | 0 / 0 |

- **Maximum observed decision latency across all 15 matches**: **45.43 ms** (far below the 1,000 ms ceiling).
- **Deadline fallback count**: **0 / 15 matches (0.0%)**.
