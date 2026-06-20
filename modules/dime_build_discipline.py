#!/usr/bin/env python3
"""STAGED step-4 BUILD-DISCIPLINE — laziness ladder for the build sub-agent.

Adopted from Bitwise/Ponytail. Steers the build stage away from over-engineering:
the cheapest rung that satisfies the requirement wins. Pairs with the autonomy
gate — less new code means smaller blast radius and easier review.

  - BUILD_PROMPT: the laziness-ladder system prompt handed to the build sub-agent.
    Preference order, cheapest first: (1) skip if unneeded, (2) stdlib, (3) a
    native/existing feature, (4) a one-liner, (5) minimal new code. Plus the
    named-ceiling convention: when you cut scope, leave a marker comment
    "# CEILING: <n> lines — <why>" so reviewers see the budget was deliberate.
  - over_ceiling(diff_text, ceiling): counts added lines (a "+" prefix, excluding
    the "+++" file header) and flags over=True only when the add count exceeds the
    ceiling AND no "CEILING:" justification comment is present in the diff.

Stdlib-only, no box wiring (later gated step). Self-test: `python3 dime_build_discipline.py`.
"""

BUILD_PROMPT = """\
You are the DIME build sub-agent. Write the LEAST code that satisfies the
requirement. Climb the laziness ladder and stop at the first rung that works —
do not reach for a higher rung out of habit.

LAZINESS LADDER (prefer earlier rungs; only descend when the rung above cannot do it):
  1. SKIP — is this even needed? If the requirement is already met, or YAGNI,
     write nothing. The cheapest line is the one you don't add.
  2. STDLIB — solve it with the Python standard library. No third-party deps.
  3. NATIVE / EXISTING FEATURE — reuse a native language feature or something the
     codebase already provides. Do not reimplement what exists.
  4. ONE-LINER — if new code is truly needed, try to make it a single expression
     or line before writing a block.
  5. MINIMAL NEW CODE — only now write new code, and keep it the smallest correct
     unit. No speculative abstraction, no config knobs nobody asked for.

NAMED-CEILING CONVENTION:
  When you deliberately cut scope to stay small, leave a marker comment naming the
  budget and the reason, in exactly this form:
      # CEILING: <n> lines — <why>
  e.g.  # CEILING: 40 lines — single-file parser, no plugin system needed.
  This tells reviewers the size was a choice, not an oversight.

Default to less. If unsure between two designs, ship the smaller one.
"""


def over_ceiling(diff_text, ceiling):
    """Flag a diff that blows the line budget without a named-ceiling justification.

    diff_text: a unified-diff-style string. Added lines start with "+"; the
               "+++" file-header line is NOT counted as an added line.
    ceiling:   the agreed added-line budget (int).

    Returns {"over": bool, "added": int, "has_ceiling_comment": bool}.
    over is True iff added > ceiling AND no "CEILING:" comment is present — a
    justified cut (the marker comment) is allowed to exceed the soft budget.
    """
    added = 0
    has_ceiling_comment = False
    for line in (diff_text or "").splitlines():
        if line.startswith("+++"):          # file header, not an added line
            continue
        if line.startswith("+"):
            added += 1
            if "CEILING:" in line:          # marker lives inside an added comment
                has_ceiling_comment = True
        elif "CEILING:" in line:            # also honor markers on context lines
            has_ceiling_comment = True
    over = added > ceiling and not has_ceiling_comment
    return {"over": over, "added": added, "has_ceiling_comment": has_ceiling_comment}


# ---------------------------------------------------------------------------
def _selftest():
    """Return 0 on all-green, 1 on any failure. Prints a terse per-case trace."""
    fails = []
    ran = []

    def check(label, got, want):
        ran.append(label)
        ok = got == want
        print("  [%s] %-46s got=%-9s want=%s" % ("ok" if ok else "XX", label, got, want))
        if not ok:
            fails.append(label)

    # --- BUILD_PROMPT: non-empty, contains the full ladder + CEILING convention ---
    check("prompt: non-empty", bool(BUILD_PROMPT.strip()), True)
    low = BUILD_PROMPT.lower()
    check("prompt: rung skip", "skip" in low, True)
    check("prompt: rung stdlib", "stdlib" in low, True)
    check("prompt: rung native/existing", "native" in low and "existing" in low, True)
    check("prompt: rung one-liner", "one-liner" in low, True)
    check("prompt: rung minimal new code", "minimal new code" in low, True)
    check("prompt: names the ladder", "ladder" in low, True)
    check("prompt: CEILING convention present", "# CEILING: <n> lines — <why>" in BUILD_PROMPT, True)

    # --- over_ceiling: 200-line add, NO ceiling comment -> over=True ---
    big = "\n".join("+    line %d" % i for i in range(200))
    r = over_ceiling("+++ b/file.py\n" + big, 100)
    check("big diff added count", r["added"], 200)
    check("big diff has no ceiling", r["has_ceiling_comment"], False)
    check("big diff flagged over", r["over"], True)

    # --- over_ceiling: small 5-line add -> over=False ---
    small = "+++ b/file.py\n" + "\n".join("+    x = %d" % i for i in range(5))
    r = over_ceiling(small, 100)
    check("small diff added count", r["added"], 5)
    check("small diff not over", r["over"], False)

    # --- over_ceiling: 200-line add WITH a CEILING justification -> over=False ---
    just = ("+++ b/file.py\n"
            "+    # CEILING: 200 lines — generated table, hand-writing it is worse.\n"
            + "\n".join("+    row %d" % i for i in range(199)))
    r = over_ceiling(just, 100)
    check("justified diff added count", r["added"], 200)
    check("justified diff has ceiling", r["has_ceiling_comment"], True)
    check("justified diff NOT over", r["over"], False)

    # --- edge: "+++" header is not counted as an added line ---
    r = over_ceiling("+++ b/only_header.py", 0)
    check("header not counted as add", r["added"], 0)
    check("header alone not over", r["over"], False)

    # --- edge: exactly at ceiling is not over (strict >) ---
    at = "\n".join("+a" for _ in range(10))
    check("at-ceiling not over", over_ceiling(at, 10)["over"], False)
    check("one-over flagged", over_ceiling(at + "\n+a", 10)["over"], True)

    # --- edge: empty/None diff ---
    check("empty diff added", over_ceiling("", 100)["added"], 0)
    check("none diff not over", over_ceiling(None, 100)["over"], False)

    total = len(ran)  # count = checks actually run, never a hardcoded constant (the number is real, not asserted)
    print("\nSELFTEST: %s (%d/%d passed)" %
          ("PASS" if not fails else "FAIL: " + ", ".join(fails),
           total - len(fails), total))
    return 0 if not fails else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
