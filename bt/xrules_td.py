"""Log #98: T1 TD Sequential / TD Combo (Tom DeMark), research/drafts/top_traders_quant.md T1 (frozen in #84), for the cross-asset
harness. LONG (buy-side) signals in the frame; the harness mirrors prices for the sell side.
  flip: C[t-1] > C[t-5] and C[t] < C[t-4] = setup bar 1; setup: each next bar with C[i] < C[i-4] adds 1, any other bar cancels;
  9 completes (s9). Perfection: min(L[s8], L[s9]) <= min(L[s6], L[s7]). TDST = highest high of the 9 setup bars.
  Sequential countdown from s9 (s9 may count): C[i] <= L[i-2]; bar 13 also needs L[i] <= C[cd8] (else deferred). Cancelled by a
  completed sell setup, a close above TDST, or a new buy setup (restarts from its s9 with its TDST).
  Combo countdown from setup bar 1 of a completed setup: C[i] <= L[i-2], L[i] <= L[i-1], C[i] < C[i-1], C[i] < close of the previous
  counted bar; 13 completes; same cancels as Sequential (the draft names none for Combo).
  Signals S9, S9P (perfected), C13, K13 -> long at the next bar's open; stop = L[b*] - TR[b*], b* = lowest low of the setup bars
  (S9/S9P) or of s9..13 (C13) / s1..13 (K13); skipped if the stop is > 4 daily ATR away; out at the close of the H-th bar after
  entry (deadline = start of bar entry+H). No target. tag = risk as a fraction of the entry price (for swaps afterwards).
Look-ahead: every signal uses only bars up to the signal bar; the entry is the next bar's open."""
import sys, numpy as np
sys.path.insert(0, "/home/claude/bt")
from numba import njit
from xgrid import Fill

REGISTRY = {}
_cache = {}


@njit(cache=True)
def td_signals(h, l, c):
    """Returns arrays (kind, bar, stop): kind 0 S9, 1 S9P, 2 C13, 3 K13 (S9P is also emitted as S9)."""
    N = len(c)
    kinds = np.empty(4 * N, np.int64); bars = np.empty(4 * N, np.int64); stops = np.empty(4 * N, np.float64); k = 0
    tr = np.empty(N)
    tr[0] = h[0] - l[0]
    for i in range(1, N): tr[i] = max(h[i], c[i - 1]) - min(l[i], c[i - 1])
    bcnt = 0; scnt = 0                                   # buy / sell setup counts (0 = waiting for a flip)
    # sequential countdown state
    sq_on = False; sq_cnt = 0; sq_tdst = 0.0; sq_c8 = 0.0; sq_start = 0
    # combo countdown state
    cb_on = False; cb_cnt = 0; cb_tdst = 0.0; cb_last = 0.0; cb_start = 0
    for i in range(5, N):
        # --- buy setup
        new_buy = False
        if bcnt == 0:
            if c[i - 1] > c[i - 5] and c[i] < c[i - 4]: bcnt = 1
        else:
            if c[i] < c[i - 4]: bcnt += 1
            else: bcnt = 0
        if bcnt == 9:
            new_buy = True; bcnt = 0
        # --- sell setup
        sell_done = False
        if scnt == 0:
            if c[i - 1] < c[i - 5] and c[i] > c[i - 4]: scnt = 1
        else:
            if c[i] > c[i - 4]: scnt += 1
            else: scnt = 0
        if scnt == 9:
            sell_done = True; scnt = 0
        if new_buy:
            s1 = i - 8
            lo = s1
            hi = h[s1]
            for j in range(s1, i + 1):
                if l[j] < l[lo]: lo = j
                if h[j] > hi: hi = h[j]
            st = l[lo] - tr[lo]
            kinds[k] = 0; bars[k] = i; stops[k] = st; k += 1
            if min(l[i - 1], l[i]) <= min(l[i - 3], l[i - 2]):
                kinds[k] = 1; bars[k] = i; stops[k] = st; k += 1
            # restart both countdowns
            sq_on = True; sq_cnt = 0; sq_tdst = hi; sq_start = i
            cb_on = True; cb_cnt = 0; cb_tdst = hi; cb_start = s1
            # combo: count retroactively s1..i-1 (all known at i), bar i handled below with the others
            for j in range(s1, i):
                if j < 2: continue
                if c[j] <= l[j - 2] and l[j] <= l[j - 1] and c[j] < c[j - 1] and (cb_cnt == 0 or c[j] < cb_last):
                    cb_cnt += 1; cb_last = c[j]
        else:
            if sell_done:
                sq_on = False; cb_on = False
            if sq_on and c[i] > sq_tdst: sq_on = False
            if cb_on and c[i] > cb_tdst: cb_on = False
        # --- sequential count on bar i
        if sq_on and c[i] <= l[i - 2]:
            if sq_cnt < 12:
                sq_cnt += 1
                if sq_cnt == 8: sq_c8 = c[i]
            elif l[i] <= sq_c8:
                lo = sq_start
                for j in range(sq_start, i + 1):
                    if l[j] < l[lo]: lo = j
                kinds[k] = 2; bars[k] = i; stops[k] = l[lo] - tr[lo]; k += 1
                sq_on = False
        # --- combo count on bar i
        if cb_on and c[i] <= l[i - 2] and l[i] <= l[i - 1] and c[i] < c[i - 1] and (cb_cnt == 0 or c[i] < cb_last):
            cb_cnt += 1; cb_last = c[i]
            if cb_cnt >= 13:
                lo = cb_start
                for j in range(cb_start, i + 1):
                    if l[j] < l[lo]: lo = j
                kinds[k] = 3; bars[k] = i; stops[k] = l[lo] - tr[lo]; k += 1
                cb_on = False
    return kinds[:k], bars[:k], stops[:k]


def _sigs(S):
    key = (id(S.c), len(S.c), float(S.c[0]), float(S.c[-1]))
    if key not in _cache:
        if len(_cache) > 4: _cache.clear()
        _cache[key] = td_signals(S.h.astype(np.float64), S.l.astype(np.float64), S.c.astype(np.float64))
    return _cache[key]


def td_rule(S, ctx, kind, H):
    kinds, bars, stops = _sigs(S); t = S.t.view("i8"); N = len(S.c); out = []
    for kk, i, st in zip(kinds, bars, stops):
        if kk != kind: continue
        j = i + 1
        if j + H >= N: continue
        e = S.o[j]; atr = S.atr[j]
        if not np.isfinite(atr) or e - st <= 0 or e - st > 4 * atr: continue
        dl = t[j + H]
        out.append(Fill(t[j], ctx["bar_ns"], e, st, e + 1e6 * (e - st), kind="market", deadline_ns=dl,
                        max_hold_ns=dl - t[j] + 1, tag=f"{(e - st) / abs(e):.3g}"))
    return out


for kind, nm in enumerate(("S9", "S9P", "C13", "K13")):
    for H in (1, 3, 5, 10):
        REGISTRY[f"T1 TD {nm} H{H}"] = (lambda kk, hh: lambda S, ctx: td_rule(S, ctx, kk, hh))(kind, H)
