"""Idea 12: volatility sizing for the live opening-candle strategy (TSLA + US100, 2022-2026, Fed days skipped).
Fixed risk 0.5% per trade vs risk 0.5% x clamp(1-year median ATR% / today's ATR%, 0.5, 1.5), ATR% known at the open.
Compared on the same trades: avg daily return, worst day, max drawdown, FTMO pass odds (10% + 5%), funded survival."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/lab')
from ftmo_data import load_export
from lab import opening_candle, ny_session
from ftmo_sim import daily_returns, challenge, funded
from news import load_calendar, fed_days

fed = fed_days(load_calendar("/home/claude/news/news_usd.csv"))
specs = {"TSLA": ("TSLA_M30", 0.00002, 1), "US100": ("US100.cash_M30", 0.0, 15)}
trades, lev, scale = {}, {}, {}
for name, (pat, comm, L) in specs.items():
    d = load_export(glob.glob(f"/home/claude/data/assets/{pat}_*.csv")[0])
    tr = opening_candle(d, first_bars=1, commission=comm, start="2022-01-01", skip_days=fed)
    s = ny_session(d); day = s.groupby("nyd").agg(h=("high","max"), l=("low","min"), c=("close","last"))
    pc = day.c.shift(1); atr = pd.concat([day.h - day.l, (day.h - pc).abs(), (day.l - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    atrp = atr / day.c.shift(1); med = atrp.rolling(250, min_periods=60).median()
    sc = (med / atrp).clip(0.5, 1.5).reindex(tr.index).fillna(1.0)
    trades[name], lev[name], scale[name] = tr, L, sc
    print(f"{name}: {len(tr)} trades, avgR {tr.R.mean():+.3f}, scale mean {sc.mean():.2f} (min {sc.min():.2f} max {sc.max():.2f}); avgR when scale>1 (calm): {tr.R[sc>1].mean():+.3f} n={int((sc>1).sum())}, scale<1 (wild): {tr.R[sc<1].mean():+.3f} n={int((sc<1).sum())}")

def summarize(label, ret):
    eq = (1 + ret).cumprod(); dd = (eq / eq.cummax() - 1).min()
    ch = challenge(ret.values); fu = funded(ret.values)
    print(f"{label:34s} avg/day {ret.mean()*100:+.3f}%  worst day {ret.min()*100:+.2f}%  maxDD {dd*100:.1f}%  pass {ch['pass rate']:.0%} in {ch['median months']:.1f} mo  funded-12m survival {fu.get('survive', fu.get('survival', float('nan'))):.0%}")

base = daily_returns(trades, lev, 0.005)
summarize("fixed 0.5%", base)
scaled = daily_returns(trades, lev, {k: 0.005 * scale[k] for k in trades} if False else 0.005)   # placeholder to keep signature
# scaled version: apply the per-trade scale inside the same formula
parts = []
for k, t in trades.items():
    allowed = np.minimum(0.005 * scale[k], t.stop_pct / 100 * lev[k]); parts.append((t.R * allowed).rename(k))
scaled = pd.concat(parts, axis=1).fillna(0).sum(axis=1).sort_index()
summarize("vol-scaled 0.5% x clamp(0.5..1.5)", scaled)
parts = []
for k, t in trades.items():
    allowed = np.minimum(0.005 * scale[k] / scale[k].mean(), t.stop_pct / 100 * lev[k]); parts.append((t.R * allowed).rename(k))
scaled2 = pd.concat(parts, axis=1).fillna(0).sum(axis=1).sort_index()
summarize("vol-scaled, same average risk", scaled2)
summarize("fixed 0.75%", daily_returns(trades, lev, 0.0075))
