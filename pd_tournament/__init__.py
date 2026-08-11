"""Axelrod-style Iterated Prisoner's Dilemma tournament.

Grounded in Philip D. Straffin, *Game Theory and Strategy* (MAA, 1993),
Ch. 11-13. See `.claude/skills/prisoners-dilemma-tournament/references/`
for the book notes this implementation follows.

`plots` is deliberately not imported here so the simulator can run without
matplotlib installed; import it explicitly when you want figures.
"""

from .payoffs import COOPERATE, DEFECT, PayoffMatrix, STANDARD
from . import analysis, engine, strategies

__all__ = [
    "COOPERATE",
    "DEFECT",
    "PayoffMatrix",
    "STANDARD",
    "analysis",
    "engine",
    "strategies",
]
