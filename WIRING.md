# WIRING — honesty ledger

A "governance" product is only as honest as its claim about how much of the
governance is actually *running*. Here is the plain, checkable truth.

> **Two separate claims, kept separate on purpose:**
> 1. **Buyer-verifiable (you can prove this yourself):** all four modules pass their own
>    selftests on *your* machine — that is exactly what `make verify` / `python3 verify.py`
>    runs and prints (19/19 · 22/22 · all-passed · 23/23, exit 0). Trust here is a
>    reproducible exit code, not our word.
> 2. **Our own internal usage (disclosed in good faith, not shippable for you to grep):**
>    **3 of the 4 modules are wired into our live systems today — all advisory / non-blocking —
>    and 1 is runnable-but-unwired.** You take this part on disclosure; we state it precisely
>    rather than implying "all four are live."

## Status table (our internal usage)

| Module | Wired into a live system? | Role | Mode |
|---|---|---|---|
| `autonomy_gate.py` | **YES** | Gates new builds in our intel/build loop | **Advisory** — guarded `try/except` import; returns `DEFER` on new builds (human-review first), fails safe to `ESCALATE`. |
| `build_discipline.py` | **YES** | Appended to the build brief + lints built code for over-ceiling diffs | **Advisory** — defensive import; if absent the build path is unchanged. |
| `model_fitness.py` | **YES** | Reports each lane's model sovereignty before promotion | **Advisory** — read-only governance; it reports, it never changes routing (a lane change stays a human gate). |
| `aegis_codereview.py` | **No** | — | **Runnable-but-unwired.** Passes 23/23; staged, no live caller yet (CVE check is a labeled stub pending a pip-audit/grype wire). |

## How to check it

- **The selftests — verify these yourself, in the product you received:**
  ```
  make verify        # or: python3 verify.py
  ```
  This runs each module as a subprocess and prints its real pass count + a combined exit code. No network, stdlib only. **This is the part that earns your trust — because you can reproduce it.**

- **The internal wiring** is a separate, internal fact. We don't ship our private
  pipelines in this copy, so this part is **disclosure, not something you can grep here**:
  three of the four modules each have a live *advisory* caller in our own systems
  (`autonomy_gate`, `build_discipline`, `model_fitness`); `aegis_codereview` is staged
  with no live caller. We state it this way rather than implying all four are live.

## Why we ship it this way

"3 wired (advisory) + 1 staged" is the honest state, so that is what we print. The part that **earns** your
trust is the part you can reproduce: every module passes its own selftest on your machine (`verify.py`). Whether a
module is *also* threaded into one of our running pipelines is a separate, internal fact — disclosed here, not
implied. Claiming all four were "wired live" would re-trigger the exact optimistic-status over-claim this product
was restructured to avoid, and over-claiming on a trust product is more toxic than a modest true claim.
