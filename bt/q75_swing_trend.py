"""Log #75 / backlog #37 (Clenow trend) and #39 (trend exit grid) — every symbol; pre-registered, run unchanged.

#37 Clenow ("Following the Trend"). Signal at a completed bar's close: EMA50 > EMA100 and the close is the highest close of the
  last 50 bars (current included) -> long at the next bar's open; EMA50 < EMA100 and the lowest close of 50 -> short. One position
  per symbol. Exit = 3 x ATR(20) trailing stop, ATR (simple 20-bar mean of the true range) taken at the signal bar and fixed;
  stop = best close since entry - 3 ATR (the entry price counts as the first 'best', so the initial stop is entry - 3 ATR and the
  stop never loosens); stop order intrabar, fills at the stop or at the open if a bar gaps through it. R = P/L after costs and
  swaps / (3 x ATR at entry). D1 (export file, full history) primary; H4 (server clock) and H1 from the intraday file.
  Group portfolios (D1): equal risk (1R = 3 ATR per position), daily mark-to-market R summed over the group's symbols.
#39 Exit grid. Entries: close above the highest high of the previous N bars -> long next open; close below the lowest low of
  the previous N bars -> short; N in {20, 55}. One exit rule per cell, nothing else (no extra stop):
  chand2/3/4 = k x ATR(20, at entry, fixed) below the highest high since entry (entry price = first 'high'), intrabar stop;
  chan10 = a close below the lowest low of the previous 10 bars (shorts: above the 10-bar high) -> out next open;
  sma50 = a close below the 50-bar SMA (shorts: above) -> out next open; time20 / time60 = out at the open 20 / 60 bars after entry.
  R = P/L after costs / (2 x ATR(20) at entry) in EVERY cell. One position at a time per cell. D1 primary, H4 too.
Baselines (both ideas): per real trade, 5 random entry bars of the same symbol/timeframe (uniform over bars where the indicators
  exist), same direction, same exit rule, same R unit; the cell's baseline = the mean of those random trades.
Walk-forward exit choice (#39): per group x timeframe x N, each year pick the exit with the best pooled mean R over the 3 previous
  years (>= 30 trades), trade it that year (done in q75_swing_report.py from the year rows).
Costs: entry bar's spread x 1.2 + commission x (|entry| + |exit|) + swap per 17:00 New York rollover held (q75_swing_common).
python3 bt/q75_swing_trend.py [--symbols A,B] [--only clenow|grid]
"""
import sys, os, time, argparse, zlib
import numpy as np, pandas as pd
from numba import njit

sys.path.insert(0, "/home/claude/ywo-lab/bt")
import q75_swing_common as C  # noqa: E402
U = C.U
M_RAND = 5
GRID_EXITS = [("chand2", 0, 2.0, 0), ("chand3", 0, 3.0, 0), ("chand4", 0, 4.0, 0), ("chan10", 1, 0.0, 0), ("sma50", 2, 0.0, 0),
              ("time20", 3, 0.0, 20), ("time60", 3, 0.0, 60)]


@njit(cache=True)
def exit_sim(o, h, l, c, ll10, hh10, sma50, e, d, E, A, kind, k, tmax):
    """kind 0 chandelier (k ATR from the best high/low since entry, intrabar), 1 opposite 10-bar channel close, 2 close beyond
    SMA50, 3 time exit after tmax bars, 4 Clenow 3-ATR trailing from the best close. Returns (exit price, exit bar, how):
    how 0 = next-open exit, 1 = stop, 2 = end of data."""
    n = len(c)
    if kind == 0 or kind == 4:
        best = E
        st = E - d * k * A
        for j in range(e, n):
            if d == 1:
                if l[j] <= st: return (st if o[j] > st else o[j]), j, 1
                if kind == 0:
                    if h[j] > best: best = h[j]
                else:
                    if c[j] > best: best = c[j]
                ns = best - k * A
                if ns > st: st = ns
            else:
                if h[j] >= st: return (st if o[j] < st else o[j]), j, 1
                if kind == 0:
                    if l[j] < best: best = l[j]
                else:
                    if c[j] < best: best = c[j]
                ns = best + k * A
                if ns < st: st = ns
        return c[n - 1], n - 1, 2
    if kind == 3:
        x = e + tmax
        if x < n: return o[x], x, 0
        return c[n - 1], n - 1, 2
    for j in range(e, n):
        if kind == 1:
            hit = (c[j] < ll10[j]) if d == 1 else (c[j] > hh10[j])
        else:
            hit = (c[j] < sma50[j]) if d == 1 else (c[j] > sma50[j])
        if hit:
            if j + 1 < n: return o[j + 1], j + 1, 0
            return c[j], j, 2
    return c[n - 1], n - 1, 2


