"""Tournament runners: one-shot, iterated, and indefinite-horizon.

The three modes are deliberately separate functions rather than one runner
with a flag, because they demonstrate three different things:

* one-shot        -> the static Nash result (D dominates; DD is the equilibrium)
* iterated        -> Axelrod's tournament (TFT does well over repeated play)
* indefinite      -> the shadow of the future (cooperation pays once p is high)
"""

import random
from dataclasses import dataclass, field

from .payoffs import COOPERATE, DEFECT, PayoffMatrix, STANDARD
from .strategies import StrategyInfo, default_pool


@dataclass
class MatchResult:
    """The outcome of one pairing over however many rounds it lasted."""

    name_a: str
    name_b: str
    moves_a: list[str]
    moves_b: list[str]
    score_a: float
    score_b: float

    @property
    def rounds(self) -> int:
        return len(self.moves_a)

    def cooperation_rate(self, which: str) -> float:
        """Fraction of rounds in which side "a" or "b" cooperated."""
        moves = self.moves_a if which == "a" else self.moves_b
        if not moves:
            return 0.0
        return moves.count(COOPERATE) / len(moves)


@dataclass
class TournamentResult:
    """Aggregate of every match in a round robin."""

    mode: str
    payoffs: PayoffMatrix
    matches: list[MatchResult] = field(default_factory=list)
    rounds_per_match: int | None = None
    continuation_probability: float | None = None

    def total_scores(self) -> dict[str, float]:
        """Total score per strategy, summed across all its matches."""
        scores: dict[str, float] = {}
        for m in self.matches:
            scores[m.name_a] = scores.get(m.name_a, 0.0) + m.score_a
            scores[m.name_b] = scores.get(m.name_b, 0.0) + m.score_b
        return scores

    def average_scores(self) -> dict[str, float]:
        """Mean score *per round played* -- the fair comparison when matches
        differ in length, as they do in indefinite-horizon mode."""
        totals: dict[str, float] = {}
        rounds: dict[str, int] = {}
        for m in self.matches:
            totals[m.name_a] = totals.get(m.name_a, 0.0) + m.score_a
            totals[m.name_b] = totals.get(m.name_b, 0.0) + m.score_b
            rounds[m.name_a] = rounds.get(m.name_a, 0) + m.rounds
            rounds[m.name_b] = rounds.get(m.name_b, 0) + m.rounds
        return {n: totals[n] / rounds[n] for n in totals if rounds[n]}

    def cooperation_rates(self) -> dict[str, float]:
        """Fraction of all rounds played in which each strategy cooperated."""
        coops: dict[str, int] = {}
        rounds: dict[str, int] = {}
        for m in self.matches:
            coops[m.name_a] = coops.get(m.name_a, 0) + m.moves_a.count(COOPERATE)
            coops[m.name_b] = coops.get(m.name_b, 0) + m.moves_b.count(COOPERATE)
            rounds[m.name_a] = rounds.get(m.name_a, 0) + m.rounds
            rounds[m.name_b] = rounds.get(m.name_b, 0) + m.rounds
        return {n: coops[n] / rounds[n] for n in coops if rounds[n]}

    def ranking(self) -> list[tuple[str, float]]:
        """(name, total score) sorted best first."""
        return sorted(self.total_scores().items(), key=lambda kv: -kv[1])

    def head_to_head(self) -> dict[tuple[str, str], tuple[float, float]]:
        """(row, column) -> (row's score, column's score) for each pairing."""
        return {(m.name_a, m.name_b): (m.score_a, m.score_b) for m in self.matches}


def play_match(
    a: StrategyInfo,
    b: StrategyInfo,
    rounds: int,
    payoffs: PayoffMatrix = STANDARD,
) -> MatchResult:
    """Play a fixed number of simultaneous rounds between two strategies.

    Both strategies see only the history *before* the current round, so the
    moves really are simultaneous -- neither can peek at the other's choice.
    """
    moves_a: list[str] = []
    moves_b: list[str] = []
    score_a = score_b = 0.0
    for _ in range(rounds):
        move_a = a.fn(list(moves_a), list(moves_b))
        move_b = b.fn(list(moves_b), list(moves_a))
        pay_a, pay_b = payoffs.both_payoffs(move_a, move_b)
        moves_a.append(move_a)
        moves_b.append(move_b)
        score_a += pay_a
        score_b += pay_b
    return MatchResult(a.name, b.name, moves_a, moves_b, score_a, score_b)


def play_indefinite_match(
    a: StrategyInfo,
    b: StrategyInfo,
    continuation_probability: float,
    payoffs: PayoffMatrix = STANDARD,
    rng: random.Random | None = None,
    max_rounds: int = 10_000,
) -> MatchResult:
    """Play until a continuation coin flip fails.

    At least one round is always played; after each round the game continues
    with probability `p`. Expected length is 1 / (1 - p). `max_rounds` is a
    safety net for p very close to 1, not part of the model.
    """
    if not 0.0 <= continuation_probability < 1.0:
        raise ValueError("continuation probability must be in [0, 1)")
    rng = rng or random.Random()
    moves_a: list[str] = []
    moves_b: list[str] = []
    score_a = score_b = 0.0
    while len(moves_a) < max_rounds:
        move_a = a.fn(list(moves_a), list(moves_b))
        move_b = b.fn(list(moves_b), list(moves_a))
        pay_a, pay_b = payoffs.both_payoffs(move_a, move_b)
        moves_a.append(move_a)
        moves_b.append(move_b)
        score_a += pay_a
        score_b += pay_b
        if rng.random() >= continuation_probability:
            break
    return MatchResult(a.name, b.name, moves_a, moves_b, score_a, score_b)


