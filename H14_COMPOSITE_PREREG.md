# H14 — Composite construction: INTEGRATE vs MIX (reduced scope) — PRE-REGISTRATION

**Status: LOCKED (2026-06-08).**

## 0. Scope reduction (honest, before testing)
H14 as originally backlogged (momentum+lowvol+quality+value rank composite) is dead — its
fundamental legs nulled (H3) or proved unvalidatable (H11/H12/H13, 35-month ceiling). What
survives is the construction question for the TWO validated legs:
- **MIX (current sleeve):** 50/50 *return blend* of two separate books — top-20% h52high +
  top-20% lowbeta.
- **INTEGRATE:** one book — combine the two signals' cross-sectional percentile ranks 50/50,
  hold the top 20% of the combined score (stocks jointly strong on both).
Evidence frame: AQR "Long-Only Style Investing: Don't Just Mix, Integrate" (Fitzgibbons et
al.) — integration captures interaction effects and reduces washed-out exposure; effect size
for a 2-factor sleeve is modest and an empirical question.

## 1. Hypothesis
The integrated rank composite beats the 50/50 return blend on BOTH net Sharpe AND maxDD.

## 2. Method (LOCKED — everything inherited, zero new freedom)
- Signals: `h52high` (252, 0) and `lowbeta` (252, 0) — exactly the validated specs.
- Integrated score at each monthly rebalance = 0.5 × pct-rank(h52high) + 0.5 × pct-rank(lowbeta)
  over the PIT universe; long top 20%, equal-weight, 30 bps round-trip.
- Benchmark: the existing blend (0.5 × h52high-book returns + 0.5 × lowbeta-book returns).
- Single comparison, no variants → no DSR deflation needed.

## 3. Decision rule (binding)
- ACCEPT integrated **iff it beats the blend on BOTH net Sharpe and maxDD** (in-sample TRAIN).
- Tie or split verdict → **keep the blend** (simpler, already validated; burden of proof on
  the challenger).
- The WINNER becomes the frozen sleeve spec on which the held-out is spent. This is a
  construction choice among validated legs (like H15), so in-sample decides it; the held-out
  validates only the final chosen sleeve, once.

## 4. Stated expectation (before running)
[Guessing] Close call. Integration should cut turnover (one book, overlapping names) and may
trim DD via the joint filter; but with only two, partially-correlated legs the interaction
benefit may be within noise. Default-to-blend on any ambiguity is the pre-committed tiebreak.

---
## VERDICT (in-sample, TRAIN 2010–2022, 30 bps): ACCEPTED — INTEGRATED becomes the sleeve
Integrated: Sharpe **0.97**, ann 14.08%, vol 14.47%, **maxDD −21.62%**, turn 25%, t=3.30,
PSR 100%, excess +3.15%. Blend: Sharpe 0.94, ann 14.32%, **maxDD −26.00%**. Integrated beats
the blend on BOTH gates (Sharpe ✓, maxDD ✓), with lower vol and turnover; corr(integrated,
blend) = +0.98 — same engine, better chassis (the joint near-high ∧ low-beta filter trims the
tail). **The frozen sleeve spec is now the integrated book**: monthly, PIT universe, score =
0.5·pctrank(h52high 252/0) + 0.5·pctrank(lowbeta 252/0), long top 20%, equal-weight, 30 bps.
The held-out is spent on THIS spec, once. Binding.
