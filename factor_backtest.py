"""
Generalized cross-sectional factor backtest (NSE) — the portfolio engine.
Signals: momentum, lowvol, resmom (residual/idiosyncratic momentum).
Modes: long-only variants, market-neutral long-short, long-only portfolio combine,
       and vol-managed momentum overlay (H6). Look-ahead-safe; PSR/DSR. TRAIN default; held-out gated.

Usage:
  python factor_backtest.py --panel ../data/nse --signal momentum --variants
  python factor_backtest.py --panel ../data/nse --signal lowvol   --variants
  python factor_backtest.py --panel ../data/nse --signal resmom   --variants   # H5
  python factor_backtest.py --panel ../data/nse --volmanaged                    # H6
  python factor_backtest.py --panel ../data/nse --portfolio
  python factor_backtest.py --panel ../data/nse --ls-portfolio
"""
import argparse
import math
import os
import numpy as np
import pandas as pd
from scipy import stats

EULER = 0.5772156649
TRAIN = ("2010-06-10", "2022-12-31")
HELDOUT = ("2023-01-01", "2100-01-01")

SPECS = {
    "momentum": {"primary": (0.20, "equal", 252, 21), "decile": (0.10, "equal", 252, 21),
                 "volscaled": (0.20, "invvol", 252, 21), "six_one": (0.20, "equal", 126, 21)},
    "lowvol":   {"primary": (0.20, "equal", 252, 0), "decile": (0.10, "equal", 252, 0),
                 "win126": (0.20, "equal", 126, 0)},
    "resmom":   {"primary": (0.20, "equal", 252, 21), "decile": (0.10, "equal", 252, 21),
                 "six_one": (0.20, "equal", 126, 21)},
    "h52high":  {"primary": (0.20, "equal", 252, 0), "decile": (0.10, "equal", 252, 0)},
    "lowbeta":  {"primary": (0.20, "equal", 252, 0), "decile": (0.10, "equal", 252, 0)},
    "reversal": {"primary": (0.20, "equal", 21, 0), "decile": (0.10, "equal", 21, 0)},
}


def load(panel_dir):
    adj = pd.read_parquet(os.path.join(panel_dir, "adjusted_panel.parquet"),
                          columns=["date", "symbol", "adj_close"])
    adj["date"] = pd.to_datetime(adj["date"])
    C = adj.pivot_table(index="date", columns="symbol", values="adj_close").sort_index()
    uni = pd.read_parquet(os.path.join(panel_dir, "universe_pit.parquet"),
                          columns=["rebalance_date", "symbol"])
    uni["rebalance_date"] = pd.to_datetime(uni["rebalance_date"])
    return C, {d: set(g["symbol"]) for d, g in uni.groupby("rebalance_date")}


def load_ranks(panel_dir):
    uni = pd.read_parquet(os.path.join(panel_dir, "universe_pit.parquet"),
                          columns=["rebalance_date", "symbol", "rank"])
    uni["rebalance_date"] = pd.to_datetime(uni["rebalance_date"])
    return {d: dict(zip(g["symbol"], g["rank"])) for d, g in uni.groupby("rebalance_date")}


def signal_at(C, i, sig, lookback, skip):
    if sig == "momentum":
        return C.iloc[i - skip] / C.iloc[i - lookback] - 1.0
    if sig == "lowvol":
        return -C.iloc[i - lookback:i].pct_change(fill_method=None).std()
    if sig == "resmom":                       # residual momentum: momentum of market-residual returns
        R = C.iloc[i - lookback:i - skip].pct_change(fill_method=None).iloc[1:]
        rm = R.mean(axis=1)
        rmc = rm - rm.mean()
        varm = float((rmc ** 2).mean())
        if varm <= 0:
            return pd.Series(dtype=float)
        beta = R.sub(R.mean(axis=0), axis=1).mul(rmc, axis=0).mean(axis=0) / varm
        alpha = R.mean(axis=0) - beta * rm.mean()
        pred = pd.DataFrame(np.outer(rm.values, beta.values), index=R.index, columns=R.columns).add(alpha, axis=1)
        resid = R - pred
        return resid.mean(axis=0) / resid.std(axis=0)     # residual information ratio
    if sig == "h52high":                      # nearness to 52-week high (George-Hwang)
        return C.iloc[i] / C.iloc[i - lookback:i].max()
    if sig == "lowbeta":                      # long low market-beta (BAB cousin)
        R = C.iloc[i - lookback:i].pct_change(fill_method=None).iloc[1:]
        rm = R.mean(axis=1)
        rmc = rm - rm.mean()
        varm = float((rmc ** 2).mean())
        if varm <= 0:
            return pd.Series(dtype=float)
        beta = R.sub(R.mean(axis=0), axis=1).mul(rmc, axis=0).mean(axis=0) / varm
        return -beta
    if sig == "reversal":                     # short-term reversal: long recent losers
        return -(C.iloc[i] / C.iloc[i - lookback] - 1.0)
    raise ValueError(sig)


