"""Daily rules (signal at the daily close, entry at the next day's open), fixed before any data is seen.

Costs: typical spread once per round trip + commission both sides + swap for every rollover held (17:00 New York,
triple on the broker's triple day), from the exporter's spec sheet when present.
Stops are checked on daily highs/lows from the entry day on (a day that opens through the stop fills at the open).
R = (P&L - costs) / risk unit; the risk unit is the initial stop distance (a multiple of the 14-day ATR).
Baselines per trade: random direction with the same entry, exit day and stop distance (coin), and always-long.
"""
import numpy as np, pandas as pd

from universe import swap_per_night, triple_day, commission_of, group_of


def rsi(c, n):
    d = np.diff(c, prepend=np.nan)
    up = pd.Series(np.clip(d, 0, None)).ewm(alpha=1 / n, adjust=False).mean().values
    dn = pd.Series(np.clip(-d, 0, None)).ewm(alpha=1 / n, adjust=False).mean().values
    with np.errstate(divide="ignore", invalid="ignore"):
        return 100 - 100 / (1 + up / dn)


def sma(x, n): return pd.Series(x).rolling(n).mean().values


class Daily:
    def __init__(self, D, sym, specs=None):
        self.sym, self.D = sym, D
        self.O, self.H, self.L, self.C = (D[k].values.astype(float) for k in ("open", "high", "low", "close"))
        self.A, self.SP = D.atr.values, D.sp.values
        self.days = D.index
        self.wd = D.index.weekday.values
        self.comm = commission_of(sym)
        self.tri = -1 if group_of(sym) == "crypto" else triple_day(sym, specs)
        self.specs = specs

    def swap_cost(self, a, b, d, price):
        """Swap paid for holding from the open of day a to day b (rollovers at the end of days a .. b-1)."""
        if b <= a: return 0.0
        mult = np.where(self.wd[a:b] == self.tri, 3, 1).sum() if self.tri >= 0 else (b - a)
        return mult * swap_per_night(self.sym, price, d, self.specs)

    def trade(self, a, d, stop_dist, exit_b, exit_kind="open", risk_dist=None):
        """Enter at the open of day a in direction d; stop at stop_dist; planned exit at day exit_b ('open' or 'close').
        Returns (R, exit day, exit price, stopped)."""
        N = len(self.C); E = self.O[a]; st = E - d * stop_dist; risk = risk_dist or stop_dist
        last = min(exit_b, N - 1)
        stopped, X, b = False, None, last
        for k in range(a, last + 1):
            if k == last and exit_kind == "open" and k > a:
                X, b = self.O[k], k; break
            o, h, l = self.O[k], self.H[k], self.L[k]
            if (d == 1 and l <= st) or (d == -1 and h >= st):
                X = st if k == a else (min(st, o) if d == 1 else max(st, o)); b, stopped = k, True; break
        if X is None: X, b = (self.C[last], last) if exit_kind == "close" or last == a else (self.O[last], last)
        cost = self.SP[a] + self.comm * (abs(E) + abs(X)) + self.swap_cost(a, b, d, E)
        return (d * (X - E) - cost) / risk, b, X, stopped

    def run(self, signals, n_flip=10, seed=0):
        """signals: list of (a, d, stop_dist, exit_b, exit_kind). Returns one row per trade with R and three baselines:
        coin (random direction, same timing), base (same direction and holding time, random entry day: does the
        timing beat just being in the market?), long_only (always long, same timing); and R2x (double spread)."""
        rows = []; rng = np.random.default_rng(seed); N = len(self.C)
        okA = np.flatnonzero(np.isfinite(self.A))
        for a, d, sd, b, kind in signals:
            if not (np.isfinite(sd) and sd > 0) or a < 1 or not np.isfinite(self.A[a - 1]): continue
            R, bx, X, stopped = self.trade(a, d, sd, b, kind)
            b_eff = bx if not stopped else min(b, N - 1)
            hold = max(b_eff - a, 0)
            coins = [self.trade(a, (1 if rng.random() < 0.5 else -1), sd, b_eff, kind)[0] for _ in range(n_flip)]
            mult = sd / self.A[a - 1]
            pool = okA[(okA >= 1) & (okA < N - hold - 1)] + 1
            rt = []
            for a2 in rng.choice(pool, size=min(n_flip, len(pool)), replace=False) if len(pool) else []:
                sd2 = mult * self.A[a2 - 1]
                if np.isfinite(sd2) and sd2 > 0: rt.append(self.trade(a2, d, sd2, a2 + hold, kind)[0])
            lo = self.trade(a, 1, sd, b_eff, kind)[0]
            R2 = R - self.SP[a] / sd
            rows.append((self.days[a], d, R, np.mean(coins), np.mean(rt) if rt else np.nan, lo, R2, sd / self.O[a], hold, stopped))
        return pd.DataFrame(rows, columns=["day", "d", "R", "coin", "base", "long_only", "R2x", "risk_frac", "hold", "stopped"])


