"""Sanity checks for the simulator.

Plain asserts, no test framework, so this runs with a bare interpreter:

    python tests/test_tournament.py

Each check encodes something the book says must be true; if one fails, the
simulator disagrees with Ch. 11-12 and the results should not be trusted.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pd_tournament import analysis, engine, strategies  # noqa: E402
from pd_tournament.payoffs import COOPERATE, DEFECT, PayoffMatrix, STANDARD  # noqa: E402

CHECKS = []


def check(fn):
    CHECKS.append(fn)
    return fn


# --- payoff structure -------------------------------------------------------


@check
def test_payoff_lookup():
    p = STANDARD
    assert p.payoff(COOPERATE, COOPERATE) == p.R
    assert p.payoff(COOPERATE, DEFECT) == p.S
    assert p.payoff(DEFECT, COOPERATE) == p.T
    assert p.payoff(DEFECT, DEFECT) == p.U
    assert p.both_payoffs(DEFECT, COOPERATE) == (p.T, p.S)
    assert p.P == p.U


@check
def test_invalid_payoffs_rejected():
    for bad in [
        dict(T=3, R=5, U=1, S=0),  # violates T > R
        dict(T=5, R=2, U=1, S=0),  # violates R > (S+T)/2 = 2.5
    ]:
        try:
            PayoffMatrix(**bad)
        except ValueError:
            continue
        raise AssertionError(f"should have rejected {bad}")


# --- Ch. 11: dominance, Nash, Pareto ---------------------------------------


@check
def test_defect_strictly_dominates():
    report = analysis.dominance(STANDARD)
    assert report.dominant_move == DEFECT and report.strict


@check
def test_dd_is_the_unique_equilibrium():
    assert analysis.pure_nash_equilibria(STANDARD) == [(DEFECT, DEFECT)]


@check
def test_equilibrium_is_pareto_inferior():
    pareto = analysis.pareto_optimal_outcomes(STANDARD)
    assert (DEFECT, DEFECT) not in pareto, "DD must not be Pareto optimal"
    assert (COOPERATE, COOPERATE) in pareto
    assert analysis.pareto_dominates((COOPERATE, COOPERATE), (DEFECT, DEFECT), STANDARD)


@check
def test_frontier_excludes_the_equilibrium():
    frontier = analysis.payoff_polygon_frontier(STANDARD)
    assert (STANDARD.U, STANDARD.U) not in frontier
    assert (STANDARD.R, STANDARD.R) in frontier


# --- strategy behaviour -----------------------------------------------------


@check
def test_tit_for_tat_opens_nice_then_mirrors():
    assert strategies.tit_for_tat([], []) == COOPERATE
    assert strategies.tit_for_tat([COOPERATE], [DEFECT]) == DEFECT
    assert strategies.tit_for_tat([DEFECT], [COOPERATE]) == COOPERATE


@check
def test_grim_never_forgives():
    assert strategies.grim_trigger([COOPERATE], [DEFECT]) == DEFECT
    long_history = [DEFECT] + [COOPERATE] * 50
    assert strategies.grim_trigger([COOPERATE] * 51, long_history) == DEFECT


@check
def test_tit_for_two_tats_needs_two_defections():
    assert strategies.tit_for_two_tats([COOPERATE], [DEFECT]) == COOPERATE
    assert strategies.tit_for_two_tats([COOPERATE] * 2, [DEFECT, DEFECT]) == DEFECT
    assert strategies.tit_for_two_tats([COOPERATE] * 2, [DEFECT, COOPERATE]) == COOPERATE


@check
def test_pavlov_wins_stays_loses_shifts():
    # opponent cooperated -> my move earned R or T -> repeat it
    assert strategies.pavlov([COOPERATE], [COOPERATE]) == COOPERATE
    assert strategies.pavlov([DEFECT], [COOPERATE]) == DEFECT
    # opponent defected -> I earned S or U -> switch
    assert strategies.pavlov([COOPERATE], [DEFECT]) == DEFECT
    assert strategies.pavlov([DEFECT], [DEFECT]) == COOPERATE


# --- engine -----------------------------------------------------------------


@check
def test_moves_are_simultaneous():
    """A strategy must not be able to see the current round's opposing move."""
    seen = []

    def spy(mine, theirs):
        seen.append((len(mine), len(theirs)))
        return COOPERATE

    spy_info = strategies.StrategyInfo("spy", spy, True, False, False, True)
    engine.play_match(spy_info, strategies.get("always_defect"), rounds=5)
    assert seen == [(i, i) for i in range(5)], seen


