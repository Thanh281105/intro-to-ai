# Experiment Methodology

## 1. Single-Agent Search Benchmark Protocol

The single-agent benchmark evaluates Uniform Cost Search (UCS) and A* search across four standard maps:
- `easy_01.txt` (trivial 3-step baseline)
- `medium_01.txt` (intermediate 7-step test)
- `hard_01.txt` (challenging 10-step multi-box bottleneck puzzle)
- `example_map.txt` (the authoritative 8x9 assignment benchmark map from PDF Page 2, featuring 7 boxes and 7 designated goal positions)

### Rigorous Two-Phase Measurement:
1. **Timing Phase (`tracemalloc` OFF)**:
   - To eliminate Python memory tracing overhead (which can distort CPU execution time by 2-5x), `tracemalloc` is explicitly disabled.
   - A warm-up run is executed first to prime caches and JIT paths.
   - Five consecutive measured runs are recorded per map-algorithm pair.
   - Both arithmetic mean and median runtimes are computed and reported.
2. **Memory Phase (`tracemalloc` ON)**:
   - A separate, isolated solver run executes with `tracemalloc.start()` and `tracemalloc.stop()`.
   - Peak memory allocation in kilobytes (KB) is captured cleanly without interfering with the timing runs.
3. **Correctness & Legality Verification**:
   - For every run, the returned plan is replayed step-by-step from initial to goal state through `verify_plan()`, ensuring every movement and push is strictly legal under Sokoban physics.
   - Optimal equivalence is verified: `cost(UCS) == cost(A*)`.

## 2. Heuristic Empirical Validation Protocol

The non-geometric reverse-push + maximum matching heuristic is empirically validated by `scripts/validate_heuristic.py`:
- Reachable states are systematically sampled via breadth-first search exploration from initial states.
- For each state $s$, the true optimal cost-to-go $h^*(s)$ is computed using an independent ground-truth UCS search.
- **Admissibility Check**: Verifies that $h(s) \le h^*(s)$. Any case where $h(s) > h^*(s)$ is flagged as a violation.
- **Consistency (Monotonicity) Check**: For every transition $(s, a, s')$ with step cost $c = 1$, verifies the triangle inequality $h(s) \le 1 + h(s')$.
- **Goal Condition**: Verifies $h(s_{\text{goal}}) = 0$.

## 3. Competitive Multi-Agent Experiment Protocol

The competitive multi-agent simulation is benchmarked across all five repository maps for horizons $n \in \{10, 25, 50\}$ by `scripts/benchmark_agents.py`:
- Evaluates `AStarAgent` (Agent 1) vs `GBFSAgent` (Agent 2).
- Both agents use wall-aware static BFS shortest-path distance heuristics (no Manhattan, no Euclidean).
- Per-turn decision latencies are measured using high-resolution hardware timers (`time.perf_counter_ns()`).
- Strict per-turn time limits (1000 ms limit, 950 ms internal safety margin) are enforced.
- Records average, median, and maximum decision latencies, along with deadline fallback occurrences and final match scores.
