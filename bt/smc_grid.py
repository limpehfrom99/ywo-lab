"""SMC timeframe grid — follow-up to #31 (Shen: "instead of the daily OB, try 4H, 15-min swings, mix 1H and 5-min").
The #31 rule with every nesting of timeframes, fixed before running and all cells reported:
  zone timeframe (where the order block must be):   D1, H4, or none
  structure timeframe (sweep + MSS + its OB):        H4, H1, M15
  entry timeframe (sweep + FVG + respected close):   M15, M5, M1
  (zone > structure > entry), target = IDM (only if >= 2R) or a fixed 2R; entries 08:00-16:00 New York as posted.
Every definition is the #31 one, counted in bars of its own timeframe so the rule is the same at every scale:
  zone OB = last down candle among the 5 before a close above their highs, live until a close below its low (max 90 bars);
  structure: 3-bar fractals usable 3 bars later, sweep of the last swing low while overlapping a live zone OB, MSS = close
  above the last swing high within 24 bars, OB = last down candle at/up to 3 bars before the low;
  entry: in the structure OB, new 12-bar low, FVG within 6 bars, respected (dip into it, close above its bottom) within 12;
  window for the entry = 48 structure bars (max 5 days); stop = min(FVG bottom, bar low) - 0.05 daily ATR.
Exits on 1-minute bars (stop first when one minute touches both), max 3 days; FTMO gold spread by year + commission; no swap.
Gold M1 2012-01..2026-10-07. In-sample before 2024, out-of-sample from 2024 (selection bar as in quant/evaluate.py).
Baseline per trade: coin flip (same entry, other side, same distances)."""
import sys, time, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, "/home/claude/bt")
from smc import pivots
from gold_m1 import COMM

TF_MIN = {"D1": 1440, "H4": 240, "H1": 60, "M15": 15, "M5": 5, "M1": 1}
RULE = {"M5": "5min", "M15": "15min", "H1": "1h", "H4": "4h"}


