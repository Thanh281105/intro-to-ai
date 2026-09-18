# Final Audit Matrix & Verification Report

| Requirement | Expected | Implemented? | Tested? | Evidence | Presentation? | Remaining Risk |
|---|---|:---:|:---:|---|:---:|---|
| **State-space model** | Static map, immutable state, actions, goal | Yes | Yes | 30 passing pytest unit tests | Outline slide 2 | None |
| **Assignment example map** | Exact B/C/D semantics, character-by-character restoration from PDF | Yes | Yes | `example_map.txt` (8 `%` final row, 35 walls, 7 boxes, 7 goals); Solved in 34 steps | Slide 2 | None (fully solved and verified) |
| **UCS and A\*** | Duplicate-aware optimal graph search, equal costs | Yes | Yes | 48-row benchmark, 4 maps, exact cost match ($3, 7, 10, 34$) | Slides 3-4 | None |
| **Heuristic function** | Reverse-push relaxed matching (admissible, consistent, no Manhattan/Euclidean) | Yes | Yes | 0 violations across 90 states and 304 edges in `heuristic_validation.csv` | Slide 5 | None |
| **Space & Time complexity** | Frontier size, expanded nodes, tracemalloc peak memory separated from timing | Yes | Yes | `benchmark.csv`, `benchmark_summary.csv`, 3 bar figures | Slide 4 | None |
| **Deadlock detection** | Sound static deadlock pruning via reverse unreachable cells | Yes | Yes | Integrated in search loops and tested | Slide 5 | None |
| **Single GUI Replay** | Playback timer tick (350ms), Space (play/pause), Right/Left (step), R (reset) | Yes | Yes | Decoupled `SingleGame.tick()` unit tested; `gui_single.png` | Slide 6 | None |
| **Status Semantics** | Clear states: READY, PLAYING, PAUSED, FINISHED, UNSOLVABLE | Yes | Yes | State machine verified in `test_gui_playback_state_machine_and_ticks` | Slide 6 | None |
| **Competitive Push Semantics** | Player moves to old box cell, box moves to beyond; player never inside box | Yes | Yes | Explicit invariant tests in `test_competitive.py` | Slide 7 | None |
| **Simultaneous Resolution** | Explicit intent model (`player_from`, `player_to`, `push_box_from`, `push_box_to`), conflict pre-resolution | Yes | Yes | 10+ conflict scenario tests (same dest, swap, entering opponent cell, dual push) | Slides 7-8 | None |
| **Deterministic Agent 2 Start** | Inside playable floor, not wall, not box, not Agent 1, deterministic | Yes | Yes | Verified on all maps in `test_deterministic_p2_start_validation` | Slide 7 | None |
| **Competitive A\* Planner** | Genuine OPEN priority queue with $f(n) = g(n) + h(n)$, `best_g`, path reconstruction | Yes | Yes | Priority search in `agent_astar.py`, latency measured | Slide 7 | None |
| **Competitive GBFS Planner** | Genuine OPEN priority queue ordered by $h(n)$, visited set, path reconstruction | Yes | Yes | Greedy search in `agent_gbfs.py`, latency measured | Slide 7 | None |
| **Decision Deadline** | Internal deadline $\le 950$ ms using `time.perf_counter_ns()`, max latency $<1000$ ms | Yes | Yes | Max latency 124.26 ms across 15 matches, 0 deadline fallbacks | Slide 7 | None |
| **Competitive GUI** | Render authentic gameplay history, box ownership colors, scores | Yes | Yes | Rendered from real history frame in `gui_competitive.png` | Slide 7 | None |
| **Reproducibility** | Clean command execution, reproducible CSVs and figures | Yes | Yes | All scripts tested end-to-end | All slides | None |
| **Packaging script** | Folder layout `AI_midterm_<group>_<student>`, PDF, demo URL, zip | Yes | Script tested | `scripts/package_submission.py` | Slide 1 | Template ready for user credentials |
