# Presentation outline (4:30–4:50, 4:3)

1. **Team and objective** (0:25): placeholders for group, students, IDs, emails, tasks, completion percentages. Proves submission context.
2. **State space** (0:35): static map, immutable state, actions, goal. Show compact diagram.
3. **UCS vs A*** (0:40): shared duplicate-aware graph search, g/f priorities, reverse-push matching heuristic.
4. **Measured comparison** (0:35): `expanded_nodes_by_map.png`, `runtime_by_map.png`, and `max_frontier_by_map.png`; distinguish runtime/frontier measurements from theoretical complexity.
5. **Heuristic properties** (0:40): lower-bound argument and validation CSV for admissibility/consistency; finite tests versus formal reasoning.
6. **Single-agent GUI** (0:30): use `experiments/figures/gui_single.png`; show action count, statistics, pause and replay controls.
7. **Competitive mode** (0:40): use `experiments/figures/gui_competitive.png`; simultaneous decisions, ownership, deterministic conflict rules, separate agents.
8. **Results and completion table** (0:25): multi-horizon agent benchmark and requirement matrix.

Do not include raw source code. Replace only personal placeholders before submission. Figures are light-background and use labels/borders/hatching so the presentation remains interpretable in grayscale.
