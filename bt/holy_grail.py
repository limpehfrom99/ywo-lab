"""Log #54 (backlog #28): Raschke Holy Grail — ADX(14) > 30 and rising, first pullback to the 20-EMA, stop entry beyond the pullback bar,
stop at the pullback extreme, target the 20-bar swing extreme. Rules pre-registered in research/log.md."""
import sys, os, time, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import classic_intraday as ci
from classic_intraday import stats, show, ROOT

AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "sp": "mean"}


def to_srv(idx):
    return idx.tz_localize("UTC").tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)


def build(base, tf):
    x = base.copy(); x["srv"] = to_srv(base.index); x["bi"] = np.arange(len(base))
    key = x.srv.dt.floor("4h") if tf == "H4" else x.srv.dt.normalize()
    g = x.groupby(key.values)
    b = g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), i0=("bi", "first"), i1=("bi", "last"))
    b["i1"] += 1
    return b[b.index.weekday < 5] if tf == "D1" else b


def adx(b, n=14):
    h, l, c = b.high.values, b.low.values, b.close.values
    up = np.r_[0, h[1:] - h[:-1]]; dn = np.r_[0, l[:-1] - l[1:]]
    pdm = np.where((up > dn) & (up > 0), up, 0.0); mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = np.maximum.reduce([h - l, np.abs(h - np.r_[c[0], c[:-1]]), np.abs(l - np.r_[c[0], c[:-1]])])
    w = lambda x: pd.Series(x).ewm(alpha=1 / n, adjust=False).mean().values
    atr = w(tr); pdi = 100 * w(pdm) / atr; mdi = 100 * w(mdm) / atr
    dx = 100 * np.abs(pdi - mdi) / np.maximum(pdi + mdi, 1e-12)
    return w(dx), pdi, mdi


def run(B, b):
    A, PDI, MDI = adx(b); E = b.close.ewm(span=20, adjust=False).mean().values
    H, L, C = b.high.values, b.low.values, b.close.values; I0, I1 = b.i0.values, b.i1.values
    BH, BL, BO, BC = B.H, B.L, B.O, B.C; rows = []; t = 30; n = len(b)
    while t < n - 4:
        side = 0
        if A[t - 1] > 30 and A[t - 1] > A[t - 2]:
            if PDI[t - 1] > MDI[t - 1] and L[t] <= E[t] and L[t - 1] > E[t - 1]: side = 1
            elif MDI[t - 1] > PDI[t - 1] and H[t] >= E[t] and H[t - 1] < E[t - 1]: side = -1
        if side == 0: t += 1; continue
        tgt = H[t - 20:t].max() if side == 1 else L[t - 20:t].min()
        ext = L[t] if side == 1 else H[t]; lvl = H[t] if side == 1 else L[t]; fill = None
        for u in range(t + 1, t + 4):
            for j in range(I0[u], I1[u]):
                if (side == 1 and BH[j] >= lvl) or (side == -1 and BL[j] <= lvl):
                    fill = (u, j, max(lvl, BO[j]) if side == 1 else min(lvl, BO[j])); break
                ext = min(ext, BL[j]) if side == 1 else max(ext, BH[j])
            if fill: break
            lvl = min(lvl, H[u]) if side == 1 else max(lvl, L[u])
        if not fill: t += 1; continue
        u, j, e = fill
        if side * (tgt - e) <= 0: t = u + 1; continue
        stop = ext; risk = abs(e - stop)
        if risk <= 0: t = u + 1; continue
        jend = I1[min(u + 20, n - 1)]
        X = ex(B, j, jend, side, stop, tgt, True); Xf = ex(B, j, jend, -side, e + side * risk, 2 * e - tgt, False)
        nights = max(0, (pd.Timestamp(B.t[jend - 1]) - pd.Timestamp(B.t[j])).days)
        nights += 2 * sum(1 for d in pd.date_range(pd.Timestamp(B.t[j]).normalize(), pd.Timestamp(B.t[jend - 1]).normalize()) if d.weekday() == 4) if nights else 0
        rows.append(dict(day=pd.Timestamp(B.t[j]), side=side, R=(side * (X[0] - e) - B.cost(j, e, X[0], X[1])) / risk,
                         R_flip=(-side * (Xf[0] - e) - B.cost(j, e, Xf[0], Xf[1])) / risk, stopped=X[2], risk_pct=risk / e,
                         rr=abs(tgt - e) / risk))
        t = u + 1
    return pd.DataFrame(rows)


def ex(B, j, jend, side, stop, tgt, check_entry):
    """-> (exit price, nights held, stopped). Stop first; target from the next base bar; conservative fill bar."""
    H, L, O = B.H, B.L, B.O; t0 = pd.Timestamp(B.t[j])
    nts = lambda i: (pd.Timestamp(B.t[i]).normalize() - t0.normalize()).days
    if check_entry and ((side == 1 and L[j] <= stop) or (side == -1 and H[j] >= stop)): return stop, 0, True
    for i in range(j + 1, jend):
        if side == 1:
            if O[i] <= stop: return O[i], nts(i), True
            if L[i] <= stop: return stop, nts(i), True
            if H[i] >= tgt: return max(tgt, O[i]) if O[i] >= tgt else tgt, nts(i), False
        else:
            if O[i] >= stop: return O[i], nts(i), True
            if H[i] >= stop: return stop, nts(i), True
            if L[i] <= tgt: return tgt, nts(i), False
    return B.C[jend - 1], nts(jend - 1), False


if __name__ == "__main__":
    t0 = time.time(); out = []; trades = []
    for m in ("gold", "US100", "US500"):
        d, bm = ci.load(m); B = ci.Bars(d, m, bm)
        B.cost = lambda j, e, x, nights=0, B=B: B.sp[j] + B.comm * (abs(e) + abs(x)) + nights * 0.0001 * abs(e)
        for tf in ("D1", "H4"):
            b = build(d, tf); df = run(B, b)
            if len(df) == 0: print(m, tf, "no trades"); continue
            trades.append(df.assign(mkt=m, tf=tf))
            r = stats(f"HolyGrail {m} {tf}", df); r["rr"] = df.rr.median(); out.append(r); show(r)
            print(f"{'':40s}median target {df.rr.median():.1f}R, stopped {df.stopped.mean():.0%}  ({time.time() - t0:.0f}s)", flush=True)
    pd.DataFrame(out).to_csv(os.path.join(ROOT, "results", "holy_grail.csv"), index=False)
    pd.concat(trades).to_pickle("/home/claude/bt/holy_grail_trades.pkl"); print(f"done in {time.time() - t0:.0f}s")
