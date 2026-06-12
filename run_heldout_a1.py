"""ONE-SHOT held-out runner for H14 under Amendment A1 (no-ETF universe).

    .venv\\Scripts\\python.exe ..\\nse_data\\run_heldout_a1.py                  -> refuses
    .venv\\Scripts\\python.exe ..\\nse_data\\run_heldout_a1.py --spend-heldout  -> the ONE look (Ayan's act)

This spends the sealed held-out (2023-01-01 -> present) on the frozen H14 spec with the
Amendment A1 universe filter (approved etf_exclusion_list.csv). SLEEVE_HELDOUT_PREREG.md
is the binding contract: thresholds, consequences, and the one-look rule live there and
only there. Harness logic (factor_backtest.py) is reused, not modified.
Prepared 2026-06-10; verified ONLY in its refusal path; never executed with the flag.
"""
import argparse
import glob
import hashlib
import os, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))


def code_hash() -> str:
    h = hashlib.sha256()
    for f in ("run_heldout_a1.py", "factor_backtest.py", "etf_exclusion_list.csv"):
        with open(os.path.join(HERE, f), "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:16]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default=os.path.join(HERE, "..", "data", "nse"))
    ap.add_argument("--cost-bps", type=float, default=30.0)
    ap.add_argument("--spend-heldout", action="store_true")
    a = ap.parse_args()

    prior = glob.glob(os.path.join(HERE, "heldout_a1_result_*.txt"))
    if prior:
        sys.exit(f"REFUSING TO RUN: {os.path.basename(prior[0])} already exists — the "
                 "held-out is SPENT. Rerunning after edits voids the test.")
    if not a.spend_heldout:
        sys.exit("REFUSING TO RUN: this spends the ONE-SHOT held-out (>= 2023-01-01).\n"
                 "SLEEVE_HELDOUT_PREREG.md governs (locked thresholds, one look, both\n"
                 "branches pre-written). Pass --spend-heldout to spend it ONCE — only on\n"
                 "the day you are ready to act on either answer.")

    # ---- one-shot path below: reached only with --spend-heldout ----
    import contextlib
    import io
    import math
    import pandas as pd
    sys.path.insert(0, HERE)
    from factor_backtest import HELDOUT, backtest, block, composite_backtest, load, sharpe

    lines: list[str] = []

    class Tee(io.TextIOBase):
        def write(self, s: str) -> int:
            sys.__stdout__.write(s)
            lines.append(s)
            return len(s)

    rt = a.cost_bps / 1e4
    excl = set(pd.read_csv(os.path.join(HERE, "etf_exclusion_list.csv"))["symbol"])
    C, members = load(a.panel)
    members = {d: set(s) - excl for d, s in members.items()}

    with contextlib.redirect_stdout(Tee()):
        print(f"H14 ONE-SHOT HELD-OUT (Amendment A1 universe)  |  "
              f"run {datetime.now(timezone.utc).isoformat()}  |  code {code_hash()}")
        print(f"window: HELD-OUT (spent once) {HELDOUT[0]}..{HELDOUT[1]}  "
              f"cost={a.cost_bps:.0f}bps  exclusions applied={len(excl)}")
        ri, bmi, tni = composite_backtest(C, members, HELDOUT, 0.20, rt)
        block(ri, bmi, tni, "H14 INTEGRATED (no-ETF) [HELD-OUT — BINDING]")
        sh = sharpe(ri)
        eq = (1 + ri).cumprod()
        dd = float((eq / eq.cummax() - 1).min())
        exc = (ri.mean() - bmi.mean()) * 12
        g1, g2, g3 = sh >= 0.50, exc > 0, dd >= -0.35
        print(f"GATE 1 net Sharpe >= 0.50:       {'PASS' if g1 else 'FAIL'} ({sh:.2f})")
        print(f"GATE 2 excess vs universe > 0:   {'PASS' if g2 else 'FAIL'} ({exc:+.2%}/yr)")
        print(f"GATE 3 maxDD no worse than -35%: {'PASS' if g3 else 'FAIL'} ({dd:.1%})")
        verdict = ("ACCEPT — deploy per DEPLOYMENT_PLAN_H14.md PASS branch"
                   if (g1 and g2 and g3) else
                   "REJECT — the equity program concludes; no re-tunes, no second window")
        print(f"VERDICT (locked rule, ALL three gates): {verdict}")
        # blend prints as reference; the decision binds on the INTEGRATED block only
        h4, _, _ = backtest(C, members, HELDOUT, "h52high", 0.20, "equal", 252, 0, rt)
        lb, _, _ = backtest(C, members, HELDOUT, "lowbeta", 0.20, "equal", 252, 0, rt)
        df = pd.concat({"h4": h4, "lb": lb}, axis=1).dropna()
        blend = 0.5 * df["h4"] + 0.5 * df["lb"]
        eqb = (1 + blend).cumprod()
        print(f"BLEND reference (gates NOTHING): net_Sharpe={sharpe(blend):.2f}  "
              f"maxDD={float((eqb / eqb.cummax() - 1).min()):.1%}")

    out = os.path.join(HERE, f"heldout_a1_result_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(lines) + "\nThis file is the one-shot record. "
                "Deleting it to rerun voids the test.\n")
    print(f"saved {os.path.basename(out)}")


main()