# -------------------------------------------------------------------------------------------------------------- rules
# Each returns a list of signals (a, d, stop_dist, exit_b, exit_kind) with a = entry day index (open of day a).

def donchian(x, n_in=20, n_out=10, stop_atr=2.0, long_only=False):
    C, H, L, A = x.C, x.H, x.L, x.A; N = len(C); sig = []
    hh = pd.Series(H).rolling(n_in).max().shift(1).values; ll = pd.Series(L).rolling(n_in).min().shift(1).values
    xh = pd.Series(H).rolling(n_out).max().shift(1).values; xl = pd.Series(L).rolling(n_out).min().shift(1).values
    i = max(n_in, 15)
    while i < N - 1:
        d = 1 if C[i] > hh[i] else (-1 if (C[i] < ll[i] and not long_only) else 0)
        if d == 0 or not np.isfinite(A[i]): i += 1; continue
        a = i + 1; sd = stop_atr * A[i]; st = x.O[a] - d * sd
        j = a; b = N - 1
        while j < N - 1:                                        # exit signal at a close -> out at the next open
            if (d == 1 and (L[j] <= st or C[j] < xl[j])) or (d == -1 and (H[j] >= st or C[j] > xh[j])): b = j + 1; break
            j += 1
        sig.append((a, d, sd, b, "open")); i = max(b - 1, i + 1)
    return sig


def trend_ma(x, fast=50, slow=200, stop_atr=3.0):
    C, A = x.C, x.A; N = len(C); f, s = sma(C, fast), sma(C, slow); sig = []; i = slow
    while i < N - 1:
        d = 1 if (C[i] > s[i] and f[i] > s[i] and C[i] > f[i]) else (-1 if (C[i] < s[i] and f[i] < s[i] and C[i] < f[i]) else 0)
        if d == 0 or not np.isfinite(A[i]): i += 1; continue
        a = i + 1; sd = stop_atr * A[i]; st = x.O[a] - d * sd; j = a; b = N - 1
        while j < N - 1:
            if (d == 1 and (x.L[j] <= st or C[j] < f[j])) or (d == -1 and (x.H[j] >= st or C[j] > f[j])): b = j + 1; break
            j += 1
        sig.append((a, d, sd, b, "open")); i = max(b - 1, i + 1)
    return sig


def tsmom(x, lookback=252, stop_atr=3.0):
    C, A, days = x.C, x.A, x.days; N = len(C); sig = []
    first = np.r_[True, days.month[1:] != days.month[:-1]]          # first trading day of each month
    idx = np.flatnonzero(first)
    for k in range(len(idx) - 1):
        a = idx[k]; b = idx[k + 1]; i = a - 1
        if i - lookback < 0 or not np.isfinite(A[i]): continue
        d = 1 if C[i] > C[i - lookback] else -1
        sig.append((a, d, stop_atr * A[i], b, "open"))
    return sig


