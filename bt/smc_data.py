import sys; sys.path.insert(0, "/home/claude/lab")
import glob, pandas as pd, numpy as np
from ftmo_data import load_export
def to_m5(d):
    b = d[["open", "high", "low", "close"]].resample("5min", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    b["sp"] = d["sp"].resample("5min", label="left", closed="left").mean().reindex(b.index).ffill()
    return b
def finish(b, comm):
    ny = b.index.tz_localize("UTC").tz_convert("America/New_York")
    b["nyd"] = pd.DatetimeIndex(ny.tz_localize(None)).normalize(); b["nym"] = ny.hour * 60 + ny.minute; b["wd"] = ny.weekday
    pc = b.close.shift(1); tr = pd.concat([b.high - b.low, (b.high - pc).abs(), (b.low - pc).abs()], axis=1).max(axis=1)
    b["atr"] = tr.ewm(alpha=1/14, adjust=False).mean().shift(1)
    b.attrs["comm"] = comm
    return b.dropna()
def gold():
    g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")
    return finish(to_m5(g), 0.000007)
def ftmo(sym, comm):
    d = load_export(glob.glob(f"/home/claude/data/assets/{sym}_M5_*.csv")[0])
    d.index = d.index - pd.Timedelta(hours=7)                 # server -> New York
    d.index = d.index.tz_localize("America/New_York").tz_convert("UTC").tz_localize(None)
    d = d[["open", "high", "low", "close", "sp"]]
    return finish(d, comm)