def backtest(C, members, window, sig, frac, weighting, lookback, skip, rt):
    lo, hi = pd.Timestamp(window[0]), pd.Timestamp(window[1])
    rebals = sorted(d for d in members if lo <= d <= hi and d in C.index)
    pos = {d: C.index.get_loc(d) for d in rebals}
    rets, bench, turns, dates, prev = [], [], [], [], pd.Series(dtype=float)
    for a, b in zip(rebals[:-1], rebals[1:]):
        i, j = pos[a], pos[b]
        if i < lookback:
            continue
        s = signal_at(C, i, sig, lookback, skip)
        u = sorted(members[a])
        su = s.reindex(u).dropna()
        if len(su) < 20:
            continue
        k = max(1, int(len(su) * frac))
        picks = su.nlargest(k).index
        if weighting == "invvol":
            v = C.iloc[i - 63:i][picks].pct_change(fill_method=None).std()
            w = (1 / v).replace([np.inf, np.nan], 0.0)
            w = w / w.sum() if w.sum() > 0 else pd.Series(1 / k, index=picks)
        else:
            w = pd.Series(1 / k, index=picks)
        fwd = (C.iloc[j] / C.iloc[i] - 1.0).reindex(picks).fillna(0.0)
        gross = float((w * fwd).sum())
        alln = prev.index.union(w.index)
        turn = 0.5 * float((w.reindex(alln).fillna(0) - prev.reindex(alln).fillna(0)).abs().sum())
        rets.append(gross - turn * rt)
        bench.append(float((C.iloc[j] / C.iloc[i] - 1.0).reindex(u).dropna().mean()))
        turns.append(turn)
        dates.append(b)
        prev = w
    return (pd.Series(rets, index=pd.DatetimeIndex(dates)),
            pd.Series(bench, index=pd.DatetimeIndex(dates)), float(np.mean(turns)))


def backtest_ls(C, members, ranks, window, sig, frac, lookback, skip, rt, short_univ=150, borrow_m=0.0025):
    lo, hi = pd.Timestamp(window[0]), pd.Timestamp(window[1])
    rebals = sorted(d for d in members if lo <= d <= hi and d in C.index)
    pos = {d: C.index.get_loc(d) for d in rebals}
    rets, dates, pl, ps = [], [], pd.Index([]), pd.Index([])
    for a, b in zip(rebals[:-1], rebals[1:]):
        i, j = pos[a], pos[b]
        if i < lookback:
            continue
        s = signal_at(C, i, sig, lookback, skip)
        longu = sorted(members[a])
        shortu = [x for x in members[a] if ranks.get(a, {}).get(x, 1e9) <= short_univ]
        sl, ss = s.reindex(longu).dropna(), s.reindex(shortu).dropna()
        if len(sl) < 20 or len(ss) < 20:
            continue
        longp = sl.nlargest(max(1, int(len(sl) * frac))).index
        shortp = ss.nsmallest(max(1, int(len(ss) * frac))).index
        fl = (C.iloc[j] / C.iloc[i] - 1).reindex(longp).fillna(0).mean()
        fs = (C.iloc[j] / C.iloc[i] - 1).reindex(shortp).fillna(0).mean()
        lturn = 1 - len(pl.intersection(longp)) / max(1, len(longp))
        sturn = 1 - len(ps.intersection(shortp)) / max(1, len(shortp))
        rets.append((fl - fs) - (lturn + sturn) * rt - borrow_m)
        dates.append(b)
        pl, ps = longp, shortp
    return pd.Series(rets, index=pd.DatetimeIndex(dates))


