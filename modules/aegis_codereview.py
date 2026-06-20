#!/usr/bin/env python3
"""STAGED step-5 AEGIS CODEREVIEW — scan agent-generated diffs (extends AEGIS Scan).

NEW SKU off the ForrestKnight local-coding video. Where AEGIS Scan screens
untrusted *prose* (scan_text/fence_untrusted), CODEREVIEW screens untrusted
*diffs* an agent proposes, for two failure classes that survive a green
type-check:

  (a) DEP-RISK   — a newly-ADDED dependency (requirements.txt / package.json
                   "dependencies" / `import X` / `from X import` / require("X")).
                   Flagged kind="dep-added"; the `why` tells the reviewer to run
                   a CVE check (pip-audit/grype) before merge. check_cve() is a
                   clearly-marked stub returning "unknown" until box-wired.
  (b) SILENT-BUG — type-clean but broken: an INSERT/UPDATE/DELETE .execute(...)
                   with no nearby .commit(); a function that builds a result but
                   returns None on a non-void path; a *_collision/*_geometry
                   helper called with a mismatched arg count; a /clear|reset
                   handler that only slices a view and never clears the backing
                   store. All heuristics are best-effort and marked so.

scan_diff(diff_text) -> {"findings":[{kind,line,snippet,why}], "risk": low|med|high}
  risk = high if any silent-bug, med if only dep-added, else low.

Stdlib-only, no box wiring (later gated step). Self-test: `python3 aegis_codereview.py`.
"""
import re

LOW, MED, HIGH = "low", "med", "high"

# unified-diff added line = leading '+' but NOT the '+++' file header
_ADDED = re.compile(r"^\+(?!\+\+)")

