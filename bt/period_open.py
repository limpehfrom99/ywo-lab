import pandas as pd, numpy as np
COMM = 0.000007
def sim(o, h, l, c, sp, i, dr, stop, tgt, j_end):
    entry = o[i]; risk = (entry - stop) * dr
    if risk <= 0: return None
    exit_px, why = c[j_end], "time"
    for j in range(i, j_end + 1):
        if dr == 1:
            if l[j] <= stop: exit_px, why = min(stop, o[j]), "stop"; break
            if tgt is not None and h[j] >= tgt: exit_px, why = max(tgt, o[j]), "target"; break
        else:
            if h[j] >= stop: exit_px, why = max(stop, o[j]), "stop"; break
            if tgt is not None and l[j] <= tgt: exit_px, why = min(tgt, o[j]), "target"; break
    cost = sp[i] + COMM * (entry + exit_px)
    return {"R": (dr * (exit_px - entry) - cost) / risk, "cost_R": cost / risk, "why": why}

def four_hour_open(g, candle_min=5, target_r=2.0, hold_min=240):
    """At every 4-hour boundary (UTC), trade the direction of the first candle_min minutes, stop at its far end."""
    o, h, l, c, sp = (g[k].values for k in ["open", "high", "low", "close", "sp"]); T = g.index
    bnd = T[(T.hour % 4 == 0) & (T.minute == 0)]
    pos = T.get_indexer(bnd); out = []
    for i0, t0 in zip(pos, bnd):
        if t0.weekday() == 5 or t0.weekday() == 6: continue
        i1 = T.searchsorted(t0 + pd.Timedelta(minutes=candle_min))      # first bar at/after the candle end
        if i1 >= len(T) - 2 or (T[i1] - t0) > pd.Timedelta(minutes=candle_min + 3): continue
        hi, lo, op, cl = h[i0:i1].max(), l[i0:i1].min(), o[i0], c[i1 - 1]
        if cl == op: continue
        dr = 1 if cl > op else -1; stop = lo if dr == 1 else hi; entry = o[i1]; risk = (entry - stop) * dr
        if risk <= 0: continue
        j_end = min(len(T) - 1, T.searchsorted(t0 + pd.Timedelta(minutes=hold_min)) - 1)
        r = sim(o, h, l, c, sp, i1, dr, stop, entry + dr * target_r * risk if target_r else None, j_end)
        if r: r.update({"t": t0, "hour": t0.hour}); out.append(r)
    return pd.DataFrame(out)

def period_open(g, period="M", candle_min=5, hold_days=1):
    """First candle_min minutes of the first trading day of each period; trade its direction; exit at the close of day hold_days."""
    o, h, l, c, sp = (g[k].values for k in ["open", "high", "low", "close", "sp"]); T = g.index
    day = T.normalize(); days = pd.Index(sorted(set(day)))
    per = pd.Series(days.to_period(period), index=days)
    firsts = per.groupby(per).apply(lambda s: s.index.min())
    out = []
    for p, d0 in firsts.items():
        i0 = T.searchsorted(d0); t0 = T[i0]
        i1 = T.searchsorted(t0 + pd.Timedelta(minutes=candle_min))
        if i1 >= len(T) - 2: continue
        hi, lo, op, cl = h[i0:i1].max(), l[i0:i1].min(), o[i0], c[i1 - 1]
        if cl == op: continue
        dr = 1 if cl > op else -1; stop = lo if dr == 1 else hi; entry = o[i1]; risk = (entry - stop) * dr
        if risk <= 0: continue
        k = days.get_loc(d0); dend = days[min(k + hold_days - 1, len(days) - 1)]
        j_end = T.searchsorted(dend + pd.Timedelta(days=1)) - 1
        r = sim(o, h, l, c, sp, i1, dr, stop, None, j_end)
        if r: r.update({"t": t0, "period": str(p)}); out.append(r)
    return pd.DataFrame(out)

def stats(df, label):
    if len(df) < 5: return {"version": label, "trades": len(df)}
    R = df.R; yr = df.t.dt.year
    return {"version": label, "trades": len(df), "win%": round((R > 0).mean() * 100), "avg R": round(R.mean(), 3),
            "t": round(R.mean() / R.std() * np.sqrt(len(R)), 1), "cost R": round(df.cost_R.mean(), 3),
            "positive years": f"{(R.groupby(yr).mean() > 0).sum()}/{yr.nunique()}"}
