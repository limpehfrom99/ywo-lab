"""Bernd Skorupinski's higher-timeframe 'bias' tools rebuilt from FTMO daily data (log #66). His indicators are invite-only, so
these are reconstructions from his own pages (bernd-skorupinski.com) and the settings visible in his screenshots:
  Valuation Tool (settings seen: DXY, ZB1!, GC1!, 480, -0.75, 0.75, 10): relative value of an asset against a reference.
    Here: s = EMA10(ln(asset) - ln(reference)); v = 2 * (s - min(s, 480 days)) / (max - min) - 1, so v is in [-1, +1];
    undervalued below -0.75, overvalued above +0.75. References: a synthetic dollar index (ICE DXY weights from the FTMO forex
    pairs; SEK missing, its 4.2% left out) and gold. Treasury bonds (ZB) are not on FTMO and not in the export.
  True Seasonality (settings seen: 15, 30): the average path of the same calendar dates over the last 15 years, projected
    forward. Here: seasN = mean over the 15 previous years of ln(close N trading days after the same calendar date / close on
    that date); its sign is the seasonal bias for the next N days.
  COT (157-week index, 20/80): needs CFTC history, not available here.
Everything is computed from data before the day it is used (the bias for day t uses closes up to t-1)."""
import os, sys, functools, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "quant"))
sys.path.insert(0, os.path.join(ROOT, "lab"))
import universe as U
from ftmo_data import load_any

DXY_W = {"EURUSD": -0.576, "USDJPY": 0.136, "GBPUSD": -0.119, "USDCAD": 0.091, "USDCHF": 0.036}


@functools.lru_cache(maxsize=None)
def d1(sym):
    cat = U.catalog()
    if (sym, "D1") not in cat: return None
    d = load_any(cat[(sym, "D1")])[["open", "high", "low", "close", "sp"]]
    d = d[d.index.weekday < 5]; d = d[~d.index.duplicated()].sort_index()
    return d


@functools.lru_cache(maxsize=None)
def dxy():
    parts = [np.log(d1(s).close).rename(s) * w for s, w in DXY_W.items()]
    x = pd.concat(parts, axis=1).dropna()
    return np.exp(x.sum(axis=1)).rename("DXY")


def valuation(asset_close, ref_close, L=480, smooth=10):
    j = pd.concat([np.log(asset_close).rename("a"), np.log(ref_close).rename("r")], axis=1).ffill().dropna()
    s = (j.a - j.r).ewm(span=smooth, adjust=False).mean()
    lo = s.rolling(L, min_periods=int(L * 0.8)).min(); hi = s.rolling(L, min_periods=int(L * 0.8)).max()
    return (2 * (s - lo) / (hi - lo) - 1).rename("val")


def valuation_roc(asset_close, ref_close, n=10, L=480):
    """The reading that reproduces his NASDAQ example (-1.0 vs the dollar and vs gold on 4-8 Apr 2025): the difference of the two
    10-day rates of change, scaled to [-1, +1] by its min and max over the last 480 days."""
    j = pd.concat([asset_close.rename("a"), ref_close.rename("r")], axis=1, sort=True).ffill().dropna()
    x = (j.a / j.a.shift(n) - 1) - (j.r / j.r.shift(n) - 1)
    lo = x.rolling(L, min_periods=int(L * 0.8)).min(); hi = x.rolling(L, min_periods=int(L * 0.8)).max()
    return (2 * (x - lo) / (hi - lo) - 1).rename("val")


def seasonal(close, years=15, N=20):
    """Mean of ln(C[d+N]/C[d]) over the `years` previous calendar years, d = the first trading day on/after the same date."""
    c = close.values; idx = close.index; out = np.full(len(c), np.nan)
    lc = np.log(c); dates = idx.values
    for t in range(len(c)):
        ts = idx[t]; vals = []
        for k in range(1, years + 1):
            try: past = ts.replace(year=ts.year - k)
            except ValueError: past = ts.replace(year=ts.year - k, day=28)
            i = np.searchsorted(dates, np.datetime64(past))
            if i + N < len(c) and i < t and i + N < t: vals.append(lc[i + N] - lc[i])
        if len(vals) >= int(years * 0.8): out[t] = np.mean(vals)
    return pd.Series(out, index=idx, name=f"seas{N}")


@functools.lru_cache(maxsize=None)
def bias_table(sym):
    """Daily table (server dates) of bias inputs known at the START of each day (shifted by one day)."""
    d = d1(sym)
    if d is None: return None
    T = pd.DataFrame(index=d.index)
    T["val_dxy"] = valuation_roc(d.close, dxy()).reindex(d.index)
    T["lvl_dxy"] = valuation(d.close, dxy()).reindex(d.index)
    g = d1("XAUUSD")
    if sym != "XAUUSD" and g is not None:
        T["val_gold"] = valuation_roc(d.close, g.close).reindex(d.index); T["lvl_gold"] = valuation(d.close, g.close).reindex(d.index)
    for N in (10, 20, 30): T[f"seas{N}"] = seasonal(d.close, 15, N)
    pc = d.close.shift(1)
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    T["atr20"] = tr.rolling(20).mean()
    return T.shift(1)                                                  # known before the day starts
