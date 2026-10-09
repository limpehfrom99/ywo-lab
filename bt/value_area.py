"""#43 — RedNote repost (RossCameron777) of a Jesse Rogers NQ trade (9.6 min, Deep Charts volume profile + heatmap): auction market
theory. Value areas (70% of a session's volume) moving higher = a "value-up" market; a dip below the prior value area is a discount
and a likely fake-out; once price is accepted back into value, buy; stop under the last pivot; target the value area high; exit
before holding overnight. The same mechanism as Dalton's Market Profile "80% rule": outside value, then two 30-minute closes back
inside -> price tends to cross to the other side of value.
Fixed before running (longs; shorts mirrored):
  Profile of each session from bar volume (tick volume) spread evenly over each bar's range, bins of 0.02 x daily ATR; POC = the
  busiest bin; value area grown from the POC one bin at a time toward the busier side until it holds 70% of the volume.
  Sessions: ETH = the broker day (17:00-17:00 New York); RTH = 09:30-16:00 New York (indices only).
  Value-up: the prior session's VAH and VAL both above the session before's (value-down: both below).
  V1 (the video): value-up day; any bar trades below the prior VAL; then two consecutive 30-minute closes inside the prior value area
     -> buy at the next open; stop = lowest low since the excursion - 0.05 daily ATR; target = prior VAH; flat at the session end.
  V2 (Dalton's 80% rule): no trend filter; the session opens below the prior VAL; then the same two closes inside -> same trade.
  V3: V1 with the prior POC as the target.
  One trade per side per session; a close beyond the far side before the second inside close cancels that side for the session.
Gold 2012 - Oct 2026 (profile and exits on 1-minute bars); US100 / US500 2021 - Oct 2026 (FTMO 30-minute bars only; earlier years have no 30-minute history: profile, entry
and exits on 30-minute bars, stop first); FTMO spread (+ commission on gold); coin flip per trade."""
import sys, glob, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/lab")
from smc_grid import exit_nb, tstat
from gold_m1 import COMM
from ftmo_data import load_export


def va_of(h, l, v, bin_):
    lo = l.min(); hi = h.max()
    if not (np.isfinite(lo) and np.isfinite(hi)) or hi <= lo or bin_ <= 0: return None
    nb = int((hi - lo) / bin_) + 1
    a = np.clip(((l - lo) / bin_).astype(int), 0, nb - 1); b = np.clip(((h - lo) / bin_).astype(int), 0, nb - 1)
    w = v / (b - a + 1); diff = np.zeros(nb + 1)
    np.add.at(diff, a, w); np.add.at(diff, b + 1, -w)
    vol = np.cumsum(diff)[:nb]; tot = vol.sum()
    if tot <= 0: return None
    p = int(np.argmax(vol)); i = j = p; s = vol[p]
    while s < 0.7 * tot:
        up = vol[j + 1] if j + 1 < nb else -1.0; dn = vol[i - 1] if i - 1 >= 0 else -1.0
        if up < 0 and dn < 0: break
        if up >= dn: j += 1; s += up
        else: i -= 1; s += dn
    return lo + i * bin_, lo + (j + 1) * bin_, lo + (p + 0.5) * bin_          # VAL, VAH, POC


def prep(df, comm):
    """df: UTC-indexed bars with open high low close vol sp. Adds broker day, New York minute, daily ATR (known before the day)."""
    ny = df.index.tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
    df = df.copy(); df["day"] = (ny + pd.Timedelta(hours=7)).normalize(); df["nym"] = ny.hour * 60 + ny.minute
    d = df.groupby("day").agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    pc = d.close.shift(1)
    d["atr"] = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    df["atr"] = d.atr.reindex(df.day).values; df.attrs["comm"] = comm
    return df[df.day.dt.weekday < 5]


def sessions(df, kind):
    sel = df if kind == "ETH" else df[(df.nym >= 570) & (df.nym < 960)]
    return {k: g for k, g in sel.groupby("day")}


