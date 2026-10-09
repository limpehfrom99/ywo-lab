"""RedNote (小红书) "SMC交易员_M", 2026-10-09: "每天如何用 SMC 制定交易计划" (daily SMC trading plan), gold.
Poster's rules (caption + 2-minute video):
  1. Higher frame: price reaches a DAILY bullish order block (OB) and sweeps liquidity there.
  2. 1H: after the sweep, a market structure shift (MSS = close above the last swing high). The last down candle at the
     low before the shift is the 1H bullish OB. The high left above (here the Asian-session high) is the "inducement"
     (IDM) = the target.
  3. 5-min, US session: price comes back into the 1H OB, sweeps a 5-min low, reacts up hard and leaves a bullish 5-min
     fair value gap (FVG). When a candle dips into the FVG and closes back above it with a lower wick ("respected"), enter.
  4. Stop below the FVG, target the IDM. Example: 1:3, "+230 pips". Shorts are the mirror image.
Fixed here before running (the post leaves these open):
  Daily OB: when a day closes above the highest high of the previous 5 days, the last down-close day among those 5 is a
    bullish OB, zone = its low..high, usable from the next day until a daily close below its low (max 90 days).
  1H swings: 3-bar fractals, usable 3 bars after the pivot. Sweep = a 1H low below the last swing low while the 1H bar
    overlaps a live daily bullish OB. MSS = a 1H close above the last swing high (as of the sweep) within 24 hours.
    1H OB = the last down-close 1H candle at or up to 3 bars before the lowest bar, zone = its low..high.
  IDM (target) = highest high from the MSS bar until the entry.
  5-min trigger, within 48 h after the MSS: price trades into the 1H OB; a 5-min low below the previous 12 bars' lows
    (sweep); a bullish FVG (low[f] > high[f-2]) forming within 6 bars after the sweep; then within 12 bars a bar whose low
    dips to the FVG top and closes above the FVG bottom -> buy at that close. Setup cancelled if a 5-min close goes below
    the 1H OB by 0.1 daily ATR, or price reaches the IDM first.
  Stop = min(FVG bottom, entry bar low) - 0.05 daily ATR. Target = IDM; trade only if reward/risk >= 2.
  Entries only 08:00-16:00 New York (the US session). Exit at stop/target on 1-minute bars (same minute: stop), else
  after 24 h. Costs: FTMO gold spread by year + commission.
Variants (all reported): no daily-OB filter; reward/risk >= 1; any session; limit entry at the FVG top instead of the
  respected close; fixed 2R target; and the 5-min trigger alone (no daily/1H context, 2R) as the context's baseline.
Baseline per trade: coin flip (same entry, random side, same distances)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt"); sys.path.insert(0, "/home/claude/lab")
from smc import pivots
from gold_m1 import COMM


def load():
    g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")[["open", "high", "low", "close", "sp"]]
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "sp": "mean"}
    m5 = g.resample("5min", label="left", closed="left").agg(agg).dropna()
    h1 = g.resample("1h", label="left", closed="left").agg(agg).dropna()
    ny = g.index.tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
    key = (ny + pd.Timedelta(hours=7)).normalize()                     # FTMO server day: 17:00 New York boundary
    d1 = g.groupby(key).agg(agg); d1 = d1[d1.index.weekday < 5]
    pc = d1.close.shift(1)
    d1["atr"] = pd.concat([d1.high - d1.low, (d1.high - pc).abs(), (d1.low - pc).abs()], axis=1).max(axis=1).rolling(14).mean().shift(1)
    return g, m5, h1, d1


def day_key(idx):
    ny = pd.DatetimeIndex(idx).tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
    return (ny + pd.Timedelta(hours=7)).normalize(), (ny.hour * 60 + ny.minute).values


class Frame:
    """Price arrays in a 'long' frame. mirror=True negates prices so the same long logic finds the short setups."""
    def __init__(self, g, m5, h1, d1, mirror):
        s = -1.0 if mirror else 1.0
        def px(df):
            o, h, l, c = (df[k].values * s for k in ("open", "high", "low", "close"))
            return (o, l, h, c) if mirror else (o, h, l, c)
        self.mirror = mirror
        self.g_t = g.index.values; (self.g_o, self.g_h, self.g_l, self.g_c) = px(g)
        self.m_t = m5.index; (self.m_o, self.m_h, self.m_l, self.m_c) = px(m5); self.m_sp = m5.sp.values
        self.h_t = h1.index; (self.h_o, self.h_h, self.h_l, self.h_c) = px(h1)
        self.d_t = d1.index; (self.d_o, self.d_h, self.d_l, self.d_c) = px(d1); self.d_atr = d1.atr.values
        self.m_day, self.m_nym = day_key(self.m_t); self.h_day, _ = day_key(self.h_t)
        dpos = pd.Series(np.arange(len(self.d_t)), index=self.d_t)
        self.m_di = dpos.reindex(self.m_day).values; self.h_di = dpos.reindex(self.h_day).values

    def daily_obs(self, k=5, life=90):
        o, h, l, c = self.d_o, self.d_h, self.d_l, self.d_c; N = len(c); obs = []
        for i in range(k, N):
            if c[i] > h[i - k:i].max():
                for j in range(i - 1, i - k - 1, -1):
                    if c[j] < o[j]:
                        lo, hi = l[j], h[j]
                        brk = next((b for b in range(i + 1, min(i + 1 + life, N)) if c[b] < lo), min(i + life, N - 1))
                        obs.append((i + 1, brk, lo, hi)); break
        return obs                                                       # (first usable day, last usable day, lo, hi)

    def ob_live(self, obs):
        """For each 1H bar: (lo, hi) of the live daily OB it overlaps (nearest above), or nan."""
        N = len(self.h_t); lo_a = np.full(N, np.nan); hi_a = np.full(N, np.nan)
        by_day = {}
        for a, b, lo, hi in obs:
            for d in range(a, b + 1): by_day.setdefault(d, []).append((lo, hi))
        for i in range(N):
            di = self.h_di[i]
            if np.isnan(di): continue
            for lo, hi in by_day.get(int(di), []):
                if self.h_l[i] <= hi and self.h_h[i] >= lo:
                    lo_a[i], hi_a[i] = lo, hi; break
        return lo_a, hi_a


def setups_1h(F, use_daily=True, n=3, wait=24):
    lo_ob, hi_ob = F.ob_live(F.daily_obs()) if use_daily else (None, None)
    h, l, o, c = F.h_h, F.h_l, F.h_o, F.h_c; N = len(c)
    ph, pl = pivots(h, l, n)
    SL = SH = None; armed = None; out = []
    for i in range(N):
        j = i - 1 - n                                                   # pivots known before bar i opens
        if j >= 0:
            if pl[j]: SL = l[j]
            if ph[j]: SH = h[j]
        if armed is None:
            ctx = (not use_daily) or np.isfinite(lo_ob[i])
            if SL is not None and SH is not None and l[i] < SL and ctx and SH > l[i]:
                armed = dict(i0=i, lo=l[i], lo_i=i, mss=SH, exp=i + wait); SL = None
            continue
        if l[i] < armed["lo"]: armed["lo"], armed["lo_i"] = l[i], i
        if c[i] > armed["mss"]:
            li = armed["lo_i"]; ob = next((q for q in range(li, max(li - 4, -1), -1) if c[q] < o[q]), li)
            out.append(dict(mss_i=i, ob_lo=l[ob], ob_hi=h[ob], sweep_lo=armed["lo"])); armed = None
        elif i >= armed["exp"]: armed = None
    return out


def trigger(F, a, b, ob_lo, ob_hi, atr, idm0, entry_mode="respect", min_rr=2.0, target_mode="idm", session="us",
            need_zone=True):
    """Scan 5-min bars a..b-1 for the entry. Returns (entry index, entry price, stop, target) or None."""
    h, l, c = F.m_h, F.m_l, F.m_c
    idm = idm0; in_zone = not need_zone; sw = None; fvg = None; buf = 0.05 * atr
    for m in range(a, b):
        if need_zone and c[m] < ob_lo - 0.1 * atr: return None           # 1H OB broken
        if not in_zone:
            if target_mode == "idm": idm = max(idm, h[m])                   # the high left above before price comes back
            if l[m] <= ob_hi: in_zone = True
            else: continue
        elif target_mode == "idm" and h[m] >= idm:
            return None                                                     # target taken before any entry
        if m >= 12 and l[m] < l[m - 12:m].min():                       # 5-min sweep: new 1-hour low
            sw = m; fvg = None
            continue
        if sw is None: continue
        if fvg is None:
            if m - sw > 6: sw = None; continue
            if m - 2 >= sw and l[m] > h[m - 2]: fvg = (h[m - 2], l[m], m)   # (bottom, top, formed at)
            continue
        bot, top, fm = fvg
        if m - fm > 12 or c[m] <= bot: sw = None; fvg = None; continue    # gap not respected in time / closed through
        ok_time = session == "any" or 480 <= F.m_nym[m] < 960
        if entry_mode == "respect":
            if l[m] <= top and c[m] > bot:
                if not ok_time: sw = None; fvg = None; continue
                e = c[m]; stop = min(bot, l[m]) - buf; idx = m
            else: continue
        else:                                                           # limit order at the FVG top
            if l[m] <= top:
                if not ok_time: sw = None; fvg = None; continue
                e = min(top, F.m_o[m]); stop = bot - buf; idx = m
            else: continue
        risk = e - stop
        if risk <= 0: sw = None; fvg = None; continue
        tgt = idm if target_mode == "idm" else e + 2.0 * risk
        if (tgt - e) / risk < min_rr: sw = None; fvg = None; continue
        return idx, e, stop, tgt, entry_mode
    return None


def exit_1m(F, t_entry, e, stop, tgt, d, hold_min=1440):
    """d = +1 in this frame. Walk 1-minute bars after the entry. Returns exit price."""
    i0 = np.searchsorted(F.g_t, t_entry); i1 = min(i0 + hold_min, len(F.g_t))
    hh, ll = F.g_h[i0:i1], F.g_l[i0:i1]
    if d == 1: s_hit = np.flatnonzero(ll <= stop); t_hit = np.flatnonzero(hh >= tgt)
    else: s_hit = np.flatnonzero(hh >= stop); t_hit = np.flatnonzero(ll <= tgt)
    s0 = s_hit[0] if len(s_hit) else 10**9; t0 = t_hit[0] if len(t_hit) else 10**9
    if s0 == t0 == 10**9: return F.g_c[i1 - 1] if i1 > i0 else e
    return stop if s0 <= t0 else tgt


def run_variant(F, setups, **kw):
    rows = []
    for s in setups:
        mi = s["mss_i"]; t_start = F.h_t[mi] + pd.Timedelta(hours=1)
        a = np.searchsorted(F.m_t, t_start); b = min(a + 576, len(F.m_t))
        di = F.m_di[a] if a < len(F.m_t) else np.nan
        if np.isnan(di) or a >= len(F.m_t): continue
        atr = F.d_atr[int(di)]
        if not np.isfinite(atr): continue
        mss_t0 = np.searchsorted(F.m_t, F.h_t[mi]); idm0 = F.m_h[mss_t0:a].max() if a > mss_t0 else F.h_h[mi]
        r = trigger(F, a, b, s["ob_lo"], s["ob_hi"], atr, idm0, **kw)
        if r is None: continue
        rows.append(record(F, r, kw.get("tag", "")))
    return rows


def record(F, r, tag, seed=None):
    idx, e, stop, tgt, mode = r
    if mode == "respect":
        t_entry = (F.m_t[idx] + pd.Timedelta(minutes=5)).to_datetime64()
    else:                                                                   # limit: walk from the minute that filled
        i0 = np.searchsorted(F.g_t, F.m_t[idx].to_datetime64()); w = np.flatnonzero(F.g_l[i0:i0 + 5] <= e)
        t_entry = F.g_t[i0 + (w[0] if len(w) else 0)]
    X = exit_1m(F, t_entry, e, stop, tgt, 1)
    risk = e - stop; cost = F.m_sp[idx] + COMM * (abs(e) + abs(X))
    R = ((X - e) - cost) / risk
    # coin flip: other side, same distances (in this frame: short with stop e+risk, target e-(tgt-e))
    Xf = exit_1m(F, t_entry, e, e + risk, e - (tgt - e), -1)
    Rf = ((e - Xf) - cost) / risk
    return dict(t=pd.Timestamp(t_entry), side=-1 if F.mirror else 1, R=R, R_flip=Rf, rr=(tgt - e) / risk, risk_pct=risk / abs(e) * 100)


def trigger_only(F, rr=2.0):
    """Baseline: the 5-min sweep + FVG + respect trigger alone, every US session, fixed 2R (no daily/1H context)."""
    rows = []; N = len(F.m_t); m = 12
    dpos = F.m_di
    while m < N - 1:
        di = dpos[m]
        if np.isnan(di) or not (480 <= F.m_nym[m] < 960): m += 1; continue
        atr = F.d_atr[int(di)]
        if not np.isfinite(atr): m += 1; continue
        b = m + 1
        while b < N and 480 <= F.m_nym[b] < 960 and dpos[b] == di: b += 1
        r = trigger(F, m, b, -np.inf, np.inf, atr, -np.inf, target_mode="2r", min_rr=rr, need_zone=False)
        if r is not None:
            rows.append(record(F, r, "trigger only")); m = r[0] + 12
        else:
            m = b
    return rows


def stats(label, df):
    if len(df) < 10: return f"{label:58s} n={len(df)}"
    R = df.R.values; t = R.mean() / R.std() * np.sqrt(len(R)); yr = df.groupby(df.t.dt.year).R.mean(); h = len(df) // 2
    d = df.sort_values("t")
    return (f"{label:58s} n={len(R):5d} ({len(R)/14.8:4.0f}/yr) avgR={R.mean():+.3f} t={t:+.1f} win={np.mean(R>0):.0%} "
            f"coin={df.R_flip.mean():+.3f} halves {d.R.iloc[:h].mean():+.3f}/{d.R.iloc[h:].mean():+.3f} yrs>0 {(yr>0).sum()}/{len(yr)} "
            f"med rr {df.rr.median():.1f}")


if __name__ == "__main__":
    import time; t0 = time.time()
    g, m5, h1, d1 = load(); print(f"loaded {len(g):,} 1-min bars {g.index[0].date()}..{g.index[-1].date()} in {time.time()-t0:.0f}s", flush=True)
    res = {}
    for mirror in (False, True):
        F = Frame(g, m5, h1, d1, mirror); side = "short" if mirror else "long"
        S = setups_1h(F, use_daily=True); S0 = setups_1h(F, use_daily=False)
        print(f"{side}: 1H setups with daily OB {len(S)}, without {len(S0)}  ({time.time()-t0:.0f}s)", flush=True)
        V = {"A  as posted (daily OB, 1H MSS+OB, 5m FVG respect, IDM, rr>=2, US)": (S, dict()),
             "B  no daily-OB filter": (S0, dict()),
             "C  reward/risk >= 1": (S, dict(min_rr=1.0)),
             "D  any session": (S, dict(session="any")),
             "E  limit at the FVG top": (S, dict(entry_mode="limit")),
             "F  fixed 2R target": (S, dict(target_mode="2r"))}
        for name, (ss, kw) in V.items():
            res.setdefault(name, []).extend(run_variant(F, ss, **kw))
        res.setdefault("G  5-min trigger alone (no context), 2R, US", []).extend(trigger_only(F))
        print(f"  done {side} ({time.time()-t0:.0f}s)", flush=True)
    out = []
    for name, rows in res.items():
        df = pd.DataFrame(rows)
        if len(df): df["t"] = pd.to_datetime(df.t); out.append(df.assign(variant=name))
        print(stats(name, df) if len(df) else f"{name}: no trades", flush=True)
        if len(df) >= 10:
            for sd, lab in ((1, "longs"), (-1, "shorts")):
                x = df[df.side == sd]
                if len(x) >= 10: print("     " + stats(lab, x))
    allr = pd.concat(out); allr.to_pickle("/home/claude/bt/smc_plan_trades.pkl")
    a = allr[allr.variant.str.startswith("A")]
    if len(a):
        print("\nA by year:", a.groupby(a.t.dt.year).R.agg(["size", "mean"]).round(2).T.to_string())
        print("A last 30 trades avg R: %+.3f" % a.sort_values("t").R.tail(30).mean())
