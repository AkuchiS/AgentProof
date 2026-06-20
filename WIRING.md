# WIRING — honesty ledger

A "governance" product is only as honest as its claim about how much of the
governance is actually *running*. Here is the plain, checkable truth.

> **Two separate claims, kept separate on purpose:**
> 1. **Buyer-verifiable (you can prove this yourself):** all four modules pass their own
>    selftests on *your* machine — that is exactly what `make verify` / `python3 verify.py`
>    runs and prints (19/19 · 22/22 · all-passed · 23/23, exit 0). Trust here is a
>    reproducible exit code, not our word.
> 2. **DIME's own internal usage (disclosed in good faith, not shippable for you to grep):**
>    **3 of the 4 modules are wired into live DIME systems today — all advisory / non-blocking —
>    and 1 is runnable-but-unwired.** You take this part on disclosure; we state it precisely
>    rather than implying "all four are live."

## Status table (DIME's internal usage, as of 2026-06-19)

| Module | Wired into a live DIME system? | Where / how | Mode |
|---|---|---|---|
| `dime_autonomy_gate.py` | **YES** | `dime_yt_pipeline.py` FEED stage (the level-7 intel loop) | **Advisory** — guarded `try/except` import; returns `DEFER` on new builds (human-review first), fails safe to `ESCALATE`. |
| `dime_build_discipline.py` | **YES** | orchestrator `product_build.py` — `BUILD_PROMPT` appended to the build brief + `over_ceiling` lint on built code | **Advisory** — defensive import; if absent the build path is unchanged. |
| `dime_model_fitness.py` | **YES** | orchestrator `engines.py` → `sovereignty_report()` → `model_sovereignty.py` | **Advisory** — read-only governance; it reports each lane's sovereignty, it never changes routing (a lane change stays a human gate). |
| `aegis_codereview.py` | **No** | — | **Runnable-but-unwired.** Passes 23/23; the step-5 SKU is staged, no live caller yet (CVE check is a labeled stub pending a pip-audit/grype wire). |

## How to check it

- **The selftests — verify these yourself, in the product you received:**
  ```
  make verify        # or: python3 verify.py
  ```
  This runs each module as a subprocess and prints its real pass count + a combined exit code. No network, stdlib only.

- **The internal wiring — auditable against DIME's own two source trees (not shipped in this copy):**
  ```
  # intel pipeline tree:   grep "import dime_autonomy_gate" dime_yt_pipeline.py      -> hit (advisory, try/except)
  # orchestrator tree:     grep "dime_build_discipline" product_build.py             -> hit (brief + lint)
  #                        grep "model_sovereignty\|dime_model_fitness" engines.py   -> hit (sovereignty_report, advisory)
  #                        grep "import aegis_codereview" <orchestrator>             -> none (staged)
  ```
  Observed: `dime_autonomy_gate`, `dime_build_discipline`, `dime_model_fitness` each have a live advisory caller; `aegis_codereview` has none.

## Why we ship it this way

"3 wired (advisory) + 1 staged" is the honest state, so that is what we print. The part that **earns** your
trust is the part you can reproduce: every module passes its own selftest on your machine (`verify.py`). Whether a
module is *also* threaded into one of DIME's running pipelines is a separate, internal fact — disclosed here, not
implied. Claiming all four were "wired live" would re-trigger the exact optimistic-status over-claim this product
was restructured to avoid, and over-claiming on a trust product is more toxic than a modest true claim.
