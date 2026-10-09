"""Log #49-51 (backlog #23-25): three classic day-trading rules on gold M1 2012-26 and FTMO M30 US100/US500 (2021+), AAPL (2015+),
TSLA (2019+). Rules are fixed in research/log.md ("49-51 pre-registered rules") before any run.
  #49 Crabel NR7/NR4 + 30-min opening-range breakout   #50 Larry Williams volatility breakout   #51 Williams "Oops"
Usage: python3 bt/classic_intraday.py [nr|wvb|oops|all] [m5]  -> prints cells, writes results/classic_intraday_<rule>.csv"""
import sys, glob, os, time, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "lab")); sys.path.insert(0, os.path.join(ROOT, "bt"))
from ftmo_data import load_export


def from_server(idx_srv):     # same as data_standard_check.from_server (inlined: that module needs numba)
    ny = (idx_srv - pd.Timedelta(hours=7)).tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
    return ny.tz_convert("UTC").tz_localize(None)

MK = {  # name: (comm per side, spread multiplier, spread floor as fraction of price)
    "gold": (0.000007, 1.0, 0.0), "US100": (0.0, 1.2, 0.0), "US500": (0.0, 1.2, 0.0),
    "AAPL": (0.00002, 1.2, 0.0001), "TSLA": (0.00002, 1.2, 0.0001)}
FILE = {"US100": "US100.cash", "US500": "US500.cash", "AAPL": "AAPL", "TSLA": "TSLA"}


M5 = "m5" in sys.argv[1:]     # resolution check: FTMO M5 pickles (TSLA/AAPL 2021-08+, US100/US500 2025-05+)


def load(m):
    if M5:
        d = pd.read_pickle(f"/home/claude/data/{m}_m5.pkl")[["open", "high", "low", "close", "sp"]]; return d[~d.index.duplicated()], 5
    if m == "gold":
        d = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")[["open", "high", "low", "close", "sp"]]; bm = 1
    else:
        d = load_export(glob.glob(os.path.join(ROOT, "data", "raw", f"{FILE[m]}_M30_*.csv.gz"))[0])
        d.index = from_server(pd.DatetimeIndex(d.index)); d = d[~d.index.isna()].sort_index()
        d = d[["open", "high", "low", "close", "sp"]]; bm = 30
        if m in ("US100", "US500"): d = d.loc["2021-01-22":]
    return d[~d.index.duplicated()], bm


class Bars:
    def __init__(self, d, m, bm):
        self.m, self.bm = m, bm
        self.O, self.H, self.L, self.C = (d[k].values.astype(float) for k in ("open", "high", "low", "close"))
        comm, mult, floor = MK[m]
        self.sp = np.maximum(d.sp.values * mult, floor * self.C); self.comm = comm
        ny = d.index.tz_localize("UTC").tz_convert("America/New_York")
        self.mins = (ny.hour * 60 + ny.minute).values
        self.nyd = ny.tz_localize(None).normalize().values
        self.srvd = (ny.tz_localize(None) + pd.Timedelta(hours=7)).normalize().values
        self.t = d.index.values

    def sessions(self, s, e, broker=False):
        """-> DataFrame indexed by day: i0, i1 (bar slice), O H L C rng atr. Sessions with < 80% of expected bars dropped."""
        if broker:
            key, mask = self.srvd, np.ones(len(self.t), bool); exp = 23 * 60 / self.bm
        else:
            key, mask = self.nyd, (self.mins >= s) & (self.mins < e); exp = (e - s) / self.bm
        pos = np.flatnonzero(mask); k = key[pos]
        u, first, cnt = np.unique(k, return_index=True, return_counts=True)
        i0 = pos[first]; i1 = pos[first + cnt - 1] + 1
        ok = (i1 - i0 == cnt) & (cnt >= 0.8 * exp)
        S = pd.DataFrame({"i0": i0[ok], "i1": i1[ok]}, index=pd.DatetimeIndex(u[ok]))
        S = S[S.index.weekday < 5] if not broker else S[S.index.weekday < 5]
        S["O"] = self.O[S.i0]; S["C"] = self.C[S.i1 - 1]
        S["H"] = [self.H[a:b].max() for a, b in zip(S.i0, S.i1)]; S["L"] = [self.L[a:b].min() for a, b in zip(S.i0, S.i1)]
        S["rng"] = S.H - S.L; S["atr"] = S.rng.rolling(14).mean().shift(1)
        return S

    def cost(self, j, e, x, nights=0):
        return self.sp[j] + self.comm * (abs(e) + abs(x)) + nights * 0.0001 * abs(e)

    def run_out(self, j, jend, side, stop, check_entry=True):
        """Exit price: stop (gap -> open) or close of bar jend-1. check_entry: the fill bar touching the stop = stopped."""
        H, L, O = self.H, self.L, self.O
        if check_entry and ((side == 1 and L[j] <= stop) or (side == -1 and H[j] >= stop)): return stop, True
        for i in range(j + 1, jend):
            if side == 1:
                if O[i] <= stop: return O[i], True
                if L[i] <= stop: return stop, True
            else:
                if O[i] >= stop: return O[i], True
                if H[i] >= stop: return stop, True
        return self.C[jend - 1], False


