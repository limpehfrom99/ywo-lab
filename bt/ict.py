"""Multi-timeframe ICT models, fixed before testing.

Bias (chosen before the session, no look-ahead):
  '4h'  : direction of the last 4-hour break of structure (close beyond the last confirmed 4H swing high -> bullish, below a swing low -> bearish; 2-bar pivots)
  'pd'  : premium/discount of the 20-day dealing range (previous 20 NY days): below the midpoint -> longs only, above -> shorts only
  'both': 4h and pd must agree
  'none': no bias, direction comes from the structure shift itself
Pools (known before they're hit): PDH/PDL, Asia 20:00-00:00 high/low, London 02:00-05:00 high/low, equal highs/lows, the last confirmed 15-minute swing high/low.
Sequence: sweep of a pool AGAINST the bias inside a killzone -> within 12 five-minute bars a close beyond the last 5m swing in the bias direction
          (the MSS), and the leg must leave a fair value gap (displacement) -> limit at the gap's midpoint, valid 12 bars -> stop beyond the sweep extreme
          -> target: 2R, or the draw on liquidity (PDH for longs / PDL for shorts, skipped if under 1.5R away) -> flat at the end of the NY day.
Silver Bullet: same, but the FVG must form inside 03:00-04:00, 10:00-11:00 or 14:00-15:00 NY, and the sweep may be any pool in the hour before or inside the window.
"""
import numpy as np, pandas as pd
from smc import pivots, killzone

