# H16 — Cross-sectional seasonality (same-calendar-month), NSE — PRE-REGISTRATION

**Status: LOCKED (2026-06-08).** Same discipline + v1.1 conventions as H1. Evidence:
Heston & Sadka (2008, JFE) "Seasonality in the cross-section of stock returns"; India
month-of-year / turn-of-month documented (Asia-Pacific Fin Markets 2021).

## 1. Hypothesis
A stock's return in a given calendar month is predicted by its OWN average return in that
**same calendar month** in prior years. A long portfolio of stocks with the highest
same-month historical return earns positive risk-adjusted return, **with low correlation to
momentum and low-vol** (the reason to test it — a genuine diversifier candidate).

## 2. Point-in-time contract
The signal at formation date `a` uses ONLY monthly-interval returns that **completed on or
before `a`**. No future or concurrent data. (Price-only, so no announce-date subtlety.)

## 3. Signal
- Build monthly-interval returns at the universe rebalance dates: interval = [r_k, r_{k+1}],
  return = adj_close[r_{k+1}]/adj_close[r_k] − 1, labelled by the calendar month of r_{k+1}.
- At formation `a` (about to hold the interval [a, b], whose month = b.month):
  `signal(stock) = mean( interval returns of that stock, over prior completed intervals
  whose month == b.month )`.
- Require **≥ minobs prior same-month observations** (i.e. ≥ minobs prior years) for a valid
  signal; else the stock is excluded that month.
- Rank cross-sectionally; long top fraction; equal-weight; 30 bps round-trip.

## 4. Variants (LOCKED — no others permitted)
- **primary:** top 20%, minobs 3
- **decile:**  top 10%, minobs 3
- **deep:**    top 20%, minobs 5 (more history → cleaner seasonal, shorter sample)

## 5. Sample
Price panel starts 2010-06; with minobs ≥ 3 the first tradable months arrive ~2014, so
in-sample (TRAIN ≤ 2022) ≈ **2014–2022, ~100 months** — long enough for a t>2 bar to be
achievable (unlike the 35-month fundamental factors). Held-out 2023+ untouched.

## 6. Accept (held-out, spent once on the single chosen variant)
ACCEPT only if: best variant **net Sharpe t > 2**, **DSR > 0.95** (deflated for the 3
variants), AND **positive excess vs the equal-weight universe**. Correlation to the H4 +
low-beta sleeve reported (the diversifier rationale) but not an acceptance gate.

## 7. Caveats
- The lag-12 same-month return overlaps annual momentum/reversal seasonally; the multi-year
  average dilutes this but does not fully remove it — flagged, not corrected. - Turnover may
  be high (signal reshuffles monthly); the net-of-cost Sharpe is the binding number. - If it
  accepts, the next gate is its correlation to the sleeve — a diversifier that's 0.8
  correlated to momentum isn't one.

---
## VERDICT (in-sample, TRAIN 2010–2022, 30 bps): NULL — REJECTED (fails the excess gate)
primary top20%/≥3y: 113 mo, ann 16.87%, Sharpe 0.68, **t=2.08 ✓, DSR 96.2% ✓, excess −0.29% ✗** —
matched the equal-weight universe minus costs. The t/DSR passes were carried by equity beta over a
bull sample, not selection: exactly the false-positive the excess gate exists to catch. Gross
selection edge ≈ +2.5%/yr, fully consumed by 78%/mo turnover × 30 bps. Concentration *inverted*
(decile excess −1.00%; real signals amplify when concentrated). maxDD −55% vs sleeve −26%.
**Binding null, not re-tuned.** Same-month seasonality does not survive costs long-only on NSE.
