"""Log #75 / backlog #33 — Bollinger squeeze breakout, every symbol x M5, M15, M30, H1, H4, D1 (pre-registered, run unchanged).

Rule (fixed before running):
- BB(20, 2) on closes (population std, as Bollinger). BandWidth = (upper - lower) / middle. Squeeze bar = BandWidth at its
  lowest of the last 125 bars (current bar included).
- Within the next 20 bars after a squeeze bar, the first CLOSE outside the bands -> enter at the next bar's open in that direction
  (a close outside the bands while armed always disarms the window: "first" close outside, even if a position is open then).
- Stop = the middle band of the signal bar (the last completed bar at entry), fixed. Trades whose entry open is already beyond the
  stop are skipped (counted); so are stops closer than 0.2 bp of price (xgrid's data-artefact rule).
- Exit at the next bar's open after a close back inside the bands; the stop is checked first on every bar from the entry bar on and
  fills at the stop, or at the bar's open if the bar gaps through it. One position at a time.
- Coin flip: same entry moment and price, opposite direction, stop at the same distance on the other side (checked first), exit at
  the next open after the same close-back-inside condition (the breakout failing) if not stopped earlier.
- Costs: entry bar's spread x 1.2 + commission x (|entry| + |exit|) + swaps per 17:00 New York rollover held.
  R = P/L after costs / |entry - stop|.
Output: results/q75_swing_squeeze_years.csv (per symbol x tf x year sufficient stats), _cells.csv (per symbol x tf),
_primary_trades.csv (gold D1/H4 and every index D1, for BCa / permutation).
python3 bt/q75_swing_squeeze.py [--symbols A,B]
"""
import sys, os, time, argparse
import numpy as np, pandas as pd
from numba import njit

sys.path.insert(0, "/home/claude/ywo-lab/bt")
import q75_swing_common as C  # noqa: E402
U = C.U

TFS = ("M5", "M15", "M30", "H1", "H4", "D1")


@njit(cache=True)
def kernel(o, h, l, c, mid, up, lo, sq, n_win):
    n = len(c)
    E_i = np.empty(n, np.int64); X_i = np.empty(n, np.int64); D = np.empty(n, np.int64); K = np.empty(n, np.int64)
    EP = np.empty(n); XP = np.empty(n); ST = np.empty(n); CXP = np.empty(n); CX_i = np.empty(n, np.int64); SIG = np.empty(n, np.int64)
    nt = 0; skipped = 0
    a_from = 1; a_to = -1
    pos = 0; e = -1; stop = 0.0
    for i in range(n):
        if pos != 0 and i >= e:
            if pos == 1:
                if l[i] <= stop:
                    XP[nt - 1] = stop if o[i] > stop else o[i]; X_i[nt - 1] = i; K[nt - 1] = 1; pos = 0
                elif c[i] <= up[i]:
                    if i + 1 < n:
                        XP[nt - 1] = o[i + 1]; X_i[nt - 1] = i + 1; K[nt - 1] = 0
                    else:
                        XP[nt - 1] = c[i]; X_i[nt - 1] = i; K[nt - 1] = 2
                    pos = 0
            else:
                if h[i] >= stop:
                    XP[nt - 1] = stop if o[i] < stop else o[i]; X_i[nt - 1] = i; K[nt - 1] = 1; pos = 0
                elif c[i] >= lo[i]:
                    if i + 1 < n:
                        XP[nt - 1] = o[i + 1]; X_i[nt - 1] = i + 1; K[nt - 1] = 0
                    else:
                        XP[nt - 1] = c[i]; X_i[nt - 1] = i; K[nt - 1] = 2
                    pos = 0
            if pos != 0 and i == n - 1:                       # data ends in the trade
                XP[nt - 1] = c[i]; X_i[nt - 1] = i; K[nt - 1] = 2; pos = 0
        if sq[i]:
            a_from = i + 1; a_to = i + n_win
        if i >= a_from and i <= a_to and (c[i] > up[i] or c[i] < lo[i]):
            d = 1 if c[i] > up[i] else -1
            a_to = -1
            if pos == 0 and i + 1 < n:
                E = o[i + 1]; st = mid[i]; risk = d * (E - st)
                if risk <= 0 or risk < 2e-5 * abs(E):
                    skipped += 1
                    continue
                pos = d; e = i + 1; stop = st
                E_i[nt] = e; D[nt] = d; EP[nt] = E; ST[nt] = st; SIG[nt] = i
                X_i[nt] = -1; XP[nt] = np.nan; K[nt] = -1
                # coin: opposite side, same distance, same band-reentry exit
                cst = E + d * risk; cx = np.nan; ci = -1
                for k in range(e, n):
                    if d == 1:
                        if h[k] >= cst:
                            cx = cst if o[k] < cst else o[k]; ci = k; break
                        if c[k] <= up[k]:
                            if k + 1 < n:
                                cx = o[k + 1]; ci = k + 1
                            else:
                                cx = c[k]; ci = k
                            break
                    else:
                        if l[k] <= cst:
                            cx = cst if o[k] > cst else o[k]; ci = k; break
                        if c[k] >= lo[k]:
                            if k + 1 < n:
                                cx = o[k + 1]; ci = k + 1
                            else:
                                cx = c[k]; ci = k
                            break
                if ci < 0:
                    cx = c[n - 1]; ci = n - 1
                CXP[nt] = cx; CX_i[nt] = ci
                nt += 1
    return E_i[:nt], X_i[:nt], D[:nt], K[:nt], EP[:nt], XP[:nt], ST[:nt], CXP[:nt], CX_i[:nt], SIG[:nt], skipped


