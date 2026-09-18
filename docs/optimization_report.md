# Optimization report

## Search audit

The audit inspected map parsing, immutable state representation, successor generation, priority-queue ordering, stale-entry handling, parent-pointer reconstruction, reverse-push preprocessing, matching, deadlock reuse, benchmark scripts, and both GUI modes.

## Problems found

The assignment example map had previously been replaced by a one-box toy map. Benchmark rows contained a misleading zero-valued peak-memory field. The heuristic was recomputed for repeated player positions with identical box layouts. Figure names did not explicitly identify the metric. The first GUI was a single compact board without a presentation information panel, and competitive GUI rendering was missing.

## Changes

The authoritative example map was restored exactly from the PDF. Reverse-push tables are built once per static board, while matching values are cached by sorted immutable box configuration. Search heap entries now carry their popped `g` value and stale entries are rejected directly. Real `tracemalloc` peak allocation is collected in the benchmark. Three grayscale figures cover expanded nodes, runtime, and maximum frontier. Agents use deadline-bounded reverse-push goal-progress evaluation and reachable-box routing. Both GUIs use the shared light renderer, information panels, grayscale-distinguishable markers, and offscreen screenshot generation.

## Correctness protection

The full test suite covers parser/state/search, competitive agents, heuristic cache reuse, and offscreen rendering. Each custom benchmark map is solved by UCS and A* and their costs are compared. A final replay verifier checked every returned action as legal and checked final goal satisfaction. The assignment map is preserved and separately audited rather than changed for performance.

## Benchmark before

The previous legitimate run used the simplified example map and reported 40 rows; it is not treated as evidence for the restored assignment map. On `hard_01`, the previous mean expanded-node counts were UCS 811 and A* 204, with mean runtimes 17.8588 ms and 10.3010 ms.

## Benchmark after

The new run uses 30 rows over three verified custom maps. On `hard_01`, UCS expanded 811 nodes in 68.8193 ms on average, while A* expanded 204 nodes in 18.4978 ms. Mean frontier sizes were 397 and 130 respectively. On `medium_01`, A* reduced expansions from 101 to 55 and frontier from 48 to 34. Real mean tracemalloc peaks were 261.28 KB for UCS and 96.52 KB for A* on `hard_01`. A* cache totals on the three maps were 1,970 hits and 235 misses across five repetitions per map.

## Interpretation

The expanded-node and frontier improvements are defensible on medium and hard maps, while the small easy map still shows heuristic overhead. Tracemalloc is process-level and machine-dependent; maximum frontier remains the primary algorithm-level search-space metric. Caching is justified because player-only moves produce many states sharing a box configuration. Equal solution costs, replay validation, and zero heuristic-validation violations protect correctness.
