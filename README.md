# AgentProof

[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-8A2BE2)](https://github.com/sponsors/AkuchiS)
[![License](https://img.shields.io/github/license/AkuchiS/agentproof?color=8A2BE2)](LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/AkuchiS/agentproof?color=8A2BE2)](https://github.com/AkuchiS/agentproof/commits)
[![Stars](https://img.shields.io/github/stars/AkuchiS/agentproof?color=8A2BE2)](https://github.com/AkuchiS/agentproof/stargazers)

**Verifiable AI-build governance you run on yourself.** Four governance modules —
an autonomy gate, build discipline, model fitness, and agent-diff code review —
that **prove themselves with one offline command**, where every claim prints its
own pass count. Not advice. Not a PDF. A runnable artifact whose trust mechanism is
a reproducible exit code on *your* machine.

```bash
git clone https://github.com/AkuchiS/agentproof.git
cd agentproof
python3 verify.py        # or: make verify
```

## What you should see

Running `python3 verify.py` on a clean machine (no install, no network):

```
================================================================
AgentProof -- verify.py
Running the REAL selftests on THIS machine. No network. Stdlib only.
python: 3.10.12
================================================================
  [PASS] autonomy gate      autonomy_gate.py  -> 19/19 (exit=0)
  [PASS] build discipline   build_discipline.py  -> 22/22 (exit=0)
  [PASS] model fitness      model_fitness.py  -> all passed (exit=0)
  [PASS] aegis codereview   aegis_codereview.py  -> 23/23 (exit=0)
================================================================
RESULT: PASS  (every governance module passed its own selftest)
================================================================
```

The pass counts above are printed by the modules themselves, not asserted by
this README. If your numbers differ, **trust your machine, not this file.** Your
exit code is the product.

## What's in the box

Four real governance modules — the same governance files we run internally — plus
a single verifier.

| File | What it does | Its own selftest |
|---|---|---|
| `modules/autonomy_gate.py` | Scores an action `AUTO / ESCALATE / DEFER` on 4 axes (reversibility, cost-of-failure, process-maturity, requirement-stability) + a hard allowlist (email/DM/payment/secrets/legal are always ESCALATE) + a goal-vs-task win-condition verifier that blocks "done at 80%". | **19/19** |
| `modules/build_discipline.py` | The laziness ladder: steers agent code generation toward *skip > stdlib > native feature > one-liner > minimal code*, and flags any diff over a line budget that lacks a named `# CEILING:` justification. | **22/22** |
| `modules/model_fitness.py` | Scores a candidate model against 5 fixed in-house tasks on 6 normalized columns, plus a sovereignty gate (license / open-weights / on-prem-feasible / ≥2 independent benchmark boards). Promotes only on fitness ≥ 60 AND sovereignty pass. | **all passed** |
| `modules/aegis_codereview.py` | Reviews agent-generated diffs for (a) newly-added dependencies and (b) silent bugs a type-checker misses — e.g. `INSERT/UPDATE/DELETE.execute()` with no `.commit()`, build-then-`return None`, wrong-arity helper reuse, view-cleared-but-backing-store-not. | **23/23** |
| `verify.py` | Runs all four selftests as subprocesses, parses the real pass counts, prints a combined `PASS/FAIL` and exit code. **This is the trust mechanism.** | — |

## Install / usage

There is nothing to install.

- **Requirement:** Python 3 (developed on 3.10; uses only the standard library —
  `re`, `json`, `sys`, `subprocess`, `os`). No pip, no venv, no internet.
- **Run everything:** `python3 verify.py`
- **Run via make (if you have it):** `make verify`
- **Run the raw, unaggregated selftests:** `make selftests`, or directly
  `python3 modules/autonomy_gate.py` (each module is its own runnable selftest).

> **Note on `make`:** `make verify` and `make selftests` are convenience wrappers.
> If `make` is not on your machine, `python3 verify.py` is the universal
> entrypoint and does exactly the same thing. The Makefile recipe body *is*
> `python3 verify.py`.

## Limits (read these)

- **These are governance modules, not a turnkey platform.** They classify,
  score, and flag. Wiring them into *your* pipeline (calling the gate before an
  action, running the codereview on *your* diffs) is your integration work. See
  `WIRING.md` for exactly how much of this is wired into our own live systems
  today — the honest answer is **3 of 4 (all advisory), 1 staged**.
- **`aegis_codereview` ships with a stubbed CVE check** (`check_cve` returns
  `unknown` offline by design) so the core stays network-free. Dependency
  *detection* is real; CVE *lookup* is left to you / AEGIS Scan.
- **No revenue, results, or P&L claims appear anywhere in this product.** The
  only numbers we publish are integers a selftest on your own machine prints.

## Part of the Proof family

AgentProof is one of AkuchiS's open trust artifacts — tools whose credibility comes
from running, not asserting. Its sibling **AEGIS Guard** is our open input/output
safety guard for AI agents, public and runnable:
<https://github.com/AkuchiS/aegis-guard>. Clone it, run its selftest, see the
numbers yourself. The same "a tool that runs beats prose that asserts" rule that
governs this repo governs that one. See the rest of the toolkit at
**[github.akuchis.com](https://github.akuchis.com)**.

## Files

- `README.md` — this file
- `verify.py` — the one-command verifier (the trust mechanism)
- `Makefile` — `make verify` / `make selftests` wrappers
- `modules/` — the 4 governance modules, copied in verbatim with selftests intact
- `RECEIPTS.md` — every claim mapped to the exact command + integer that proves it
- `METHODOLOGY.md` — the kill-gate rubric + written method, as docs *for* the code
- `WIRING.md` — the honesty ledger: which modules are wired live vs runnable-but-unwired

---

<sub>An [AkuchiS](https://github.com/AkuchiS) tool · MIT · part of the Proof family →
[github.akuchis.com](https://github.com/AkuchiS) · [Sponsor the work](https://github.com/sponsors/AkuchiS)</sub>
