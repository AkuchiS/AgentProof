# METHODOLOGY

This is the written governance method **that the shipped modules implement**. It
is documentation *for* the runnable code in `modules/` — not standalone advice,
and not the thing being sold. If a sentence here describes a behavior, there is a
selftest case in the corresponding module that checks it (run `python3 verify.py`).

Source of the method: DIME's internal Decision & Communication Curriculum
(`DIME_DECISION_CURRICULUM.md`). Every rule below is traceable to a module file
and to a selftest assertion.

---

## 1. The pre-build KILL-GATE  → documented here, applied by hand

A scored rubric every candidate build / capital / compute commitment passes
**before** spend.

**Hard gates (auto-fail, no scoring):**

- **H1 · One-sentence explainability** — can the value prop be said in one plain
  sentence to a non-expert? Fail → auto-quarantine. (Same signal as "looks like a
  scam/hack": opacity flags a bad pitch *and* a bad bet.)
- **H2 · Supplier-is-competitor + non-positive unit margin** — a thin wrapper
  reselling a model whose vendor ships a competing product, where marginal output
  fails to clear marginal inference cost → kill-or-restructure.
- **H3 · Hostile upstream-platform dependency** — sits on a platform that can
  throttle/ban it → auto-kill.

**Scored axes (0–2 each):** unfair advantage / always-true-vs-fad / compounding /
structural-dependency positioning / usage-not-signups validation / analogical
positioning anchor / differentiation quality / real-bottleneck-named / 50% barbell
fit / defensibility vs frontier labs. Sum → `BUILD · RESTRUCTURE · REUSE/BUY · KILL`.

> **Note:** the kill-gate is a *rubric you apply by judgment*; it is documented,
> not shipped as one of the four runnable modules. The runnable modules are the
> three operational gates below + the codereview. Do not read this section as
> "there is a kill-gate selftest" — there is not. (Honesty boundary.)

---

## 2. Autonomy gate + goal-vs-task verifier  → `modules/dime_autonomy_gate.py`  (selftest 19/19)

Before any irreversible/external action, score
`{reversibility, cost_of_failure, process_maturity, requirement_stability}` →
`AUTO | ESCALATE | DEFER`.

- **Hard human-approval allowlist:** outbound email/DM, social posting, any
  payment/Stripe, secret/API-key handling, anything legally binding → always
  ESCALATE. *(Selftest cases 1–5 check each allowlist trigger.)*
- **Goal ≠ task:** every build carries an explicit win-condition + a verifier
  that confirms the GOAL, blocking "claimed done at 80%." *(Selftest `verify:*`
  cases check missing / unmet / present-and-met win conditions.)*

What the code actually enforces is what the selftest prints: **19/19**.

---

## 3. Build discipline — the laziness ladder  → `modules/dime_build_discipline.py`  (selftest 22/22)

Steer agent code generation away from over-engineering by preferring, in order:
**skip > stdlib > native feature > one-liner > minimal new code.** The module:

- emits a prompt that names every rung of the ladder and the `# CEILING:`
  convention *(selftest checks each rung + the convention is present)*;
- flags any diff whose added-line count exceeds the budget **without** a named
  `# CEILING: <n> lines — <why>` justification comment *(selftest checks
  over-ceiling, at-ceiling, one-over, justified-diff-not-over, header-not-counted)*.

This very product was built under that ladder — see the `# CEILING` marker in the
module-runner choice (we run modules as subprocesses rather than importing them, to
keep `verify.py` honest about exit codes). What the code enforces is what the
selftest prints: **22/22**.

---

## 4. Model-fitness scorecard + sovereignty gate  → `modules/dime_model_fitness.py`  (selftest: all passed)

Per candidate model: a fixed in-house battery (scratch-build · env-from-zero ·
deep-research+tables · visual job · long agentic-coding run) scored on
`{one-shot rate, follow-ups-to-fix, error rate, $/task, cache-hit %, self-verifies}`,
plus a **sovereignty gate**: reject impermissive license, closed weights, on-prem
infeasible (e.g. a 753B-param model is not local-runnable at 4-bit), or fewer than
two independent benchmark boards. Promote only on fitness ≥ 60 **AND** sovereignty
pass. The selftest exercises a strong candidate (promotes), a weak one (does not),
and the sovereignty rejections. Output: **all passed**.

---

## 5. Agent-diff codereview  → `modules/aegis_codereview.py`  (selftest 23/23)

Extends AEGIS Scan to agent-generated diffs. Flags:

- **dep-added** — a newly-introduced dependency (`import`, `from … import`,
  `require(...)`, a `package.json` dep entry) → triggers an advisory CVE check
  *(the CVE lookup is stubbed `unknown` offline by design; detection is real)*;
- **silent bugs a type-checker misses** — `INSERT/UPDATE/DELETE.execute()` with no
  `.commit()`; a function that builds a result then `return None`; wrong-arity reuse
  of a shape-helper; a clear/reset handler that slices the view but never clears the
  backing store.

Risk = `high` iff any silent-bug, else `med` iff a dep was added, else `low`. What
the code enforces is what the selftest prints: **23/23**.

---

## Allocation & communication (doctrine, not shipped code)

- **50% barbell:** reserve ~half of allocatable compute/capital for low-risk
  maintenance; deploy the rest into higher-variance bets; never zero the reserve.
- **Communication voice:** lead with the caveat not the hype; ignore astroturf
  ("DM me for the playbook" = noise); open with a category anchor; lead venture
  commentary with unit economics; show real demo failures, not hidden ones.

These are judgment doctrines documented for completeness; they are **not** among the
four runnable modules and carry no selftest. They are included so the method is
whole, not to be re-sold as standalone advice.

---

### Traceability summary

| Method section | Runnable module | Proof |
|---|---|---|
| Autonomy gate + goal verifier | `dime_autonomy_gate.py` | selftest **19/19** |
| Laziness ladder / build discipline | `dime_build_discipline.py` | selftest **22/22** |
| Model fitness + sovereignty | `dime_model_fitness.py` | selftest **all passed** |
| Agent-diff codereview | `aegis_codereview.py` | selftest **23/23** |
| Kill-gate rubric | *(documented, applied by judgment)* | no selftest — stated honestly |
| Allocation / communication | *(doctrine)* | no selftest — stated honestly |