def bands(c):
    s = pd.Series(c)
    mid = s.rolling(20).mean(); sd = s.rolling(20).std(ddof=0)
    up = mid + 2 * sd; lo = mid - 2 * sd
    w = (up - lo) / mid
    wmin = w.rolling(125).min()
    sq = (w <= wmin * (1 + 1e-12)) & w.notna() & wmin.notna()
    return mid.values, up.values, lo.values, sq.values


def run_frame(x, sym, tf, sw, comm):
    """Runs the rule on each contiguous segment of x (no trade spans a data hole > 10 days)."""
    out, skipped_all, nsq_all = [], 0, 0
    for a, b in C.segments(C.ns(x.index)):
        if b - a < 200: continue
        xs = x.iloc[a:b]
        o, h, l, c = (xs[k].values.astype(float) for k in ("open", "high", "low", "close"))
        t = C.ns(xs.index); sp = xs.sp.values.astype(float)
        mid, up, lo, sq = bands(c)
        mid = np.nan_to_num(mid, nan=0.0); up = np.nan_to_num(up, nan=np.inf); lo = np.nan_to_num(lo, nan=-np.inf)
        E_i, X_i, D, K, EP, XP, ST, CXP, CX_i, SIG, skipped = kernel(o, h, l, c, mid, up, lo, sq, 20)
        skipped_all += skipped; nsq_all += int(sq.sum())
        if len(E_i) == 0: continue
        risk = D * (EP - ST)
        t_in = t[E_i]; t_out = t[X_i]; t_cout = t[CX_i]
        spc = sp[E_i] * 1.2
        sw_r = sw.nights(t_in, t_out) * sw.per_night(D, EP)
        sw_c = sw.nights(t_in, t_cout) * sw.per_night(-D, EP)
        R = (D * (XP - EP) - spc - comm * (np.abs(EP) + np.abs(XP)) - sw_r) / risk
        Rc = (-D * (CXP - EP) - spc - comm * (np.abs(EP) + np.abs(CXP)) - sw_c) / risk
        out.append(pd.DataFrame(dict(t=t_in, side=D, R=R, coin=Rc, hold=X_i - E_i, stopped=(K == 1), risk_bp=risk / EP * 1e4,
                                     cost_R=(spc + comm * (np.abs(EP) + np.abs(XP)) + sw_r) / risk)))
    if not out: return None, skipped_all, nsq_all
    return pd.concat(out, ignore_index=True), skipped_all, nsq_all


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--symbols", default=""); ap.add_argument("--tag", default="")
    a = ap.parse_args()
    cat = U.catalog(); syms = a.symbols.split(",") if a.symbols else C.symbols(cat)
    pre = os.path.join(C.RES, f"q75_swing_squeeze{a.tag}")
    for suf in ("_years.csv", "_cells.csv", "_primary_trades.csv"):
        if os.path.exists(pre + suf): os.remove(pre + suf)
    t0 = time.time()
    for sym in syms:
        grp = U.group_of(sym); comm = U.commission_of(sym)
        intra, btf, rel = C.load_intraday(sym, cat)
        d1 = C.load_d1(sym, cat, intra, rel)
        frames = {}
        if intra is not None:
            if btf == "M5": frames["M5"] = intra
            frames["M15"] = intra if btf == "M15" else C.resample(intra, "M15")
            for tf in ("M30", "H1", "H4"): frames[tf] = C.resample(intra, tf)
        if d1 is not None and len(d1) > 200: frames["D1"] = d1
        tmin = min(C.ns(f.index)[0] for f in frames.values()); tmax = max(C.ns(f.index)[-1] for f in frames.values())
        p_ref = max(frames.values(), key=lambda f: f.index[-1]).close.iloc[-1]
        sw = C.Swaps(sym, tmin, tmax, p_ref)
        yrows, crows, prim = [], [], []
        for tf in TFS:
            if tf not in frames or len(frames[tf]) < 300: continue
            T, skipped, nsq = run_frame(frames[tf], sym, tf, sw, comm)
            if T is None: continue
            yrows += C.year_rows(T.R.values, T.t.values, T.coin.values, idea="squeeze", symbol=sym, group=grp, tf=tf, cell="BB20_2_sq125")
            st = C.stats_from_years(pd.DataFrame(C.year_rows(T.R.values, T.t.values, T.coin.values)))
            st.pop("by_year", None)
            crows.append(dict(symbol=sym, group=grp, tf=tf, start=str(frames[tf].index[0].date()), bars=len(frames[tf]), squeezes=nsq,
                              skipped=skipped, **st, longs=T.R[T.side == 1].mean(), shorts=T.R[T.side == -1].mean(),
                              stopped=T.stopped.mean(), hold_med=T.hold.median(), risk_bp_med=T.risk_bp.median(),
                              cost_R_med=T.cost_R.median()))
            if (sym == "XAUUSD" and tf in ("D1", "H4")) or (grp in ("us_index", "index") and tf == "D1"):
                prim.append(T.assign(symbol=sym, tf=tf))
            print(f"  {sym:11s} {tf:3s} " + C.fmt_stats(st), flush=True)
        C.append_csv(pd.DataFrame(yrows), pre + "_years.csv")
        C.append_csv(pd.DataFrame(crows), pre + "_cells.csv")
        if prim: C.append_csv(pd.concat(prim), pre + "_primary_trades.csv")
        print(f"{sym} done {time.time() - t0:.0f}s", flush=True)
        del frames, intra, d1


if __name__ == "__main__":
    main()
