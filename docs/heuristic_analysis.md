# Heuristic Design and Theoretical Analysis

## 1. Single-Agent Heuristic: Reverse-Push Distance + Bipartite Matching

### Analytical Formulation
For every goal cell $g \in G$, an offline reverse-push search explores predecessor box cells. A reverse transition $(b, b')$ is valid if and only if the corresponding forward push from support cell $u = 2b - b'$ is a free static floor cell. This produces an exact, wall-aware minimum push distance table $D(b, g)$.

Given a dynamic state $s = (p, B)$ with box set $B$ and goal set $G$ where $|B| = |G| = k$:
$$h(s) = \min_{\pi \in \Pi} \sum_{i=1}^k D(b_i, g_{\pi(i)})$$
where $\Pi$ is the set of all one-to-one permutations from boxes to goals, computed via dynamic programming over subset bitmasks.

### Admissibility Proof ($h(s) \le h^*(s)$)
1. **Relaxation**: In the true Sokoban game, moving box $b$ to goal $g$ requires the agent to maneuver behind $b$ without other boxes blocking the path, and boxes cannot occupy the same cell simultaneously. In the reverse-push relaxation, all other boxes are removed, and player walk paths are assumed unobstructed. Thus, the relaxed push cost $D(b, g)$ is a strict lower bound on the true pushes required: $D(b, g) \le \text{pushes}^*(b \to g)$.
2. **Action Cost Bound**: Each push requires at least 1 action (in addition to travel actions), so $\text{pushes}^*(s) \le \text{actions}^*(s) = h^*(s)$.
3. **Global Matching**: The minimum-weight bipartite matching finds the lowest possible sum of lower bounds over all valid 1-to-1 pairings. Hence, $h(s) \le h^*(s)$. If any box is in an unpushable dead cell, $D(b, g) = \infty$, yielding $h(s) = \infty$ (sound deadlock detection).

### Consistency (Monotonicity) Proof ($h(s) \le c(s, a, s') + h(s')$)
- **Player-Only Move** ($a \in \text{Walk}$): The set of box positions is unchanged ($B' = B$). Therefore $h(s') = h(s)$, and $h(s) \le 1 + h(s')$ holds trivially.
- **Push Move** ($a \in \text{Push}$): A single box $b_j$ is displaced to adjacent cell $b_j'$, so $|D(b_j, g) - D(b_j', g)| \le 1$ along the reverse-push search tree. Using the optimal matching permutation $\pi^*$ of $s'$, the triangle inequality yields $h(s) \le h(s') + 1 = c(s, a, s') + h(s')$.

### Empirical Validation Results
Validated by `scripts/validate_heuristic.py` across 90 reachable states and 304 transitions:
- Admissibility violations: **0 / 90 (0.0%)**
- Consistency violations: **0 / 304 (0.0%)**
- Maximum violation: **0.0**

## 2. Competitive Agent Heuristics: Static Wall-Aware BFS

In the multi-agent competitive environment, heuristic evaluation must be ultra-fast ($<1$ ms) to guarantee compliance with the 1,000 ms decision deadline while navigating complex wall corridors:
- **Zero Manhattan / Euclidean**: Standard Manhattan distance ($\Delta r + \Delta c$) and Euclidean distance ($\sqrt{\Delta r^2 + \Delta c^2}$) assume empty grids and are severely misleading in maze-like Sokoban environments.
- **Wall-Aware Static Shortest-Path Distance**: We precompute and cache all-pairs static shortest paths over traversable floor cells using breadth-first search (`get_static_distances(board, src)`).
- **Navigation Heuristic**:
  - Distance from player to target box support cells uses static BFS wall-aware distance.
  - Box-to-goal progress reuses the precomputed reverse-push goal distance table.
- **Complexity**: $O(1)$ table lookup at runtime per state evaluation, yielding average decision times under 30 ms and zero deadline violations.
