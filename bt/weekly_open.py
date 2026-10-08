"""Ideas 2+3: weekly-open bias and weekly-open magnet. Gold M1 2012-2026, US100/US500 M30 2017-2026."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/bt'); sys.path.insert(0,'/home/claude/lab')
import sr_diag
from ftmo_data import load_export
from smc_data import finish
from gold_m1 import COMM as GCOMM

def frames():
    sr_diag.START = "2012-01-01"; g = sr_diag.load(); g.attrs["comm"] = GCOMM; yield "gold", g
    for sym in ("US100.cash", "US500.cash"):
        f = glob.glob(f"/home/claude/data/assets/{sym}_M30_*.csv")[0]
        x = load_export(f); x.index = x.index - pd.Timedelta(hours=7)
        x.index = x.index.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").tz_convert("UTC").tz_localize(None)
        x = x[~x.index.isna()][["open","high","low","close","sp"]]
        b = finish(x, 0.0); b = b[["open","high","low","close","sp","nyd","nym"]].copy(); b.attrs["comm"] = 0.0
        yield sym.split(".")[0], b

def weekly(g):
    ny = g.index.tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
    wk = (ny + pd.Timedelta(hours=6)).to_period("W-SAT")           # week starts Sunday 18:00 NY
    return pd.Series(wk.values, index=g.index)

for sym, g in frames():
    d, atr = sr_diag.daily_atr(g); wk = weekly(g)
    grp = g.groupby(wk.values)
    wo = grp.open.first(); wc = grp.close.last(); whi = grp.high.max(); wlo = grp.low.min()
    first_day = grp.apply(lambda x: x.nyd.iloc[0]); a = first_day.map(atr)
    # --- idea 2a: Monday close vs weekly open -> rest of week
    mon = g[g.nyd.dt.weekday == 0].groupby(wk[g.nyd.dt.weekday == 0].values).close.last()
    t = pd.DataFrame({"wo": wo, "wc": wc, "mon": mon, "atr": a}).dropna()
    t["mon_dir"] = np.sign(t.mon - t.wo); t["rest"] = (t.wc - t.mon) / t.atr
    print(f"\n==== {sym} ({len(t)} weeks) ====")
    print("2a Monday above/below weekly open -> rest-of-week return (ATR):",
          t.groupby("mon_dir").rest.agg(["count", "mean"]).round(3).to_dict())
    corr = np.corrcoef(np.sign(t.mon - t.wo), t.rest)[0, 1]; print("   corr(sign(mon-wo), rest) = %.3f" % corr)
    # --- idea 2b: each day's return conditioned on day-open above/below the weekly open
    day = g.groupby("nyd").agg(o=("open", "first"), c=("close", "last")); day["wo"] = g.groupby("nyd").apply(lambda x: wo.get(wk.loc[x.index[0]], np.nan))
    day["atr"] = atr; day = day.dropna(); day["above"] = np.sign(day.o - day.wo); day["ret"] = (day.c - day.o) / day.atr
    print("2b day return (ATR) when day opens above(+1)/below(-1) weekly open:",
          day.groupby("above").ret.agg(["count", "mean"]).round(3).to_dict())
    print("   by half:", day.iloc[:len(day)//2].groupby("above").ret.mean().round(3).to_dict(), day.iloc[len(day)//2:].groupby("above").ret.mean().round(3).to_dict())
    # --- idea 3a: magnet. After first moving > 0.5 ATR away from the weekly open, does price come back within 0.05 ATR?
    def magnet(open_shift):
        hits = []; 
        for w, x in grp:
            if w not in a.index or not np.isfinite(a[w]): continue
            o = x.open.iloc[0] + open_shift * a[w]; z = 0.05 * a[w]
            hi, lo = x.high.values, x.low.values
            away = np.where((hi > o + 0.5 * a[w]) | (lo < o - 0.5 * a[w]))[0]
            if len(away) == 0: continue
            k = away[0]; back = ((lo[k+1:] <= o + z) & (hi[k+1:] >= o - z)).any()
            hits.append(back)
        return np.mean(hits), len(hits)
    r_real, n = magnet(0.0); r_fake, _ = magnet(0.37)
    print(f"3a returns to weekly open after moving 0.5 ATR away: real {r_real:.0%}  fake(+0.37 ATR) {r_fake:.0%}  (weeks={n})")
    # --- idea 3b: fade rule. First time in the week price is 1 ATR from the weekly open: trade back toward it.
    comm = g.attrs["comm"]; rows = []
    for w, x in grp:
        if w not in a.index or not np.isfinite(a[w]): continue
        o = x.open.iloc[0]; A = a[w]; c = x.close.values; hi, lo = x.high.values, x.low.values; sp = x.sp.values
        far = np.where(np.abs(c - o) > A)[0]
        if len(far) == 0: continue
        k = far[0]; side = -1 if c[k] > o else 1          # above -> short back to open
        entry = c[k] + side * sp[k] / 2; tgt = o; stop = c[k] + (-side) * A    # stop 1 ATR further away
        risk = abs(entry - stop); px = None
        for q in range(k + 1, len(c)):
            if side == 1:
                if lo[q] <= stop: px = stop; why = "stop"; break
                if hi[q] >= tgt: px = tgt; why = "target"; break
            else:
                if hi[q] >= stop: px = stop; why = "stop"; break
                if lo[q] <= tgt: px = tgt; why = "target"; break
        if px is None: px = c[-1]; why = "week end"
        cost = sp[k] / 2 + comm * entry * 2
        rows.append(dict(week=str(w), year=x.index[0].year, R=(side * (px - entry) - cost) / risk, why=why))
    r = pd.DataFrame(rows)
    print(f"3b fade 1-ATR move back to weekly open (stop 1 ATR further): n={len(r)} avgR={r.R.mean():+.3f} t={r.R.mean()/(r.R.std()/np.sqrt(len(r))):+.1f} win={np.mean(r.why=='target'):.0%}")
    print("   per year:", r.groupby("year").R.mean().round(2).to_dict())
