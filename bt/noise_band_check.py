"""Idea 21a follow-ups: (1) M5 vs M30 on the overlapping 17 months (VWAP approximation check), (2) overlap with the
live opening-candle rule (daily correlation, results on the same days), (3) Fed days and the latest 60 sessions,
(4) FTMO pass odds alone and combined with the opening candle, at full and half edge."""
import sys, glob
import numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab"); sys.path.insert(0, "/home/claude/bt")
from ftmo_data import load_export
from lab import opening_candle
from ftmo_sim import challenge, funded
from news import load_calendar, fed_days
from noise_band import rth_bars, session_matrix, run

out = pd.read_pickle("/home/claude/data/noise_band_out.pkl")
fed = set(pd.to_datetime(list(fed_days(load_calendar("/home/claude/news/news_usd.csv")))))

# (1) M5 vs M30 on the same days
for sym in ("US100.cash", "US500.cash"):
    d5 = rth_bars(sym, "M5")
    days5, O5, C5, VW5, SP5 = session_matrix(d5, step=5)
    r5, l5, t5 = run(days5, O5, C5, VW5, SP5)
    r30 = out[sym][0]
    common = r5.dropna().index.intersection(r30.dropna().index)
    a, b = r5.reindex(common), r30.reindex(common)
    print(f"{sym} M5-built vs M30-built, {len(common)} common days {common[0].date()}..{common[-1].date()}: "
          f"avg/day {a.mean() * 1e4:+.2f} vs {b.mean() * 1e4:+.2f} bp, daily correlation {a.corr(b):.2f}")

# (2) opening candle (live rule) daily results
oc = {}
for name, pat, comm in (("US100.cash", "US100.cash_M30", 0.0), ("TSLA", "TSLA_M30", 0.00002)):
    d = load_export(glob.glob(f"/home/claude/data/assets/{pat}_*.csv")[0])
    oc[name] = opening_candle(d, first_bars=1, commission=comm, start="2022-01-01", skip_days=fed)

for sym in ("US100.cash", "TSLA"):
    raw = out[sym][0].dropna(); raw = raw[raw.index >= "2022-01-01"]
    o = oc[sym].R
    common = raw.index.intersection(o.index)
    print(f"\n{sym}: noise band vs opening candle on {len(common)} common days: daily correlation {raw.reindex(common).corr(o.reindex(common)):.2f}")
    same = oc[sym].dir.reindex(common)
    tr = out[sym][2]; tr = tr[tr.day >= "2022-01-01"]
    first = tr[tr.k_in == 0].set_index("day")
    agree = first.side.reindex(common).dropna()
    print(f"   10:00 band entries: {len(first)}, same direction as the opening candle: {np.mean(agree.values == same.reindex(agree.index).values):.0%}")
    nb_on_oc_loss = raw.reindex(common)[o.reindex(common) < 0]
    print(f"   band result on days the opening candle lost: {nb_on_oc_loss.mean() * 1e4:+.1f} bp/day (n={len(nb_on_oc_loss)});"
          f" on days it won: {raw.reindex(common)[o.reindex(common) > 0].mean() * 1e4:+.1f} bp/day")
    isfed = raw.index.isin(list(fed))
    print(f"   Fed decision days: {raw[isfed].mean() * 1e4:+.1f} bp/day (n={isfed.sum()}), other days {raw[~isfed].mean() * 1e4:+.1f}")
    last = raw.iloc[-60:]
    roll = raw.rolling(60).mean().dropna()
    print(f"   latest 60 sessions: {last.mean() * 1e4:+.1f} bp/day (whole sample {raw.mean() * 1e4:+.1f}); "
          f"{np.mean(roll < last.mean()):.0%} of all 60-day stretches were worse")

# (4) FTMO pass odds. Opening candle at 0.5% risk per trade (Fed days skipped). Noise band at a fixed notional
# multiple of the account (1x = position value equal to the balance), flat every night.
def oc_daily(risk=0.005, lev={"US100.cash": 15, "TSLA": 1}):
    parts = []
    for k, t in oc.items():
        allowed = np.minimum(risk, t.stop_pct / 100 * lev[k]); parts.append((t.R * allowed).rename("oc_" + k))
    return pd.concat(parts, axis=1)

def nb_daily(sym, mult):
    raw = out[sym][0].dropna(); raw = raw[raw.index >= "2022-01-01"]
    return (raw * mult).rename(f"nb_{sym}")

def sim(label, parts, keep=1.0):
    df = pd.concat(parts, axis=1).fillna(0)
    if keep < 1:
        df = df - (1 - keep) * df.mean()
    ret = df.sum(axis=1)
    eq = (1 + ret).cumprod(); dd = (eq / eq.cummax() - 1).min()
    c = challenge(ret.values); f = funded(ret.values)
    mo = None if c["median months"] is None else round(c["median months"], 1)
    print(f"   {label:46s} edge {keep:.0%}: avg/day {ret.mean() * 100:+.3f}%  worst day {ret.min() * 100:+.2f}%  maxDD {dd * 100:5.1f}%"
          f"  pass {c['pass rate']:.0%} in {mo} mo  keep funded 12m {f['keep account']:.0%}")
    return ret

print("\nFTMO 10k, both phases (10% + 5%), 5% daily / 10% total limits, 10-day blocks, 2022-2026:")
for keep in (1.0, 0.5):
    o = oc_daily()
    sim("opening candle TSLA+US100, 0.5% (live plan)", [o], keep)
    for m in (1.0, 2.0, 3.0):
        sim(f"noise band US100 at {m:.0f}x notional", [nb_daily("US100.cash", m)], keep)
    sim("noise band TSLA at 0.5x notional", [nb_daily("TSLA", 0.5)], keep)
    for m in (1.0, 2.0):
        sim(f"opening candle 0.5% + band US100 {m:.0f}x", [o, nb_daily("US100.cash", m)], keep)
    sim("opening candle 0.5% + band US100 2x + TSLA 0.5x", [o, nb_daily("US100.cash", 2.0), nb_daily("TSLA", 0.5)], keep)
