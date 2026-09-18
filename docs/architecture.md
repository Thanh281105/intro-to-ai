# Architecture

A static `SokobanMap` stores dimensions, walls, and goals. A dynamic `State` stores only player position and an immutable set of box positions, making equality and hashing safe for graph search. `SokobanProblem` exposes initial state, successors, goal test, unit cost, and heuristic.

UCS and A* share one duplicate-aware priority-queue implementation. Search returns actions, trajectory states, cost, expansion/generation counts, frontier maximum, and elapsed time. Rendering consumes the stored trajectory and never searches backward.

The heuristic preprocesses wall-aware reverse pushes from every goal, then computes a minimum-cost one-to-one assignment using dependency-free bitmask dynamic programming. It is a relaxed lower bound because it ignores other boxes and detailed player routing. Competitive state is separate because it adds two player positions and ownership.
