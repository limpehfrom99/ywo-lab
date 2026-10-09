"""Session matrices: one row per trading day, one column per bar of the session (local exchange time).

Intraday rules are vectorised over these matrices, so a whole symbol-session is simulated in a few array operations.
Missing bars inside a session (no ticks) are filled flat from the previous close; a day is kept only if its first bar
starts within 10 minutes of the session open, its last bar ends within 10 minutes of the close, and at least 70% of the
bars exist. FTMO stock CFDs open at 9:35 New York since 2024, so their first bar is 9:35 and that still counts.
"""
import numpy as np, pandas as pd

from universe import SESSIONS


def _hm(s):
    h, m = s.split(":"); return int(h) * 60 + int(m)


class Session:
    """Attributes: days (DatetimeIndex, local date), O H L C SP V (days x K arrays), bar (minutes per column),
    t (column start times as 'HH:MM'), ok (bool per day), prev_close (previous kept day's close), atr (14-day, previous
    days only), utc_start (UTC timestamp of each day's session open)."""

    def __init__(self, d, name, bar=None, min_cov=0.7, edge_min=10):
        tz, a, b = SESSIONS[name]
        self.name, self.tz = name, tz
        if bar is None:
            step = pd.Series(d.index[1:] - d.index[:-1]).dt.total_seconds().div(60).mode()
            bar = int(step.iloc[0]) if len(step) else 5
        self.bar = bar
        o_m, c_m = _hm(a), _hm(b); K = (c_m - o_m) // bar
        loc = d.index.tz_convert(tz)
        mins = (loc.hour * 60 + loc.minute).values
        sel = (mins >= o_m) & (mins < c_m) & ((mins - o_m) % bar == 0)
        ld = loc[sel].tz_localize(None).normalize()
        days, row = np.unique(ld.values, return_inverse=True)
        col = (mins[sel] - o_m) // bar
        shape = (len(days), K)
        M = {}
        for k, src in (("O", "open"), ("H", "high"), ("L", "low"), ("C", "close"), ("SP", "sp"), ("V", "tickvol")):
            A = np.full(shape, np.nan)
            vals = d[src].values[sel] if src in d else np.zeros(sel.sum())
            A[row, col] = vals
            M[k] = A
        have = ~np.isnan(M["C"])
        first = np.where(have.any(1), have.argmax(1), K)
        last = np.where(have.any(1), K - 1 - have[:, ::-1].argmax(1), -1)
        edge = max(1, edge_min // bar)
        ok = (first <= edge) & (last >= K - 1 - edge) & (have.mean(1) >= min_cov)
        if name in ("us_cash",):                               # weekends never; also drop half days (early close)
            ok &= pd.DatetimeIndex(days).weekday.values < 5
        days = pd.DatetimeIndex(days)[ok]
        for k in M: M[k] = M[k][ok]
        first, last = first[ok], last[ok]
        # fill missing bars flat from the previous close; leading gap (e.g. 9:30-9:35) from the first bar's open
        C = pd.DataFrame(M["C"]).ffill(axis=1).values
        O1 = M["O"][np.arange(len(days)), first] if len(days) else np.array([])
        C = np.where(np.isnan(C), O1[:, None], C)
        fill = np.isnan(M["O"])
        prevC = np.concatenate([O1[:, None], C[:, :-1]], axis=1)
        M["O"] = np.where(fill, prevC, M["O"]); M["H"] = np.where(fill, prevC, M["H"]); M["L"] = np.where(fill, prevC, M["L"])
        M["C"] = C
        M["SP"] = pd.DataFrame(M["SP"]).ffill(axis=1).bfill(axis=1).values
        M["V"] = np.nan_to_num(M["V"])
        self.O, self.H, self.L, self.C, self.SP, self.V = M["O"], M["H"], M["L"], M["C"], M["SP"], M["V"]
        self.days, self.K = days, K
        self.first = first
        self.t = [f"{(o_m + i * bar) // 60:02d}:{(o_m + i * bar) % 60:02d}" for i in range(K)]
        self.open = self.O[np.arange(len(days)), first] if len(days) else np.array([])
        self.close = self.C[:, -1]
        self.high, self.low = self.H.max(1), self.L.min(1)
        self.prev_close = np.r_[np.nan, self.close[:-1]]
        gapdays = np.r_[np.nan, (days[1:] - days[:-1]).days]
        self.prev_close[gapdays > 5] = np.nan                    # long breaks in the data: no "previous close"
        pc = self.prev_close
        tr = np.nanmax(np.vstack([self.high - self.low, np.abs(self.high - pc), np.abs(self.low - pc)]), axis=0)
        self.atr = pd.Series(tr).rolling(14, min_periods=10).mean().shift(1).values   # known before the day opens
        self.utc_start = (pd.DatetimeIndex(days) + pd.Timedelta(minutes=o_m)).tz_localize(tz, ambiguous="NaT", nonexistent="shift_forward").tz_convert("UTC")

    def cols(self, minutes):
        """Number of columns covering the first `minutes` of the session."""
        return max(1, int(round(minutes / self.bar)))

    def col_at(self, hhmm):
        return (_hm(hhmm) - _hm(self.t[0])) // self.bar
