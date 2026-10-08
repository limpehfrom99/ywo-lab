"""Four strategy families on gold 5-minute bars, each returning trades with t and R (after costs)."""
import numpy as np, pandas as pd
import smc

def opening_candle(b, open_min, bars=6, exit_min=None, hold_bars=None):
    """Direction of the first `bars` 5-min bars from the session open (NY minutes), stop at the far end, exit at exit_min or after hold_bars."""
    o, h, l, c, sp, atr = (b[k].values for k in ["open", "high", "low", "close", "sp", "atr"]); nym = b.nym.values; nyd = b.nyd.values; comm = b.attrs["comm"]
    idx = np.where(nym == open_min)[0]; out = []
    for i0 in idx:
        i1 = i0 + bars
        if i1 >= len(o) - 1 or nyd[i1] != nyd[i0] or (nym[i1] - open_min) != bars * 5: continue
        hi, lo, op, cl = h[i0:i1].max(), l[i0:i1].min(), o[i0], c[i1 - 1]
        if cl == op: continue
        dr = 1 if cl > op else -1; entry = o[i1]; stop = lo if dr == 1 else hi; risk = (entry - stop) * dr
        if risk <= 0.2 * atr[i1]: continue
        if exit_min is not None:
            j_end = i1
            while j_end + 1 < len(o) and nyd[j_end + 1] == nyd[i0] and nym[j_end + 1] < exit_min: j_end += 1
        else: j_end = min(len(o) - 1, i1 + hold_bars - 1)
        exit_px, why = c[j_end], "time"
        for j in range(i1, j_end + 1):
            if dr == 1 and l[j] <= stop: exit_px, why = min(stop, o[j]), "stop"; break
            if dr == -1 and h[j] >= stop: exit_px, why = max(stop, o[j]), "stop"; break
        cost = sp[i1] + comm * (entry + exit_px)
        out.append({"t": b.index[i1], "R": (dr * (exit_px - entry) - cost) / risk, "why": why})
    return pd.DataFrame(out)

def vwap_fade(b, k_atr=2.0, hold=12):
    """Mean reversion: close more than k ATR from the day's VWAP -> fade back to it, stop 1 ATR, 12 bars."""
    o, h, l, c, sp, atr = (b[k].values for k in ["open", "high", "low", "close", "sp", "atr"]); nyd = b.nyd.values; comm = b.attrs["comm"]
    tp = (h + l + c) / 3; vol = np.ones(len(o))
    day_ids = pd.factorize(nyd)[0]; cum = np.zeros(len(o)); n = np.zeros(len(o))
    s = 0.0; k = 0; prev = -1
    for i in range(len(o)):
        if day_ids[i] != prev: s = 0.0; k = 0; prev = day_ids[i]
        s += tp[i]; k += 1; cum[i] = s / k; n[i] = k
    out = []; busy = -1
    for i in range(20, len(o) - hold - 1):
        if i <= busy or n[i] < 12 or not np.isfinite(atr[i]) or atr[i] <= 0: continue
        dev = c[i] - cum[i]
        if abs(dev) < k_atr * atr[i]: continue
        dr = -1 if dev > 0 else 1; entry = o[i + 1]; stop = entry - dr * atr[i]; tgt = cum[i]
        if (tgt - entry) * dr < 0.5 * atr[i]: continue
        j_end = i + hold; exit_px, why = c[j_end], "time"
        for j in range(i + 1, j_end + 1):
            if dr == 1:
                if l[j] <= stop: exit_px, why = min(stop, o[j]), "stop"; break
                if h[j] >= tgt: exit_px, why = max(tgt, o[j]), "target"; break
            else:
                if h[j] >= stop: exit_px, why = max(stop, o[j]), "stop"; break
                if l[j] <= tgt: exit_px, why = min(tgt, o[j]), "target"; break
        risk = atr[i]; cost = sp[i + 1] + comm * (entry + exit_px)
        out.append({"t": b.index[i + 1], "R": (dr * (exit_px - entry) - cost) / risk, "why": why}); busy = j_end + 6
    return pd.DataFrame(out)

def all_families(b):
    fam = {}
    fam["NY open candle (8:30, 30 min, hold to 16:00)"] = opening_candle(b, 510, 6, exit_min=960)
    fam["London open candle (3:00 NY, 30 min, hold 4h)"] = opening_candle(b, 180, 6, hold_bars=48)
    fam["Tokyo open candle (20:00 NY, 30 min, hold 4h)"] = opening_candle(b, 1200, 6, hold_bars=48)
    fam["momentum: structure break (CHoCH), 2R"] = smc.run(b, mode="choch", entry="market", target_r=2.0)
    fam["reversal: liquidity sweep fade, 2R"] = smc.run(b, mode="sweep", entry="market", target_r=2.0)
    fam["mean reversion: VWAP fade (2 ATR)"] = vwap_fade(b)
    return fam
