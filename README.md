# NSE Cross-Sectional Factor Backtester

A research-grade backtesting engine for systematic equity strategies on the Indian market (NSE),
built with the statistical discipline of institutional quant research — not the curve-fit
"90%-win-rate" backtests you see everywhere.

## What it does
Each month, ranks the NSE universe cross-sectionally by a chosen factor, builds a long-only
portfolio of the top names, and reports honest, cost-adjusted performance — with the
out-of-sample and multiple-testing controls that separate a real edge from a lucky fit.

## Why it's different — the discipline
- **Survivorship-free** — tests on a point-in-time universe that includes delisted stocks. No hindsight bias.
- **Pre-registration** — every hypothesis's pass/fail thresholds are locked *before* testing. No p-hacking.
- **Deflated Sharpe Ratio + PSR** — corrects the Sharpe for how many strategies were tried (the #1 reason backtests lie).
- **Held-out discipline** — a sealed out-of-sample window, spent exactly once.
- **Realistic costs** — 30 bps round-trip, turnover-aware; nets every result.

## Factors implemented
Momentum (12-1, 52-week-high, residual/idiosyncratic), low-volatility, low-beta, short-term
reversal, volatility-managed momentum, cross-sectional seasonality, and an integrated
multi-factor composite. ~12 pre-registered hypotheses tested; every verdict — pass *and* null —
documented honestly.

## Tech
Python · pandas · NumPy · SciPy. Built on a survivorship-free, corporate-action-adjusted NSE
dataset (companion repo: **nse-data-pipeline**).

---
*Showcase project demonstrating quant-research methodology. I build backtests that tell you the
truth about a strategy — including when it doesn't work.*
