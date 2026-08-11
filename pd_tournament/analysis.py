"""Live checks of the Ch. 11-12 mathematics.

Nothing here asserts a result in prose: every function computes its answer
from the actual `PayoffMatrix` constants or from a `TournamentResult`, so if
the payoffs are changed the checks re-derive rather than go stale.
"""

from dataclasses import dataclass

from .payoffs import COOPERATE, DEFECT, MOVES, PayoffMatrix, STANDARD
from .engine import TournamentResult
from .strategies import REGISTRY


# --------------------------------------------------------------------------
# Ch. 11: dominance, Nash equilibrium, Pareto optimality
# --------------------------------------------------------------------------


@dataclass
class DominanceReport:
    dominant_move: str | None
    strict: bool
    comparisons: list[tuple[str, float, float]]  # (opponent move, D payoff, C payoff)

    def __str__(self) -> str:
        lines = [
            f"  vs opponent {opp}: D pays {d}, C pays {c} -> "
            f"{'D better' if d > c else 'C better' if c > d else 'tie'}"
            for opp, d, c in self.comparisons
        ]
        verdict = (
            f"{self.dominant_move} strictly dominates"
            if self.dominant_move and self.strict
            else "no strictly dominant move"
        )
        return "\n".join(lines + [f"  => {verdict}"])


def dominance(payoffs: PayoffMatrix = STANDARD) -> DominanceReport:
    """Does one move beat the other no matter what the opponent does?

    The game is symmetric, so checking one player suffices.
    """
    comparisons = [
        (opp, payoffs.payoff(DEFECT, opp), payoffs.payoff(COOPERATE, opp))
        for opp in MOVES
    ]
    if all(d > c for _, d, c in comparisons):
        return DominanceReport(DEFECT, True, comparisons)
    if all(c > d for _, d, c in comparisons):
        return DominanceReport(COOPERATE, True, comparisons)
    return DominanceReport(None, False, comparisons)


def pure_nash_equilibria(
    payoffs: PayoffMatrix = STANDARD,
) -> list[tuple[str, str]]:
    """Every pure-strategy Nash equilibrium, by unilateral-deviation check.

    An outcome is an equilibrium when neither player can raise their own
    payoff by changing their move alone.
    """
    equilibria = []
    for rose in MOVES:
        for colin in MOVES:
            rose_pay = payoffs.payoff(rose, colin)
            colin_pay = payoffs.payoff(colin, rose)
            rose_can_improve = any(
                payoffs.payoff(alt, colin) > rose_pay for alt in MOVES if alt != rose
            )
            colin_can_improve = any(
                payoffs.payoff(alt, rose) > colin_pay for alt in MOVES if alt != colin
            )
            if not rose_can_improve and not colin_can_improve:
                equilibria.append((rose, colin))
    return equilibria


def pareto_optimal_outcomes(
    payoffs: PayoffMatrix = STANDARD,
) -> list[tuple[str, str]]:
    """The pure outcomes no other pure outcome Pareto-dominates.

    X dominates Y when X is at least as good for both players and strictly
    better for at least one.
    """
    outcomes = payoffs.outcomes()
    optimal = []
    for outcome, (a, b) in outcomes.items():
        dominated = any(
            (a2 >= a and b2 >= b) and (a2 > a or b2 > b)
            for other, (a2, b2) in outcomes.items()
            if other != outcome
        )
        if not dominated:
            optimal.append(outcome)
    return optimal


def pareto_dominates(
    better: tuple[str, str],
    worse: tuple[str, str],
    payoffs: PayoffMatrix = STANDARD,
) -> bool:
    """Does outcome `better` Pareto-dominate outcome `worse`?"""
    outcomes = payoffs.outcomes()
    a1, b1 = outcomes[better]
    a2, b2 = outcomes[worse]
    return (a1 >= a2 and b1 >= b2) and (a1 > a2 or b1 > b2)


def _convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Andrew's monotone chain hull, counter-clockwise."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[tuple[float, float]] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[tuple[float, float]] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def payoff_polygon(payoffs: PayoffMatrix = STANDARD) -> list[tuple[float, float]]:
    """Vertices of the payoff polygon (Rose's payoff on x, Colin's on y).

    This is the book's Figure 11.1: the four pure outcomes, and the convex
    hull of them is the set of payoffs reachable by joint randomisation.
    """
    return _convex_hull(list(payoffs.outcomes().values()))


def payoff_polygon_frontier(
    payoffs: PayoffMatrix = STANDARD,
) -> list[tuple[float, float]]:
    """The polygon's Pareto (north-east) boundary, left to right.

    These are the hull vertices no other hull vertex dominates -- the points
    the book describes as the "northeast" edge of the polygon.
    """
    hull = payoff_polygon(payoffs)
    frontier = [
        p
        for p in hull
        if not any(
            (q[0] >= p[0] and q[1] >= p[1]) and (q[0] > p[0] or q[1] > p[1])
            for q in hull
            if q != p
        )
    ]
    return sorted(frontier)


# --------------------------------------------------------------------------
# Ch. 12: the shadow of the future
# --------------------------------------------------------------------------


@dataclass
class ShadowReport:
    threshold: float
    formula: str
    crossing_simulated: float | None

    def __str__(self) -> str:
        line = f"  threshold p-bar = {self.formula} = {self.threshold:.4f}"
        if self.crossing_simulated is not None:
            line += f"\n  simulated crossing at p ~ {self.crossing_simulated:.4f}"
        return line


