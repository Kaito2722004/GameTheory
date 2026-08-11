"""CLI entry point for the Prisoner's Dilemma tournament.

    python run_tournament.py all                  # everything, with figures
    python run_tournament.py one-shot
    python run_tournament.py iterated --rounds 200
    python run_tournament.py indefinite --p 0.9 --trials 100
    python run_tournament.py sweep                # verify the shadow threshold
    python run_tournament.py math                 # Ch. 11-12 checks only
"""

import argparse
import sys

from pd_tournament import analysis, engine, strategies
from pd_tournament.payoffs import PayoffMatrix


def _pool(names: list[str] | None) -> list[strategies.StrategyInfo]:
    if not names:
        return strategies.default_pool()
    return [strategies.get(n) for n in names]


def _print_ranking(result: engine.TournamentResult) -> None:
    rows = analysis.ranking_table(result)
    width = max(len(r["name"]) for r in rows)
    print(
        f"  {'#':>2}  {'strategy':<{width}}  {'total':>9}  {'per round':>9}  "
        f"{'coop':>6}  properties"
    )
    for r in rows:
        print(
            f"  {r['rank']:>2}  {r['name']:<{width}}  {r['total']:>9.1f}  "
            f"{r['per_round']:>9.3f}  {r['cooperation_rate']:>6.1%}  {r['properties']}"
        )


def _heading(text: str) -> None:
    print(f"\n{text}\n{'=' * len(text)}")


def cmd_math(args, payoffs: PayoffMatrix) -> None:
    _heading("Ch. 11-12 checks")
    print(analysis.summary(payoffs))


def cmd_one_shot(args, payoffs: PayoffMatrix) -> engine.TournamentResult:
    _heading("One-shot round robin")
    result = engine.one_shot_round_robin(_pool(args.strategies), payoffs)
    _print_ranking(result)
    print(
        "\n  With no future to protect, D strictly dominates: any strategy that\n"
        "  opens with C is simply exploited. Cooperation losing here is the\n"
        "  theory working, not a bug."
    )
    return result


def cmd_iterated(args, payoffs: PayoffMatrix) -> engine.TournamentResult:
    _heading(f"Iterated round robin ({args.rounds} rounds per pairing)")
    strategies.seed(args.seed)
    result = engine.iterated_round_robin(_pool(args.strategies), args.rounds, payoffs)
    _print_ranking(result)
    print()
    for line in analysis.explain_ranking(result):
        print(f"  {line}")
    return result


def cmd_indefinite(args, payoffs: PayoffMatrix) -> engine.TournamentResult:
    _heading(
        f"Indefinite-horizon round robin (p={args.p}, {args.trials} trials per pairing)"
    )
    strategies.seed(args.seed)
    result = engine.indefinite_round_robin(
        _pool(args.strategies), args.p, args.trials, payoffs, seed=args.seed
    )
    _print_ranking(result)
    print(
        f"\n  Expected match length 1/(1-p) = {1 / (1 - args.p):.1f} rounds.\n"
        f"  Compare per-round scores here, not totals: matches differ in length."
    )
    return result


def cmd_sweep(args, payoffs: PayoffMatrix) -> list[dict[str, float]]:
    _heading("Shadow of the future: sweeping the continuation probability")
    probabilities = [i / 20 for i in range(1, 20)]  # 0.05 .. 0.95
    strategies.seed(args.seed)
    rows = engine.sweep_continuation_probability(
        probabilities, payoffs, trials=args.trials, seed=args.seed
    )
    print(f"  {'p':>5}  {'coop sim':>9}  {'coop thy':>9}  {'defect sim':>10}  {'defect thy':>10}")
    for r in rows:
        print(
            f"  {r['p']:>5.2f}  {r['cooperate_simulated']:>9.2f}  "
            f"{r['cooperate_theory']:>9.2f}  {r['defect_simulated']:>10.2f}  "
            f"{r['defect_theory']:>10.2f}"
        )
    print()
    print(analysis.shadow_of_the_future(payoffs, rows))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "mode",
        choices=["all", "math", "one-shot", "iterated", "indefinite", "sweep"],
        help="which part of the project to run",
    )
    parser.add_argument("--strategies", nargs="*", help="subset of the pool to use")
    parser.add_argument("--rounds", type=int, default=200, help="rounds per iterated match")
    parser.add_argument("--p", type=float, default=0.9, help="continuation probability")
    parser.add_argument("--trials", type=int, default=100, help="repeats per stochastic pairing")
    parser.add_argument("--seed", type=int, default=20260811, help="RNG seed")
    parser.add_argument("--payoffs", nargs=4, type=float, metavar=("T", "R", "U", "S"),
                        help="override the payoffs (default 5 3 1 0)")
    parser.add_argument("--figures", action="store_true", help="also write PNGs to figures/")
    args = parser.parse_args(argv)

    payoffs = PayoffMatrix(*args.payoffs) if args.payoffs else PayoffMatrix()

    figures = []
    iterated_result = None
    sweep_rows = None

    if args.mode in ("all", "math"):
        cmd_math(args, payoffs)
    if args.mode in ("all", "one-shot"):
        cmd_one_shot(args, payoffs)
    if args.mode in ("all", "iterated"):
        iterated_result = cmd_iterated(args, payoffs)
    if args.mode in ("all", "indefinite"):
        cmd_indefinite(args, payoffs)
    if args.mode in ("all", "sweep"):
        sweep_rows = cmd_sweep(args, payoffs)

    if args.figures or args.mode == "all":
        try:
            from pd_tournament import plots
        except ImportError:
            print("\n(matplotlib not installed -- skipping figures)", file=sys.stderr)
        else:
            _heading("Figures")
            figures.append(plots.plot_payoff_polygon(payoffs))
            if iterated_result is not None:
                figures.append(plots.plot_tournament(iterated_result))
            if sweep_rows is not None:
                figures.append(plots.plot_shadow_sweep(sweep_rows, payoffs))
            for path in figures:
                print(f"  wrote {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
