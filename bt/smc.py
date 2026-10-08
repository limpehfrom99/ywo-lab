"""Mechanical Smart Money Concepts model (the ICT '2022'-style sequence), fixed before testing.

Liquidity levels, all known before they are hit:
  previous New York day high/low (PDH/PDL), Asia session high/low (20:00-00:00 NY), London killzone high/low (02:00-05:00 NY),
  equal highs/lows: two consecutive 5-min swing highs (lows) within 0.15 ATR of each other.
Sweep: a 5-min bar trades through a level and closes back on the original side (depth >= 0.1 ATR).
CHoCH / market structure shift: within 12 bars of a sweep, a 5-min close beyond the last confirmed swing low (for a bearish
  reversal) or swing high (bullish). Swings use a 3-bar pivot, confirmed 3 bars later. Displacement variant: the break bar's
  range >= 1 ATR.
Entry: (a) market at the next open after the CHoCH; (b) limit at the midpoint of the fair value gap left by the CHoCH leg
  (the 3-candle gap), valid for 12 bars; (c) limit at the 50% of the order block (last opposite candle before the leg).
Stop: beyond the sweep extreme by 0.1 ATR. Target: 2R (also 3R). Exit by time at the end of the New York day.
Killzones (NY time): Asia 20:00-00:00, London 02:00-05:00, NY AM 08:30-11:00, NY PM 13:30-16:00.
"""
import numpy as np, pandas as pd

def pivots(h, l, n=3):
    from numpy.lib.stride_tricks import sliding_window_view as swv
    N = len(h); ph = np.zeros(N, bool); pl = np.zeros(N, bool)
    if N < 2 * n + 1: return ph, pl
    wh = swv(h, 2 * n + 1); wl = swv(l, 2 * n + 1)
    ph[n:N-n] = (h[n:N-n] == wh.max(axis=1)) & ((wh == h[n:N-n, None]).sum(axis=1) == 1)
    pl[n:N-n] = (l[n:N-n] == wl.min(axis=1)) & ((wl == l[n:N-n, None]).sum(axis=1) == 1)
    return ph, pl

def killzone(nym):
    if 1200 <= nym or nym < 0: return "asia"
    if 120 <= nym < 300: return "london"
    if 510 <= nym < 660: return "ny_am"
    if 810 <= nym < 960: return "ny_pm"
    return "other"

