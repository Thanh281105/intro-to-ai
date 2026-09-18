# Experiment methodology

The assignment `example_map.txt` is preserved exactly from the PDF, including its seven boxes and seven designated positions. An independent audit run parsed it as 10 columns by 9 rows and expanded 782,942 states before reporting unsolved under the current sound static-deadlock pruning; it is therefore not silently relabeled as an easy custom benchmark. The quantitative comparison uses only `easy_01.txt`, `medium_01.txt`, and `hard_01.txt`, each verified solvable by both UCS and A* with equal solution cost.

The benchmark executes UCS and A* five repetitions per custom map with deterministic successor order. It records solution status/cost, actions, runtime, expanded/generated nodes, maximum frontier, real `tracemalloc` peak memory, and heuristic cache hits/misses. Maximum frontier is the primary algorithm-level empirical space metric; tracemalloc is reported separately as process-level peak allocation and is machine-dependent.

The heuristic validator enumerates reachable states on the three custom maps, solves each sampled state with UCS, and checks the lower-bound inequality. It also checks every sampled legal edge for consistency. Measurements are environment-dependent and are not presented as Big-O complexity.
