import pandas as pd, numpy as np, datetime as dt
SPREAD_BY_YEAR = {2012: .30, 2013: .30, 2014: .30, 2015: .30, 2016: .28, 2017: .25, 2018: .25, 2019: .22, 2020: .06, 2021: .08, 2022: .08, 2023: .08, 2024: .17, 2025: .24, 2026: .46}
COMM = 0.000007
def eu_dst_mask(idx):
    y = idx.year.values; out = np.zeros(len(idx), bool)
    for yr in np.unique(y):
        d = pd.Timestamp(yr, 3, 31); start = d - pd.Timedelta(days=(d.weekday() + 1) % 7) + pd.Timedelta(hours=1)
        d = pd.Timestamp(yr, 10, 31); end = d - pd.Timedelta(days=(d.weekday() + 1) % 7) + pd.Timedelta(hours=1)
        m = y == yr; v = idx[m]; out[m] = (v >= start) & (v < end)
    return out
def load(start="2012-01-01"):
    d = pd.read_csv("/home/claude/data/mt4/m5frommt4.csv", header=None, names=["date", "time", "open", "high", "low", "close", "vol"], dtype={"date": str, "time": str})
    d.index = pd.to_datetime(d["date"] + " " + d["time"], format="%Y.%m.%d %H:%M"); d = d.drop(columns=["date", "time"]).sort_index()
    d = d.loc[start:]
    srv = d.index; approx_utc = srv - pd.Timedelta(hours=2)
    shift = np.where(eu_dst_mask(approx_utc), 3, 2)
    d.index = srv - pd.to_timedelta(shift, unit="h"); d.index.name = "utc"
    d = d[~d.index.duplicated(keep="last")]
    d["sp"] = d.index.year.map(SPREAD_BY_YEAR).astype(float)
    return d
