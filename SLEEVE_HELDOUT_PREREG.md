# EQUITY SLEEVE — ONE-SHOT HELD-OUT PRE-REGISTRATION (the deployment gate)

**Status: LOCKED (2026-06-08). Thresholds set BEFORE any held-out data is touched.**

## What is being tested
The final equity sleeve, frozen by H14: **integrated rank composite** — monthly rebalance on
the PIT universe, score = 0.5 × pctrank(h52high, 252/0) + 0.5 × pctrank(lowbeta, 252/0),
long top 20%, equal-weight, 30 bps round-trip.
In-sample (2010–2022): Sharpe 0.97, ann 14.1%, vol 14.5%, maxDD −21.6%, turnover 25%.

## The window
HELDOUT = 2023-01-01 → present (~41 months of price data, untouched by every in-sample
decision in this program). Spent **once**, on this spec only:

    python factor_backtest.py --panel ../data/nse --composite --heldout --spend-heldout

(The blend prints as reference; the decision binds on the INTEGRATED block only.)

## Acceptance gates (ALL three)
Calibrated for decay + 41-month noise — a t>2 gate here would demand Sharpe ≥ 1.08 and reject
true strategies most of the time; the bar is retention-based instead:
1. **Held-out net Sharpe ≥ 0.50** (≈50% retention of in-sample — the standard decay allowance).
2. **Excess vs the equal-weight universe > 0** (selection still adds value out-of-sample).
3. **maxDD no worse than −35%** (≤1.6× in-sample — the risk profile must remain recognizable).

## Pre-committed consequences
- **ACCEPT →** deploy via the implementation roadmap: paper for 2–3 rebalance cycles → live at
  ⅓ size → full size, with the documented kill-switches (DD breach, live-vs-shadow divergence,
  decay rule).
- **REJECT →** the equity program concludes. No deployment; passive index fund or nothing.
  No re-tunes, no second window, no "but it almost passed."

## Caveats stated now, so they can't be invented later
- ~20% false-reject risk even if the true Sharpe equals in-sample (41-month sampling noise).
  Accepted: the gate protects capital, not feelings.
- The window contains the 2024–25 NIFTY correction — a fair live stress test of the low-beta leg.
- 30 bps assumed; live slippage is tracked against this in the shadow phase.

## When to spend
Only on the day you are ready to act on either answer. Not as entertainment.
