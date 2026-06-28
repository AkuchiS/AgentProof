#!/usr/bin/env python3
"""STAGED step-4 AUTONOMY-GATE — risk-gated autonomy (adopted from Eric Michaud).

SAFETY-CRITICAL. Sits in front of the selfop spine: every candidate action is
classified AUTO / ESCALATE / DEFER before it can run unattended.

  - A HARD ALLOWLIST (outbound email/DM, social post, payment/Stripe, secret/
    API-key handling, anything legally binding) ALWAYS forces ESCALATE — the
    risk score cannot promote these to AUTO. Mirrors the selfop AMBER/RED bands.
  - Otherwise a 4-axis score (reversibility, cost_of_failure/blast-radius,
    process_maturity, requirement_stability; each 0-2) decides:
        AUTO     iff reversible AND low-cost AND matured-once AND stable reqs
        ESCALATE iff high blast-radius OR irreversible
        DEFER    iff neither AUTO nor ESCALATE — run manual-then-assisted first.
  - goal_vs_task.verify() blocks "done-at-80%": a task is only complete with an
    explicit win_condition that is actually met.

Stdlib-only, no box wiring (later gated step). Self-test: `python3 autonomy_gate.py`.
"""
import re

AUTO, ESCALATE, DEFER = "AUTO", "ESCALATE", "DEFER"

# kinds that ALWAYS require a human, regardless of score (substring/word match, case-insensitive)
_ALLOWLIST = (
    r"e[\-\s]?mail", r"\bdm\b", r"direct[\-\s]?message",
    r"social[\-\s]?post", r"\bpost\b", r"\btweet\b", r"publish",
    r"payment", r"stripe", r"charge", r"refund", r"payout", r"invoice",
    r"secret", r"api[\-\s]?key", r"token", r"credential", r"password",
    r"legal", r"binding", r"contract", r"sign",
)
_ALLOWLIST_RE = re.compile("|".join(_ALLOWLIST), re.I)


def _is_allowlisted(kind):
    """True iff the action kind names a human-approval-required category."""
    return bool(_ALLOWLIST_RE.search(kind or ""))


def _axis(action, name, default=0):
    """Read an optional 0-2 risk axis, clamped; missing/garbage -> worst-case `default`."""
    try:
        v = int(action.get(name, default))
    except (TypeError, ValueError):
        return default
    return 0 if v < 0 else 2 if v > 2 else v


def classify(action):
    """Risk-gate one candidate action -> {"decision": AUTO|ESCALATE|DEFER, "reason": str}.

    action: {"kind": str, optional ints 0-2: reversibility, cost_of_failure,
             process_maturity, requirement_stability}. Missing axes default to
             worst-case (0) so absence of evidence never promotes to AUTO.
    """
    kind = (action.get("kind") or "").strip()

    # 1. HARD ALLOWLIST overrides the score — always escalate to a human.
    if _is_allowlisted(kind):
        return {"decision": ESCALATE, "reason": "allowlisted kind requires human approval: %r" % kind}

    rev = _axis(action, "reversibility")          # 2 reversible .. 0 irreversible
    cost = _axis(action, "cost_of_failure")        # 0 low blast-radius .. 2 high
    mat = _axis(action, "process_maturity")        # 0 never done .. 2 routine
    stab = _axis(action, "requirement_stability")  # 0 churning .. 2 stable

    # 2. ESCALATE on the dangerous edges: irreversible OR high blast-radius.
    if cost >= 2:
        return {"decision": ESCALATE, "reason": "high cost_of_failure (blast radius >= 2)"}
    if rev == 0:
        return {"decision": ESCALATE, "reason": "irreversible action (reversibility == 0)"}

    # 3. AUTO only when ALL safety conditions hold.
    if rev >= 2 and cost <= 1 and mat >= 1 and stab >= 1:
        return {"decision": AUTO, "reason": "reversible, low-cost, matured-once, stable requirements"}

    # 4. Otherwise DEFER — not yet AUTO, not dangerous enough to ESCALATE.
    #    Includes the cost-low-but-immature case: run manual-then-assisted first.
    why = []
    if mat == 0:
        why.append("process not yet done manually (maturity == 0)")
    if rev < 2:
        why.append("only partially reversible (reversibility == 1)")
    if stab == 0:
        why.append("unstable requirements")
    reason = "defer: " + ("; ".join(why) if why else "preconditions for AUTO unmet") + \
             " — run manual-then-assisted first"
    return {"decision": DEFER, "reason": reason}


