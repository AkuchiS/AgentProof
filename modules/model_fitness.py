#!/usr/bin/env python3
"""MODEL-FITNESS SCORECARD — step-4 adopt-decision for the AI Search loop.

Scores a candidate model against the 5 fixed in-house BATTERY tasks, then gates on
SOVEREIGNTY (permissive license + open weights + on-prem feasibility + >=2 independent
boards). promote() returns True only when the weighted fitness clears 60 AND the
sovereignty gate passes. STAGED — box-wiring is a later gated step. stdlib only.

on-prem heuristic: 4-bit weights cost ~params_billion*0.6 GB; the two A6000s expose
~21 GB free each (42 GB total), so a model fits when params_billion*0.6 <= 42.
"""
import json, sys

# The 5 fixed in-house tasks. weights sum to 1.0; tuned to what actually hurts us.
BATTERY = [
    {"id": "scratch_build",  "desc": "from-scratch / no-library build",        "weight": 0.25},
    {"id": "env_zero",       "desc": "env-setup-from-zero",                     "weight": 0.15},
    {"id": "deep_research",  "desc": "deep-research + tables",                  "weight": 0.20},
    {"id": "visual_gen",     "desc": "a visual-gen job",                        "weight": 0.15},
    {"id": "agentic_coding", "desc": "a long agentic-coding run",              "weight": 0.25},
]

# Column normalizers -> 0..1 (1 = best). Cost/error/follow-ups are lower-better.
USD_CEIL = 2.0          # usd_per_task >= this scores 0
FOLLOWUP_CEIL = 6       # follow_ups_to_fix >= this scores 0

# Per-column weights inside a single task's 0..1 sub-score (sum to 1.0).
_COL_W = {
    "one_shot_rate":     0.30,
    "follow_ups_to_fix": 0.15,
    "error_rate":        0.20,
    "usd_per_task":      0.15,
    "cache_hit_pct":     0.10,
    "self_verifies":     0.10,
}


def _clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def _task_subscore(col):
    """One task's columns -> 0..1. Missing columns default to the worst sensible value."""
    one_shot = _clamp(float(col.get("one_shot_rate", 0.0)))
    follow = max(0, int(col.get("follow_ups_to_fix", FOLLOWUP_CEIL)))
    err = _clamp(float(col.get("error_rate", 1.0)))
    usd = max(0.0, float(col.get("usd_per_task", USD_CEIL)))
    cache = _clamp(float(col.get("cache_hit_pct", 0.0)))
    verifies = 1.0 if col.get("self_verifies", False) else 0.0

    n_follow = 1.0 - _clamp(follow / FOLLOWUP_CEIL)        # lower follow-ups -> higher
    n_err = 1.0 - err                                      # lower error -> higher
    n_usd = 1.0 - _clamp(usd / USD_CEIL)                   # cheaper -> higher

    return (one_shot * _COL_W["one_shot_rate"]
            + n_follow * _COL_W["follow_ups_to_fix"]
            + n_err   * _COL_W["error_rate"]
            + n_usd   * _COL_W["usd_per_task"]
            + cache   * _COL_W["cache_hit_pct"]
            + verifies * _COL_W["self_verifies"])


def score(results):
    """results: {task_id -> column-dict}. -> weighted 0..100 fitness number.

    Battery weights are renormalized over the tasks actually present, so a partial
    run still yields a comparable 0..100 (and an empty run scores 0).
    """
    present = [t for t in BATTERY if t["id"] in results]
    wsum = sum(t["weight"] for t in present)
    if wsum <= 0:
        return 0.0
    acc = 0.0
    for t in present:
        acc += (t["weight"] / wsum) * _task_subscore(results[t["id"]])
    return round(acc * 100.0, 2)


def sovereignty_gate(meta):
    """meta: {license_permissive, open_weights, params_billion, independent_boards}.
    -> {"pass": bool, "reasons": [...]}. reasons lists every failed condition.
    """
    reasons = []
    if not meta.get("license_permissive", False):
        reasons.append("license not permissive")
    if not meta.get("open_weights", False):
        reasons.append("weights not open")
    pb = float(meta.get("params_billion", 0.0))
    if not (pb * 0.6 <= 42.0):                             # ~4-bit footprint vs 42 GB free across the A6000s
        reasons.append("on-prem infeasible: %.1fB needs ~%.1fGB at 4-bit > 42GB free" % (pb, pb * 0.6))
    boards = int(meta.get("independent_boards", 0))
    if boards < 2:
        reasons.append("independent_boards=%d < 2" % boards)
    return {"pass": len(reasons) == 0, "reasons": reasons}


