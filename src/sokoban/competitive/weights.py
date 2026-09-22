from dataclasses import dataclass

@dataclass(frozen=True)
class CompetitiveWeights:
    """Weights governing the RL-inspired state potential function Phi_i(s).
    
    IMPORTANT NOTE ON step_penalty:
    The step_penalty parameter is used exclusively in the conceptual reward-shaping
    transition interpretation:
        R_i(s, a, s') = step_penalty + Phi_i(s') - Phi_i(s)
    It is NOT an independent tunable parameter for GBFS (which prioritizes states
    strictly using h_comp(s) = -Phi_i(s) and does not accumulate step costs).
    For A*, path cost g(n) natively penalizes elapsed steps.
    """
    w_score: float = 30.0
    w_push: float = 3.0
    w_route: float = 2.0
    w_threat: float = 6.0
    w_defense: float = 4.0
    w_disrupt: float = 4.0
    w_blocking: float = 3.0
    step_penalty: float = -1.0
    terminal_win: float = 1000.0
    terminal_loss: float = -1000.0
    terminal_draw: float = 0.0
    horizon_alpha: float = 0.5

DEFAULT_WEIGHTS = CompetitiveWeights()
