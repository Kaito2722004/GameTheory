"""Payoff structure for the Prisoner's Dilemma.

Straffin's general form (Game 12.2), with C = cooperate, D = defect:

              Colin C     Colin D
    Rose C    (R, R)      (S, T)
    Rose D    (T, S)      (U, U)

Note on naming: `U` is Straffin's label for the mutual-defection payoff
("uncooperative"). Most later PD literature and code calls this `P`
("punishment"). This project uses Straffin's `U` throughout to match the
book; `PayoffMatrix.P` is provided as a read-only alias so cross-referencing
other PD material stays painless.
"""

from dataclasses import dataclass

COOPERATE = "C"
DEFECT = "D"
MOVES = (COOPERATE, DEFECT)


@dataclass(frozen=True)
class PayoffMatrix:
    """The four PD payoffs, validated on construction.

    Both conditions come from the notes on Ch. 12:

    * ``T > R > U > S`` makes D strictly dominant for both players, so the
      unique equilibrium is DD -- which is Pareto-inferior to CC.
    * ``R > (S + T) / 2`` makes CC Pareto optimal: steady mutual cooperation
      must beat alternating exploitation (CD, DC, CD, ...) on average.
      Without it the game is not a Prisoner's Dilemma.
    """

    T: int | float = 5  # Temptation: defect while the opponent cooperates
    R: int | float = 3  # Reward: mutual cooperation
    U: int | float = 1  # Uncooperative: mutual defection (a.k.a. P)
    S: int | float = 0  # Sucker: cooperate while the opponent defects

    def __post_init__(self) -> None:
        if not self.T > self.R > self.U > self.S:
            raise ValueError(
                f"PD requires T > R > U > S, got "
                f"T={self.T}, R={self.R}, U={self.U}, S={self.S}"
            )
        if not self.R > (self.S + self.T) / 2:
            raise ValueError(
                f"PD requires R > (S + T) / 2, got R={self.R} and "
                f"(S + T) / 2 = {(self.S + self.T) / 2}. Without this, "
                f"alternating exploitation beats mutual cooperation."
            )

    @property
    def P(self) -> int | float:
        """Alias for `U`, for readers coming from non-Straffin PD sources."""
        return self.U

    def payoff(self, my_move: str, their_move: str) -> int | float:
        """My payoff when I play `my_move` and my opponent plays `their_move`."""
        if my_move not in MOVES or their_move not in MOVES:
            raise ValueError(
                f"moves must be {COOPERATE!r} or {DEFECT!r}, "
                f"got {my_move!r} and {their_move!r}"
            )
        if my_move == COOPERATE:
            return self.R if their_move == COOPERATE else self.S
        return self.T if their_move == COOPERATE else self.U

    def both_payoffs(self, move_a: str, move_b: str) -> tuple[float, float]:
        """(payoff to A, payoff to B) for one simultaneous round."""
        return self.payoff(move_a, move_b), self.payoff(move_b, move_a)

    def outcomes(self) -> dict[tuple[str, str], tuple[float, float]]:
        """All four outcomes keyed by (Rose's move, Colin's move)."""
        return {
            (a, b): self.both_payoffs(a, b) for a in MOVES for b in MOVES
        }

    def shadow_threshold(self) -> float:
        """Straffin's shadow-of-the-future threshold, p-bar = (T - R) / (T - U).

        Against an opponent playing a grim/TFT-like conditional strategy,
        cooperating forever beats defecting when the continuation probability
        `p` exceeds this value. Derivation in the Ch. 12 notes; verified
        empirically by `engine.sweep_continuation_probability`.
        """
        return (self.T - self.R) / (self.T - self.U)


#: The classic Axelrod tournament numbers, and this project's default.
#: Check: T(5) > R(3) > U(1) > S(0), and R(3) > (S + T) / 2 = 2.5.
STANDARD = PayoffMatrix(T=5, R=3, U=1, S=0)
