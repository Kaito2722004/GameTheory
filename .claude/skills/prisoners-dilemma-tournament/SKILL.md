---
name: prisoners-dilemma-tournament
description: Build an Axelrod-style Iterated Prisoner's Dilemma tournament project grounded in Straffin's "Game Theory and Strategy" Ch. 11-13 (Nash equilibria, Pareto optimality, the Prisoner's Dilemma, shadow of the future, and the Deutsch F-scale trust experiment). Use this whenever the user wants to write, code, or resume the "Prisoner's Dilemma tournament" project, wants a round-robin/iterated PD simulator, wants strategies like Tit-for-Tat/Grim Trigger/Always Defect scored against each other, wants to demonstrate Nash equilibria or Pareto optimality with a payoff matrix, or references the game-theory book project brief about "Ch. 11-13" or "the shadow of the future." Trigger even if they just say "let's build that PD tournament thing" or "continue the game theory project" without repeating the full brief.
---

# Prisoner's Dilemma Tournament Project

This skill packages everything needed to actually build the "Prisoner's
Dilemma Tournament (Axelrod-style, per Ch. 11-13)" project idea from
Philip D. Straffin's *Game Theory and Strategy*, so a future session can
go straight to building without re-reading or re-parsing the source PDF.

**Before writing any code, read
[`references/book-notes-ch11-13.md`](references/book-notes-ch11-13.md)
in full.** It contains the cleaned math, definitions, and citations from
the book's actual Chapters 11-13 (Nash Equilibria, The Prisoner's Dilemma,
and the Trust/F-Scale application). `references/raw-ocr-ch11-13.txt` is
the verbatim OCR backup if you need to check exact wording or find a quote
— prefer the notes file for everything else, since the raw OCR has garbled
characters in places.

## What "done" looks like

Unless the user says otherwise, build **all three** of these, in this
order — they build on each other and together they *are* the project:

1. **A working tournament simulator** (Python). This is the load-bearing
   deliverable — everything else explains and visualizes its output.
2. **A short written report** (Markdown or, if the user wants something
   presentable, an artifact/HTML page) that walks through the math using
   the simulator's actual output as evidence, not hypothetical numbers.
3. *(Optional, only if the user wants a classroom/live component)* a
   simple "submit your own strategy" interface and a live-demo mode.

If the user has already told you which of these they want (or picked one
in an earlier conversation), build only that — don't pad scope back in.

## Step 1 — The payoff structure

Use Straffin's general-form parameterization (Game 12.2), not an ad hoc
matrix. Define it as data so every strategy and every analysis function
reads from the same source of truth:

```python
T, R, U, S = 5, 3, 1, 0   # Temptation, Reward, (Un)cooperative/Punishment, Sucker
# conditions that MUST hold for this to be a valid Prisoner's Dilemma:
assert T > R > U > S
assert R > (S + T) / 2
```

`U` here is Straffin's label for mutual defection; most modern PD code and
literature calls it `P` (for "Punishment"). Either name is fine — just be
consistent and note the correspondence once in a comment, since the user
may cross-reference other PD material that uses P.

## Step 2 — Strategies to implement

Each strategy is a function of (own history, opponent's history) -> next
move. Implement at minimum, since these are the ones the book and the
Axelrod story actually discuss:

- `always_cooperate`, `always_defect`
- `tit_for_tat` — Rapoport's actual 4-line winner: cooperate first, then
  mirror the opponent's last move.
- `grim_trigger` — cooperate until the opponent ever defects once, then
  defect forever.
- `random_choice` — cooperate/defect with some fixed probability (a naive
  baseline).
- `tit_for_two_tats` — a forgiving variant: only retaliate after the
  opponent defects twice in a row. Useful for illustrating "forgiving."
- `pavlov` / win-stay-lose-shift — repeat last move if it earned R or T,
  switch if it earned S or U. Good optional extra; historically strong.

For each strategy, note in a docstring or comment which of Axelrod's four
properties (Nice / Retaliatory / Forgiving / Clear — see the notes file)
it does and doesn't have. That mapping is itself a piece of the analysis,
not just flavor text — it's what the write-up should use to *explain* the
tournament results rather than just report them.

If the project is meant to let real students/users submit strategies
(check with the user if unclear), keep the strategy interface dead simple
— a pure function taking two lists of past moves and returning `"C"` or
`"D"` — so a non-programmer's submission is a few lines.

## Step 3 — The tournament engine

Two distinct modes, both grounded in the book — don't collapse them into
one, since they demonstrate different things:

- **One-shot round robin**: every pair plays exactly once. This is the
  right mode for showing the static Nash-equilibrium result (mutual
  defection dominates, is the unique equilibrium, is Pareto-inferior to
  mutual cooperation) — it should NOT show cooperation winning, because
  one-shot PD's dominant strategy is always defect. If your one-shot
  results show cooperation paying off, something is wrong with the payoff
  matrix or scoring, not the theory.
- **Iterated round robin** (the actual Axelrod tournament format): every
  pair plays N rounds against each other (Axelrod used 200 in the real
  tournaments), scores accumulate, and strategies are ranked by total
  score across all opponents. This is where Tit-for-Tat should win or
  place near the top against a reasonably diverse strategy pool — if it
  doesn't, sanity-check the strategy pool (an all-nasty pool with no
  cooperators to reward TFT will make aggressive strategies look better,
  which is itself a fine thing to discuss in the write-up).
