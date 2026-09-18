# Heuristic analysis

For every goal, reverse search adds a predecessor box square only when the corresponding forward push has a free static support square. This produces a wall-aware relaxed push distance. A state heuristic assigns boxes to distinct goals with minimum total distance using bitmask dynamic programming.

The relaxation ignores other boxes and detailed player routing, so each relaxed plan removes constraints from the real problem. Its push count is therefore a lower bound on required real pushes, and every real push costs at least one action. The matching is a minimum over valid one-to-one assignments, so the resulting value is a lower bound for solvable states. It is not a geometric-distance heuristic.

The reverse-push tables are built once per static board. Matching values are cached using a sorted tuple of box positions, so player-only states with identical box layouts reuse the same value. The cache is safe because the heuristic depends on boxes, goals, and walls, not player position. Current benchmark cache totals are reported in `benchmark_summary.csv`.

For a player-only move, box positions do not change and the heuristic is unchanged. For a push, every reverse-distance edge changes by at most one in the relevant direction; replacing one assignment edge yields the consistency inequality `h(s) <= 1 + h(s')`. The executable validator sampled 90 reachable states and 304 transitions across three custom maps: 0 admissibility violations and 0 consistency violations. This supports, but does not replace, the analytical argument.
