# RECEIPTS

Every claim this product makes is listed here with **the exact command that
proves it** and **the exact integer that command prints**. No claim appears
without a runnable command. Run them yourself; if a number differs on your
machine, trust your machine.

All commands are run from the `receipt_product/` directory. No network, no
install — stdlib Python 3 only.

---

## The one command (covers all four at once)

```
python3 verify.py
```

Real output captured on the build machine (python 3.10.12):

```
  [PASS] autonomy gate      dime_autonomy_gate.py  -> 19/19 (exit=0)
  [PASS] build discipline   dime_build_discipline.py  -> 22/22 (exit=0)
  [PASS] model fitness      dime_model_fitness.py  -> all passed (exit=0)
  [PASS] aegis codereview   aegis_codereview.py  -> 23/23 (exit=0)
RESULT: PASS  (every governance module passed its own selftest)
```

`echo $?` after this prints **0**.

---

## Claim-by-claim

| # | Claim | Command that proves it | Exact integer it prints |
|---|---|---|---|
| 1 | The autonomy gate passes its full selftest. | `python3 modules/dime_autonomy_gate.py` | `SELFTEST: PASS (19/19 passed)` → **19/19** |
| 2 | The build-discipline (laziness ladder) module passes its full selftest. | `python3 modules/dime_build_discipline.py` | `SELFTEST: PASS (22/22 passed)` → **22/22** |
| 3 | The model-fitness scorecard passes its selftest. | `python3 modules/dime_model_fitness.py` | `SELFTEST: all passed` (this module prints no counter; it asserts each case and exits 0) |
| 4 | The agent-diff codereview passes its full selftest. | `python3 modules/aegis_codereview.py` | `SELFTEST: PASS (23/23 passed)` → **23/23** |
| 5 | All four pass together and the product exits 0. | `python3 verify.py` | `RESULT: PASS`, exit code **0** |

Each module also returns its selftest exit code as the process exit code, so
`python3 modules/<file>.py; echo $?` prints `0` on pass — machine-checkable
without reading any text.

---

## What is NOT claimed (honesty boundary)

- **No revenue, sales, or P&L number** appears in this product. DIME's real
  sales to date are **$0** and no money-results claim is made here.
- **No "wired live across the board" claim.** **3 of 4** modules have a live *advisory*
  caller in DIME's own systems today (autonomy-gate → intel pipeline; build-discipline +
  model-fitness → orchestrator); the 4th (`aegis_codereview`) is runnable-but-unwired.
  This is stated plainly and checkably in `WIRING.md`.
- **No "75-case corpus" or any integer a selftest in this repo does not print.**
  The public AEGIS Guard repo (linked in `README.md`) carries its own separate,
  independently runnable selftest; this product pins its numbers only to the four
  modules shipped here.