- **Indefinite-horizon variant** (optional but book-faithful and a strong
  addition): each round continues with probability `p`; stop the moment a
  simulated "coin flip" fails. Run many trials and average. Use this to
  empirically verify the shadow-of-the-future threshold
  `p_threshold = (T - R) / (T - U)` from the notes file — show cooperation
  rates/scores flip around that threshold as you sweep `p`.

Track and expose, per matchup and in aggregate: total score per strategy,
cooperation rate per strategy, and (for indefinite-horizon) score as a
function of `p`.

## Step 4 — The math the write-up must actually demonstrate

Don't just narrate these — compute them from the simulator's own data
structures:

1. **Nash equilibrium at DD**: write a small checker that, given the 2x2
   payoff matrix, verifies DD is the unique pure-strategy equilibrium
   (neither player can improve by unilateral deviation) and that D
   strictly dominates C for both players. This is a ~10 line function, not
   a library — the point is it should run against the actual `T,R,U,S`
   constants from Step 1, so it's a live check, not an assertion in prose.
2. **Pareto dominance of CC over DD**: check that both payoffs at CC
   exceed both payoffs at DD, and plot the payoff polygon (Rose's payoff
   on x, Colin's on y) as in the book's Figure 11.1, shading the Pareto
   frontier.
3. **Shadow of the future**: derive/print the threshold formula, then
   empirically sweep `p` in the indefinite-horizon mode and show the
   cooperate-forever expected payoff crossing the defect-first payoff at
   that threshold. This ties Ch. 12's algebra to a real plotted curve.
4. **Why Tit-for-Tat wins**: report cooperation rate and score by
   strategy, and explicitly connect the winners/losers back to the
   Nice/Retaliatory/Forgiving/Clear rubric — e.g. "always_defect scores
   well against suckers but craters against grim_trigger and other
   always_defect copies; tit_for_tat never loses by much because it is
   Nice+Retaliatory+Forgiving+Clear."

## Step 5 — Optional Ch. 13 extension (only if the user wants the social-psychology angle)

Deutsch's operational definitions (trust/suspicion/trustworthiness — see
notes file) map cleanly onto a **sequential** (not simultaneous) PD:
first player moves and it's revealed, second player responds. If the user
wants this angle, implement it as a distinct mode from the simultaneous
round robin (don't bolt it onto the Axelrod engine) — it is about a single
revealed-then-response pair, not iteration or scoring against a pool.
This is naturally a place to invite live participation (real choices from
real people) rather than pure simulation, if the user wants a
human-subject or classroom component. Preserve Deutsch's causal-direction
caveat if summarizing his F-scale finding — the notes file spells out why
that correlation is genuinely ambiguous, and quietly dropping the caveat
would misrepresent the book's own discussion of it.

## Suggested project layout

```
Game-Theory/
├── pd_tournament/
│   ├── payoffs.py        # T,R,U,S constants + validity assertions
│   ├── strategies.py      # each strategy as a small pure function
│   ├── engine.py          # round-robin, iterated, indefinite-horizon runners
│   ├── analysis.py        # Nash/Pareto checks, threshold calc, aggregation
│   └── plots.py           # payoff polygon, tournament bar chart, p-sweep curve
├── run_tournament.py       # CLI entry point: pick strategies, mode, N, p
├── report.md (or report artifact)  # write-up citing book chapters + simulator output
└── tests/                  # sanity checks: one-shot never rewards cooperation,
                             # TFT beats a nasty-but-not-universally-defecting pool, etc.
```

Keep it this flat — this is a personal study project, not a package meant
for distribution. Don't add packaging, CI, or config-file layers the user
didn't ask for.

## When invoked

1. Confirm scope only if genuinely unclear (e.g. "just the simulator, or
   the write-up too?") — otherwise default to the simulator + report
   combo described above and proceed.
2. Scaffold the layout above, implement Steps 1-4 first (they're the
   spine), run the tournament, sanity-check results against the
   "what done looks like" notes in Step 3 (one-shot never rewards
   cooperation; TFT does well in the iterated version).
3. Only then write the report, using the simulator's real output — plots
   and numbers, not invented ones — as the evidence for each math claim
   in Step 4.
4. If the user wants the Ch. 13 extension, treat it as an add-on after the
   core tournament works, per Step 5.