# --- (a) dependency signatures on an added line -----------------------------
_PY_IMPORT = re.compile(r"^\s*import\s+([A-Za-z_][\w]*)")
_PY_FROM = re.compile(r"^\s*from\s+([A-Za-z_][\w]*)")
_JS_REQUIRE = re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""")
# a requirements.txt-style pin: `name`, `name==1.2`, `name>=1` ... (no spaces/operators-as-name)
_REQ_PIN = re.compile(r"^\s*([A-Za-z_][\w\-.]*)\s*(?:[=<>!~]=|[<>])?")
# a package.json dependency entry: `"name": "^1.2.3"`
_PKG_DEP = re.compile(r"""^\s*['"]([^'"]+)['"]\s*:\s*['"][~^>=<*\d][^'"]*['"]""")

# --- (b) silent-bug signatures ----------------------------------------------
_WRITE_EXEC = re.compile(r"\.execute(?:many)?\s*\(\s*['\"].*?\b(INSERT|UPDATE|DELETE)\b", re.I)
_COMMIT = re.compile(r"\.commit\s*\(")
_DEF = re.compile(r"^\s*def\s+(\w+)\s*\(")
_RETURN_NONE = re.compile(r"^\s*return\s+None\s*$")
_BARE_RETURN = re.compile(r"^\s*return\s*$")
_ANY_RETURN = re.compile(r"^\s*return\b")
_ASSIGN_RESULT = re.compile(r"^\s*(result|out|res|output|ret|acc|results)\s*=")
_SHAPE_HELPER = re.compile(r"\b(\w*(?:collision|geometry))\s*\(([^()]*)\)")
_DEF_SHAPE_HELPER = re.compile(r"^\s*def\s+\w*(?:collision|geometry)\s*\(([^()]*)\)")
_CLEAR_HANDLER = re.compile(r"/?(?:clear|reset)", re.I)  # matches /clear, clear_view, reset_state
_VIEW_SLICE = re.compile(r"\b([\w.]+)\s*=\s*[\w.]+\s*\[\s*:?\s*\d*\s*:?\s*\d*\s*\]")
_BACKING_CLEAR = re.compile(r"\.clear\s*\(\s*\)|\bdel\s+\w|=\s*\[\s*\]|=\s*\{\s*\}|truncate|DELETE\s+FROM", re.I)


def check_cve(pkg):
    """STUB hook — real impl shells pip-audit/grype at box-wire time.

    Returns "unknown" for every package for now; callers must treat that as
    'CVE status not yet verified', never as 'clean'.
    """
    return "unknown"  # TODO(box-wire): pip-audit / grype lookup


def _added_lines(diff_text):
    """Yield (1-based diff-line-no, added-content-without-leading-'+') tuples."""
    for i, raw in enumerate((diff_text or "").splitlines(), 1):
        if _ADDED.match(raw):
            yield i, raw[1:]


def _ctx_added(diff_text):
    """Full ordered list of added (lineno, content) so we can look at neighbours."""
    return list(_added_lines(diff_text))


def _dep_name(content, in_requirements, in_pkg_deps):
    """Best-effort: return the dependency name an added line introduces, or None."""
    m = _PY_FROM.match(content) or _PY_IMPORT.match(content)
    if m:
        return m.group(1)
    m = _JS_REQUIRE.search(content)
    if m:
        return m.group(1)
    if in_pkg_deps:
        m = _PKG_DEP.match(content)
        if m:
            return m.group(1)
    if in_requirements:
        s = content.strip()
        if s and not s.startswith("#"):
            m = _REQ_PIN.match(s)
            if m:
                return m.group(1)
    return None


def _in_section(diff_text, target_lineno, file_re, region_open_re=None, region_close_re=None):
    """True if `target_lineno` sits under a +++ b/<file_re> hunk, optionally inside
    an open region (e.g. package.json "dependencies": { ... })."""
    in_file = False
    in_region = region_open_re is None
    for i, raw in enumerate((diff_text or "").splitlines(), 1):
        if raw.startswith("+++ ") or raw.startswith("--- "):
            in_file = bool(file_re.search(raw))
            in_region = region_open_re is None
        elif in_file and region_open_re is not None:
            body = raw[1:] if raw[:1] in "+- " else raw
            if region_open_re.search(body):
                in_region = True
            elif region_close_re and region_close_re.search(body):
                in_region = False
        if i == target_lineno:
            return in_file and in_region
    return False


_REQ_FILE = re.compile(r"requirements[\w\-.]*\.txt$|requirements[\w\-.]*\.txt\b")
_PKG_FILE = re.compile(r"package\.json\b")
_DEPS_OPEN = re.compile(r'"(?:dependencies|devDependencies)"\s*:\s*\{')
_DEPS_CLOSE = re.compile(r"^\s*\}")


def scan_diff(diff_text):
    """Scan one agent-generated unified diff for dep-risk + silent-bug findings.

    Returns {"findings":[{"kind","line","snippet","why"}], "risk": low|med|high}.
    """
    findings = []
    added = _ctx_added(diff_text)

    # ----- (a) DEP-RISK: newly added dependencies ---------------------------
    for lineno, content in added:
        in_req = _in_section(diff_text, lineno, _REQ_FILE)
        in_pkg = _in_section(diff_text, lineno, _PKG_FILE, _DEPS_OPEN, _DEPS_CLOSE)
        pkg = _dep_name(content, in_req, in_pkg)
        if pkg:
            findings.append({
                "kind": "dep-added",
                "line": lineno,
                "snippet": content.strip()[:120],
                "why": ("new dependency %r added; run a CVE check (pip-audit/grype) "
                        "before merge [check_cve=%s]" % (pkg, check_cve(pkg))),
            })

    # ----- (b) SILENT-BUG signatures ----------------------------------------
    # b1. write .execute(...) with no .commit() anywhere in the added lines.
    write_lines = [(ln, c) for ln, c in added if _WRITE_EXEC.search(c)]
    if write_lines and not any(_COMMIT.search(c) for _, c in added):
        ln, c = write_lines[0]
        findings.append({
            "kind": "silent-bug",
            "line": ln,
            "snippet": c.strip()[:120],
            "why": "insert/update/delete .execute(...) with no nearby .commit() — "
                   "writes silently roll back (best-effort)",
        })

    # b2. function that assigns a result then returns None on a non-void path.
    findings += _scan_returns(added)

    # b3. *_collision / *_geometry helper called with mismatched arg count.
    findings += _scan_shape_reuse(added)

    # b4. /clear|reset handler that only slices a view, never clears backing store.
    findings += _scan_clear_handler(added)

    silent = any(f["kind"] == "silent-bug" for f in findings)
    dep = any(f["kind"] == "dep-added" for f in findings)
    risk = HIGH if silent else MED if dep else LOW
    return {"findings": findings, "risk": risk}


def _scan_returns(added):
    """Best-effort: a def that builds `result = ...` but then `return None`/bare
    return on what looks like its value-producing path."""
    out = []
    cur_def = None
    cur_def_line = None
    built = False
    built_line = None
    for ln, c in added:
        m = _DEF.match(c)
        if m:
            cur_def, cur_def_line, built, built_line = m.group(1), ln, False, None
            continue
        if cur_def is None:
            continue
        if _ASSIGN_RESULT.match(c):
            built, built_line = True, ln
        elif built and (_RETURN_NONE.match(c) or _BARE_RETURN.match(c)):
            out.append({
                "kind": "silent-bug",
                "line": ln,
                "snippet": c.strip()[:120],
                "why": "function %r builds a result but returns None/nothing on a "
                       "non-void path (best-effort)" % cur_def,
            })
            built = False
    return out


def _scan_shape_reuse(added):
    """Best-effort wrong-shape reuse: a *_collision/*_geometry helper whose def
    arity differs from a call site's arg count, within the added lines."""
    out = []
    arity = {}
    for _, c in added:
        m = _DEF_SHAPE_HELPER.match(c)
        if m:
            name = re.match(r"^\s*def\s+(\w+)", c).group(1)
            arity[name] = _count_params(m.group(1))
    for ln, c in added:
        if _DEF_SHAPE_HELPER.match(c):
            continue
        for m in _SHAPE_HELPER.finditer(c):
            name, args = m.group(1), m.group(2)
            if name in arity and _count_args(args) != arity[name]:
                out.append({
                    "kind": "silent-bug",
                    "line": ln,
                    "snippet": c.strip()[:120],
                    "why": "helper %r called with %d args but defined with %d — "
                           "wrong-shape reuse (best-effort)"
                           % (name, _count_args(args), arity[name]),
                })
    return out


def _count_params(sig):
    sig = sig.strip()
    if not sig:
        return 0
    return len([p for p in sig.split(",") if p.strip() and p.strip() != "self"])


def _count_args(call):
    call = call.strip()
    if not call:
        return 0
    return len([a for a in call.split(",") if a.strip()])


def _scan_clear_handler(added):
    """Best-effort: a clear/reset handler that only reslices a view/list and never
    touches a backing store (no .clear()/del/= []/truncate/DELETE FROM)."""
    out = []
    block = [(ln, c) for ln, c in added if _CLEAR_HANDLER.search(c)]
    if not block:
        return out
    slices = [(ln, c) for ln, c in added if _VIEW_SLICE.search(c)]
    backing = any(_BACKING_CLEAR.search(c) for _, c in added)
    if slices and not backing:
        ln, c = slices[0]
        out.append({
            "kind": "silent-bug",
            "line": ln,
            "snippet": c.strip()[:120],
            "why": "clear/reset handler only reslices a view; backing store never "
                   "cleared (no .clear()/del/truncate) (best-effort)",
        })
    return out


# ---------------------------------------------------------------------------
def _selftest():
    """Return 0 on all-green, 1 on any failure. Prints a terse per-case trace."""
    fails = []
    ran = []

    def check(label, got, want):
        ran.append(label)
        ok = got == want
        print("  [%s] %-46s got=%-22r want=%r" % ("ok" if ok else "XX", label, str(got), want))
        if not ok:
            fails.append(label)

    # --- spec case 1: add 'requests' to requirements.txt -> dep-added (med) ---
    d_dep = "+++ b/requirements.txt\n@@ -1,2 +1,3 @@\n flask\n+requests==2.31.0\n"
    r = scan_diff(d_dep)
    check("requirements: requests -> dep-added", any(f["kind"] == "dep-added" for f in r["findings"]), True)
    check("requirements: risk == med", r["risk"], MED)
    check("requirements: why mentions CVE check",
          "pip-audit" in (r["findings"][0]["why"] if r["findings"] else ""), True)

    # --- spec case 2: INSERT .execute with no commit -> silent-bug (high) ---
    d_sql = ('+++ b/db.py\n@@\n+def save(cur, row):\n'
             '+    cur.execute("INSERT INTO t (a) VALUES (?)", (row,))\n')
    r = scan_diff(d_sql)
    check("sql: insert-no-commit -> silent-bug", any(f["kind"] == "silent-bug" for f in r["findings"]), True)
    check("sql: risk == high", r["risk"], HIGH)

    # insert WITH commit -> not flagged
    d_sql_ok = ('+++ b/db.py\n@@\n+    cur.execute("INSERT INTO t VALUES (1)")\n'
                '+    conn.commit()\n')
    check("sql: insert+commit -> clean",
          any(f["kind"] == "silent-bug" for f in scan_diff(d_sql_ok)["findings"]), False)

    # --- spec case 3: clean trivial diff -> [] (low) ---
    d_clean = "+++ b/util.py\n@@ -1 +1,2 @@\n x = 1\n+y = x + 2\n"
    r = scan_diff(d_clean)
    check("clean: no findings", r["findings"], [])
    check("clean: risk == low", r["risk"], LOW)

    # --- dep: python import / from / require -------------------------------
    check("import X -> dep-added",
          any(f["kind"] == "dep-added" for f in scan_diff("+++ b/a.py\n@@\n+import yaml\n")["findings"]), True)
    check("from X import -> dep-added",
          any(f["kind"] == "dep-added" for f in scan_diff("+++ b/a.py\n@@\n+from boto3 import client\n")["findings"]), True)
    check("require('x') -> dep-added",
          any(f["kind"] == "dep-added" for f in scan_diff('+++ b/a.js\n@@\n+const z = require("lodash");\n')["findings"]), True)

    # package.json dependency entry inside "dependencies": { }
    d_pkg = ('+++ b/package.json\n@@\n+  "dependencies": {\n+    "left-pad": "^1.3.0"\n+  }\n')
    check("package.json dep entry -> dep-added",
          any(f["kind"] == "dep-added" and "left-pad" in f["why"] for f in scan_diff(d_pkg)["findings"]), True)

    # check_cve is a stub -> "unknown"
    check("check_cve stub -> unknown", check_cve("requests"), "unknown")

    # --- silent-bug: builds result, returns None ---------------------------
    d_ret = ('+++ b/calc.py\n@@\n+def total(items):\n'
             '+    result = sum(items)\n'
             '+    return None\n')
    check("returns-none-after-build -> silent-bug",
          any(f["kind"] == "silent-bug" for f in scan_diff(d_ret)["findings"]), True)
    # building a result and actually returning it -> clean
    d_ret_ok = ('+++ b/calc.py\n@@\n+def total(items):\n'
                '+    result = sum(items)\n'
                '+    return result\n')
    check("returns-result -> clean",
          any(f["kind"] == "silent-bug" for f in scan_diff(d_ret_ok)["findings"]), False)

    # --- silent-bug: wrong-shape helper reuse ------------------------------
    d_shape = ('+++ b/phys.py\n@@\n+def check_collision(a, b):\n'
               '+    return a == b\n'
               '+hit = check_collision(x, y, z)\n')
    check("wrong-arity helper call -> silent-bug",
          any(f["kind"] == "silent-bug" and "wrong-shape" in f["why"] for f in scan_diff(d_shape)["findings"]), True)
    # matched arity -> clean
    d_shape_ok = ('+++ b/phys.py\n@@\n+def check_collision(a, b):\n'
                  '+    return a == b\n'
                  '+hit = check_collision(x, y)\n')
    check("matched-arity helper call -> clean",
          any("wrong-shape" in f["why"] for f in scan_diff(d_shape_ok)["findings"]), False)

    # --- silent-bug: /clear only reslices view, no backing clear -----------
    d_clear = ('+++ b/chat.py\n@@\n+def clear_view(self):\n'
               '+    self.visible = self.messages[:0]\n')
    check("clear-view-only -> silent-bug",
          any(f["kind"] == "silent-bug" and "backing" in f["why"] for f in scan_diff(d_clear)["findings"]), True)
    # clear that also clears backing store -> clean
    d_clear_ok = ('+++ b/chat.py\n@@\n+def clear_view(self):\n'
                  '+    self.visible = self.messages[:0]\n'
                  '+    self.messages.clear()\n')
    check("clear-view+backing -> clean",
          any("backing" in f["why"] for f in scan_diff(d_clear_ok)["findings"]), False)

    # --- risk precedence: dep + silent-bug -> high -------------------------
    d_mix = (d_dep + d_sql)
    check("dep+silent -> high", scan_diff(d_mix)["risk"], HIGH)

    # --- '+++' file header is not mistaken for an added code line ----------
    check("+++ header not a dep line",
          scan_diff("+++ b/import_me.py\n@@\n x = 1\n")["findings"], [])

    # --- empty / None input is safe ----------------------------------------
    check("empty diff -> low/[]", scan_diff("")["risk"], LOW)
    check("None diff -> low/[]", scan_diff(None)["risk"], LOW)

    total = len(ran)  # count = checks actually run, never a hardcoded constant (the number is real, not asserted)
    print("\nSELFTEST: %s (%d/%d passed)" %
          ("PASS" if not fails else "FAIL: " + ", ".join(fails), total - len(fails), total))
    return 0 if not fails else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