def trade(B, day, j, jend, side, e, stop, x_override=None, nights=0, both=False):
    """One trade row incl. the coin flip (opposite side, same risk, checked from the next bar)."""
    risk = abs(e - stop)
    if both:     # bar touched both entry sides (or entry + stop): stopped
        X = stop; R = (-risk - B.cost(j, e, X)) / risk; return dict(day=day, side=side, R=R, R_flip=R, stopped=True, risk_pct=risk / e)
    X, st = B.run_out(j, jend, side, stop)
    if x_override is not None and not st: X = x_override
    R = (side * (X - e) - B.cost(j, e, X, nights if not st else 0)) / risk
    Xf, stf = B.run_out(j, jend, -side, e + side * risk, check_entry=False)
    if x_override is not None and not stf: Xf = x_override
    Rf = (-side * (Xf - e) - B.cost(j, e, Xf, nights if not stf else 0)) / risk
    return dict(day=day, side=side, R=R, R_flip=Rf, stopped=st, risk_pct=risk / e)


# ---------------- #49 Crabel NR7 / NR4 + ORB30 ----------------
def rule_nr(B, S, Dref, or_bars):
    rows = []
    dr = Dref.rng.values; dlab = Dref.index.values
    for day, s in S.iterrows():
        k = np.searchsorted(dlab, day.to_datetime64()) - 1          # last completed reference day before this session's day
        if k < 7 or not np.isfinite(s.atr): continue
        nr7 = dr[k] <= dr[k - 6:k + 1].min(); nr4 = dr[k] <= dr[k - 3:k + 1].min()
        a, b = int(s.i0), int(s.i1); oe = a + or_bars
        if oe >= b: continue
        orh, orl = B.H[a:oe].max(), B.L[a:oe].min()
        if orh - orl < 0.02 * s.atr: continue
        r = None
        for j in range(oe, b):
            up, dn = B.H[j] >= orh, B.L[j] <= orl
            if up and dn:
                e = max(orh, B.O[j]); r = trade(B, day, j, b, 1, e, orl, both=True); break
            if up: r = trade(B, day, j, b, 1, max(orh, B.O[j]), orl); break
            if dn: r = trade(B, day, j, b, -1, min(orl, B.O[j]), orh); break
        if r: r.update(nr7=nr7, nr4=nr4); rows.append(r)
    return pd.DataFrame(rows)