def run(b, mode="smc", entry="market", target_r=2.0, need_disp=False, piv_n=3, wait=12, eq_tol=0.15, seed=0):
    """mode: 'smc' (sweep then CHoCH), 'sweep' (sweep only), 'choch' (CHoCH only, no sweep), 'random' (coin flip at sweeps)."""
    o, h, l, c, sp, atr = (b[k].values for k in ["open", "high", "low", "close", "sp", "atr"])
    nym = b.nym.values; nyd = b.nyd.values; comm = b.attrs["comm"]; N = len(o)
    ph, pl = pivots(h, l, piv_n)
    rng = np.random.default_rng(seed)
    # daily levels
    days = pd.Series(np.arange(N)).groupby(nyd).agg(["min", "max"])
    day_hi = pd.Series(h).groupby(nyd).max(); day_lo = pd.Series(l).groupby(nyd).min()
    out = []
    last_ph = -1; last_pl = -1          # index of the last confirmed pivot high / low
    pend = None                          # pending sweep: dict(dir, level_name, i, extreme, ref_pivot_idx, deadline)
    order = None                         # pending limit order
    pos = None
    sess = {}                            # session extremes for the current day
    prev_day = None; levels = {}
    for i in range(20, N - 1):
        d = nyd[i]
        if d != prev_day:
            # new NY day: previous day high/low become levels; reset sessions
            if prev_day is not None and prev_day in day_hi.index:
                levels = {"PDH": day_hi[prev_day], "PDL": day_lo[prev_day]}
                if np.isfinite(sess.get("asia_hi", -np.inf)): levels["ASIAH"], levels["ASIAL"] = sess["asia_hi"], sess["asia_lo"]
            else: levels = {}
            sess = {"asia_hi": -np.inf, "asia_lo": np.inf, "ldn_hi": -np.inf, "ldn_lo": np.inf}
            used = set(); prev_day = d; pend = None; order = None
        m = nym[i]
        if m >= 1200 or m < 0:   # Asia 20:00-24:00 (the "day" here is the NY calendar day, so Asia belongs to the evening)
            sess["asia_hi"] = max(sess["asia_hi"], h[i]); sess["asia_lo"] = min(sess["asia_lo"], l[i])
        if 120 <= m < 300:
            sess["ldn_hi"] = max(sess["ldn_hi"], h[i]); sess["ldn_lo"] = min(sess["ldn_lo"], l[i])
        if m == 300 and np.isfinite(sess["ldn_hi"]): levels["LDNH"], levels["LDNL"] = sess["ldn_hi"], sess["ldn_lo"]
        # pivots confirmed piv_n bars later
        j = i - piv_n
        if j >= 0:
            if ph[j]:
                if last_ph >= 0 and abs(h[j] - h[last_ph]) <= eq_tol * atr[i] and (i - last_ph) < 60: levels["EQH"] = max(h[j], h[last_ph])
                last_ph = j
            if pl[j]:
                if last_pl >= 0 and abs(l[j] - l[last_pl]) <= eq_tol * atr[i] and (i - last_pl) < 60: levels["EQL"] = min(l[j], l[last_pl])
                last_pl = j
        a = atr[i]
        if not np.isfinite(a) or a <= 0: continue
        # ---- manage open position ----
        if pos is not None:
            dr, ent, stop, tgt, i_in = pos["dr"], pos["entry"], pos["stop"], pos["tgt"], pos["i"]
            exit_px = None; why = None
            if dr == 1:
                if l[i] <= stop: exit_px, why = min(stop, o[i]), "stop"
                elif tgt is not None and h[i] >= tgt: exit_px, why = max(tgt, o[i]), "target"
            else:
                if h[i] >= stop: exit_px, why = max(stop, o[i]), "stop"
                elif tgt is not None and l[i] <= tgt: exit_px, why = min(tgt, o[i]), "target"
            if exit_px is None and (nyd[i+1] != d or i == N - 2): exit_px, why = c[i], "time"
            if exit_px is not None:
                risk = (ent - stop) * dr; cost = sp[i_in] + comm * (ent + exit_px)
                out.append({"t": b.index[i_in], "dir": dr, "R": (dr * (exit_px - ent) - cost) / risk, "cost_R": cost / risk, "why": why,
                            "kz": killzone(nym[i_in]), "level": pos["level"], "stop_atr": risk / atr[i_in]})
                pos = None
            continue
        # ---- pending limit order ----
        if order is not None:
            if i > order["deadline"] or nyd[i] != d: order = None
            else:
                dr, px = order["dr"], order["px"]
                hit = (l[i] <= px) if dr == 1 else (h[i] >= px)
                if hit:
                    ent = px if (o[i] - px) * dr > 0 else o[i]
                    stop = order["stop"]; risk = (ent - stop) * dr
                    pos = {"dr": dr, "entry": ent, "stop": stop, "tgt": ent + dr * target_r * risk if target_r else None, "i": i, "level": order["level"]}
                    order = None
                    stopped_same_bar = (l[i] <= stop) if dr == 1 else (h[i] >= stop)
                    if stopped_same_bar:   # filled and stopped within the same bar: count it as a full loss
                        cost = sp[i] + comm * (ent + stop)
                        out.append({"t": b.index[i], "dir": dr, "R": (-risk - cost) / risk, "cost_R": cost / risk, "why": "stop", "kz": killzone(nym[i]), "level": pos["level"], "stop_atr": risk / atr[i]})
                        pos = None
                continue
        # ---- CHoCH after a sweep (or CHoCH alone) ----
        if pend is not None and i > pend["deadline"]: pend = None
        signal = None
        if mode in ("smc", "choch", "random"):
            if mode == "choch":
                if last_pl >= 0 and c[i] < l[last_pl] and (not need_disp or (h[i] - l[i]) >= a) and last_ph > last_pl:
                    signal = (-1, h[last_ph], "none"); last_pl = -1
                elif last_ph >= 0 and c[i] > h[last_ph] and (not need_disp or (h[i] - l[i]) >= a) and last_pl > last_ph:
                    signal = (1, l[last_pl], "none"); last_ph = -1
            elif pend is not None:
                dr = pend["dr"]
                if dr == -1 and pend["ref"] >= 0 and c[i] < l[pend["ref"]] and (not need_disp or (h[i] - l[i]) >= a):
                    signal = (-1, pend["ext"], pend["level"]); pend = None
                elif dr == 1 and pend["ref"] >= 0 and c[i] > h[pend["ref"]] and (not need_disp or (h[i] - l[i]) >= a):
                    signal = (1, pend["ext"], pend["level"]); pend = None
                elif dr == -1: pend["ext"] = max(pend["ext"], h[i])
                elif dr == 1: pend["ext"] = min(pend["ext"], l[i])
        if signal is not None:
            dr, ext, lv = signal
            if mode == "random": dr = int(rng.choice([-1, 1]))
            stop = ext + dr * -1 * 0.1 * a if False else (ext + 0.1 * a if dr == -1 else ext - 0.1 * a)
            if entry == "market":
                ent = o[i+1]; risk = (ent - stop) * dr
                if risk > 0.2 * a:
                    pos = {"dr": dr, "entry": ent, "stop": stop, "tgt": ent + dr * target_r * risk if target_r else None, "i": i + 1, "level": lv}
            else:
                # fair value gap or order block inside the leg from the sweep bar to the CHoCH bar
                k0 = max(0, i - wait - 2); px = None
                if entry == "fvg":
                    for k in range(i, k0 + 2, -1):
                        if dr == -1 and h[k] < l[k-2]: px = (h[k] + l[k-2]) / 2; break
                        if dr == 1 and l[k] > h[k-2]: px = (l[k] + h[k-2]) / 2; break
                else:
                    for k in range(i - 1, k0, -1):
                        if dr == -1 and c[k] > o[k]: px = (o[k] + c[k]) / 2; break
                        if dr == 1 and c[k] < o[k]: px = (o[k] + c[k]) / 2; break
                if px is not None and (px - stop) * dr > 0.2 * a:
                    order = {"dr": dr, "px": px, "stop": stop, "deadline": i + wait, "level": lv}
            continue
        # ---- sweeps ----
        if mode in ("smc", "sweep", "random") and pend is None:
            for name, L in list(levels.items()):
                if name in used: continue
                if name in ("PDH", "LDNH", "EQH") or (name == "ASIAH"):
                    if h[i] > L and c[i] < L and (h[i] - L) >= 0.1 * a:
                        used.add(name)
                        if mode == "sweep" or mode == "random":
                            dr = -1 if mode == "sweep" else int(rng.choice([-1, 1])); ext = h[i]; stop = ext + 0.1 * a if dr == -1 else l[i] - 0.1 * a
                            ent = o[i+1]; risk = (ent - stop) * dr
                            if risk > 0.2 * a: pos = {"dr": dr, "entry": ent, "stop": stop, "tgt": ent + dr * target_r * risk if target_r else None, "i": i + 1, "level": name}
                        else:
                            pend = {"dr": -1, "level": name, "i": i, "ext": h[i], "ref": last_pl, "deadline": i + wait}
                        break
                else:
                    if l[i] < L and c[i] > L and (L - l[i]) >= 0.1 * a:
                        used.add(name)
                        if mode == "sweep" or mode == "random":
                            dr = 1 if mode == "sweep" else int(rng.choice([-1, 1])); ext = l[i]; stop = ext - 0.1 * a if dr == 1 else h[i] + 0.1 * a
                            ent = o[i+1]; risk = (ent - stop) * dr
                            if risk > 0.2 * a: pos = {"dr": dr, "entry": ent, "stop": stop, "tgt": ent + dr * target_r * risk if target_r else None, "i": i + 1, "level": name}
                        else:
                            pend = {"dr": 1, "level": name, "i": i, "ext": l[i], "ref": last_ph, "deadline": i + wait}
                        break
    return pd.DataFrame(out)

def stats(df, label):
    if len(df) < 10: return {"version": label, "trades": len(df)}
    R = df.R; yr = df.t.dt.year
    return {"version": label, "trades": len(df), "win%": round((R > 0).mean() * 100), "avg R": round(R.mean(), 3),
            "t": round(R.mean() / R.std() * np.sqrt(len(R)), 1), "cost R": round(df.cost_R.mean(), 3),
            "pos years": f"{(R.groupby(yr).mean() > 0).sum()}/{yr.nunique()}"}
