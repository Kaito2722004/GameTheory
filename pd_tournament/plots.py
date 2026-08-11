"""Figures: the payoff polygon, the tournament ranking, and the p-sweep.

Uses the non-interactive Agg backend so this runs headless. Every function
takes the same data structures the analysis functions return, so the plots
can never drift from the numbers in the report.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (must follow the backend call)

from .analysis import payoff_polygon, payoff_polygon_frontier, ranking_table
from .engine import TournamentResult
from .payoffs import PayoffMatrix, STANDARD

FIGURE_DIR = Path(__file__).resolve().parent.parent / "figures"


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_payoff_polygon(
    payoffs: PayoffMatrix = STANDARD, path: Path | None = None
) -> Path:
    """The book's Figure 11.1: Rose's payoff on x, Colin's on y.

    The four pure outcomes are labelled, the convex hull is the set of
    payoffs reachable by joint randomisation, and the north-east edge (the
    Pareto frontier) is drawn heavy. DD sits visibly inside and below CC.
    """
    fig, ax = plt.subplots(figsize=(6, 6))

    outcomes = payoffs.outcomes()
    hull = payoff_polygon(payoffs)
    frontier = payoff_polygon_frontier(payoffs)

    closed = hull + [hull[0]]
    ax.fill(
        [p[0] for p in closed],
        [p[1] for p in closed],
        alpha=0.12,
        color="tab:blue",
        label="payoff polygon",
    )
    ax.plot(
        [p[0] for p in frontier],
        [p[1] for p in frontier],
        color="tab:green",
        linewidth=3,
        label="Pareto frontier",
    )

    for (rose, colin), (x, y) in outcomes.items():
        equilibrium = rose == "D" and colin == "D"
        ax.scatter(
            [x],
            [y],
            s=110,
            zorder=3,
            color="tab:red" if equilibrium else "tab:blue",
        )
        label = f"{rose}{colin} ({x:g}, {y:g})"
        if equilibrium:
            label += "  <- Nash"
        ax.annotate(label, (x, y), textcoords="offset points", xytext=(8, 6))

    ax.set_xlabel("Rose's payoff")
    ax.set_ylabel("Colin's payoff")
    ax.set_title("Payoff polygon: the unique equilibrium is Pareto-inferior")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower left")
    return _save(fig, path or FIGURE_DIR / "payoff_polygon.png")


def plot_tournament(result: TournamentResult, path: Path | None = None) -> Path:
    """Score per round by strategy, coloured by how many Axelrod properties it has."""
    rows = ranking_table(result)
    names = [r["name"] for r in rows]
    scores = [r["per_round"] for r in rows]
    counts = [r["property_count"] for r in rows]

    fig, ax = plt.subplots(figsize=(9, 5))
    cmap = plt.get_cmap("viridis")
    bars = ax.bar(names, scores, color=[cmap(c / 4) for c in counts])
    for bar, row in zip(bars, rows):
        ax.annotate(
            f"{row['cooperation_rate']:.0%} C",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            textcoords="offset points",
            xytext=(0, 4),
            ha="center",
            fontsize=8,
        )

    mode = result.mode.replace("_", "-")
    detail = (
        f", {result.rounds_per_match} rounds"
        if result.rounds_per_match and result.rounds_per_match > 1
        else f", p={result.continuation_probability}"
        if result.continuation_probability is not None
        else ""
    )
    ax.set_ylabel("score per round")
    ax.set_title(
        f"{mode} round robin{detail}\n"
        "bar colour = number of Axelrod properties held; label = cooperation rate"
    )
    ax.tick_params(axis="x", rotation=30)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    ax.grid(axis="y", alpha=0.3)
    return _save(fig, path or FIGURE_DIR / f"tournament_{result.mode}.png")


def plot_shadow_sweep(
    rows: list[dict[str, float]],
    payoffs: PayoffMatrix = STANDARD,
    path: Path | None = None,
) -> Path:
    """Simulated and closed-form payoffs against TFT as `p` varies.

    The vertical line is the predicted threshold (T - R) / (T - U); the
    simulated curves should cross it there.
    """
    ps = [r["p"] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(ps, [r["cooperate_theory"] for r in rows], "--", color="tab:green",
            alpha=0.6, label="cooperate forever, theory  R/(1-p)")
    ax.plot(ps, [r["defect_theory"] for r in rows], "--", color="tab:red",
            alpha=0.6, label="defect first, theory  T + Up/(1-p)")
    ax.plot(ps, [r["cooperate_simulated"] for r in rows], "o-", color="tab:green",
            markersize=4, label="cooperate forever, simulated")
    ax.plot(ps, [r["defect_simulated"] for r in rows], "o-", color="tab:red",
            markersize=4, label="defect first, simulated")

    threshold = payoffs.shadow_threshold()
    ax.axvline(threshold, color="black", linestyle=":", linewidth=2)
    ax.annotate(
        f"predicted threshold\np = {threshold:.2f}",
        (threshold, ax.get_ylim()[1] * 0.55),
        textcoords="offset points",
        xytext=(8, 0),
        fontsize=9,
    )

    ax.set_xlabel("continuation probability p")
    ax.set_ylabel("expected total score vs tit_for_tat")
    ax.set_title("Shadow of the future: cooperation overtakes defection at (T-R)/(T-U)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    return _save(fig, path or FIGURE_DIR / "shadow_of_the_future.png")
