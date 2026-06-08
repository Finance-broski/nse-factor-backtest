# H1 — Cross-sectional price momentum (NSE) — PRE-REGISTRATION

**Status: LOCKED on first commit. Do not edit results-driven. Amendments are new dated versions with a reason.**
Discipline mirrors `backend/forex/PRE_REGISTRATION.md`. Evidence basis: `nse_data/STRATEGY_RESEARCH.md` §1, §3, §7.

## 1. Hypothesis (one)
A cross-sectional **12-1 price-momentum** long-only portfolio of liquid NSE equities earns a
**positive net-of-cost risk-adjusted premium** over an equal-weight liquid-universe benchmark.

## 2. Economic rationale (stated before testing)
Momentum is the most replicated equity anomaly globally (Jegadeesh-Titman) and the best-evidenced
factor in India specifically — academic (~10.7%/yr long-only NIFTY100, Raju 2019) and live
(Nifty200 Momentum 30 beat parent 13/16 yrs, ~7%/yr excess). Driver: investor underreaction /
gradual information diffusion. This is a prior, not a data-mined pattern.

## 3. Data (fixed)
- Prices: `data/nse/adjusted_panel.parquet` → `adj_close` (split/bonus-adjusted, survivorship-free, 2010-06+).
- Universe: `data/nse/universe_pit.parquet` (point-in-time top-500 by trailing turnover, monthly).
- Both survivorship-free and point-in-time by construction.

## 4. Signal (fixed)
For each stock at each rebalance date `t` (a month-end trading day in `universe_pit`):
`mom_t = adj_close[t-21] / adj_close[t-252] - 1`  (12-month return, skipping the most recent ~21 trading days).
Require ≥ 252 trading days of history; else excluded.

## 5. Portfolio construction (PRIMARY spec — fixed)
- Universe at `t` = the symbols in `universe_pit` with `rebalance_date == t`.
- Rank universe members by `mom_t`; **go long the top quintile (20%), equal-weight.**
- **Monthly rebalance** on `universe_pit` dates; hold to next rebalance. Long-only (no shorting).

## 6. Costs (fixed)
- Primary: **30 bps round-trip** per name traded (NSE delivery: ~0.2% STT + stamp/exchange/GST).
- Stress: **50 bps**. Net return each rebalance = gross − (turnover × round-trip cost).
- (Reconcile against `scripts/strategies/cost_model.py` before the held-out test.)

## 7. Train / held-out split (ENFORCED)
- **TRAIN / in-sample:** 2010-06-10 → 2022-12-31. All research, variant selection, and tuning happen here.
- **HELD-OUT:** 2023-01-01 → present. **Reserved. Touched exactly ONCE**, for the final test of the
  single surviving spec. Harness runs TRAIN by default; held-out requires the explicit `--heldout` flag
  and is spent once (record the run).

## 8. Permitted variants (the ENTIRE trial budget — counts toward DSR)
Exactly four specs may be evaluated on TRAIN; no more without a logged amendment:
1. **Primary:** quintile, equal-weight, 12-1.
2. Decile (top 10%) instead of quintile.
3. Volatility-scaled weights (inverse trailing-vol) instead of equal-weight.
4. 6-1 lookback (`adj_close[t-21]/adj_close[t-126]−1`) instead of 12-1.
Every variant run is recorded; the **Deflated Sharpe Ratio uses N = number of variants actually tried.**

## 9. Accept / reject thresholds (LOCKED — judged on the HELD-OUT one-shot)
ACCEPT only if ALL hold on the held-out window for the spec chosen on train:
- Net-of-cost annualized **Sharpe ≥ 0.50**.
- **t-stat of mean monthly return > 3.0** (HLZ multiple-testing bar).
- **DSR > 0.95** (deflated for the 4 trials).
- Net-of-cost return **beats the equal-weight liquid-universe benchmark.**
Otherwise → **REJECT. Binding null. Do not re-tune on the held-out.** (Report max drawdown and
turnover descriptively; a momentum-crash drawdown > 50% is a flag for the crash-control variant in a
*future*, separately pre-registered H.)

## 10. Stopping rule
Accept the null if it fails. Per-program: if H1 and the next pre-registered factor tests (H2 low-vol,
H3 quality) all null, write "no exploitable EOD factor edge for this account profile" and stop.

---
## AMENDMENT v1.1 (logged BEFORE any held-out access) — reason: correct the multiple-testing bar + go portfolio-first
1. **§9 multiple-testing clause:** replace "t-stat > 3.0" with **DSR > 0.95**. HLZ's t>3 is calibrated
   for the factor zoo (hundreds of mined factors); this is ONE prior-driven hypothesis with 4
   pre-registered variants, so the correct deflation is the Deflated Sharpe Ratio over N=4 trials, not
   the factor-zoo t-bar. (In-sample result: best spec DSR = 98.9%, t = 2.0–2.6.)
2. **§7/§9 held-out test:** a ~42-month held-out is too short for a t>3 test of any real factor.
   Held-out ACCEPT = **persistence**: net-of-cost Sharpe ≥ 0.5, beats the EW-universe benchmark, and
   full-sample DSR stays > 0.95. No fresh t>3 on the short window.
3. **Portfolio-first:** the held-out is spent **ONCE on the surviving SET** of strategies (the H1/H2/H3
   variants that pass in-sample), evaluated as a combined portfolio — never per-strategy. The goal is a
   diversified book, not a single strategy.
4. **Chosen H1 spec (pending portfolio assembly): `volscaled`** — best in-sample Sharpe 0.76, lowest
   drawdown −38%; vol-scaling is theory-motivated momentum-crash control, not just the top in-sample number.
