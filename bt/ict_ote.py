"""Reddit r/Daytrading (Oct 2026): ICT 1-minute model on NQ, tested as written.
Rule (poster): MSS = a candle BODY closes beyond the last swing high/low (wick-only break = sweep, not MSS). Fib on the MSS leg using
wicks: 1.0 = leg extreme before the break, 0.0 = leg extreme at the break. Limit entry at the 0.705 OTE, which must sit inside an FVG,
iFVG or order block (confluence). SL at 1.0, TP at 0.0 (2.39R every trade). Setup invalid if price breaks 0.0 before the fill.
Sessions (NY time): Asia 18:00-02:00, London 03:00-05:00, NY AM 09:30-11:30 (tagged by the MSS bar).
Poster's result (NQ futures 1m, Dec 2022-Dec 2025, AI-written script): 4,202 trades, 65.6% wins, +1.22R per trade, max DD 8R.

Choices the post leaves open (fixed here before running, all reported):
  swing = n-bar fractal (n = 3 and 5), known only n bars after the pivot; MSS structure = any break, or only after a lower low
  (bearish structure before a bullish MSS); fill window 240 bars; max hold 1,440 bars; one setup per broken swing.
Fills: bid/ask modelled (buy limit fills when ask <= entry, i.e. bid low <= entry - spread; short TP/SL trigger on the ask).
Same-bar rule (honest): a bar that fills and also hits the stop is a loss; TP is never counted on the fill bar; if one bar touches
both SL and TP, it is a loss. The "bugged" modes reproduce common backtest mistakes to show what they do to the numbers."""
import sys, glob, bisect, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/lab"); sys.path.insert(0, "/home/claude/bt")
from ftmo_data import load_export
from smc import pivots
from gold_m1 import COMM as GCOMM

FILL_WIN, HOLD = 240, 1440

def detect(h, l, o, c, n, lookahead=False):
    """Bullish MSS setups in this price frame (pass negated prices for bearish). Returns list of dicts."""
    N = len(h); ph, pl = pivots(h, l, n); lag = 0 if lookahead else n
    out = []; last_sh = None; swl_i = []; swl_p = []   # confirmed swing lows (index, price), in time order
    for k in range(N):
        j = k - lag
        if j >= n:
            if ph[j]: last_sh = (h[j], j)
            if pl[j]: swl_i.append(j); swl_p.append(l[j])
        if last_sh is not None and c[k] > last_sh[0] and k > last_sh[1]:
            sh_p, sh_i = last_sh; last_sh = None
            seg = l[sh_i:k + 1]; L_i = sh_i + int(np.argmin(seg)); L = l[L_i]
            H = h[L_i:k + 1].max()
            if H <= L: continue
            E = H - 0.705 * (H - L)
            q = bisect.bisect_left(swl_i, sh_i)
            lower_low = q > 0 and L < swl_p[q - 1]
            # confluence: bullish FVG inside the leg containing E
            fvg = False
            if k - L_i >= 2:
                jj = np.arange(L_i + 2, k + 1)
                lo_z, hi_z = h[jj - 2], l[jj]
                fvg = bool(np.any((hi_z > lo_z) & (lo_z <= E) & (E <= hi_z)))
            # iFVG: bearish FVG after the swing high, closed back above (inverted), containing E
            ifvg = False
            if k - sh_i >= 2:
                for j2 in range(max(sh_i + 2, k - 300), k + 1):
                    if h[j2] < l[j2 - 2] and h[j2] <= E <= l[j2 - 2] and c[j2 + 1:k + 1].max(initial=-np.inf) > l[j2 - 2]:
                        ifvg = True; break
            # order block: last down-close candle at or just before the leg low, its range containing E
            ob = False
            for j3 in range(min(L_i + 1, k), max(L_i - 10, 0), -1):
                if c[j3] < o[j3]:
                    ob = l[j3] <= E <= h[j3]; break
            out.append(dict(k=k, sh_i=sh_i, L_i=L_i, L=L, H=H, E=E, lower_low=lower_low, fvg=fvg, ifvg=ifvg, ob=ob))
    return out