def _pairings(
    pool: list[StrategyInfo], include_self_play: bool
) -> list[tuple[StrategyInfo, StrategyInfo]]:
    """Every unordered pair, optionally including each strategy against a twin.

    Axelrod's tournaments included self-play, and it matters: it is what
    punishes always_defect (a defector meeting its twin earns only U) and
    rewards the nice strategies (a cooperator meeting its twin earns R).
    """
    pairs = []
    for i, a in enumerate(pool):
        start = i if include_self_play else i + 1
        for b in pool[start:]:
            pairs.append((a, b))
    return pairs


def one_shot_round_robin(
    pool: list[StrategyInfo] | None = None,
    payoffs: PayoffMatrix = STANDARD,
    include_self_play: bool = True,
) -> TournamentResult:
    """Every pair plays exactly one round.

    This is the mode that should show cooperation *losing*: with no future to
    protect, D strictly dominates, so any strategy that opens with C is simply
    exploited. If cooperation wins here, the payoff matrix or the scoring is
    wrong -- not the theory.
    """
    pool = pool if pool is not None else default_pool()
    result = TournamentResult(mode="one_shot", payoffs=payoffs, rounds_per_match=1)
    for a, b in _pairings(pool, include_self_play):
        result.matches.append(play_match(a, b, rounds=1, payoffs=payoffs))
    return result


def iterated_round_robin(
    pool: list[StrategyInfo] | None = None,
    rounds: int = 200,
    payoffs: PayoffMatrix = STANDARD,
    include_self_play: bool = True,
) -> TournamentResult:
    """Axelrod's format: every pair plays `rounds` rounds (he used 200).

    Note that the round count is known and fixed, so by strict backward
    induction both players "should" defect throughout (Ch. 12's domino
    argument). They don't, because these strategies are not backward
    inductors -- which is precisely the gap between theory and practice the
    tournament exists to expose.
    """
    pool = pool if pool is not None else default_pool()
    result = TournamentResult(
        mode="iterated", payoffs=payoffs, rounds_per_match=rounds
    )
    for a, b in _pairings(pool, include_self_play):
        result.matches.append(play_match(a, b, rounds=rounds, payoffs=payoffs))
    return result


def indefinite_round_robin(
    pool: list[StrategyInfo] | None = None,
    continuation_probability: float = 0.9,
    trials: int = 100,
    payoffs: PayoffMatrix = STANDARD,
    include_self_play: bool = True,
    seed: int | None = 20260811,
) -> TournamentResult:
    """Round robin where each match runs to a random length.

    Each pairing is played `trials` times and every trial is recorded, so the
    aggregate methods average over them. Use `average_scores()` rather than
    `total_scores()` here, since matches differ in length.
    """
    pool = pool if pool is not None else default_pool()
    rng = random.Random(seed)
    result = TournamentResult(
        mode="indefinite",
        payoffs=payoffs,
        continuation_probability=continuation_probability,
    )
    for a, b in _pairings(pool, include_self_play):
        for _ in range(trials):
            result.matches.append(
                play_indefinite_match(a, b, continuation_probability, payoffs, rng)
            )
    return result


def sweep_continuation_probability(
    probabilities: list[float],
    payoffs: PayoffMatrix = STANDARD,
    trials: int = 2000,
    seed: int | None = 20260811,
) -> list[dict[str, float]]:
    """Empirically verify the shadow-of-the-future threshold.

    For each `p`, pit both always_cooperate and always_defect against
    tit_for_tat (a grim/TFT-like conditional opponent, which is the setting
    Straffin's derivation assumes) and record mean score per match.

    Theory says the two curves cross at p = (T - R) / (T - U):

    * cooperating forever earns  R / (1 - p)
    * defecting from round one earns  T + U * p / (1 - p)

    The returned rows carry both the simulated and closed-form values so the
    plot can show them on top of each other.
    """
    from .strategies import get  # local import keeps module import order simple

    tft = get("tit_for_tat")
    coop = get("always_cooperate")
    defect = get("always_defect")

    rows = []
    for p in probabilities:
        rng = random.Random(seed)
        coop_scores = [
            play_indefinite_match(coop, tft, p, payoffs, rng).score_a
            for _ in range(trials)
        ]
        defect_scores = [
            play_indefinite_match(defect, tft, p, payoffs, rng).score_a
            for _ in range(trials)
        ]
        rows.append(
            {
                "p": p,
                "cooperate_simulated": sum(coop_scores) / len(coop_scores),
                "defect_simulated": sum(defect_scores) / len(defect_scores),
                "cooperate_theory": payoffs.R / (1 - p),
                "defect_theory": payoffs.T + payoffs.U * p / (1 - p),
            }
        )
    return rows