# ---------------- #50 Williams volatility breakout ----------------
def rule_wvb(B, S, k, exit_next):
    rows = []; idx = S.index
    for n in range(1, len(S)):
        s, p = S.iloc[n], S.iloc[n - 1]
        if (idx[n] - idx[n - 1]).days > 4: continue
        R0 = p.rng; a, b = int(s.i0), int(s.i1)
        if R0 <= 0: continue
        bu, sl = s.O + k * R0, s.O - k * R0
        xo, nights = None, 0
        if exit_next:
            if n + 1 >= len(S) or (idx[n + 1] - idx[n]).days > 4: continue
            xo = B.O[int(S.i0.iloc[n + 1])]; nights = (idx[n + 1] - idx[n]).days
        r = None
        for j in range(a, b):
            up, dn = B.H[j] >= bu, B.L[j] <= sl
            if up and dn:
                e = max(bu, B.O[j]); r = trade(B, idx[n], j, b, 1, e, e - 0.5 * R0, both=True); break
            if up: e = max(bu, B.O[j]); r = trade(B, idx[n], j, b, 1, e, e - 0.5 * R0, xo, nights); break
            if dn: e = min(sl, B.O[j]); r = trade(B, idx[n], j, b, -1, e, e + 0.5 * R0, xo, nights); break
        if r: rows.append(r)
    return pd.DataFrame(rows)


# ---------------- #51 Williams Oops ----------------
def rule_oops(B, S, optimistic=False):
    rows = []; idx = S.index
    for n in range(1, len(S)):
        s, p = S.iloc[n], S.iloc[n - 1]
        if (idx[n] - idx[n - 1]).days > 4 or not np.isfinite(s.atr): continue
        a, b = int(s.i0), int(s.i1)
        if s.O < p.L: side, lvl = 1, p.L
        elif s.O > p.H: side, lvl = -1, p.H
        else: continue
        lo, hi = s.O, s.O
        for j in range(a, b):
            hit = B.H[j] >= lvl if side == 1 else B.L[j] <= lvl
            if not hit:
                lo, hi = min(lo, B.L[j]), max(hi, B.H[j]); continue
            e = max(lvl, B.O[j]) if side == 1 else min(lvl, B.O[j])
            newx = B.L[j] < lo if side == 1 else B.H[j] > hi       # fill bar made a new session extreme: order unknown
            if optimistic: lo, hi = min(lo, B.L[j]), max(hi, B.H[j])
            ext = lo if side == 1 else hi
            stop = min(ext, e - 0.1 * s.atr) if side == 1 else max(ext, e + 0.1 * s.atr)
            if newx and not optimistic: r = trade(B, idx[n], j, b, side, e, stop, both=True)
            else:
                r = trade(B, idx[n], j, b, side, e, stop) if not optimistic else None
                if optimistic:   # fill bar's extreme came first: stop checked from the next bar only
                    X, st = B.run_out(j, b, side, stop, check_entry=False); risk = abs(e - stop)
                    Xf, _ = B.run_out(j, b, -side, e + side * risk, check_entry=False)
                    r = dict(day=idx[n], side=side, R=(side * (X - e) - B.cost(j, e, X)) / risk,
                             R_flip=(-side * (Xf - e) - B.cost(j, e, Xf)) / risk, stopped=st, risk_pct=risk / e)
            rows.append(r); break
    return pd.DataFrame(rows)


def tstat(x):
    x = np.asarray(x); return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def stats(lab, df):
    if len(df) < 10: return dict(cell=lab, n=len(df))
    df = df.sort_values("day"); IS = df.day < "2024-01-01"; yr = df.groupby(df.day.dt.year).R.mean(); yn = df.groupby(df.day.dt.year).size()
    yr_ok = yr[yn >= 5]
    return dict(cell=lab, n=len(df), per_yr=round(len(df) / max(1, df.day.dt.year.nunique()), 1), avgR=df.R.mean(), t=tstat(df.R),
                win=(df.R > 0).mean(), coin=df.R_flip.mean(), longs=df[df.side == 1].R.mean(), shorts=df[df.side == -1].R.mean(),
                IS=df.R[IS].mean(), OOS=df.R[~IS].mean(), n_OOS=int((~IS).sum()), yrs_pos=f"{(yr_ok > 0).sum()}/{len(yr_ok)}",
                worst_yr=yr_ok.min(), last60=df.R.tail(60).mean(), stop_pct=df.stopped.mean(), med_risk_bp=df.risk_pct.median() * 1e4,
                years=" ".join(f"{y % 100}:{v:+.2f}" for y, v in yr.items()))