def simulate(setups, h, l, c, sp, mirrored, mode="honest", cost_pts=None, comm=0.0):
    """mirrored=False: real longs; True: real shorts in a negated frame. mode: honest | optimistic.
    cost_pts: None = bid/ask from the data's spread; 0 = no costs; x = fixed round-trip cost in price units (futures-like)."""
    N = len(h); R = np.full(len(setups), np.nan)
    for s_i, s in enumerate(setups):
        k, E, SL, TP = s["k"], s["E"], s["L"], s["H"]; risk = E - SL
        if risk <= 0: continue
        spr = sp[k] if cost_pts is None else 0.0
        f_sh, t_sh, s_sh = (0.0, spr, spr) if mirrored else (-spr, 0.0, 0.0)
        a, b = k + 1, min(k + 1 + FILL_WIN, N)
        if a >= b: continue
        hi, lo = h[a:b], l[a:b]
        fill = np.flatnonzero(lo <= E + f_sh); inval = np.flatnonzero(hi > TP)
        if len(fill) == 0: continue
        f = fill[0]
        if len(inval) and (inval[0] < f or (inval[0] == f and mode == "honest")): continue
        f += a
        if mode == "honest" and l[f] <= SL + s_sh: R[s_i] = -1.0
        elif mode == "optimistic" and h[f] >= TP + t_sh: R[s_i] = (TP - E) / risk
        else:
            a2, b2 = f + 1, min(f + 1 + HOLD, N)
            if a2 >= b2: continue
            hs, ls = h[a2:b2], l[a2:b2]
            st = np.flatnonzero(ls <= SL + s_sh); tg = np.flatnonzero(hs >= TP + t_sh)
            st0 = st[0] if len(st) else 10**9; tg0 = tg[0] if len(tg) else 10**9
            if st0 == 10**9 and tg0 == 10**9: R[s_i] = (c[b2 - 1] - E) / risk
            elif mode == "honest": R[s_i] = -1.0 if st0 <= tg0 else (TP - E) / risk
            else: R[s_i] = (TP - E) / risk if tg0 <= st0 else -1.0
        if cost_pts: R[s_i] -= cost_pts / risk
        if comm: R[s_i] -= comm * abs(E) * 2 / risk
    return R

def session(ny_min):
    if ny_min >= 1080 or ny_min < 120: return "asia"
    if 180 <= ny_min < 300: return "london"
    if 570 <= ny_min < 690: return "nyam"
    return "other"

def run(name, d, comm, n_list=(3, 5)):
    ny = d.index.tz_localize("UTC").tz_convert("America/New_York") if d.index.tz is None else d.index.tz_convert("America/New_York")
    nym = (ny.hour * 60 + ny.minute).values; years = ny.year.values
    h, l, o, c, sp = (d[k].values.astype(float) for k in ("high", "low", "open", "close", "sp"))
    rows = []
    for n in n_list:
        for look in (False, True):
            for mir in (False, True):
                H_, L_, O_, C_ = (h, l, o, c) if not mir else (-l, -h, -o, -c)
                st = detect(H_, L_, O_, C_, n, lookahead=look)
                base = dict(n=n, lookahead=look, side=-1 if mir else 1)
                modes = [("honest", None), ("honest", 0.0), ("optimistic", 0.0)] if not look else [("honest", 0.0), ("optimistic", 0.0)]
                if name.startswith("US100"): modes.append(("honest", 0.5))
                for mode, cost in modes:
                    R = simulate(st, H_, L_, C_, sp, mir, mode, cost, comm if cost is None else 0.0)
                    for s, r in zip(st, R):
                        if np.isnan(r): continue
                        rows.append(dict(**base, mode=mode, cost="spread" if cost is None else ("none" if cost == 0 else f"{cost}pt"), R=r,
                                         sess=session(nym[s["k"]]), year=years[s["k"]], lower_low=s["lower_low"],
                                         conf=s["fvg"] or s["ifvg"] or s["ob"], risk_pts=s["E"] - s["L"]))
    df = pd.DataFrame(rows); df["inst"] = name
    return df

def summarize(df):
    df = df[df.sess != "other"]
    g = df.groupby(["inst", "n", "lookahead", "mode", "cost", "lower_low", "conf"])
    out = g.R.agg(n_tr="count", avgR="mean", win=lambda x: (x > 0).mean(), t=lambda x: x.mean() / (x.std() / np.sqrt(len(x))) if len(x) > 2 else np.nan)
    return out.reset_index()

if __name__ == "__main__":
    which = sys.argv[1]
    if which == "us100m1":
        d = load_export(glob.glob("/home/claude/data/assets/US100.cash_M1_*.csv")[0]); d.index = d.index - pd.Timedelta(hours=7)
        d.index = d.index.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT"); d = d[~d.index.isna()]
        df = run("US100 M1", d, 0.0)
    elif which == "us500m1":
        d = load_export(glob.glob("/home/claude/data/assets/US500.cash_M1_*.csv")[0]); d.index = d.index - pd.Timedelta(hours=7)
        d.index = d.index.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT"); d = d[~d.index.isna()]
        df = run("US500 M1", d, 0.0)
    elif which == "us100m5":
        d = pd.read_pickle("/home/claude/data/US100_m5.pkl")[["open", "high", "low", "close", "sp"]]; df = run("US100 M5", d, 0.0)
    elif which == "gold":
        g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl").loc[sys.argv[2]:sys.argv[3]]
        df = run(f"gold M1 {sys.argv[2][:4]}-{sys.argv[3][:4]}", g[["open", "high", "low", "close", "sp"]], GCOMM, n_list=(3,))
    df.to_pickle(f"/home/claude/bt/ict_ote_{which}{'_' + sys.argv[2][:4] if which == 'gold' else ''}.pkl")
    s = summarize(df); pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(s.round(3).to_string(index=False))