def vol_manage(r, target=0.15, maxlev=1.5, win=6):
    """Scale month t by target/(trailing win-month annualised vol), using lagged vol (no look-ahead)."""
    rv = r.rolling(win).std().shift(1) * math.sqrt(12)
    w = (target / rv).clip(upper=maxlev).fillna(1.0)
    return w * r


def psr(r, srstar=0.0):
    sr = r.mean() / r.std(ddof=1)
    n = len(r)
    sk = stats.skew(r)
    ku = stats.kurtosis(r, fisher=False)
    den = math.sqrt(max(1e-9, 1 - sk * sr + (ku - 1) / 4 * sr ** 2))
    return float(stats.norm.cdf((sr - srstar) * math.sqrt(n - 1) / den))


def block(r, bench, turn, label):
    n = len(r)
    m = r.mean()
    sd = r.std(ddof=1)
    sh = m / sd * math.sqrt(12)
    t = m / (sd / math.sqrt(n))
    eq = (1 + r).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    print(f"=== {label} ===")
    print(f"  months={n} ann_ret={m*12:6.2%} ann_vol={sd*math.sqrt(12):6.2%} net_Sharpe={sh:5.2f} "
          f"t={t:4.2f} maxDD={dd:6.2%} hit={(r>0).mean():4.0%} turn={turn:4.0%} PSR={psr(r):4.0%} "
          f"excess={(m-bench.mean())*12:+5.2%}")
    return r.mean() / r.std(ddof=1)


def dsr(pps, best, nobs):
    N = len(pps)
    s = np.std(pps, ddof=1) if N > 1 else 0.0
    emax = s * ((1 - EULER) * stats.norm.ppf(1 - 1 / N) + EULER * stats.norm.ppf(1 - 1 / (N * math.e))) if N > 1 else 0.0
    return float(stats.norm.cdf((best - emax) * math.sqrt(nobs - 1))), emax


def sharpe(x):
    return x.mean() / x.std(ddof=1) * math.sqrt(12)


def seasonality_backtest(C, members, window, frac, rt, minobs):
    """H16 cross-sectional seasonality (Heston-Sadka): rank stocks by their mean return in the
    SAME calendar month across prior years; long top frac. PIT — uses only intervals that
    completed on or before the formation date."""
    lo, hi = pd.Timestamp(window[0]), pd.Timestamp(window[1])
    rebals = sorted(d for d in members if d in C.index)
    R, L, ends = {}, {}, []
    for s, e in zip(rebals[:-1], rebals[1:]):
        R[e] = C.loc[e] / C.loc[s] - 1.0       # interval return, realised at end date e
        L[e] = e.month                          # labelled by the month being predicted
        ends.append(e)
    rets, bench, turns, dates, prev = [], [], [], [], pd.Series(dtype=float)
    for a, b in zip(rebals[:-1], rebals[1:]):
        if not (lo <= a <= hi):
            continue
        hist = [x for x in ends if x <= a and L[x] == b.month]   # prior same-month, completed
        if len(hist) < minobs:
            continue
        sig = pd.concat([R[x] for x in hist], axis=1).mean(axis=1)
        u = sorted(members[a])
        su = sig.reindex(u).dropna()
        if len(su) < 20:
            continue
        k = max(1, int(len(su) * frac))
        picks = su.nlargest(k).index
        w = pd.Series(1.0 / k, index=picks)
        fwd = (C.loc[b] / C.loc[a] - 1.0).reindex(picks).fillna(0.0)
        gross = float((w * fwd).sum())
        alln = prev.index.union(w.index)
        turn = 0.5 * float((w.reindex(alln).fillna(0) - prev.reindex(alln).fillna(0)).abs().sum())
        rets.append(gross - turn * rt)
        bench.append(float((C.loc[b] / C.loc[a] - 1.0).reindex(u).dropna().mean()))
        turns.append(turn); dates.append(b); prev = w
    return (pd.Series(rets, index=pd.DatetimeIndex(dates)),
            pd.Series(bench, index=pd.DatetimeIndex(dates)),
            float(np.mean(turns)) if turns else 0.0)


