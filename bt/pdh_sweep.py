"""#45 — RedNote 大道无形我有型 (30 s, silent; rules from the frames, caption "突破前高点买入策略详解"): mark the previous day's high and
low; today price breaks above the previous day's high ("流动性诱多", a bull trap) and the candle closes back below it -> sell; stop
above the sweep high (0.17-0.19% in the example); target the previous day's low (4.73R in the example). Longs mirrored at the
previous day's low.
Fixed before running: day = broker day (17:00-17:00 New York); PDH / PDL = the previous broker day's high / low. Short: the first bar
of the day that trades above PDH starts the sweep; the first later-or-same bar that closes back below PDH triggers; sell at the
next bar's open; stop = the highest high since the sweep began + 0.05 daily ATR; target = PDL (if below the entry) or a fixed 2R;
flat at the end of the broker day. One trade per side per day.
Markets: gold 2012 - Oct 2026 (5- and 15-minute bars, exits on 1-minute); EURUSD / GBPUSD / USDCHF 2018-26 and US100 / US500
2022-26 (FTMO 30-minute bars, exits on 30-minute bars, stop first). FTMO costs; coin flip per trade."""
import sys, glob, time, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/lab")
from smc_grid import exit_nb, tstat
from data_standard_check import to_server, from_server, AGG
from ftmo_data import load_export

COMM = {"gold": 0.000007, "fx": 0.000025, "idx": 0.0}


def prep(df):
    srv = to_server(df.index); df = df.copy(); df["day"] = srv.normalize()
    d = df.groupby("day").agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    pc = d.close.shift(1)
    d["atr"] = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    d["pdh"], d["pdl"] = d.high.shift(1), d.low.shift(1)
    d = d[d.index.weekday < 5]
    return df[df.day.isin(d.index)], d


def prep_exits(exb):
    """Times as int64 nanoseconds (searchsorted on datetime64 with a mismatched key copies the whole array every call)."""
    day = to_server(exb.index).normalize()
    t = exb.index.values.astype("datetime64[ns]").view("i8")
    day_end = pd.Series(t, index=exb.index).groupby(day.values).max().to_dict()
    return (t,) + tuple(exb[k].values for k in ("high", "low", "close", "open", "sp")) + (day_end,)


def run(dec, ex, comm, target, bar_min):
    """dec: decision bars (UTC index); ex: prep_exits() of the exit bars (1-minute for gold, = dec otherwise)."""
    dec, D = prep(dec)
    Et, Eh, El, Ec, Eo, Esp, day_end = ex
    rows = []
    for day, g in dec.groupby("day"):
        if day not in D.index: continue
        pdh, pdl, atr = D.at[day, "pdh"], D.at[day, "pdl"], D.at[day, "atr"]
        if not (np.isfinite(pdh) and np.isfinite(pdl) and np.isfinite(atr)) or day not in day_end: continue
        H, L, C = g.high.values, g.low.values, g.close.values; T = g.index.values.astype("datetime64[ns]").view("i8")
        bar = np.int64(bar_min) * 60_000_000_000
        for side in (-1, 1):                                   # -1: sweep of PDH -> short; +1: sweep of PDL -> long
            lvl, far = (pdh, pdl) if side == -1 else (pdl, pdh)
            ext = None; trig = None
            for m in range(len(C)):
                beyond = H[m] > lvl if side == -1 else L[m] < lvl
                if ext is None and beyond: ext = H[m] if side == -1 else L[m]
                if ext is None: continue
                ext = max(ext, H[m]) if side == -1 else min(ext, L[m])
                if (side == -1 and C[m] < lvl) or (side == 1 and C[m] > lvl): trig = m; break
            if trig is None or trig + 1 >= len(T): continue
            i0 = np.searchsorted(Et, T[trig] + bar); i1 = np.searchsorted(Et, day_end[day], side="right")
            if i0 >= i1: continue
            e = Eo[i0]; stop = ext - side * 0.05 * atr; risk = abs(stop - e)
            if (side == -1 and stop <= e) or (side == 1 and stop >= e): continue
            tgt = far if target == "far" else e + side * 2 * risk
            if side * (tgt - e) <= 0: continue
            X = exit_nb(Eh, El, Ec, i0, i1, stop, tgt, side); cost = Esp[i0] + comm * (abs(e) + abs(X))
            Xf = exit_nb(Eh, El, Ec, i0, i1, e + side * risk, 2 * e - tgt, -side)
            rows.append((pd.Timestamp(int(Et[i0])), side, (side * (X - e) - cost) / risk, (-side * (Xf - e) - cost) / risk, side * (tgt - e) / risk))
    return pd.DataFrame(rows, columns=["t", "side", "R", "R_flip", "rr"])


def line(lab, df):
    if len(df) < 10: return f"{lab:40s} n={len(df)}"
    IS = df.t < "2024-01-01"; yr = df.groupby(df.t.dt.year).R.mean()
    return (f"{lab:40s} n={len(df):5d} avgR={df.R.mean():+.3f} t={tstat(df.R):+.1f} win={np.mean(df.R>0):.0%} rr {df.rr.median():.1f} "
            f"coin={df.R_flip.mean():+.3f} | short at PDH {df[df.side==-1].R.mean():+.3f} long at PDL {df[df.side==1].R.mean():+.3f} | "
            f"<24 {df.R[IS].mean():+.3f} 24+ {df.R[~IS].mean():+.3f} | yrs>0 {(yr>0).sum()}/{len(yr)}")


def ftmo_m30(path, spx=1.2):
    d = load_export(path); d.index = from_server(pd.DatetimeIndex(d.index)); d = d[~d.index.isna()].sort_index()
    d = d[["open", "high", "low", "close", "sp"]].copy(); d["sp"] = d.sp * spx; return d


if __name__ == "__main__":
    t0 = time.time(); out = []
    g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")[["open", "high", "low", "close", "sp"]]
    gex = prep_exits(g)
    for tf in ("5min", "15min"):
        dec = g.resample(tf, label="left", closed="left").agg(AGG).dropna()
        for target in ("far", "2R"):
            r = run(dec, gex, COMM["gold"], target, int(tf.replace("min", ""))); out.append(r.assign(mkt="gold", tf=tf, target=target))
            print(line(f"gold {tf}, target {'PDL/PDH' if target == 'far' else '2R'}", r), flush=True)
    for grp, paths in (("fx", [glob.glob(f"/home/claude/data/fx2/{s}_M30_*.csv")[0] for s in ("EURUSD", "GBPUSD", "USDCHF")]),
                       ("idx", [glob.glob(f"/home/claude/data/assets/{s}_M30_*.csv")[0] for s in ("US100.cash", "US500.cash")])):
        for target in ("far", "2R"):
            rs = []
            for p in paths:
                d = ftmo_m30(p)
                if grp == "idx": d = d.loc["2022-01-01":]
                rs.append(run(d, prep_exits(d), COMM[grp], target, 30).assign(sym=p.split("/")[-1].split("_")[0]))
            r = pd.concat(rs); out.append(r.assign(mkt=grp, tf="30min", target=target))
            print(line(f"{'forex x3' if grp == 'fx' else 'US100+US500'} 30-min, target {'PDL/PDH' if target == 'far' else '2R'}", r)
                  + " | " + " ".join(f"{s} {v:+.3f}" for s, v in r.groupby("sym").R.mean().items()), flush=True)
    pd.concat(out).to_pickle("/home/claude/bt/pdh_sweep_trades.pkl")
    print(f"done in {time.time() - t0:.0f}s")