def on_prem_feasible(params_billion):
    """True when a model's 4-bit weights fit the ~42 GB free across the two A6000s."""
    return float(params_billion) * 0.6 <= 42.0


def promote(results, meta):
    """Adopt iff weighted fitness >= 60 AND sovereignty_gate passes."""
    return score(results) >= 60.0 and sovereignty_gate(meta)["pass"]


# --------------------------------------------------------------------------- self-test
def _full_battery(col):
    """Apply one column-dict to all 5 tasks (synthetic convenience)."""
    return {t["id"]: dict(col) for t in BATTERY}


def _selftest():
    fails = []

    # 1) strong + cheap + open model: should PASS adopt.
    strong = _full_battery({"one_shot_rate": 0.9, "follow_ups_to_fix": 1, "error_rate": 0.05,
                            "usd_per_task": 0.2, "cache_hit_pct": 0.8, "self_verifies": True})
    strong_meta = {"license_permissive": True, "open_weights": True,
                   "params_billion": 32.0, "independent_boards": 3}
    s_score = score(strong)
    if s_score < 60.0:
        fails.append("strong model scored %.2f < 60" % s_score)
    if not sovereignty_gate(strong_meta)["pass"]:
        fails.append("strong model failed sovereignty gate: %r" % sovereignty_gate(strong_meta)["reasons"])
    if not promote(strong, strong_meta):
        fails.append("strong model not promoted")

    # 2) a 753B model FAILS on-prem feasibility (still great scores otherwise).
    huge_meta = {"license_permissive": True, "open_weights": True,
                 "params_billion": 753.0, "independent_boards": 3}
    g = sovereignty_gate(huge_meta)
    if g["pass"]:
        fails.append("753B model wrongly passed sovereignty gate")
    if not any("on-prem infeasible" in r for r in g["reasons"]):
        fails.append("753B failure reason missing on-prem note: %r" % g["reasons"])
    if on_prem_feasible(753.0):
        fails.append("on_prem_feasible(753) returned True")
    if promote(strong, huge_meta):
        fails.append("753B model wrongly promoted despite scores")

    # 3) single-board "#1" FAILS the boards>=2 gate.
    solo_meta = {"license_permissive": True, "open_weights": True,
                 "params_billion": 32.0, "independent_boards": 1}
    g = sovereignty_gate(solo_meta)
    if g["pass"]:
        fails.append("single-board model wrongly passed sovereignty gate")
    if not any("independent_boards" in r for r in g["reasons"]):
        fails.append("single-board failure reason missing boards note: %r" % g["reasons"])
    if promote(strong, solo_meta):
        fails.append("single-board model wrongly promoted")

    # 4) a weak model fails on SCORE even with clean sovereignty.
    weak = _full_battery({"one_shot_rate": 0.2, "follow_ups_to_fix": 5, "error_rate": 0.6,
                          "usd_per_task": 1.8, "cache_hit_pct": 0.1, "self_verifies": False})
    w_score = score(weak)
    if w_score >= 60.0:
        fails.append("weak model scored %.2f >= 60 (expected fail)" % w_score)
    if promote(weak, strong_meta):
        fails.append("weak model wrongly promoted")

    # 5) on-prem boundary: 70B fits (42GB), 71B does not.
    if not on_prem_feasible(70.0):
        fails.append("70B should fit (42.0GB <= 42)")
    if on_prem_feasible(71.0):
        fails.append("71B should NOT fit (42.6GB > 42)")

    # 6) empty results -> 0.0, never promoted.
    if score({}) != 0.0:
        fails.append("empty results did not score 0.0")

    if fails:
        for f in fails:
            print("FAIL:", f)
        print("SELFTEST: %d failure(s)" % len(fails))
        return 1
    print("strong score=%.2f  weak score=%.2f" % (s_score, w_score))
    print("strong promote=%s  753B gate=%s  solo gate=%s"
          % (promote(strong, strong_meta),
             sovereignty_gate(huge_meta)["pass"],
             sovereignty_gate(solo_meta)["pass"]))
    print("SELFTEST: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(_selftest())