def show(r):
    if "avgR" not in r: print(f"{r['cell']:38s} n={r['n']}", flush=True); return
    print(f"{r['cell']:38s} n={r['n']:5d} ({r['per_yr']}/yr) avgR={r['avgR']:+.3f} t={r['t']:+.1f} win={r['win']:.0%} coin={r['coin']:+.3f} "
          f"L {r['longs']:+.3f} S {r['shorts']:+.3f} | IS {r['IS']:+.3f} OOS {r['OOS']:+.3f} (n {r['n_OOS']}) | yrs+ {r['yrs_pos']} worst {r['worst_yr']:+.2f} "
          f"last60 {r['last60']:+.2f} | risk {r['med_risk_bp']:.0f}bp\n{'':40s}{r['years']}", flush=True)


SESS = {"cash": (570, 960)}
if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"; t0 = time.time()
    out = {"nr": [], "wvb": [], "oops": []}; trades = []
    for m in (("TSLA", "AAPL", "US100", "US500") if M5 else ("gold", "US100", "US500", "AAPL", "TSLA")):
        d, bm = load(m); B = Bars(d, m, bm)
        if m == "gold":
            BD = B.sessions(0, 0, broker=True)
            sess = {"gold_ldn": B.sessions(180, 690), "gold_comex": B.sessions(500, 960)}
        else:
            BD = None; sess = {m: B.sessions(570, 960)}
        print(f"--- {m}: {len(d)} bars, sessions {', '.join(f'{k} {len(v)}' for k, v in sess.items())}  ({time.time() - t0:.0f}s)", flush=True)
        if which in ("nr", "all"):
            for name, S in sess.items():
                df = rule_nr(B, S, BD if BD is not None else S, 30 // bm)
                if len(df) == 0: continue
                df["day"] = pd.to_datetime(df.day); trades.append(df.assign(rule="nr", mkt=name))
                for lab, sub in (("all days", df), ("NR7", df[df.nr7]), ("NR4", df[df.nr4]), ("not NR4", df[~df.nr4])):
                    r = stats(f"NR {name} {lab}", sub); out["nr"].append(r); show(r)
        if which in ("wvb", "all"):
            S = BD if m == "gold" else sess[m]
            for k in (0.3, 0.5, 0.7):
                for xn in ((False,) if m == "gold" else (False, True)):
                    df = rule_wvb(B, S, k, xn)
                    if len(df) == 0: continue
                    df["day"] = pd.to_datetime(df.day); trades.append(df.assign(rule=f"wvb{k}{'n' if xn else 'c'}", mkt=m))
                    r = stats(f"WVB {m} k={k} exit {'next open' if xn else 'close'}", df); out["wvb"].append(r); show(r)
        if which in ("oops", "all"):
            S = sess["gold_comex"] if m == "gold" else sess[m]
            for opt in ((False,) if m == "gold" else (False, True)):
                df = rule_oops(B, S, opt)
                if len(df) == 0: continue
                df["day"] = pd.to_datetime(df.day); trades.append(df.assign(rule=f"oops{'_opt' if opt else ''}", mkt=m))
                r = stats(f"OOPS {m}{' (optimistic fill)' if opt else ''}", df); out["oops"].append(r); show(r)
    for k, v in out.items():
        if v: pd.DataFrame(v).to_csv(os.path.join(ROOT, "results", f"classic_intraday_{k}{'_m5' if M5 else ''}.csv"), index=False)
    if trades: pd.concat(trades).to_pickle(f"/home/claude/bt/classic_intraday_trades{'_m5' if M5 else ''}.pkl")
    print(f"done in {time.time() - t0:.0f}s")
