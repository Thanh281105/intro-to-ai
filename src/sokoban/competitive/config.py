"""Configuration constants for competitive multi-agent Sokoban.
Centralizes execution deadlines, search depth limits, and node expansion ceilings.
"""

# Maximum allowed search latency under competition rules (in milliseconds)
DEFAULT_TIME_LIMIT_MS: int = 1000

# High-precision safety deadline margin (in milliseconds) to ensure zero timeouts
SAFETY_DEADLINE_MS: int = 950

# Search bounds for bounded real-time graph search
MAX_SEARCH_DEPTH: int = 14
MAX_SEARCH_EXPANSIONS: int = 600