def composite_backtest(C, members, window, frac, rt):
    """H14 (reduced): one integrated book from 50/50 percentile-ranks of h52high + lowbeta."""
    lo, hi = pd.Timestamp(window[0]), pd.Timestamp(window[1])
    rebals = sorted(d for d in members if lo <= d <= hi and d in C.index)
    pos = {d: C.index.get_loc(d) for d in rebals}
    rets, bench, turns, dates, prev = [], [], [], [], pd.Series(dtype=float)
    for a, b in zip(rebals[:-1], rebals[1:]):
        i, j = pos[a], pos[b]
        if i < 252:
            continue
        u = sorted(members[a])
        s1 = signal_at(C, i, "h52high", 252, 0).reindex(u)
        s2 = signal_at(C, i, "lowbeta", 252, 0).reindex(u)
        df = pd.concat({"m": s1, "b": s2}, axis=1).dropna()
        if len(df) < 20:
            continue
        comb = 0.5 * df["m"].rank(pct=True) + 0.5 * df["b"].rank(pct=True)
        k = max(1, int(len(comb) * frac))
        picks = comb.nlargest(k).index
        w = pd.Series(1.0 / k, index=picks)
        fwd = (C.iloc[j] / C.iloc[i] - 1.0).reindex(picks).fillna(0.0)
        gross = float((w * fwd).sum())
        alln = prev.index.union(w.index)
        turn = 0.5 * float((w.reindex(alln).fillna(0) - prev.reindex(alln).fillna(0)).abs().sum())
        rets.append(gross - turn * rt)
        bench.append(float((C.iloc[j] / C.iloc[i] - 1.0).reindex(u).dropna().mean()))
        turns.append(turn); dates.append(b); prev = w
    return (pd.Series(rets, index=pd.DatetimeIndex(dates)),
            pd.Series(bench, index=pd.DatetimeIndex(dates)),
            float(np.mean(turns)) if turns else 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--signal", choices=list(SPECS), default="momentum")
    ap.add_argument("--variants", action="store_true")
    ap.add_argument("--portfolio", action="store_true")
    ap.add_argument("--ls-portfolio", action="store_true")
    ap.add_argument("--volmanaged", action="store_true", help="H6: vol-target overlay on momentum")
    ap.add_argument("--volmanaged-plain", action="store_true",
                    help="H15: clean Barroso-Santa-Clara — vol-target overlay on PLAIN (equal-wt) momentum")
    ap.add_argument("--seasonality", action="store_true",
                    help="H16: cross-sectional same-calendar-month seasonality (Heston-Sadka)")
    ap.add_argument("--composite", action="store_true",
                    help="H14 (reduced): integrated rank composite (h52high+lowbeta) vs the 50/50 return blend")
    ap.add_argument("--cost-bps", type=float, default=30.0)
    ap.add_argument("--heldout", action="store_true")
    ap.add_argument("--spend-heldout", action="store_true")
    a = ap.parse_args()
    rt = a.cost_bps / 1e4
    window, tag = TRAIN, "TRAIN/in-sample"
    if a.heldout:
        if not a.spend_heldout:
            raise SystemExit("HELD-OUT gated: pass --spend-heldout to spend it ONCE on the chosen set.")
        window, tag = HELDOUT, "HELD-OUT (spent once)"
    C, members = load(a.panel)
    print(f"window: {tag}  {window[0]}..{window[1]}  cost={a.cost_bps:.0f}bps\n")

    if a.volmanaged:
        base, _, _ = backtest(C, members, window, "momentum", 0.20, "invvol", 252, 21, rt)
        eqb = (1 + base).cumprod(); ddb = (eqb / eqb.cummax() - 1).min()
        print(f"  base momentum (volscaled): Sharpe={sharpe(base):.2f}  maxDD={ddb:.1%}  ann_ret={base.mean()*12:.1%}")
        for lev in (1.0, 1.5):
            sc = vol_manage(base, target=0.15, maxlev=lev)
            eqs = (1 + sc).cumprod(); dds = (eqs / eqs.cummax() - 1).min()
            print(f"  vol-managed (target 15%, maxlev {lev}): Sharpe={sharpe(sc):.2f}  maxDD={dds:.1%}  ann_ret={sc.mean()*12:.1%}")
        print("  (H6 wins if Sharpe rises AND maxDD shrinks vs base; maxlev 1.0 = retail no-leverage de-risk)")
        return

    if a.volmanaged_plain:
        # H15: B-S-C as published — overlay on a PLAIN base (H6 overlaid the invvol base: confound).
        # Overlay params inherited verbatim from H6's lock; zero new degrees of freedom.
        plain, _, _ = backtest(C, members, window, "momentum", 0.20, "equal", 252, 21, rt)
        inv, _, _ = backtest(C, members, window, "momentum", 0.20, "invvol", 252, 21, rt)
        for name, r in (("PLAIN momentum (equal-wt)", plain), ("invvol momentum (H1 base)", inv)):
            eq = (1 + r).cumprod(); dd = (eq / eq.cummax() - 1).min()
            print(f"  {name}: Sharpe={sharpe(r):.2f}  maxDD={dd:.1%}  ann_ret={r.mean()*12:.1%}")
        for lev in (1.0, 1.5):
            sc = vol_manage(plain, target=0.15, maxlev=lev)
            eq = (1 + sc).cumprod(); dd = (eq / eq.cummax() - 1).min()
            print(f"  vol-managed PLAIN (target 15%, maxlev {lev}): Sharpe={sharpe(sc):.2f}  maxDD={dd:.1%}  ann_ret={sc.mean()*12:.1%}")
        print("  (H15-A accepts if Sharpe rises AND maxDD shrinks vs PLAIN base;")
        print("   H15-B only if A accepts: best variant must also beat the invvol base on both.)")
        return

    if a.seasonality:
        specs_s = [("H16 seasonality primary (top20%, >=3y)", 0.20, 3),
                   ("H16 seasonality decile  (top10%, >=3y)", 0.10, 3),
                   ("H16 seasonality deep    (top20%, >=5y)", 0.20, 5)]
        res = []
        for label, frac, mo in specs_s:
            r, bm, tn = seasonality_backtest(C, members, window, frac, rt, mo)
            if len(r) < 12:
                print(f"=== {label} ===  only {len(r)} months — skipped"); continue
            res.append((label, block(r, bm, tn, label), len(r)))
        if res:
            srs = [s for _, s, _ in res]; bi = int(np.argmax(srs))
            d, emax = dsr(srs, srs[bi], res[bi][2])
            print(f"\nDSR(best='{res[bi][0]}', of {len(srs)})={d:.1%}  E[max Sharpe|null]={emax:.2f}")
            print("ACCEPT iff best net-Sharpe t>2 AND DSR>0.95 AND positive excess. Binding — no re-tunes.")
        return

    if a.composite:
        ri, bmi, tni = composite_backtest(C, members, window, 0.20, rt)
        block(ri, bmi, tni, "H14 INTEGRATED (rank 50/50 h52high+lowbeta, top20%)")
        h4, _, t4 = backtest(C, members, window, "h52high", 0.20, "equal", 252, 0, rt)
        lb, _, tl = backtest(C, members, window, "lowbeta", 0.20, "equal", 252, 0, rt)
        df = pd.concat({"h4": h4, "lb": lb}, axis=1).dropna()
        blend = 0.5 * df["h4"] + 0.5 * df["lb"]
        eqb = (1 + blend).cumprod(); ddb = (eqb / eqb.cummax() - 1).min()
        eqi = (1 + ri).cumprod(); ddi = (eqi / eqi.cummax() - 1).min()
        both = pd.concat({"i": ri, "bl": blend}, axis=1).dropna()
        print(f"\n  BLEND (current sleeve, 50/50 returns): net_Sharpe={sharpe(blend):.2f}  "
              f"ann={blend.mean()*12:.2%}  maxDD={ddb:.2%}  avg_leg_turn={(t4+tl)/2:.0%}")
        print(f"  INTEGRATED (one book):                 net_Sharpe={sharpe(ri):.2f}  "
              f"ann={ri.mean()*12:.2%}  maxDD={ddi:.2%}  turn={tni:.0%}")
        print(f"  corr(integrated, blend) = {both['i'].corr(both['bl']):+.2f}")
        print("  (H14 ACCEPTS integrated iff it beats the blend on BOTH net Sharpe AND maxDD; tie/split -> keep blend.)")
        return

    if a.portfolio:
        h4, _, _ = backtest(C, members, window, "h52high", 0.20, "equal", 252, 0, rt)
        lb, _, _ = backtest(C, members, window, "lowbeta", 0.20, "equal", 252, 0, rt)
        lv, _, _ = backtest(C, members, window, "lowvol", 0.20, "equal", 252, 0, rt)
        df = pd.concat({"h52high": h4, "lowbeta": lb, "lowvol": lv}, axis=1).dropna()
        print(f"  standalone Sharpe: h52high={sharpe(df['h52high']):.2f}  lowbeta={sharpe(df['lowbeta']):.2f}  lowvol={sharpe(df['lowvol']):.2f}")
        print(f"  corr(h52high, lowbeta) = {df['h52high'].corr(df['lowbeta']):+.2f}   (momentum vs defensive)")
        print(f"  corr(lowbeta, lowvol)  = {df['lowbeta'].corr(df['lowvol']):+.2f}   (defensive twins -> keep one)")
        combo = 0.5 * df["h52high"] + 0.5 * df["lowbeta"]
        eq = (1 + combo).cumprod(); dd = (eq / eq.cummax() - 1).min()
        print(f"\n  SLEEVE  H4 + low-beta (50/50): net_Sharpe={sharpe(combo):.2f}  ann_ret={combo.mean()*12:.2%}  maxDD={dd:.2%}")
        print("  (combo Sharpe > each leg AND lower DD = the sleeve is better than its parts)")
        return

    if a.ls_portfolio:
        ranks = load_ranks(a.panel)
        m = backtest_ls(C, members, ranks, window, "momentum", 0.20, 252, 21, rt)
        l = backtest_ls(C, members, ranks, window, "lowvol", 0.20, 252, 0, rt)
        df = pd.concat({"mom_LS": m, "lowvol_LS": l}, axis=1).dropna()
        print(f"  momentum LS Sharpe={sharpe(df['mom_LS']):.2f} ann={df['mom_LS'].mean()*12:6.2%}")
        print(f"  lowvol   LS Sharpe={sharpe(df['lowvol_LS']):.2f} ann={df['lowvol_LS'].mean()*12:6.2%}")
        print(f"  correlation(mom_LS, lowvol_LS) = {df['mom_LS'].corr(df['lowvol_LS']):+.2f}")
        combo = 0.5 * df["mom_LS"] + 0.5 * df["lowvol_LS"]
        eq = (1 + combo).cumprod(); dd = (eq / eq.cummax() - 1).min()
        print(f"\n  50/50 LS PORTFOLIO: net_Sharpe={sharpe(combo):.2f}  ann_ret={combo.mean()*12:.2%}  maxDD={dd:.2%}")
        return

    specs = SPECS[a.signal]
    if a.variants and not a.heldout:
        pps = {}
        for nm, (f, w, lb, sk) in specs.items():
            r, b, tn = backtest(C, members, window, a.signal, f, w, lb, sk, rt)
            pps[nm] = (block(r, b, tn, f"{a.signal}:{nm}"), len(r))
        vals = [v[0] for v in pps.values()]
        best = max(pps, key=lambda k: pps[k][0])
        d, emax = dsr(vals, pps[best][0], pps[best][1])
        print(f"\nDSR across {len(vals)} variants: best={best} per-period-SR={pps[best][0]:.3f} "
              f"Emax-by-chance={emax:.3f} DSR={d:4.0%}  (accept if >95%)")
        return

    f, w, lb, sk = specs["primary"]
    r, b, tn = backtest(C, members, window, a.signal, f, w, lb, sk, rt)
    block(r, b, tn, f"{a.signal}:primary [{tag}]")


if __name__ == "__main__":
    main()
