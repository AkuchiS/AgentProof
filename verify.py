#!/usr/bin/env python3
"""
verify.py - the trust mechanism for GOVERNANCE-IN-A-BOX (Verifiable Edition).

Runs the real selftest of each governance module ON YOUR MACHINE, parses the
pass count each module actually prints, and exits 0 only if every module passes.
No network, no install, stdlib-only. The number you see is the number the code
emits -- not a number this script asserts.

Usage:
    python3 verify.py            # run all modules, print real pass counts
    make verify                  # same, via Makefile

Exit code: 0 = every module PASS, 1 = any module FAIL or unparseable.
"""
import os
import re
import subprocess
import sys

# CEILING: ~95 lines — we run each module as a SUBPROCESS rather than importing
# it. That costs a few lines over a direct import, but it is the honest choice:
# the buyer's trust comes from the module's real process exit code, which we can
# only observe by launching it. Importing would let this file fake the result.
HERE = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.join(HERE, "modules")

# (filename, human label, regex capturing the integer(s) the selftest prints).
# Each pattern is anchored to the EXACT string the module emits in its selftest
# so the printed claim is pinned to a real integer, never asserted by this file.
MODULES = [
    ("dime_autonomy_gate.py",   "autonomy gate",     r"SELFTEST:\s*PASS\s*\((\d+)/(\d+)\s*passed\)"),
    ("dime_build_discipline.py","build discipline",  r"SELFTEST:\s*PASS\s*\((\d+)/(\d+)\s*passed\)"),
    ("dime_model_fitness.py",   "model fitness",     r"SELFTEST:\s*all passed"),
    ("aegis_codereview.py",     "aegis codereview",  r"SELFTEST:\s*PASS\s*\((\d+)/(\d+)\s*passed\)"),
]


def run_one(filename, pattern):
    """Run a module's selftest as a subprocess. Return (ok, summary_str)."""
    path = os.path.join(MODULES_DIR, filename)
    if not os.path.isfile(path):
        return False, "MISSING FILE"
    try:
        proc = subprocess.run(
            [sys.executable, path],
            cwd=MODULES_DIR, capture_output=True, text=True, timeout=120,
        )
    except Exception as exc:  # noqa: BLE001 - report any launch failure honestly
        return False, "CRASH: %s" % exc
    out = (proc.stdout or "") + (proc.stderr or "")
    m = re.search(pattern, out)
    code_ok = proc.returncode == 0
    if not m:
        return False, "no PASS line (exit=%d)" % proc.returncode
    if m.groups():  # numeric "x/y" modules
        passed, total = int(m.group(1)), int(m.group(2))
        ok = code_ok and passed == total
        return ok, "%d/%d (exit=%d)" % (passed, total, proc.returncode)
    # model_fitness prints "all passed" with no counter
    return code_ok, "all passed (exit=%d)" % proc.returncode


def main():
    print("=" * 64)
    print("GOVERNANCE-IN-A-BOX -- verify.py")
    print("Running the REAL selftests on THIS machine. No network. Stdlib only.")
    print("python:", sys.version.split()[0])
    print("=" * 64)
    all_ok = True
    for filename, label, pattern in MODULES:
        ok, summary = run_one(filename, pattern)
        flag = "PASS" if ok else "FAIL"
        all_ok = all_ok and ok
        print("  [%s] %-18s %s  -> %s" % (flag, label, filename, summary))
    print("=" * 64)
    if all_ok:
        print("RESULT: PASS  (every governance module passed its own selftest)")
        print("=" * 64)
        return 0
    print("RESULT: FAIL  (at least one module did not pass -- see above)")
    print("=" * 64)
    return 1


if __name__ == "__main__":
    sys.exit(main())
