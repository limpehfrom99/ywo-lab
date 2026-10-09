"""Log #52-53 (backlog #26-27): Raschke Turtle Soup and 80-20s, rules pre-registered in research/log.md. Uses bt/classic_intraday.py.
Usage: python3 bt/raschke_daily.py [m5]"""
import sys, os, time, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import classic_intraday as ci
from classic_intraday import Bars, stats, show, ROOT


def reclaim(B, a, b, side, lvl, trig, atr):
    """Scan session bars a..b-1: wait for trig (price beyond trig level), then from the next bar a stop entry at lvl.
    Returns (j, e, stop, ambiguous) or None."""
    swept = False; lo = hi = B.O[a]
    for j in range(a, b):
        if swept:
            hit = B.H[j] >= lvl if side == 1 else B.L[j] <= lvl
            if hit:
                e = max(lvl, B.O[j]) if side == 1 else min(lvl, B.O[j])
                newx = B.L[j] < lo if side == 1 else B.H[j] > hi
                ext = lo if side == 1 else hi
                stop = min(ext, e - 0.1 * atr) if side == 1 else max(ext, e + 0.1 * atr)
                return j, e, stop, newx
        lo, hi = min(lo, B.L[j]), max(hi, B.H[j])
        if not swept and ((side == 1 and B.L[j] < trig) or (side == -1 and B.H[j] > trig)): swept = True
    return None


def mk_trade(B, day, j, jend, side, e, stop, amb, nights):
    risk = abs(e - stop)
    if amb:
        R = (-risk - B.cost(j, e, stop)) / risk
        return dict(day=day, side=side, R=R, R_flip=R, stopped=True, amb=True, risk_pct=risk / e)
    X, st = B.run_out(j, jend, side, stop, check_entry=False)
    Xf, stf = B.run_out(j, jend, -side, e + side * risk, check_entry=False)
    return dict(day=day, side=side, R=(side * (X - e) - B.cost(j, e, X, nights)) / risk,
                R_flip=(-side * (Xf - e) - B.cost(j, e, Xf, nights)) / risk, stopped=st, amb=False, risk_pct=risk / e)


def turtle_soup(B, S, hold):
    rows = []; idx = S.index; Lw, Hw = S.L.values, S.H.values
    for n in range(21, len(S) - hold):
        s = S.iloc[n]
        if not np.isfinite(s.atr) or (idx[n + hold] - idx[n]).days > 7: continue
        a, b = int(s.i0), int(s.i1); jend = int(S.i1.iloc[n + hold])
        nights = (idx[n + hold] - idx[n]).days
        for side in (1, -1):
            w = Lw[n - 20:n] if side == 1 else Hw[n - 20:n]
            k = int(np.argmin(w) if side == 1 else np.argmax(w)); lvl = w[k]
            if k > 16: continue                                    # set fewer than 4 sessions ago
            if (side == 1 and s.L >= lvl) or (side == -1 and s.H <= lvl): continue
            r = reclaim(B, a, b, side, lvl, lvl, s.atr)
            if r: rows.append(mk_trade(B, idx[n], r[0], jend, side, r[1], r[2], r[3], nights))
    return pd.DataFrame(rows)


def eighty_twenty(B, S):
    rows = []; idx = S.index
    for n in range(1, len(S)):
        s, p = S.iloc[n], S.iloc[n - 1]
        if not np.isfinite(s.atr) or (idx[n] - idx[n - 1]).days > 4 or p.rng <= 0: continue
        po, pc = (p.O - p.L) / p.rng, (p.C - p.L) / p.rng
        if po >= 0.8 and pc <= 0.2: side, lvl = 1, p.L
        elif po <= 0.2 and pc >= 0.8: side, lvl = -1, p.H
        else: continue
        a, b = int(s.i0), int(s.i1)
        r = reclaim(B, a, b, side, lvl, lvl - side * 0.1 * s.atr, s.atr)
        if r: rows.append(mk_trade(B, idx[n], r[0], b, side, r[1], r[2], r[3], 0))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    t0 = time.time(); out = []; trades = []
    for m in (("TSLA", "AAPL", "US100", "US500") if ci.M5 else ("gold", "US100", "US500", "AAPL", "TSLA")):
        d, bm = ci.load(m); B = Bars(d, m, bm)
        S = B.sessions(0, 0, broker=True) if m == "gold" else B.sessions(570, 960)
        print(f"--- {m} ({len(S)} sessions, {time.time() - t0:.0f}s)", flush=True)
        for hold in (0, 1, 3):
            df = turtle_soup(B, S, hold)
            if len(df) == 0: continue
            df["day"] = pd.to_datetime(df.day); trades.append(df.assign(rule=f"ts{hold}", mkt=m))
            r = stats(f"TurtleSoup {m} exit day+{hold}", df); r["amb"] = df.amb.mean(); out.append(r); show(r); print(f"{'':40s}ambiguous fills {df.amb.mean():.0%}")
        df = eighty_twenty(B, S)
        if len(df):
            df["day"] = pd.to_datetime(df.day); trades.append(df.assign(rule="8020", mkt=m))
            r = stats(f"80-20s {m}", df); r["amb"] = df.amb.mean(); out.append(r); show(r); print(f"{'':40s}ambiguous fills {df.amb.mean():.0%}")
    sfx = "_m5" if ci.M5 else ""
    pd.DataFrame(out).to_csv(os.path.join(ROOT, "results", f"raschke_daily{sfx}.csv"), index=False)
    pd.concat(trades).to_pickle(f"/home/claude/bt/raschke_trades{sfx}.pkl"); print(f"done in {time.time() - t0:.0f}s")
