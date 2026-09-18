# Requirements traceability

|Requirement|Exact expectation|Implementation|Source|Tests|Experimental evidence|Presentation|Demo|Status|
|---|---|---|---|---|---|---|---|---|
|State-space|Static map, immutable dynamic state, actions, goal|`map.py`, `state.py`, `problem.py`|Current PDF p1-2|Core tests|Custom solver runs|Slide 2|CLI|PASS|
|Assignment example|Preserve map semantics including B/C/D|`maps/example_map.txt` restored verbatim|Current PDF p2|Parser count audit|Separate 782,942-state audit|Slide 2|CLI|PASS / unsolved audit disclosed|
|UCS/A*|Optimal graph search and statistics|`search/common.py`, `ucs.py`, `astar.py`|Current PDF p2|Core tests + replay|30-row benchmark, equal costs|Slides 3-4|CLI|PASS|
|Non-geometric heuristic|Reverse-push + minimum matching|`heuristic.py` with layout cache|Current PDF p2; prompt §8|Cache tests|Validation CSV, 0 violations|Slide 5|CLI|PASS|
|Space evidence|Time and empirical search-space comparison|frontier plus tracemalloc|Current PDF p2|Benchmark pipeline|frontier figures and CSV|Slide 4|CLI|PASS|
|Deadlock|Sound static reverse reachability pruning|`deadlock.py`|Prompt §9|Solver regression|Benchmark|Slide 5|CLI|PASS|
|Single-agent GUI|UCS/A*, count, pause, forward/back|`gui/renderer.py`, `single_game.py`|Current PDF p2|Offscreen render test|`gui_single.png`|Slide 6|run_gui|PASS headless; desktop review recommended|
|Competitive game|Two agents, simultaneous actions, horizon, scoring|`competitive/`|Current PDF p2-3|Competitive tests|12 multi-horizon rows|Slides 7-8|run_competitive|PASS|
|Competitive agents|Separate deadline-aware controllers|`agents/`|Current PDF p3|Agent tests|Latency and scores CSV|Slide 7|CLI|PASS|
|Competitive GUI|Both agents, scores, ownership, winner|`competitive_game.py`, renderer|Prompt §27|Offscreen screenshot|`gui_competitive.png`|Slide 7|run_competitive_gui|PASS headless|
|Submission|source, presentation, demo URL, zip|`package_submission.py`|Current PDF p4|Script present|Requires real personal inputs|Slide 1|demo template|PARTIAL: personal data/PDF pending|
