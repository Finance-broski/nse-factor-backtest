# Strategy backlog — split by what we can test NOW vs LATER

Grounded in `STRATEGY_RESEARCH.md` (evidence) and the actual dataset. Each is a *candidate hypothesis*
to be pre-registered and tested the same way as H1/H2 (DSR>0.95, NSE costs, train/held-out-once,
portfolio-first). "Now" = needs only what we already have & validated.

## Dataset on hand
- `adjusted_panel.parquet` — price (adj_close/tr_close), survivorship-free, **2010+** ✓
- `universe_pit.parquet` — PIT liquidity universe (+rank) ✓
- `fundamentals_pit.parquet` — announcement-dated quarterly P&L + EPS, **2016+** (fetch finishing)
- NOT yet: shares outstanding / market cap, sector classification, full balance sheet, pre-2016
  fundamentals, intraday bars.

---

## ✅ TESTABLE NOW — price-only, full 2010+ history (no fundamentals needed)

| # | Strategy | One-line definition | Notes / why |
|---|---|---|---|
| H1 | **Momentum 12-1** | top-quintile trailing 12-1 return | **done** — Sharpe 0.71–0.76, DSR 98.9% |
| H2 | **Low-volatility** | bottom-quintile trailing vol | **done** — Sharpe 0.79–0.86, low DD/turnover |
| H4 | **52-week-high momentum** | rank by price / 252-day-high (George-Hwang) | robust momentum cousin, **lower turnover**, anchoring story; may not reverse long-run |
| H5 | **Residual / idiosyncratic momentum** | momentum on market-beta-residual returns | cleaner momentum, historically **fewer crashes** than price momentum → diversifies H1 |
| H6 | **Vol-managed momentum** | scale momentum exposure by inverse realised vol | the H1 **crash-control** follow-up (Daniel-Moskowitz); test if it cuts the −38% DD |
| H7 | **Low-beta (BAB-style)** | rank by estimated market beta, long low-beta | cousin of H2; price-only beta estimate |
| H8 | **Short-term reversal (1-month)** | long prior-month losers | **expect costs to kill it** in India (high turnover, bid-ask artifact) — test to *refute* cleanly |
| H9 | **Amihud illiquidity** | rank by \|ret\|/turnover | documented premium, but buying illiquid names fights the liquidity filter — capacity-capped |
| H10 | **Seasonality** | turn-of-month / Samvat / month-of-year effects | price-only, India-specific; usually thin after costs |

Priority among these: **H5 (residual momentum) and H6 (vol-managed momentum)** first — both directly
address H1's biggest weakness (crash/drawdown) and may genuinely diversify the price-momentum leg.

---

## 🟡 TESTABLE SOON — once `fundamentals_pit.parquet` (2016+) lands

| # | Strategy | Definition | Notes |
|---|---|---|---|
| H3 | **Quality (profitability/ROE)** | top-quintile gross-profit/ROE | **queued** — robust globally + India; low turnover (tax-friendly) |
| H11 | **PEAD** (post-earnings drift) | long high earnings-surprise (SUE vs prior-yr qtr) after announcement | **strong, genuinely different signal** — you have announce dates; event-driven, lower turnover; best diversifier candidate |
| H12 | **Value (earnings yield E/P)** | long high E/P (EPS ÷ price) | confirm/refute the "value is weak in India" finding on *your* data |
| H13 | **Earnings / sales growth** | long high YoY PAT or revenue growth | growth tilt; pairs with quality |
| H14 | **Multi-factor composite** | combine momentum+lowvol+quality(+value) ranks | the destination book; only after each leg is validated |
| H15 | **Clean B–S–C vol-target** | TS vol-target on PLAIN (equal-wt) momentum, vs plain AND vs invvol base | **VERDICT: NULL (2026-06-08), as pre-stated** — invvol base dominates plain AND targeted-plain on both metrics; keep invvol, never stack; H6 reconciliation confirmed; thread closed |

Priority: **H11 (PEAD)** — it's the most likely to be *uncorrelated* with the price factors (event-driven,
not trend/vol), so it's the strongest lever for an actually-diversified equity book.

---

## 🔵 TESTABLE LATER — needs data we don't have yet

| Strategy | Blocked on |
|---|---|
| **Size factor, market-cap weighting, P/B (book-to-market)** | shares outstanding / market cap (reference data) |
| **Sector-neutral factors, sector/industry rotation** | sector classification |
| **Full quality: accruals, asset growth, Piotroski F-score** | full balance sheet + cash flow (only headline P&L now) |
| **Pre-2016 fundamental factors** | HTML-parse backfill of old NSE filings |
| **All intraday: ORB, intraday reversal, VWAP, gap-fill** | intraday bar tier (deferred by choice) |
| **Options / vol-risk-premium / skew** | derivatives data (out of scope) |

---

## SLEEVE DECISION (in-sample, TRAIN 2010–2022) — recorded
- **Core = H4 (52-week-high momentum):** Sharpe 0.95, t 3.23, maxDD −31%, DSR 100%. Best single factor;
  supersedes H1 raw momentum.
- **Defensive (optional) = low-beta:** Sharpe 0.88; adds **drawdown control only** (sleeve −31%→−26%),
  **no Sharpe gain** (combo 0.94 ≈ H4 0.95). Low-beta ≈ low-vol (corr +0.95) — keep one.
- **Long-only factors do NOT diversify** (corr: mom/low-vol +0.88, mom/low-beta +0.92, low-beta/low-vol
  +0.95; long-short rejected). The equity book is ONE beta bet + tilt. **Diversify cross-asset (equity vs
  forex), not within long-only equity.**
- **Next real lever = multi-factor COMPOSITE SIGNAL** (combine momentum+low-beta+quality at the stock-rank
  level → one portfolio) — beats single factors via better *selection* even when legs are correlated.
  Test once quality (H3) is available. **H11 PEAD** still worth a standalone run (event-driven → best
  shot at a genuinely lower-correlation leg).
- Held-out: spend once on the chosen book (H4, or the composite if it beats H4), deflated for all
  families screened.

## Cross-cutting note on construction (from the H1/H2 finding)
Long-only equity factors are **~0.9 correlated** (shared market beta) → little diversification from
stacking them. Real within-equity diversification needs **market-neutral long-short** (test in progress)
or genuinely different signals (**PEAD**). The biggest cross-strategy diversification, though, is
**cross-asset**: the NSE equity book vs the prop forex book. Build the equity book for what it is — a
diversified *equity* sleeve — and diversify at the portfolio level across asset classes.
