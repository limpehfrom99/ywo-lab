"""Universe for the cross-market battery: symbol metadata (group, sessions, costs, FTMO Swing leverage, swaps) and loaders.

Bars come from the FTMO exports (tools/export -> .npz, or MT5 "Export Bars" text files). Their clock is MT5 server time =
New York + 7 h all year, so every frame is converted to a UTC index here and sessions are cut in each exchange's own time zone.
"""
import os, re, glob, sys
import numpy as np, pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lab"))
from ftmo_data import load_any  # noqa: E402

NEW_DIR = os.environ.get("YWO_DEST", "/home/claude/data/x")
OLD_DIRS = ["/home/claude/data/assets", "/home/claude/data/mt4"]
# once the full export has been unpacked, use only it; before that, the old 100k-bar exports
EXPORT_DIRS = [NEW_DIR] if (os.path.isdir(NEW_DIR) and any(f.endswith((".npz", ".csv.gz")) for f in os.listdir(NEW_DIR))) else OLD_DIRS
CCY = {"USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"}
METALS = {"XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD", "XCUUSD"}
CRYPTO = {"BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "LTCUSD", "ADAUSD", "DOGEUSD"}
ENERGY = {"USOIL.cash", "UKOIL.cash", "NATGAS.cash"}
US_INDICES = {"US100.cash", "US500.cash", "US30.cash", "US2000.cash"}
EU_INDICES = {"GER40.cash", "EU50.cash", "FRA40.cash", "SPN35.cash", "N25.cash"}

# exchange sessions in local time (tz, open, close). Intraday rules are anchored to these.
SESSIONS = {
    "us_cash":  ("America/New_York", "09:30", "16:00"),
    "eu_cash":  ("Europe/Berlin", "09:00", "17:30"),
    "uk_cash":  ("Europe/London", "08:00", "16:30"),
    "jp_cash":  ("Asia/Tokyo", "09:00", "15:00"),
    "hk_cash":  ("Asia/Hong_Kong", "09:30", "16:00"),
    "au_cash":  ("Australia/Sydney", "10:00", "16:00"),
    "nymex":    ("America/New_York", "09:00", "14:30"),
    "london24": ("Europe/London", "00:00", "16:30"),    # Asian range + London session in one frame (FX, metals)
    "ny_fx":    ("America/New_York", "08:00", "16:00"),
}

# per-side commission as a fraction of position value (FTMO, Oct 2026; see the lab skill's ftmo.md)
COMMISSION = {"stock": 0.00002, "us_index": 0.0, "index": 0.0, "metal": 0.000007, "energy": 0.00002, "soft": 0.00002,
              "crypto": 0.000325, "forex": 0.000025, "other": 0.00002}
# FTMO Swing leverage (max position value = balance x leverage)
LEVERAGE = {"stock": 1, "us_index": 15, "index": 15, "metal": 9, "energy": 1, "soft": 1, "crypto": 1, "forex": 30, "other": 1}
LOW_LEV_INDICES = {"HK50.cash", "US2000.cash", "SPN35.cash"}           # 1:9 on Swing


def group_of(sym):
    if sym in US_INDICES: return "us_index"
    if sym in ENERGY: return "energy"
    if sym.endswith(".cash"): return "index"
    if sym.endswith(".c"): return "soft"
    if sym in METALS: return "metal"
    if sym in CRYPTO: return "crypto"
    if len(sym) == 6 and sym[:3] in CCY and sym[3:] in CCY: return "forex"
    if re.fullmatch(r"[A-Z]{1,5}", sym): return "stock"
    return "other"


def sessions_of(sym):
    g = group_of(sym)
    if g in ("stock", "us_index") or sym == "DXY.cash": return ["us_cash"]
    if sym in EU_INDICES: return ["eu_cash"]
    if sym == "UK100.cash": return ["uk_cash"]
    if sym == "JP225.cash": return ["jp_cash", "us_cash"]
    if sym == "HK50.cash": return ["hk_cash"]
    if sym == "AUS200.cash": return ["au_cash"]
    if g == "metal": return ["london24", "us_cash"]
    if g == "energy": return ["nymex"]
    if g == "crypto": return ["us_cash", "london24"]
    if g == "forex": return ["london24", "ny_fx"]
    return []


def leverage_of(sym):
    return 9 if sym in LOW_LEV_INDICES else LEVERAGE[group_of(sym)]


def commission_of(sym):
    return COMMISSION[group_of(sym)]


# ---------------------------------------------------------------------------------------------------------------- files
NAME_RE = re.compile(r"^(?P<sym>[A-Za-z0-9.]+?)_(?P<tf>M1|M5|M15|M30|H1|H4|D1)_(?P<a>\d{12})_(?P<b>\d{12})\.(npz|csv|csv\.gz)$")


def catalog(dirs=None):
    """{(symbol, tf): path}, keeping the file that starts earliest (then ends latest) when there are several."""
    best = {}
    for d in dirs or EXPORT_DIRS:
        for p in glob.glob(os.path.join(d, "*")):
            m = NAME_RE.match(os.path.basename(p))
            if not m: continue
            k = (m["sym"], m["tf"]); key = (m["a"], "-" + m["b"])
            if k not in best or key < best[k][0]: best[k] = (key, p)
    return {k: v[1] for k, v in best.items()}


def to_utc(d, clock="server"):
    """Add a UTC index. clock='server': FTMO MT5 time (New York + 7 h); 'utc': already UTC."""
    d = d.copy()
    if clock == "utc":
        idx = d.index.tz_localize("UTC") if d.index.tz is None else d.index.tz_convert("UTC")
    else:
        ny = (d.index - pd.Timedelta(hours=7)).tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
        idx = ny.tz_convert("UTC")
    d.index = idx
    return d[~d.index.isna()]


def fix_stock_clock(d):
    """FTMO's second batch of US stock CFDs (AMD, AVGO, BA, CVX, DIS, INTC, JNJ, JPM, KO, MSTR, NKE, PLTR, QCOM, XOM; Oct 2026
    export) carry history 1 hour early until late Jan 2026: their session shows as 08:35-14:55 New York instead of 9:35-15:55
    (checked against tick volume: the open/close spikes sit one hour early). Shift every server day whose first intraday bar
    falls at 08:25-08:45 New York by +1 hour. Daily bars are unaffected (the day boundary is 17:00 New York)."""
    if len(d) < 2 or (d.index[1] - d.index[0]) >= pd.Timedelta(hours=1): return d
    ny = d.index - pd.Timedelta(hours=7)
    day = ny.normalize()
    first = pd.Series(ny, index=d.index).groupby(day).transform("min")
    m = (first.dt.hour * 60 + first.dt.minute).values
    early = (m >= 8 * 60 + 25) & (m <= 8 * 60 + 45)
    if early.any():
        d = d.copy(); idx = d.index.values.copy(); idx[early] = idx[early] + np.timedelta64(60, "m")
        d.index = pd.DatetimeIndex(idx); d = d[~d.index.duplicated(keep="last")].sort_index()
    return d


def drop_daily_artifacts(d):
    """FTMO's intraday histories hold a whole-day bar stamped at server midnight (17:00 New York) on most days of 2015-2020 for
    metals, 2018-21 for crypto and 2019 for forex (range ~ the day's range, tick volume ~100x normal, spread 0). Left in, every
    pending order inside the day's range would 'fill' on it. Drop bars at server 00:00 whose range > 10x and tick volume > 20x
    the rolling median (log #65)."""
    if len(d) < 500 or "tickvol" not in d: return d
    rng = (d.high - d.low).values
    med_r = pd.Series(rng).rolling(2000, min_periods=200).median().bfill().values
    tv = d.tickvol.values.astype(float); med_t = pd.Series(tv).rolling(2000, min_periods=200).median().bfill().values
    mid = (d.index.hour == 0) & (d.index.minute == 0)
    bad = mid & (rng > 10 * med_r) & (tv > 20 * np.maximum(med_t, 1))
    return d[~bad] if bad.any() else d


def load(sym, tf, cat=None):
    cat = cat or catalog()
    p = cat.get((sym, tf))
    if p is None: return None
    raw = load_any(p)
    if tf != "D1": raw = drop_daily_artifacts(raw)
    if group_of(sym) == "stock": raw = fix_stock_clock(raw)
    d = to_utc(raw)
    d.attrs.update(symbol=sym, tf=tf, path=p)
    return d


def specs(dirs=None):
    """Symbol specs saved by the exporter (spread, swap, contract size...), or an empty frame."""
    for d in dirs or EXPORT_DIRS:
        p = os.path.join(d, "symbol_specs.csv")
        if os.path.exists(p): return pd.read_csv(p).set_index("name")
    return pd.DataFrame()


def swap_per_night(sym, price, side, sp_df=None):
    """Swap cost per night in price units per unit of the instrument (positive = cost). Uses the exporter's spec sheet;
    without it, an assumption of 5%/yr for longs and 2%/yr for shorts on CFDs, 1%/yr either way on FX and metals."""
    if sp_df is not None and sym in sp_df.index:
        s = sp_df.loc[sym]; mode = int(s.get("swap_mode", 1)); val = float(s["swap_long"] if side > 0 else s["swap_short"])
        if mode == 1: return -val * float(s["point"])                       # points per lot -> price units per unit
        if mode in (4, 5): return -val / 100.0 / 360.0 * price               # annual interest in %
        if mode == 0: return 0.0
    g = group_of(sym)
    yearly = 0.01 if g in ("forex", "metal") else (0.05 if side > 0 else 0.02)
    return yearly / 360.0 * price


def triple_day(sym, sp_df=None):
    """Weekday (0=Mon) whose rollover is charged three times; FTMO: Wednesday for FX/metals, Friday for CFDs."""
    if sp_df is not None and sym in sp_df.index and "swap_rollover3days" in sp_df.columns:
        w = int(sp_df.loc[sym, "swap_rollover3days"])        # MT5: 0 = Sunday ... 6 = Saturday
        return (w - 1) % 7
    return 2 if group_of(sym) in ("forex", "metal") else 4


def daily_bars(sym, cat=None, intraday=None):
    """Daily bars on the server day (00:00 server = 17:00 New York), from the D1 export when there is one, else built from
    intraday bars. Adds atr (14-day, known at the close) and sp (typical spread: median intraday spread that day x 1.2,
    falling back to the D1 spread x 2)."""
    cat = cat or catalog()

    def vol_of(x):                                   # real volume when the symbol has it, else tick volume, else none
        if "vol" in x and (x.vol > 0).mean() > 0.5: return x.vol.astype(float)
        if "tickvol" in x: return x.tickvol.astype(float)
        return pd.Series(np.nan, index=x.index)

    if (sym, "D1") in cat:
        d = load_any(cat[(sym, "D1")])
        v = vol_of(d)
        d = d[["open", "high", "low", "close", "sp"]].copy(); d["sp_src"] = "d1"; d["volume"] = v
    elif intraday is not None:
        x = intraday.copy(); x.index = x.index.tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)
        g = x.groupby(x.index.normalize())
        d = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last(), "sp": g.sp.median()})
        d["volume"] = vol_of(x).groupby(x.index.normalize()).sum(min_count=1)
        d["sp_src"] = "intraday"
    else:
        return None
    d = d[d.index.weekday < 5] if group_of(sym) != "crypto" else d
    if intraday is not None:
        x = intraday.copy(); x.index = x.index.tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)
        med = x.sp.groupby(x.index.normalize()).median()
        d["sp"] = np.where(d.index.isin(med.index), med.reindex(d.index).values * 1.2, d.sp.values * 2.0)
    else:
        d["sp"] = d.sp * 2.0
    d["sp"] = d.sp.replace(0, np.nan).ffill().bfill()
    pc = d.close.shift(1)
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    d["atr"] = tr.rolling(14).mean()
    d.attrs.update(symbol=sym)
    return d.dropna(subset=["atr"])
