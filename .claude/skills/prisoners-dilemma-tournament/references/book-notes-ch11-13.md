# Straffin, *Game Theory and Strategy* — Notes on Ch. 11–13

Source: *Game Theory and Strategy* by Philip D. Straffin (MAA New Mathematical
Library, Vol. 36, 1993). Extracted from the user's local PDF, PDF pages 77–96
(book pages 65–84). Raw OCR text of these pages is in `raw-ocr-ch11-13.txt` in
this same folder for verbatim lookup — use these notes for the cleaned-up
math and content instead of re-parsing the PDF.

This is the grounding material for the "Prisoner's Dilemma Tournament"
project. Read this file fully before building anything.

## Chapter 11 — Nash Equilibria and Non-Cooperative Solutions

- Two-person non-zero-sum games: payoffs to both players must be written
  (not just one, as in zero-sum games).
- **Dominance Principle** still applies: if one strategy gives a player a
  better payoff no matter what the opponent does, the player should use it.
- **Equilibrium outcome** (non-zero-sum analogue of a saddle point): an
  outcome from which neither player can unilaterally improve their payoff.
  Nash (1950) proved every two-person game has at least one equilibrium in
  pure or mixed strategies — hence **Nash equilibrium**.
- Problems with using Nash equilibrium as *the* solution concept:
  1. A game can have **multiple non-equivalent, non-interchangeable**
     equilibria (Game 11.3: one favors Rose, one favors Colin; if each
     player goes for their favorite, they land on a third, worse outcome).
  2. A **unique** equilibrium can still be **non-Pareto-optimal** (Game
     11.4 — this is literally an ordinal Prisoner's Dilemma, and the book
     says "we will return to it in Chapter 12").
- **Pareto optimality** (Vilfredo Pareto, ~1900): an outcome is
  *Pareto optimal* if no other outcome gives both players a higher payoff
  (or one player the same and the other higher). **Pareto Principle**: an
  acceptable solution should be Pareto optimal. This directly conflicts
  with the Dominance Principle in games like 11.4 / Prisoner's Dilemma —
  that conflict is the whole point of the chapter.
- **Prudential strategy**: a player's optimal (minimax) strategy in "their
  own game" (ignoring the opponent's payoffs) — guarantees at least their
  **security level**. **Counter-prudential strategy**: the best response to
  the opponent's prudential strategy. Playing prudentially and
  counter-prudentially do *not* generally form an equilibrium and are not
  generally Pareto optimal — cautious play, which worked for zero-sum
  games, fails to produce stability here.
- **Solvable in the Strict Sense (SSS)**: a game is SSS if (i) at least one
  equilibrium is Pareto optimal, and (ii) if there are several Pareto
  optimal equilibria, they're all equivalent and interchangeable. Only for
  SSS games can the book give an unambiguous prescription.