def load():
    g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")[["open", "high", "low", "close", "sp"]]
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "sp": "mean"}
    B = {"M1": g}
    for tf, r in RULE.items(): B[tf] = g.resample(r, label="left", closed="left").agg(agg).dropna()
    ny = g.index.tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
    key = (ny + pd.Timedelta(hours=7)).normalize()
    d1 = g.groupby(key).agg(agg); d1 = d1[d1.index.weekday < 5]
    pc = d1.close.shift(1)
    d1["atr"] = pd.concat([d1.high - d1.low, (d1.high - pc).abs(), (d1.low - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    start = (d1.index - pd.Timedelta(hours=7)).tz_localize("America/New_York", ambiguous="NaT", nonexistent="shift_forward").tz_convert("UTC").tz_localize(None)
    d1 = d1[~start.isna()]; d1.index = start[~start.isna()]               # D1 bars indexed by their UTC start
    B["D1"] = d1
    return B


class TF:
    def __init__(self, df, mirror, atr_df=None):
        s = -1.0 if mirror else 1.0
        o, h, l, c = (df[k].values * s for k in ("open", "high", "low", "close"))
        if mirror: h, l = l, h
        self.o, self.h, self.l, self.c = o, h, l, c
        self.t = df.index.values.astype("datetime64[ns]")
        self.sp = df.sp.values
        ny = df.index.tz_localize("UTC").tz_convert("America/New_York")
        self.nym = (ny.hour * 60 + ny.minute).values.astype(np.int64)
        if atr_df is not None:                                             # daily ATR known before each bar's day
            k = np.searchsorted(atr_df.index.values, self.t, side="right") - 1
            self.atr = np.where(k >= 0, atr_df.atr.values[np.clip(k, 0, None)], np.nan)


def zone_obs(z, k=5, life=90):
    o, h, l, c = z.o, z.h, z.l, z.c; N = len(c); obs = []
    for i in range(k, N):
        if c[i] > h[i - k:i].max():
            for j in range(i - 1, i - k - 1, -1):
                if c[j] < o[j]:
                    lo, hi = l[j], h[j]
                    brk = next((b for b in range(i + 1, min(i + 1 + life, N)) if c[b] < lo), min(i + life, N - 1))
                    obs.append((i + 1, brk, lo, hi)); break
    return obs


def zone_context(S, Z):
    if Z is None: return np.ones(len(S.c), bool)
    by_bar = {}
    for a, b, lo, hi in zone_obs(Z):
        for d in range(a, b + 1): by_bar.setdefault(d, []).append((lo, hi))
    zi = np.searchsorted(Z.t, S.t, side="right") - 1
    ok = np.zeros(len(S.c), bool)
    for i in range(len(S.c)):
        for lo, hi in by_bar.get(int(zi[i]), ()):
            if S.l[i] <= hi and S.h[i] >= lo: ok[i] = True; break
    return ok


def setups(S, ctx, n=3, wait=24):
    h, l, o, c = S.h, S.l, S.o, S.c; N = len(c); ph, pl = pivots(h, l, n)
    SL = SH = None; armed = None; out = []
    for i in range(N):
        j = i - 1 - n
        if j >= 0:
            if pl[j]: SL = l[j]
            if ph[j]: SH = h[j]
        if armed is None:
            if SL is not None and SH is not None and l[i] < SL and ctx[i] and SH > l[i]:
                armed = [i, l[i], i, SH, i + wait]; SL = None
            continue
        if l[i] < armed[1]: armed[1], armed[2] = l[i], i
        if c[i] > armed[3]:
            li = armed[2]; ob = next((q for q in range(li, max(li - 4, -1), -1) if c[q] < o[q]), li)
            out.append((i, l[ob], h[ob])); armed = None
        elif i >= armed[4]: armed = None
    return out


@njit(cache=True)
def trigger_nb(h, l, c, nym, a, b, ob_lo, ob_hi, atr, idm0, min_rr, tgt_idm):
    idm = idm0; in_zone = False; sw = -1; fm = -1; bot = 0.0; top = 0.0; buf = 0.05 * atr
    for m in range(a, b):
        if c[m] < ob_lo - 0.1 * atr: return -1, 0.0, 0.0, 0.0
        if not in_zone:
            if tgt_idm: idm = max(idm, h[m])
            if l[m] <= ob_hi: in_zone = True
            else: continue
        elif tgt_idm and h[m] >= idm:
            return -1, 0.0, 0.0, 0.0
        if m >= 12:
            mn = l[m - 12]
            for q in range(m - 11, m): mn = min(mn, l[q])
            if l[m] < mn:
                sw = m; fm = -1; continue
        if sw < 0: continue
        if fm < 0:
            if m - sw > 6: sw = -1; continue
            if m - 2 >= sw and l[m] > h[m - 2]: bot = h[m - 2]; top = l[m]; fm = m
            continue
        if m - fm > 12 or c[m] <= bot: sw = -1; fm = -1; continue
        if l[m] <= top and c[m] > bot:
            if not (480 <= nym[m] < 960): sw = -1; fm = -1; continue
            e = c[m]; stop = min(bot, l[m]) - buf; risk = e - stop
            if risk <= 0: sw = -1; fm = -1; continue
            tgt = idm if tgt_idm else e + 2.0 * risk
            if (tgt - e) / risk < min_rr: sw = -1; fm = -1; continue
            return m, e, stop, tgt
    return -1, 0.0, 0.0, 0.0


@njit(cache=True)
def exit_nb(gh, gl, gc, i0, i1, stop, tgt, d):
    for i in range(i0, i1):
        if d == 1:
            if gl[i] <= stop: return stop
            if gh[i] >= tgt: return tgt
        else:
            if gh[i] >= stop: return stop
            if gl[i] <= tgt: return tgt
    return gc[i1 - 1]


def run_cell(T, zone, struct, entry, tgt_idm, ctx_cache, setup_cache):
    S, E, G = T[struct], T[entry], T["M1"]
    key = (zone, struct)
    if key not in setup_cache:
        if (zone, struct) not in ctx_cache: ctx_cache[(zone, struct)] = zone_context(S, T[zone] if zone else None)
        setup_cache[key] = setups(S, ctx_cache[(zone, struct)])
    st_ns = TF_MIN[struct] * 60_000_000_000; en_ns = TF_MIN[entry] * 60_000_000_000
    win = int(min(48 * TF_MIN[struct], 5 * 1440) / TF_MIN[entry]); hold = 3 * 1440
    rows = []
    for mi, ob_lo, ob_hi in setup_cache[key]:
        t_end = S.t[mi] + np.timedelta64(st_ns, "ns")
        a = np.searchsorted(E.t, t_end); b = min(a + win, len(E.t))
        if a >= len(E.t): continue
        atr = E.atr[a]
        if not np.isfinite(atr): continue
        a0 = np.searchsorted(E.t, S.t[mi]); idm0 = E.h[a0:a].max() if a > a0 else S.h[mi]
        m, e, stop, tgt = trigger_nb(E.h, E.l, E.c, E.nym, a, b, ob_lo, ob_hi, atr, idm0, 2.0, tgt_idm)
        if m < 0: continue
        i0 = np.searchsorted(G.t, E.t[m] + np.timedelta64(en_ns, "ns")); i1 = min(i0 + hold, len(G.t))
        if i1 <= i0: continue
        X = exit_nb(G.h, G.l, G.c, i0, i1, stop, tgt, 1)
        risk = e - stop; cost = E.sp[m] + COMM * (abs(e) + abs(X))
        Xf = exit_nb(G.h, G.l, G.c, i0, i1, e + risk, e - (tgt - e), -1)
        rows.append((E.t[m], (X - e - cost) / risk, (e - Xf - cost) / risk, (tgt - e) / risk, risk / abs(e) * 100))
    return rows


def tstat(x):
    x = np.asarray(x); return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


if __name__ == "__main__":
    t0 = time.time(); B = load(); print(f"loaded in {time.time() - t0:.0f}s", flush=True)
    atr_df = B["D1"][["atr"]]
    cells = [(z, s, e) for z in ("D1", "H4", None) for s in ("H4", "H1", "M15") for e in ("M15", "M5", "M1")
             if TF_MIN[s] > TF_MIN[e] and (z is None or TF_MIN[z] > TF_MIN[s])]
    results = {}
    for mirror in (False, True):
        T = {tf: TF(df, mirror, atr_df) for tf, df in B.items()}
        ctx_cache, setup_cache = {}, {}
        for z, s, e in cells:
            for tgt_idm in (True, False):
                rows = run_cell(T, z, s, e, tgt_idm, ctx_cache, setup_cache)
                results.setdefault((z or "none", s, e, "IDM" if tgt_idm else "2R"), []).extend([r + (-1 if mirror else 1,) for r in rows])
        print(f"{'shorts' if mirror else 'longs'} done in {time.time() - t0:.0f}s", flush=True)
    out = []
    for (z, s, e, tg), rows in results.items():
        df = pd.DataFrame(rows, columns=["t", "R", "R_flip", "rr", "risk_pct", "side"])
        if len(df) == 0: out.append(dict(zone=z, structure=s, entry=e, target=tg, n=0)); continue
        df["t"] = pd.to_datetime(df.t); IS = df.t < "2024-01-01"
        yr = df[IS].groupby(df[IS].t.dt.year).R.agg(["mean", "size"]); yr = yr[yr["size"] >= 10]
        r = dict(zone=z, structure=s, entry=e, target=tg, n=len(df), per_yr=round(len(df) / 14.8, 1), avgR=df.R.mean(), t=tstat(df.R),
                 win=(df.R > 0).mean(), coin=df.R_flip.mean(), longs=df[df.side == 1].R.mean(), shorts=df[df.side == -1].R.mean(),
                 n_is=int(IS.sum()), avg_is=df[IS].R.mean(), t_is=tstat(df[IS].R), coin_is=df[IS].R_flip.mean(),
                 pos_years_is=(yr["mean"] > 0).mean() if len(yr) else np.nan,
                 n_oos=int((~IS).sum()), avg_oos=df[~IS].R.mean(), t_oos=tstat(df[~IS].R), stop_pct=df.risk_pct.median())
        sel = (r["n_is"] >= 60 and r["t_is"] >= 2.5 and r["avg_is"] - r["coin_is"] >= 0.03 and (r["pos_years_is"] or 0) >= 0.6)
        r["verdict"] = ("SURVIVOR" if sel and r["avg_oos"] > 0 and r["t_oos"] >= 1.65 else "WATCH" if sel and r["avg_oos"] > 0
                        else "FAILED OOS" if sel else "not selected")
        out.append(r)
        df.assign(zone=z, structure=s, entry=e, target=tg).to_pickle(f"/home/claude/bt/smc_grid_{z}_{s}_{e}_{tg}.pkl")
    res = pd.DataFrame(out).sort_values("avgR", ascending=False)
    res.to_csv("/home/claude/bt/smc_grid.csv", index=False, float_format="%.4f")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
    print(res[["zone", "structure", "entry", "target", "n", "per_yr", "avgR", "t", "win", "coin", "longs", "shorts", "avg_is", "t_is",
               "avg_oos", "t_oos", "stop_pct", "verdict"]].round(3).to_string(index=False))
    print(f"\n{len(res)} cells; {(res.avgR > 0).sum()} positive; done in {time.time() - t0:.0f}s")
