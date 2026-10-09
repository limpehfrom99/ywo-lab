"""FTMO pass odds for the live opening candle (TSLA + US100, 0.5% risk, Fed days skipped) alone and with the new
candidates added: noise band US100 (21a, at 1x notional, flat nightly) and IBS<0.2 US100 (21c, at 0.5x notional,
held overnight -> Swing accounts only). 2022-2026, daily mark-to-market, full and half edge."""
import sys, glob
import numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab"); sys.path.insert(0, "/home/claude/bt")
from ftmo_data import load_export
from lab import opening_candle
from ftmo_sim import challenge, funded
from news import load_calendar, fed_days
from ibs_published import daily, run as ibs_run

fed = fed_days(load_calendar("/home/claude/news/news_usd.csv"))
oc = []
for name, pat, comm, lev in (("US100", "US100.cash_M30", 0.0, 15), ("TSLA", "TSLA_M30", 0.00002, 1)):
    d = load_export(glob.glob(f"/home/claude/data/assets/{pat}_*.csv")[0])
    t = opening_candle(d, first_bars=1, commission=comm, start="2022-01-01", skip_days=fed)
    oc.append((t.R * np.minimum(0.005, t.stop_pct / 100 * lev)).rename("oc_" + name))
oc = pd.concat(oc, axis=1).fillna(0).sum(axis=1).rename("oc")
oc.index = pd.DatetimeIndex(oc.index).normalize()

nb = pd.read_pickle("/home/claude/data/noise_band_out.pkl")["US100.cash"][0].dropna().rename("band")
nb = nb[nb.index >= "2022-01-01"]

def ibs_daily(sym, spread, rule, mult):
    d = daily(sym); t = ibs_run(d, spread, rule)
    r = pd.Series(0.0, index=d.index)
    c = d.c
    for _, x in t.iterrows():
        i = d.index.get_loc(x.day); q = i + int(x.days)
        seg = c.iloc[i:q + 1].pct_change().iloc[1:]
        r.loc[seg.index] += seg.values * mult
        r.iloc[i] -= spread / 2 / c.iloc[i] * mult; r.iloc[q] -= spread / 2 / c.iloc[q] * mult
        nights = (d.index[q] - d.index[i]).days
        r.iloc[q] -= 0.0001 * nights * mult
    # the M30 trading day is the server date; label it with the New York date of its close (same calendar day)
    return r[r.index >= "2022-01-01"].rename(f"ibs_{rule}")

ibs = ibs_daily("US100.cash", 1.5, "ibs<0.2", 0.5)

def sim(label, parts, keep):
    df = pd.concat(parts, axis=1).fillna(0)
    if keep < 1:
        df = df - (1 - keep) * df.mean()
    ret = df.sum(axis=1)
    eq = (1 + ret).cumprod(); dd = (eq / eq.cummax() - 1).min()
    c = challenge(ret.values); f = funded(ret.values)
    mo = None if c["median months"] is None else round(c["median months"], 1)
    print(f"  {label:48s} edge {keep:.0%}: avg/day {ret.mean() * 100:+.3f}% worst day {ret.min() * 100:+.2f}% maxDD {dd * 100:5.1f}%"
          f" pass {c['pass rate']:.0%} in {mo} mo, keep funded 12m {f['keep account']:.0%}")

print("corr daily: oc-band %.2f, oc-ibs %.2f, band-ibs %.2f" % (
    pd.concat([oc, nb], axis=1).fillna(0).corr().iloc[0, 1], pd.concat([oc, ibs], axis=1).fillna(0).corr().iloc[0, 1],
    pd.concat([nb, ibs], axis=1).fillna(0).corr().iloc[0, 1]))
for keep in (1.0, 0.5):
    sim("opening candle 0.5% (live plan)", [oc], keep)
    sim("+ band US100 1x", [oc, nb], keep)
    sim("+ IBS<0.2 US100 0.5x (Swing only)", [oc, ibs], keep)
    sim("+ band 1x + IBS 0.5x (Swing only)", [oc, nb, ibs], keep)
    sim("band US100 1x + IBS 0.5x, no opening candle", [nb, ibs], keep)