- Payoffs can be plotted on a **payoff polygon** (Rose's payoff on the
  x-axis, Colin's on the y-axis); Pareto optimal outcomes are exactly the
  points on the "northeast" boundary.

## Chapter 12 — The Prisoner's Dilemma

- Origin: Melvin Dresher and Merrill Flood, RAND Corporation, 1950. Story
  attributed to Albert W. Tucker (told at a Stanford seminar).
- **Original game (Game 12.1)**, A = "don't confess", B = "confess":

  |          | Colin A     | Colin B      |
  |----------|-------------|--------------|
  | Rose A   | (0, 0)      | (-2, 1)      |
  | Rose B   | (1, -2)     | (-1, -1)     |

  B (confess/defect) dominates A for both players → unique equilibrium at
  BB, payoff (-1,-1) — but both would do better at AA, payoff (0,0). This
  is ordinally the same game as Game 11.4.

- **General form (Game 12.2)** — the canonical parameterization to use in
  code, with C = cooperate, D = defect:

  |          | Colin C   | Colin D   |
  |----------|-----------|-----------|
  | Rose C   | (R, R)    | (S, T)    |
  | Rose D   | (T, S)    | (U, U)    |

  - T = **T**emptation payoff (defect while opponent cooperates)
  - R = **R**eward for mutual cooperation
  - U = **U**ncooperative payoff (mutual defection) — Straffin's own label;
    most later literature calls this **P** (punishment)
  - S = **S**ucker payoff (cooperate while opponent defects)
  - **Conditions**: `T > R > U > S` and `R > (S + T) / 2`
    - `T > R > U > S` makes D strictly dominant for both players → unique
      equilibrium at DD, which is Pareto-inferior to CC.
    - `R > (S+T)/2` ensures CC is Pareto optimal — mutual cooperation
      beats alternating exploitation (CD/DC) on average.
  - Classic tournament numbers matching this (and matching the "3/3, 0/5,
    5/0, 1/1" scheme from the project brief): R=3, S=0, T=5, U(P)=1.
    Check: T(5) > R(3) > U(1) > S(0) ✓, and R(3) > (S+T)/2 = 2.5 ✓.
  - Citation: [Rapoport and Chammah, 1970].

- **Repeated play in theory — backward induction ("domino") argument**:
  if there are exactly N known plays, both players know D dominates on
  play N (no future to protect), so DD happens on N. That makes play N-1
  effectively "the last play," so DD happens there too, and so on back to
  play 1. **Finite, known-length repetition cannot rescue cooperation by
  pure backward-induction logic.**

- **Shadow of the future**: if instead the game continues after each round
  with probability `p` (0 < p < 1) — i.e., an *indefinite* horizon — the
  domino argument has no last play to anchor on. Straffin derives (assume
  the opponent plays Tit-for-Tat-like: cooperates until you first defect,
  then defects forever):
  - Payoff from cooperating forever: `R / (1-p)` (geometric series).
  - Payoff from defecting first on round `m`: a geometric-series sum ending
    in perpetual mutual defection payoff, algebraically reduces to
    comparing `R/(1-p)` against a one-shot-defection payoff mixed with
    `U/(1-p)`.
  - The conclusion: **always cooperate is better than ever defecting iff**

    ```
    p > (T - R) / (T - U)
    ```

    (Straffin writes it as `p̄ = (T-R)/(T-U)`, the *threshold* continuation
    probability.) For Game 12.1 (R=0,S=-2,T=1,U=-1): threshold =
    `(1-0)/(1-(-1)) = 1/2`. For Game 11.4 (their numbers: R=5,S=0,T ratio
    per book text "the threshold is (5-3)/(5-0) = 2/5"): reflects the same
    formula with that game's payoffs.
  - **This is the formal "shadow of the future" result**: if the
    probability of the game continuing is high enough, mutual cooperation
    can be sustained as a Nash equilibrium of the repeated (indefinite
    horizon) game, *given* the assumption the opponent is playing a
    grim/TFT-like conditional strategy. Note the reasoning is conditional
    on that assumption about the opponent — Straffin flags this as "less
    than completely convincing" but suggestive.
  - Formal citations: [Shubik, 1970], [Hill, 1975].

- **Metagame argument** (Nigel Howard, 1971): lets a player's strategy be
  contingent on a prediction of the opponent's strategy (assuming perfect
  mutual prediction). At the *second* level of this recursive contingency,
  a cooperative equilibrium emerges ("cooperate iff you believe your
  opponent will cooperate iff you do"). Straffin is explicit that he finds
  this unconvincing because of the implausible amount of mutual mind
  reading required — worth mentioning as a *rejected/limited* resolution
  if the project discusses "why is cooperation rational," not as the
  headline result.

- **Repeated play in practice — Axelrod's tournaments** (the core of what
  this project should recreate):
  - Robert Axelrod (reported in *Axelrod, 1984*) invited game theorists to
    submit computer programs to play round-robin **iterated** Prisoner's
    Dilemma against each other.
  - **Round 1**: 14 programs entered. Winner: **TIT FOR TAT**, submitted
    by Anatol Rapoport — a 4-line program:
    1. Start by choosing C (cooperate).
    2. Thereafter, do whatever your opponent did last round.
  - **Round 2**: 62 programs entered (many built specifically to beat TFT).
    Rapoport re-entered TIT FOR TAT unchanged. **It won again.**
  - Axelrod's analysis found the top-scoring programs tended to share four
    properties — **use these as the explicit rubric for the project's
    strategy commentary / write-up**:
    - **Nice** — starts by cooperating, never the first to defect.
    - **Retaliatory** — reliably punishes defection.
    - **Forgiving** — willing to cooperate again after retaliating.
    - **Clear** — its pattern of play is easy for opponents to read/predict.
  - Straffin's own framing: "It is tempting to speculate about the extent
    to which these four properties might characterize successful social
    behavior in competitive situations" — good line to riff on in a
    discussion section.

## Chapter 13 — Application to Social Psychology: Trust, Suspicion, and the F-Scale

- Background: Adorno et al., *The Authoritarian Personality* (1950)
  developed the **F-scale**, a personality inventory (items scored 1–7,
  "strongly disagree" to "strongly agree") measuring traits hypothesized to
  underlie susceptibility to authoritarianism (conventionalism,
  authoritarian submission/aggression, anti-introspection, superstition,
  power/toughness, destructiveness/cynicism, projection).
- **Morton Deutsch (1958, 1960)** used a *sequential* Prisoner's Dilemma to
  operationalize trust/suspicion/trustworthiness. Game used:

  |               | 2nd player A | 2nd player B |
  |---------------|--------------|--------------|
  | 1st player A  | (9, 9)       | (-10, 10)    |
  | 1st player B  | (0, 0)*      | (-10, -10)*  |

  (*book states if the first player chooses B the outcome is effectively
  -9/-9 regardless of the second player's move.) First player moves and
  announces; second player then responds knowing the first player's move.
  Each subject played once as first player, once as second, against
  different unknown partners.
- **Operational definitions** (directly reusable for a project rubric or
  survey component):
  - **Trust** = choosing A as first player.
  - **Suspicion** = choosing B as first player.
  - **Trustworthiness** = choosing A as second player *after* the first
    player chose A.
  - **Untrustworthiness** = choosing B as second player after the first
    player chose A.
- **Finding 1** — trust and trustworthiness are strongly correlated
  (contingency table, χ² = 24.7, p < .001): people play consistently
  across both roles, which Deutsch reads as **"do unto others as you
  expect them to do unto you"** rather than the Golden Rule.
- **Finding 2** — F-scale score (grouped low/medium/high) correlates with
  suspicious+untrustworthy play (χ² = 23.6, p < .005): higher F-scale
  scorers were more likely to be both suspicious and untrustworthy.
- **Interpretive caution** (important nuance to preserve, not just the
  headline correlation): Deutsch flags two competing explanations —
  (a) high F-scale = an incompletely-integrated superego/personality
  structure that produces suspicion (the original psychoanalytic reading),
  vs. (b) high F-scale scores are *themselves* downstream of learned
  experience with untrustworthy others (suspicion causes the trait
  measurement, not the reverse). **The game only reveals a behavioral
  correlate — it does not by itself settle causal direction.**
- Context for scale: ~200 PD experiments reported 1965–1973 (Rapoport
  estimate), ~1000 by 1982 (Coleman estimate) — PD is probably the single
  most-used paradigm in experimental social psychology of that era.

## How these three chapters fit together for the project

1. Ch. 11 supplies the vocabulary and proof obligations: Nash equilibrium,
   Pareto optimality, the Dominance vs. Pareto Principle conflict, and the
   SSS classification. A project should *show* PD's unique DD equilibrium
   is Pareto-dominated by CC using this exact apparatus, not just assert it.
2. Ch. 12 supplies (a) the exact payoff-condition definition of PD to
   parameterize any simulator, (b) the backward-induction reason finite
   PD "should" always defect, (c) the closed-form shadow-of-the-future
   threshold `p > (T-R)/(T-U)` for why *indefinitely* repeated PD can
   sustain cooperation, and (d) Axelrod's two real tournaments as the
   direct model for a round-robin simulator, plus the Nice/Retaliatory/
   Forgiving/Clear rubric for evaluating any submitted strategy.
3. Ch. 13 supplies an optional but book-faithful "why does this matter for
   people" extension: reframe trust/suspicion/trustworthiness as concrete,
   measurable PD choices, and (if desired) an actual mini-replication where
   participants' one-shot sequential-PD choices are compared against some
   personality/attitude proxy — with the causal-direction caveat intact.