def verify(task):
    """goal_vs_task: True ONLY if an explicit win_condition is present AND met.

    Blocks "claimed done" / done-at-80%: a bare completion claim without a met,
    explicit win-condition does not pass.
    """
    if not isinstance(task, dict):
        return False
    if "win_condition" not in task:
        return False
    wc = task.get("win_condition")
    if wc is None or (isinstance(wc, str) and not wc.strip()):
        return False
    return task.get("win_condition_met") is True


# ---------------------------------------------------------------------------
def _selftest():
    """Return 0 on all-green, 1 on any failure. Prints a terse per-case trace."""
    fails = []
    ran = []

    def check(label, got, want):
        ran.append(label)
        ok = got == want
        print("  [%s] %-44s got=%-9s want=%s" % ("ok" if ok else "XX", label, got, want))
        if not ok:
            fails.append(label)

    # --- classify: allowlist overrides score (even a perfectly safe-looking score) ---
    safe_score = {"reversibility": 2, "cost_of_failure": 0, "process_maturity": 2, "requirement_stability": 2}
    check("allowlist: outbound email",
          classify(dict(safe_score, kind="send outbound email to lead"))["decision"], ESCALATE)
    check("allowlist: social post",
          classify(dict(safe_score, kind="social post to X"))["decision"], ESCALATE)
    check("allowlist: stripe payment",
          classify(dict(safe_score, kind="issue Stripe refund"))["decision"], ESCALATE)
    check("allowlist: api-key handling",
          classify(dict(safe_score, kind="rotate API-key"))["decision"], ESCALATE)
    check("allowlist: legally binding",
          classify(dict(safe_score, kind="sign binding contract"))["decision"], ESCALATE)

    # --- AUTO: reversible + low + mature + stable, non-allowlisted kind ---
    check("auto: reversible/low/mature/stable",
          classify({"kind": "rebuild local cache", "reversibility": 2, "cost_of_failure": 1,
                    "process_maturity": 1, "requirement_stability": 1})["decision"], AUTO)
    check("auto: all axes maxed",
          classify({"kind": "regenerate report", "reversibility": 2, "cost_of_failure": 0,
                    "process_maturity": 2, "requirement_stability": 2})["decision"], AUTO)

    # --- ESCALATE: irreversible ---
    check("escalate: irreversible",
          classify({"kind": "delete prod data", "reversibility": 0, "cost_of_failure": 1,
                    "process_maturity": 2, "requirement_stability": 2})["decision"], ESCALATE)
    # --- ESCALATE: high blast-radius (takes precedence) ---
    check("escalate: high cost_of_failure",
          classify({"kind": "migrate schema", "reversibility": 2, "cost_of_failure": 2,
                    "process_maturity": 2, "requirement_stability": 2})["decision"], ESCALATE)

    # --- DEFER: cost-low-but-immature (never done manually) ---
    check("defer: low-cost but immature",
          classify({"kind": "auto-tune ranker", "reversibility": 2, "cost_of_failure": 1,
                    "process_maturity": 0, "requirement_stability": 2})["decision"], DEFER)
    # --- DEFER: partially reversible, low cost, otherwise fine (not AUTO, not dangerous) ---
    check("defer: partially reversible",
          classify({"kind": "tweak config", "reversibility": 1, "cost_of_failure": 1,
                    "process_maturity": 2, "requirement_stability": 2})["decision"], DEFER)
    # --- DEFER: unstable requirements ---
    check("defer: unstable requirements",
          classify({"kind": "build feature", "reversibility": 2, "cost_of_failure": 1,
                    "process_maturity": 2, "requirement_stability": 0})["decision"], DEFER)

    # --- missing axes default to worst-case -> never AUTO ---
    check("missing axes -> not AUTO",
          classify({"kind": "mystery op"})["decision"] != AUTO, True)

    # --- verify: blocks done-at-80%, passes a met explicit win-condition ---
    check("verify: missing win_condition",
          verify({"status": "claimed done"}), False)
    check("verify: win_condition present but unmet",
          verify({"win_condition": "all tests green", "win_condition_met": False}), False)
    check("verify: win_condition present, not asserted met",
          verify({"win_condition": "all tests green"}), False)
    check("verify: empty win_condition",
          verify({"win_condition": "  ", "win_condition_met": True}), False)
    check("verify: present AND met -> pass",
          verify({"win_condition": "all tests green", "win_condition_met": True}), True)
    check("verify: non-dict",
          verify("done"), False)

    total = len(ran)  # count = checks actually run, never a hardcoded constant (the number is real, not asserted)
    print("\nSELFTEST: %s (%d/%d passed)" %
          ("PASS" if not fails else "FAIL: " + ", ".join(fails),
           total - len(fails), total))
    return 0 if not fails else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