@njit(cache=True)
def run_rule(o, h, l, c, sig, atr, ll10, hh10, sma50, start, kind, k, tmax):
    """sig[i] = +1 / -1 / 0 signal at the close of bar i. One position at a time. Returns per-trade arrays."""
    n = len(c)
    S_i = np.empty(n, np.int64); E_i = np.empty(n, np.int64); X_i = np.empty(n, np.int64); D = np.empty(n, np.int64)
    EP = np.empty(n); XP = np.empty(n); AT = np.empty(n); HW = np.empty(n, np.int64)
    nt = 0; i = start
    while i < n - 1:
        d = sig[i]
        if d == 0 or not (atr[i] > 0):
            i += 1; continue
        e = i + 1; E = o[e]; A = atr[i]
        xp, xi, how = exit_sim(o, h, l, c, ll10, hh10, sma50, e, d, E, A, kind, k, tmax)
        S_i[nt] = i; E_i[nt] = e; X_i[nt] = xi; D[nt] = d; EP[nt] = E; XP[nt] = xp; AT[nt] = A; HW[nt] = how; nt += 1
        i = xi if xi > i else i + 1
    return S_i[:nt], E_i[:nt], X_i[:nt], D[:nt], EP[:nt], XP[:nt], AT[:nt], HW[:nt]


@njit(cache=True)
def run_random(o, h, l, c, atr, ll10, hh10, sma50, start, kind, k, tmax, dirs, m, seed):
    """For each direction in dirs, m random signal bars in [start, n-2] with atr > 0; same exit. Returns per-trade arrays."""
    np.random.seed(seed)
    n = len(c)
    tot = len(dirs) * m
    S_i = np.empty(tot, np.int64); E_i = np.empty(tot, np.int64); X_i = np.empty(tot, np.int64); D = np.empty(tot, np.int64)
    EP = np.empty(tot); XP = np.empty(tot); AT = np.empty(tot); PAIR = np.empty(tot, np.int64)
    nt = 0
    for q in range(len(dirs)):
        for r in range(m):
            for _ in range(100):
                i = np.random.randint(start, n - 1)
                if atr[i] > 0: break
            if not (atr[i] > 0): continue
            d = dirs[q]; e = i + 1; E = o[e]; A = atr[i]
            xp, xi, how = exit_sim(o, h, l, c, ll10, hh10, sma50, e, d, E, A, kind, k, tmax)
            S_i[nt] = i; E_i[nt] = e; X_i[nt] = xi; D[nt] = d; EP[nt] = E; XP[nt] = xp; AT[nt] = A; PAIR[nt] = q; nt += 1
    return S_i[:nt], E_i[:nt], X_i[:nt], D[:nt], EP[:nt], XP[:nt], AT[:nt], PAIR[:nt]