def shadow_of_the_future(
    payoffs: PayoffMatrix = STANDARD,
    sweep_rows: list[dict[str, float]] | None = None,
) -> ShadowReport:
    """The closed-form threshold, optionally matched against a simulated sweep.

    If `sweep_rows` from `engine.sweep_continuation_probability` are supplied,
    the empirical crossing point (where cooperating overtakes defecting) is
    located by linear interpolation between the bracketing samples.
    """
    threshold = payoffs.shadow_threshold()
    formula = f"(T - R) / (T - U) = ({payoffs.T} - {payoffs.R}) / ({payoffs.T} - {payoffs.U})"

    crossing = None
    if sweep_rows:
        rows = sorted(sweep_rows, key=lambda r: r["p"])
        for prev, cur in zip(rows, rows[1:]):
            before = prev["cooperate_simulated"] - prev["defect_simulated"]
            after = cur["cooperate_simulated"] - cur["defect_simulated"]
            if before <= 0 < after:
                span = after - before
                crossing = (
                    prev["p"] + (cur["p"] - prev["p"]) * (-before / span)
                    if span
                    else cur["p"]
                )
                break
    return ShadowReport(threshold, formula, crossing)


# --------------------------------------------------------------------------
# Tournament aggregation and the Nice/Retaliatory/Forgiving/Clear rubric
# --------------------------------------------------------------------------


def ranking_table(result: TournamentResult) -> list[dict[str, object]]:
    """Rows of (rank, name, total, per-round, cooperation rate, properties)."""
    totals = result.total_scores()
    per_round = result.average_scores()
    coop = result.cooperation_rates()
    rows = []
    for rank, (name, total) in enumerate(result.ranking(), start=1):
        info = REGISTRY.get(name)
        rows.append(
            {
                "rank": rank,
                "name": name,
                "total": total,
                "per_round": per_round.get(name, 0.0),
                "cooperation_rate": coop.get(name, 0.0),
                "properties": info.properties() if info else "unknown",
                "property_count": info.property_count if info else 0,
            }
        )
    return rows


def explain_ranking(result: TournamentResult) -> list[str]:
    """Connect the finishing order back to Axelrod's four properties.

    Everything here is derived from the tournament's own numbers -- the
    per-opponent breakdown is read off `head_to_head`, not assumed.
    """
    rows = ranking_table(result)
    if not rows:
        return ["no matches were played"]

    lines = []
    nice_rows = [r for r in rows if REGISTRY.get(r["name"]) and REGISTRY[r["name"]].nice]
    nasty_rows = [r for r in rows if r not in nice_rows]
    if nice_rows and nasty_rows:
        nice_avg = sum(r["per_round"] for r in nice_rows) / len(nice_rows)
        nasty_avg = sum(r["per_round"] for r in nasty_rows) / len(nasty_rows)
        lines.append(
            f"Nice strategies averaged {nice_avg:.3f} per round; "
            f"strategies that defect first averaged {nasty_avg:.3f}. "
            + (
                "Being nice paid."
                if nice_avg > nasty_avg
                else "Being nice did not pay in this pool."
            )
        )

    winner = rows[0]
    lines.append(
        f"Winner: {winner['name']} ({winner['total']:.0f} total, "
        f"{winner['per_round']:.3f}/round, cooperated "
        f"{winner['cooperation_rate']:.1%} of the time) -- "
        f"properties: {winner['properties']}."
    )

    h2h = result.head_to_head()
    for focus in ("always_defect", "tit_for_tat"):
        scores = {
            (b if a == focus else a): (sa if a == focus else sb)
            for (a, b), (sa, sb) in h2h.items()
            if focus in (a, b)
        }
        if not scores:
            continue
        best = max(scores.items(), key=lambda kv: kv[1])
        worst = min(scores.items(), key=lambda kv: kv[1])
        lines.append(
            f"{focus}: best haul against {best[0]} ({best[1]:.0f}), "
            f"worst against {worst[0]} ({worst[1]:.0f})."
        )

    return lines


def summary(payoffs: PayoffMatrix = STANDARD) -> str:
    """A printable block of every Ch. 11-12 check, computed live."""
    eq = pure_nash_equilibria(payoffs)
    pareto = pareto_optimal_outcomes(payoffs)
    dom = dominance(payoffs)
    lines = [
        f"Payoffs: T={payoffs.T} R={payoffs.R} U={payoffs.U} S={payoffs.S}",
        f"  valid PD: T>R>U>S and R>(S+T)/2 = {(payoffs.S + payoffs.T) / 2}",
        "",
        "Dominance (Ch. 11):",
        str(dom),
        "",
        f"Pure Nash equilibria: {['/'.join(e) for e in eq]}",
        f"Pareto optimal outcomes: {['/'.join(p) for p in pareto]}",
        f"  CC Pareto-dominates DD: "
        f"{pareto_dominates((COOPERATE, COOPERATE), (DEFECT, DEFECT), payoffs)}",
        f"  equilibrium DD is Pareto optimal: {(DEFECT, DEFECT) in pareto}",
        "",
        "Shadow of the future (Ch. 12):",
        str(shadow_of_the_future(payoffs)),
    ]
    return "\n".join(lines)