def run(px, dec, kind):
    """px: exit/profile bars (1-min gold, 30-min indices); dec: 30-minute decision bars with the same columns."""
    P, D = sessions(px, kind), sessions(dec, kind); days = sorted(set(P) & set(D)); comm = px.attrs["comm"]; out = []
    vas = {}
    for k in days:
        g = P[k]; atr = g.atr.iloc[0]
        if np.isfinite(atr): vas[k] = va_of(g.high.values, g.low.values, g.vol.values.astype(float), 0.02 * atr)
    for n in range(2, len(days)):
        d0, d1, d2 = days[n], days[n - 1], days[n - 2]
        v1, v2 = vas.get(d1), vas.get(d2); g = D[d0]; e_bars = P[d0]
        if v1 is None or v2 is None or len(g) < 3: continue
        VAL, VAH, POC = v1; atr = g.atr.iloc[0]
        trend = 1 if (VAL > v2[0] and VAH > v2[1]) else (-1 if (VAL < v2[0] and VAH < v2[1]) else 0)
        H, L, C, O = g.high.values, g.low.values, g.close.values, g.open.values; T = g.index.values
        Eh, El, Ec, Eo, Et = e_bars.high.values, e_bars.low.values, e_bars.close.values, e_bars.open.values, e_bars.index.values
        for side in (1, -1):
            # in this side's frame: below = beyond VAL for longs, beyond VAH for shorts
            near, far = (VAL, VAH) if side == 1 else (VAH, VAL)
            beyond = (lambda x: x < near) if side == 1 else (lambda x: x > near)
            opened_out = beyond(O[0])
            started = False; x_ext = None; cnt = 0; entry_bar = None
            for m in range(len(C)):
                ext = L[m] if side == 1 else H[m]
                if not started and beyond(ext): started = True; x_ext = ext
                if not started: continue
                x_ext = min(x_ext, ext) if side == 1 else max(x_ext, ext)
                inside = (VAL < C[m] < VAH)
                if (side == 1 and C[m] >= VAH) or (side == -1 and C[m] <= VAL): break
                cnt = cnt + 1 if inside else 0
                if cnt >= 2: entry_bar = m; break
            if entry_bar is None: continue
            t_dec_end = T[entry_bar] + np.timedelta64(30, "m")
            i0 = np.searchsorted(Et, t_dec_end)
            if i0 >= len(Et): continue
            e = Eo[i0]; stop = x_ext - side * 0.05 * atr; risk = side * (e - stop)
            if risk <= 0: continue
            sp = e_bars.sp.values[i0]
            for cell, tgt, need in (("V1", far, trend == side), ("V2", far, opened_out), ("V3", POC, trend == side)):
                if not need or side * (tgt - e) <= 0: continue
                rr = side * (tgt - e) / risk
                X = exit_nb(Eh, El, Ec, i0, len(Et), stop, tgt, side); cost = sp + comm * (abs(e) + abs(X))
                Xf = exit_nb(Eh, El, Ec, i0, len(Et), e + side * risk, 2 * e - tgt, -side)
                hit = (X == tgt)
                out.append((cell, pd.Timestamp(Et[i0]), side, (side * (X - e) - cost) / risk, (-side * (Xf - e) - cost) / risk, rr, hit))
    return pd.DataFrame(out, columns=["cell", "t", "side", "R", "R_flip", "rr", "hit"])


def report(name, df):
    lab = {"V1": "V1 value-up dip, back inside -> far side", "V2": "V2 Dalton 80% rule (open outside)", "V3": "V3 = V1, target POC"}
    for cell, r in df.groupby("cell"):
        if len(r) < 10: print(f"{name:14s} {lab[cell]:42s} n={len(r)}"); continue
        IS = r.t < "2024-01-01"; yr = r.groupby(r.t.dt.year).R.mean()
        print(f"{name:14s} {lab[cell]:42s} n={len(r):4d} avgR={r.R.mean():+.3f} t={tstat(r.R):+.1f} win={np.mean(r.R>0):.0%} "
              f"reach target {r.hit.mean():.0%} (rr {r.rr.median():.2f}) coin={r.R_flip.mean():+.3f} | L {r[r.side==1].R.mean():+.3f} "
              f"S {r[r.side==-1].R.mean():+.3f} | <24 {r.R[IS].mean():+.3f} 24+ {r.R[~IS].mean():+.3f} | yrs>0 {(yr>0).sum()}/{len(yr)}", flush=True)


if __name__ == "__main__":
    t0 = time.time(); allr = []
    g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")[["open", "high", "low", "close", "vol", "sp"]]
    gp = prep(g, COMM)
    g30 = g.resample("30min", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last", "vol": "sum", "sp": "mean"}).dropna()
    g30 = prep(g30, COMM); g30["atr"] = gp.groupby("day").atr.first().reindex(g30.day).values
    r = run(gp, g30, "ETH"); report("gold ETH", r); allr.append(r.assign(mkt="gold ETH"))
    print(f"   ({time.time() - t0:.0f}s)", flush=True)
    for sym in ("US100.cash", "US500.cash"):
        d = load_export(glob.glob(f"/home/claude/data/assets/{sym}_M30_*.csv")[0])
        d.index = (d.index - pd.Timedelta(hours=7)).tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").tz_convert("UTC").tz_localize(None)
        d = d[~d.index.isna()].rename(columns={"tickvol": "tv"}); d["vol"] = d.tv
        d = prep(d[["open", "high", "low", "close", "vol", "sp"]].loc["2018-01-01":], 0.0)
        for kind in ("ETH", "RTH"):
            r = run(d, d, kind); report(f"{sym[:5]} {kind}", r); allr.append(r.assign(mkt=f"{sym[:5]} {kind}"))
    pd.concat(allr).to_pickle("/home/claude/bt/value_area_trades.pkl")
    print(f"done in {time.time() - t0:.0f}s")