def indicators(x):
    o, h, l, c = (x[k].values.astype(float) for k in ("open", "high", "low", "close"))
    H, L, Cs = pd.Series(h), pd.Series(l), pd.Series(c)
    pc = Cs.shift(1)
    tr = pd.concat([H - L, (H - pc).abs(), (L - pc).abs()], axis=1).max(axis=1)
    I = dict(o=o, h=h, l=l, c=c, atr=tr.rolling(20).mean().fillna(0).values,
             hh10=H.rolling(10).max().shift(1).fillna(np.inf).values, ll10=L.rolling(10).min().shift(1).fillna(-np.inf).values,
             sma50=Cs.rolling(50).mean().fillna(0).values)
    for N in (20, 55):
        hh = H.rolling(N).max().shift(1).values; ll = L.rolling(N).min().shift(1).values
        s = np.where(c > hh, 1, np.where(c < ll, -1, 0)); s[~(np.isfinite(hh) & np.isfinite(ll))] = 0
        I[f"sig{N}"] = s.astype(np.int64)
    e50 = Cs.ewm(span=50, adjust=False).mean().values; e100 = Cs.ewm(span=100, adjust=False).mean().values
    hc = Cs.rolling(50).max().values; lc = Cs.rolling(50).min().values
    s = np.where((e50 > e100) & (c >= hc), 1, np.where((e50 < e100) & (c <= lc), -1, 0)); s[~np.isfinite(hc)] = 0
    I["sig_clenow"] = s.astype(np.int64)
    return I


def costs_R(I, sp, t, sw, comm, E_i, X_i, how, D, EP, XP, risk):
    spc = sp[E_i] * 1.2
    t_in = t[E_i]; t_out = t[X_i]
    swp = sw.nights(t_in, t_out) * sw.per_night(D, EP)
    return (D * (XP - EP) - spc - comm * (np.abs(EP) + np.abs(XP)) - swp) / risk


