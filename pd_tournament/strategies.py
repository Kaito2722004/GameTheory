"""The strategy pool.

Every strategy is a pure function with the same dead-simple signature::

    def my_strategy(my_history: list[str], their_history: list[str]) -> str:
        return "C"  # or "D"

Both histories are lists of past moves, oldest first, always the same length.
On the first round both are empty. That is the whole interface -- a
non-programmer's submission is a few lines, and nothing here needs to know
about the engine.

Each strategy is tagged with Axelrod's four properties (see the Ch. 12
notes): Nice, Retaliatory, Forgiving, Clear. That mapping is analysis, not
flavour text -- `analysis.explain_ranking` uses it to explain *why* the
tournament came out the way it did.
"""

import random
from dataclasses import dataclass
from typing import Callable

from .payoffs import COOPERATE, DEFECT

Strategy = Callable[[list[str], list[str]], str]

# Seeded for reproducibility; `seed(...)` re-seeds it before a tournament so
# that runs with the same seed give identical results.
_rng = random.Random(20260811)


def seed(value: int) -> None:
    """Re-seed the RNG used by the stochastic strategies."""
    _rng.seed(value)


def always_cooperate(my_history: list[str], their_history: list[str]) -> str:
    """Cooperate unconditionally -- the "sucker" baseline.

    Nice: yes. Retaliatory: no (this is what makes it exploitable).
    Forgiving: vacuously, it never retaliates in the first place.
    Clear: yes.
    """
    return COOPERATE


def always_defect(my_history: list[str], their_history: list[str]) -> str:
    """Defect unconditionally -- the one-shot dominant strategy.

    Nice: no. Retaliatory: only vacuously; it punishes everything
    unconditionally rather than in response to defection.
    Forgiving: no. Clear: yes.
    """
    return DEFECT


def tit_for_tat(my_history: list[str], their_history: list[str]) -> str:
    """Rapoport's four-line tournament winner: cooperate, then mirror.

    Nice, Retaliatory, Forgiving, and Clear -- the only strategy here with
    all four of Axelrod's properties, which is the result the iterated
    tournament is supposed to reproduce.
    """
    if not their_history:
        return COOPERATE
    return their_history[-1]


def grim_trigger(my_history: list[str], their_history: list[str]) -> str:
    """Cooperate until the opponent defects once, then defect forever.

    Nice: yes. Retaliatory: maximally. Forgiving: no -- a single defection
    is unrecoverable, which is exactly why it does badly against noisy or
    probing opponents. Clear: yes.
    """
    if DEFECT in their_history:
        return DEFECT
    return COOPERATE


def tit_for_two_tats(my_history: list[str], their_history: list[str]) -> str:
    """Retaliate only after two defections in a row -- the forgiving variant.

    Nice: yes. Retaliatory: yes, but slowly. Forgiving: more than TFT, which
    lets it recover from mutual-recrimination spirals TFT gets stuck in.
    Clear: yes.
    """
    if len(their_history) >= 2 and their_history[-1] == their_history[-2] == DEFECT:
        return DEFECT
    return COOPERATE


def pavlov(my_history: list[str], their_history: list[str]) -> str:
    """Win-stay, lose-shift: repeat the last move if it earned R or T.

    With T > R > U > S the "winning" payoffs R and T are exactly the ones
    where the opponent cooperated, so this reduces to: repeat my last move
    if they cooperated, switch if they defected. Implemented that way to
    keep the pure (history, history) interface.

    Nice: yes (opens with C). Retaliatory: yes. Forgiving: yes -- two
    defectors playing Pavlov drift back into cooperation. Clear: least
    clear of the nice strategies; its behaviour is harder to read than TFT's.
    """
    if not my_history:
        return COOPERATE
    if their_history[-1] == COOPERATE:
        return my_history[-1]
    return DEFECT if my_history[-1] == COOPERATE else COOPERATE


def random_choice(my_history: list[str], their_history: list[str]) -> str:
    """Cooperate with probability 0.5 -- the naive stochastic baseline.

    None of the four properties. Axelrod included a RANDOM entry for exactly
    this reason: it is the control that shows the others are doing something.
    """
    return COOPERATE if _rng.random() < 0.5 else DEFECT


@dataclass(frozen=True)
class StrategyInfo:
    """A strategy plus its Axelrod-property tags."""

    name: str
    fn: Strategy
    nice: bool
    retaliatory: bool
    forgiving: bool
    clear: bool

    @property
    def property_count(self) -> int:
        return sum([self.nice, self.retaliatory, self.forgiving, self.clear])

    def properties(self) -> str:
        """e.g. "Nice, Retaliatory, Forgiving, Clear" or "none"."""
        tags = [
            label
            for label, held in (
                ("Nice", self.nice),
                ("Retaliatory", self.retaliatory),
                ("Forgiving", self.forgiving),
                ("Clear", self.clear),
            )
            if held
        ]
        return ", ".join(tags) if tags else "none"


#: The default pool. Order here is only for display; the tournament is a
#: full round robin so it has no effect on results.
REGISTRY: dict[str, StrategyInfo] = {
    info.name: info
    for info in (
        StrategyInfo("tit_for_tat", tit_for_tat, True, True, True, True),
        StrategyInfo("tit_for_two_tats", tit_for_two_tats, True, True, True, True),
        StrategyInfo("pavlov", pavlov, True, True, True, False),
        StrategyInfo("grim_trigger", grim_trigger, True, True, False, True),
        StrategyInfo("always_cooperate", always_cooperate, True, False, True, True),
        StrategyInfo("always_defect", always_defect, False, False, False, True),
        StrategyInfo("random_choice", random_choice, False, False, False, False),
    )
}


def get(name: str) -> StrategyInfo:
    """Look up a strategy by name, with a helpful error if it's missing."""
    try:
        return REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"unknown strategy {name!r}; available: {', '.join(sorted(REGISTRY))}"
        ) from None


def default_pool() -> list[StrategyInfo]:
    """Every registered strategy, in registry order."""
    return list(REGISTRY.values())


def register(
    name: str,
    fn: Strategy,
    *,
    nice: bool = False,
    retaliatory: bool = False,
    forgiving: bool = False,
    clear: bool = False,
) -> StrategyInfo:
    """Add a strategy to the pool at runtime.

    This is the hook for a "submit your own strategy" component: import this
    module, call `register("my_strategy", my_fn, nice=True, ...)`, and it
    joins the round robin like any built-in.
    """
    if name in REGISTRY:
        raise ValueError(f"strategy {name!r} is already registered")
    info = StrategyInfo(name, fn, nice, retaliatory, forgiving, clear)
    REGISTRY[name] = info
    return info