@check
def test_mutual_cooperation_scores_r_per_round():
    coop = strategies.get("always_cooperate")
    m = engine.play_match(coop, coop, rounds=10)
    assert m.score_a == m.score_b == 10 * STANDARD.R
    assert m.cooperation_rate("a") == 1.0


@check
def test_exploitation_scores_t_and_s():
    m = engine.play_match(
        strategies.get("always_defect"), strategies.get("always_cooperate"), rounds=10
    )
    assert m.score_a == 10 * STANDARD.T
    assert m.score_b == 10 * STANDARD.S


@check
def test_one_shot_never_rewards_cooperation():
    """The book's hard constraint: in one-shot play, defecting must win."""
    result = engine.one_shot_round_robin()
    scores = result.total_scores()
    top = max(scores.values())
    assert scores["always_defect"] == top, scores
    assert scores["always_defect"] > scores["always_cooperate"]
    # No nice strategy may out-earn always_defect in a single round.
    for info in strategies.default_pool():
        if info.nice:
            assert scores[info.name] <= scores["always_defect"], info.name


@check
def test_tit_for_tat_does_well_when_iterated():
    strategies.seed(20260811)
    result = engine.iterated_round_robin(rounds=200)
    ranking = [name for name, _ in result.ranking()]
    assert "tit_for_tat" in ranking[:3], ranking
    assert ranking.index("tit_for_tat") < ranking.index("always_defect"), ranking


@check
def test_tit_for_tat_never_beats_an_opponent_head_to_head():
    """TFT can never out-score an opponent in a direct match -- it never
    defects first, so the most it can do is draw. Its tournament win comes
    from doing well *overall*, not from winning matches."""
    strategies.seed(20260811)
    tft = strategies.get("tit_for_tat")
    for opponent in strategies.default_pool():
        m = engine.play_match(tft, opponent, rounds=200)
        assert m.score_a <= m.score_b + 1e-9, (opponent.name, m.score_a, m.score_b)


@check
def test_indefinite_matches_have_random_lengths():
    result = engine.indefinite_round_robin(continuation_probability=0.9, trials=30)
    lengths = {m.rounds for m in result.matches}
    assert len(lengths) > 1, "every match came out the same length"
    assert min(lengths) >= 1


# --- Ch. 12: the shadow of the future ---------------------------------------


@check
def test_threshold_matches_closed_form():
    assert abs(STANDARD.shadow_threshold() - 0.5) < 1e-12  # (5-3)/(5-1)
    assert abs(PayoffMatrix(T=1, R=0, U=-1, S=-2).shadow_threshold() - 0.5) < 1e-12


@check
def test_simulated_crossing_matches_the_threshold():
    """The empirical crossing must land on (T - R) / (T - U)."""
    probabilities = [i / 20 for i in range(1, 20)]
    rows = engine.sweep_continuation_probability(probabilities, trials=400)
    report = analysis.shadow_of_the_future(STANDARD, rows)
    assert report.crossing_simulated is not None, "curves never crossed"
    assert abs(report.crossing_simulated - report.threshold) < 0.05, report


@check
def test_theory_curves_cross_exactly_at_the_threshold():
    p = STANDARD.shadow_threshold()
    cooperate = STANDARD.R / (1 - p)
    defect = STANDARD.T + STANDARD.U * p / (1 - p)
    assert abs(cooperate - defect) < 1e-9, (cooperate, defect)


def main() -> int:
    failures = []
    for fn in CHECKS:
        try:
            fn()
        except AssertionError as exc:
            failures.append((fn.__name__, exc))
            print(f"FAIL  {fn.__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failures.append((fn.__name__, exc))
            print(f"ERROR {fn.__name__}: {type(exc).__name__}: {exc}")
        else:
            print(f"ok    {fn.__name__}")
    print(f"\n{len(CHECKS) - len(failures)}/{len(CHECKS)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