def mtm_daily(c, t, sp, sw, comm, E_i, X_i, D, EP, XP, risk):
    """Daily (per D1 bar) mark-to-market R of a set of trades; sums to each trade's R."""
    n = len(c); out = np.zeros(n)
    nb = np.r_[0.0, sw.nights(t[:-1], t[1:])]
    for e, x, d, E, X, r in zip(E_i, X_i, D, EP, XP, risk):
        pn = float(sw.per_night(d, E)); sp_e = sp[e] * 1.2
        if x <= e:
            out[e] += (d * (X - E) - sp_e - comm * (abs(E) + abs(X))) / r; continue
        out[e] += (d * (c[e] - E) - sp_e - comm * abs(E)) / r
        if x - 1 > e:
            j = np.arange(e + 1, x)
            out[j] += (d * (c[j] - c[j - 1]) - nb[j] * pn) / r
        out[x] += (d * (X - c[x - 1]) - comm * abs(X) - nb[x] * pn) / r
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--symbols", default=""); ap.add_argument("--only", default="")
    a = ap.parse_args()
    cat = U.catalog(); syms = a.symbols.split(",") if a.symbols else C.symbols(cat)
    P = {k: os.path.join(C.RES, f"q75_swing_{k}") for k in ("clenow", "exitgrid")}
    for k in P.values():
        for suf in ("_years.csv", "_cells.csv", "_d1_trades.csv", "_portfolio_daily.csv"):
            if os.path.exists(k + suf): os.remove(k + suf)
    port = {}                                                       # group -> daily R Series (Clenow D1)
    t0 = time.time()
    for si, sym in enumerate(syms):
        grp = U.group_of(sym); comm = U.commission_of(sym)
        intra, btf, rel = C.load_intraday(sym, cat)
        d1 = C.load_d1(sym, cat, intra, rel)
        frames = {}
        if d1 is not None and len(d1) > 300: frames["D1"] = d1
        if intra is not None:
            for tf in ("H4", "H1"): frames[tf] = C.resample(intra, tf)
        del intra
        tmin = min(C.ns(f.index)[0] for f in frames.values()); tmax = max(C.ns(f.index)[-1] for f in frames.values())
        p_ref = max(frames.values(), key=lambda f: f.index[-1]).close.iloc[-1]
        sw = C.Swaps(sym, tmin, tmax, p_ref)
        Y = {"clenow": [], "exitgrid": []}; Cl = {"clenow": [], "exitgrid": []}; d1_trades = []
        for tf, x in frames.items():
            if len(x) < 300: continue
            acc = {}                                                # (idea, cell) -> list of per-segment trade frames
            for sa, sb in C.segments(C.ns(x.index)):
                if sb - sa < 200: continue
                xs = x.iloc[sa:sb]
                I = indicators(xs); t = C.ns(xs.index); sp = xs.sp.values.astype(float)
                args = (I["o"], I["h"], I["l"], I["c"])
                jobs = []
                if a.only in ("", "clenow"):
                    jobs.append(("clenow", "clenow_3atr", I["sig_clenow"], 100, 4, 3.0, 0, 3.0))
                if a.only in ("", "grid") and tf in ("D1", "H4"):
                    for N in (20, 55):
                        for name, kind, k, tm in GRID_EXITS:
                            jobs.append(("exitgrid", f"N{N}_{name}", I[f"sig{N}"], 60, kind, k, tm, 2.0))
                for idea, cell, sig, start, kind, k, tm, runit in jobs:
                    S_i, E_i, X_i, D, EP, XP, AT, HW = run_rule(*args, sig, I["atr"], I["ll10"], I["hh10"], I["sma50"], start, kind, k, tm)
                    if len(E_i) == 0: continue
                    risk = runit * AT
                    R = costs_R(I, sp, t, sw, comm, E_i, X_i, HW, D, EP, XP, risk)
                    rs = run_random(*args, I["atr"], I["ll10"], I["hh10"], I["sma50"], start, kind, k, tm, D, M_RAND,
                                    zlib.crc32(f"{sym}|{tf}|{cell}|{sa}".encode()) & 0x7FFFFFFF)
                    Rr = costs_R(I, sp, t, sw, comm, rs[1], rs[2], None, rs[3], rs[4], rs[5], runit * rs[6])
                    base = pd.Series(Rr).groupby(rs[7]).mean().reindex(range(len(R))).values
                    acc.setdefault((idea, cell), []).append(pd.DataFrame(dict(t=t[E_i], t_exit=t[X_i], side=D, R=R, base=base,
                                                                              hold=X_i - E_i)))
                    if idea == "clenow" and tf == "D1":
                        daily = mtm_daily(I["c"], t, sp, sw, comm, E_i, X_i, D, EP, XP, risk)
                        s = pd.Series(daily, index=C.to_server(xs.index).normalize()).groupby(level=0).sum()
                        port[grp] = s if grp not in port else port[grp].add(s, fill_value=0.0)
            yrs_span = max((C.ns(x.index)[-1] - C.ns(x.index)[0]) / 3.156e16, 0.5)
            for (idea, cell), parts in acc.items():
                T = pd.concat(parts, ignore_index=True)
                R, D = T.R.values, T.side.values
                Y[idea] += C.year_rows(R, T.t.values, T.base.values, idea=idea, symbol=sym, group=grp, tf=tf, cell=cell)
                st = C.stats_from_years(pd.DataFrame(C.year_rows(R, T.t.values, T.base.values))); st.pop("by_year", None)
                Cl[idea].append(dict(symbol=sym, group=grp, tf=tf, cell=cell, start=str(x.index[0].date()), **st,
                                     longs=R[D == 1].mean() if (D == 1).any() else np.nan,
                                     shorts=R[D == -1].mean() if (D == -1).any() else np.nan,
                                     hold_med=float(T.hold.median()), per_yr=len(R) / yrs_span))
                if idea == "clenow" and tf == "D1":
                    d1_trades.append(T.assign(symbol=sym, group=grp))
                if idea == "clenow" or cell in ("N20_chand3", "N55_chand3"):
                    print(f"  {sym:11s} {tf:3s} {cell:12s} " + C.fmt_stats(st), flush=True)
        for idea in ("clenow", "exitgrid"):
            C.append_csv(pd.DataFrame(Y[idea]), P[idea] + "_years.csv")
            C.append_csv(pd.DataFrame(Cl[idea]), P[idea] + "_cells.csv")
        if d1_trades: C.append_csv(pd.concat(d1_trades), P["clenow"] + "_d1_trades.csv")
        print(f"{sym} done ({si + 1}/{len(syms)}) {time.time() - t0:.0f}s", flush=True)
        del frames
    if port:
        pd.DataFrame(port).fillna(0.0).sort_index().to_csv(P["clenow"] + "_portfolio_daily.csv", float_format="%.5g")


if __name__ == "__main__":
    main()
