"""Competitive evaluator package entrypoint.
Re-exports competitive evaluators and weight structures for full backward compatibility.
"""

from .config import (
    DEFAULT_TIME_LIMIT_MS,
    SAFETY_DEADLINE_MS,
    MAX_SEARCH_DEPTH,
    MAX_SEARCH_EXPANSIONS,
)
from .weights import CompetitiveWeights, DEFAULT_WEIGHTS
from .evaluator_base import BaseCompetitiveEvaluator
from .evaluator_old import OldEvaluator
from .evaluator_potential import CompetitiveEvaluator

__all__ = [
    'DEFAULT_TIME_LIMIT_MS',
    'SAFETY_DEADLINE_MS',
    'MAX_SEARCH_DEPTH',
    'MAX_SEARCH_EXPANSIONS',
    'CompetitiveWeights',
    'DEFAULT_WEIGHTS',
    'BaseCompetitiveEvaluator',
    'OldEvaluator',
    'CompetitiveEvaluator',
]