def resample(b, rule):
    x = b[["open", "high", "low", "close"]].resample(rule, label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    return x

def bias_4h(b):
    """Per 5m bar: +1/-1/0 from the last 4H structure break, using only 4H bars that closed before the 5m bar opened."""
    h4 = resample(b, "4h"); hh, ll, cc = h4.high.values, h4.low.values, h4.close.values
    ph, pl = pivots(hh, ll, 2); state = np.zeros(len(h4), int)
    last_ph = last_pl = -1; s = 0
    for i in range(len(h4)):
        j = i - 2
        if j >= 0:
            if ph[j]: last_ph = j
            if pl[j]: last_pl = j
        if last_ph >= 0 and cc[i] > hh[last_ph]: s = 1; last_ph = -1
        elif last_pl >= 0 and cc[i] < ll[last_pl]: s = -1; last_pl = -1
        state[i] = s
    ser = pd.Series(state, index=h4.index + pd.Timedelta(hours=4))     # known from the 4H close
    return ser.reindex(b.index, method="ffill").fillna(0).astype(int).values

def bias_pd(b):
    hi = pd.Series(b.high.values).groupby(b.nyd.values).max(); lo = pd.Series(b.low.values).groupby(b.nyd.values).min()
    mid = ((hi.rolling(20).max() + lo.rolling(20).min()) / 2).shift(1)
    m = pd.Series(b.nyd.values).map(mid).values
    return np.where(np.isnan(m), 0, np.where(b.close.values < m, 1, -1)), m

def swings_15m(b):
    """Per 5m bar: the last confirmed 15-minute swing high and low (2-bar pivots, confirmed 2 bars = 30 min later) and their ids."""
    m15 = resample(b, "15min"); h, l = m15.high.values, m15.low.values
    ph, pl = pivots(h, l, 2); N = len(m15)
    sh = np.full(N, np.nan); sl = np.full(N, np.nan); idh = np.zeros(N, int); idl = np.zeros(N, int)
    ch = cl = np.nan; ih = il = 0
    for i in range(N):
        j = i - 2
        if j >= 0:
            if ph[j]: ch = h[j]; ih = j
            if pl[j]: cl = l[j]; il = j
        sh[i], sl[i], idh[i], idl[i] = ch, cl, ih, il
    idx = m15.index + pd.Timedelta(minutes=15)       # known from the 15m close
    out = pd.DataFrame({"sh": sh, "sl": sl, "ih": idh, "il": idl}, index=idx).reindex(b.index, method="ffill")
    return out.sh.values, out.sl.values, out.ih.values, out.il.values

_CACHE = {}
def prep(b, piv_n=3):
    key = (id(b), piv_n)
    if key not in _CACHE:
        h, l = b.high.values, b.low.values
        _CACHE[key] = (pivots(h, l, piv_n), bias_4h(b), bias_pd(b)[0], swings_15m(b))
    return _CACHE[key]

def run(b, bias="4h", windows="killzones", target="2R", need_sweep=True, entry="fvg", piv_n=3, wait=12, seed=0, random_dir=False):
    o, h, l, c, sp, atr = (b[k].values for k in ["open", "high", "low", "close", "sp", "atr"])
    nym = b.nym.values; nyd = b.nyd.values; comm = b.attrs["comm"]; N = len(o)
    (ph, pl), b4, bpd, (sh15, sl15, ih15, il15) = prep(b, piv_n)
    day_hi = pd.Series(h).groupby(nyd).max(); day_lo = pd.Series(l).groupby(nyd).min()
    rng = np.random.default_rng(seed)
    def in_window(m):
        if windows == "killzones": return (120 <= m < 300) or (420 <= m < 660)          # London 2-5, NY 7-11
        if windows == "silver": return (180 <= m < 240) or (600 <= m < 660) or (840 <= m < 900)
        return True
    out = []; last_ph = last_pl = -1; pend = order = pos = None; prev_day = None; levels = {}; used = set(); sess = {}; used_sw = set()
    for i in range(20, N - 1):
        d = nyd[i]
        if d != prev_day:
            levels = {}
            if prev_day is not None and prev_day in day_hi.index:
                levels = {"PDH": day_hi[prev_day], "PDL": day_lo[prev_day]}
                if np.isfinite(sess.get("asia_hi", -np.inf)): levels["ASIAH"], levels["ASIAL"] = sess["asia_hi"], sess["asia_lo"]
            sess = {"asia_hi": -np.inf, "asia_lo": np.inf, "ldn_hi": -np.inf, "ldn_lo": np.inf}
            used = set(); prev_day = d; pend = None; order = None
        m = nym[i]
        if m >= 1200: sess["asia_hi"] = max(sess["asia_hi"], h[i]); sess["asia_lo"] = min(sess["asia_lo"], l[i])
        if 120 <= m < 300: sess["ldn_hi"] = max(sess["ldn_hi"], h[i]); sess["ldn_lo"] = min(sess["ldn_lo"], l[i])
        if m == 300 and np.isfinite(sess["ldn_hi"]): levels["LDNH"], levels["LDNL"] = sess["ldn_hi"], sess["ldn_lo"]
        j = i - piv_n
        if j >= 0:
            if ph[j]:
                if last_ph >= 0 and abs(h[j] - h[last_ph]) <= 0.15 * atr[i] and (i - last_ph) < 60: levels["EQH"] = max(h[j], h[last_ph]); used.discard("EQH")
                last_ph = j
            if pl[j]:
                if last_pl >= 0 and abs(l[j] - l[last_pl]) <= 0.15 * atr[i] and (i - last_pl) < 60: levels["EQL"] = min(l[j], l[last_pl]); used.discard("EQL")
                last_pl = j
        if not np.isnan(sh15[i]): levels["STH"] = sh15[i]; 
        if not np.isnan(sl15[i]): levels["STL"] = sl15[i]
        a = atr[i]
        if not np.isfinite(a) or a <= 0: continue
        # bias for this bar
        if bias == "4h": bs = b4[i]
        elif bias == "pd": bs = bpd[i]
        elif bias == "both": bs = b4[i] if b4[i] == bpd[i] else 0
        else: bs = 0
        # ---- open position ----
        if pos is not None:
            dr, ent, stop, tgt, i_in = pos["dr"], pos["entry"], pos["stop"], pos["tgt"], pos["i"]
            exit_px = why = None
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
                            "kz": killzone(nym[i_in]), "level": pos["level"], "bias": pos["bias"]})
                pos = None
            continue
        # ---- pending limit ----
        if order is not None:
            if i > order["deadline"] or nyd[i] != d: order = None
            else:
                dr, px = order["dr"], order["px"]
                if (l[i] <= px) if dr == 1 else (h[i] >= px):
                    ent = px if (o[i] - px) * dr > 0 else o[i]; stop = order["stop"]; risk = (ent - stop) * dr
                    tgt = order["tgt"] if order["tgt"] is not None else None
                    if tgt is None and target == "2R": tgt = ent + dr * 2 * risk
                    pos = {"dr": dr, "entry": ent, "stop": stop, "tgt": tgt, "i": i, "level": order["level"], "bias": order["bias"]}
                    order = None
                    if (l[i] <= stop) if dr == 1 else (h[i] >= stop):
                        cost = sp[i] + comm * (ent + stop)
                        out.append({"t": b.index[i], "dir": dr, "R": (-risk - cost) / risk, "cost_R": cost / risk, "why": "stop", "kz": killzone(nym[i]), "level": pos["level"], "bias": pos["bias"]}); pos = None
                continue
        # ---- MSS after a sweep (or without one) ----
        if pend is not None and (i > pend["deadline"]): pend = None
        signal = None
        if need_sweep:
            if pend is not None:
                dr = pend["dr"]
                if dr == 1 and pend["ref"] >= 0 and c[i] > h[pend["ref"]]: signal = (1, pend["ext"], pend["level"]); pend = None
                elif dr == -1 and pend["ref"] >= 0 and c[i] < l[pend["ref"]]: signal = (-1, pend["ext"], pend["level"]); pend = None
                elif dr == 1: pend["ext"] = min(pend["ext"], l[i])
                elif dr == -1: pend["ext"] = max(pend["ext"], h[i])
        else:
            want = bs if bs != 0 else None
            if want in (1, None) and last_ph >= 0 and c[i] > h[last_ph] and last_pl > last_ph and in_window(m):
                signal = (1, l[last_pl], "none"); last_ph = -1
            elif want in (-1, None) and last_pl >= 0 and c[i] < l[last_pl] and last_ph > last_pl and in_window(m):
                signal = (-1, h[last_ph], "none"); last_pl = -1
        if signal is not None:
            dr, ext, lv = signal
            stop = ext - 0.1 * a if dr == 1 else ext + 0.1 * a
            # displacement = the leg left a fair value gap; entry at its midpoint
            px = None
            for k in range(i, max(2, i - wait - 2), -1):
                if dr == 1 and l[k] > h[k-2]: px = (l[k] + h[k-2]) / 2; break
                if dr == -1 and h[k] < l[k-2]: px = (h[k] + l[k-2]) / 2; break
            if windows == "silver" and px is not None and not in_window(m): px = None
            if px is not None:
                if random_dir:
                    dr = int(rng.choice([-1, 1])); ext2 = ext if dr == signal[0] else (h[i] if dr == -1 else l[i]); stop = ext2 - 0.1 * a if dr == 1 else ext2 + 0.1 * a
                    px = o[i+1] if entry == "market" else px
                if entry == "market": px = o[i+1]
                risk = (px - stop) * dr
                if risk > 0.2 * a:
                    tgt = None
                    if target == "draw":
                        draw = levels.get("PDH") if dr == 1 else levels.get("PDL")
                        if draw is None or (draw - px) * dr < 1.5 * risk: continue
                        tgt = draw
                    elif target == "2R": tgt = px + dr * 2 * risk
                    if entry == "market":
                        pos = {"dr": dr, "entry": px, "stop": stop, "tgt": tgt, "i": i + 1, "level": lv, "bias": bs}
                    else:
                        order = {"dr": dr, "px": px, "stop": stop, "tgt": tgt, "deadline": i + wait, "level": lv, "bias": bs}
            continue
        # ---- sweeps against the bias, inside the window ----
        if need_sweep and pend is None and in_window(m) and bs != 0:
            for name, L in list(levels.items()):
                if name in used: continue
                if name in ("STH", "STL"):
                    key = (name, ih15[i] if name == "STH" else il15[i])
                    if key in used_sw: continue
                if bs == 1 and name in ("PDL", "ASIAL", "LDNL", "EQL", "STL"):
                    if l[i] < L and c[i] > L and (L - l[i]) >= 0.1 * a:
                        used.add(name); 
                        if name == "STL": used_sw.add(("STL", il15[i]))
                        pend = {"dr": 1, "level": name, "i": i, "ext": l[i], "ref": last_ph, "deadline": i + wait}; break
                if bs == -1 and name in ("PDH", "ASIAH", "LDNH", "EQH", "STH"):
                    if h[i] > L and c[i] < L and (h[i] - L) >= 0.1 * a:
                        used.add(name)
                        if name == "STH": used_sw.add(("STH", ih15[i]))
                        pend = {"dr": -1, "level": name, "i": i, "ext": h[i], "ref": last_pl, "deadline": i + wait}; break
    return pd.DataFrame(out)