def rsi2(x, lo=10, hi=90, max_hold=10, stop_atr=3.0, long_only=False):
    C, A = x.C, x.A; N = len(C); r = rsi(C, 2); s200 = sma(C, 200); s5 = sma(C, 5); sig = []; i = 200
    while i < N - 1:
        d = 1 if (r[i] < lo and C[i] > s200[i]) else (-1 if (r[i] > hi and C[i] < s200[i] and not long_only) else 0)
        if d == 0 or not np.isfinite(A[i]): i += 1; continue
        a = i + 1; sd = stop_atr * A[i]; st = x.O[a] - d * sd; j = a; b = min(a + max_hold, N - 1)
        while j < min(a + max_hold, N - 1):
            if (d == 1 and (x.L[j] <= st or C[j] > s5[j])) or (d == -1 and (x.H[j] >= st or C[j] < s5[j])): b = j + 1; break
            j += 1
        sig.append((a, d, sd, b, "open")); i = max(b - 1, i + 1)
    return sig


def turn_of_month(x, stop_atr=2.0):
    days = x.days; N = len(days); sig = []
    ym = days.year * 12 + days.month
    last = np.r_[ym[1:] != ym[:-1], False]
    for a in np.flatnonzero(last):
        b = a + 3                                                     # close of the 3rd trading day of the new month
        if a < 15 or b >= N or not np.isfinite(x.A[a - 1]): continue
        sig.append((a, 1, stop_atr * x.A[a - 1], b, "close"))
    return sig


def high52(x, hold=20, stop_atr=2.0):
    C, A = x.C, x.A; N = len(C); hh = pd.Series(C).rolling(252).max().values; sig = []; i = 252
    while i < N - 1:
        if C[i] >= hh[i] and np.isfinite(A[i]):
            a = i + 1; b = min(a + hold, N - 1); sig.append((a, 1, stop_atr * A[i], b, "open")); i = b
        else: i += 1
    return sig


VARIANTS = [
    ("DON20", donchian, dict(n_in=20, n_out=10)),
    ("DON55", donchian, dict(n_in=55, n_out=20)),
    ("DON20_long", donchian, dict(n_in=20, n_out=10, long_only=True)),
    ("MA50_200", trend_ma, dict()),
    ("TSMOM12", tsmom, dict(lookback=252)),
    ("TSMOM3", tsmom, dict(lookback=63)),
    ("RSI2", rsi2, dict()),
    ("RSI2_long", rsi2, dict(long_only=True)),
    ("TOM", turn_of_month, dict()),
    ("HIGH52", high52, dict()),
]


def cross_section(dailies, kind="xsmom", top=0.2, stop_atr=3.0):
    """Cross-sectional rules over a group (US stocks). xsmom: each month rank by the return from t-126 to t-21, long the
    top fifth, short the bottom fifth, hold one month. xsrev: each week rank by the last 5 days' return, long the bottom
    fifth, short the top fifth, hold one week. Returns {symbol: DataFrame of trades} (same columns as Daily.run)."""
    closes = pd.DataFrame({s: x.D.close for s, x in dailies.items()}).sort_index()
    cal = closes.index
    if kind == "xsmom":
        first = np.r_[True, cal.month[1:] != cal.month[:-1]]; reb = np.flatnonzero(first)
        score = closes.shift(21) / closes.shift(126) - 1; sign = 1
    else:
        first = np.r_[True, cal.isocalendar().week.values[1:] != cal.isocalendar().week.values[:-1]]; reb = np.flatnonzero(first)
        score = closes / closes.shift(5) - 1; sign = -1
    sigs = {s: [] for s in dailies}
    for k in range(len(reb) - 1):
        a_day, b_day = cal[reb[k]], cal[reb[k + 1]]
        sc = score.iloc[reb[k] - 1].dropna() if reb[k] >= 1 else pd.Series(dtype=float)
        if len(sc) < 8: continue
        q = int(max(1, round(len(sc) * top)))
        ranked = sc.sort_values()
        picks = [(s, -sign) for s in ranked.index[:q]] + [(s, sign) for s in ranked.index[-q:]]
        for s, d in picks:
            x = dailies[s]; pos = x.days.get_indexer([a_day, b_day])
            if pos[0] < 1 or pos[1] < 0: continue
            sigs[s].append((pos[0], d, stop_atr * x.A[pos[0] - 1], pos[1], "open"))
    return {s: dailies[s].run(v) for s, v in sigs.items() if v}
