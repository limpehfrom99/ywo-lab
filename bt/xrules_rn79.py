"""Log #79 — RedNote repost (油管中文配音檔案館) of Inter Equity Trading (Marco), "Liquidity Mastery | Volume 1" (EURUSD, daily -> 15-min).
His reading, shorts as told (longs mirrored by the harness): price leaves lows "intact" (= liquidity, future targets); a sell-off that
takes out lows "induces sellers" (a bearish break of structure); price then runs above the high those sellers sell under, "trapping"
them; "anything above this high is a valid sell", stop "covering the liquidity block" with breathing room, target the structural
low / the intact lows (his examples 1:1.6 and 1:3). He says the video is about reading liquidity, not entries, and that his two
example entries came off news spikes.

Fixed before running:
  swings  = 3-bar fractals, usable 3 bars after the pivot (smc.pivots).
  BOS     = a close below the last usable swing low (each swing low used once). H* = the last usable swing high at that bar.
  LB      = the most recent usable swing high ABOVE H* before the BOS (the "liquidity block" the move came from); none -> no setup.
  entry   = sell limit at H*, live for 48 bars after the BOS; fill on the first bar whose high >= H* (at the bar's open if it opened
            above H*). Fill checked first on each bar; a bar that OPENS at or above the stop cancels the order; a close above the
            stop before the fill cancels it from the next bar on (#57 rule).
  stop    = LB + 0.05 x daily ATR.
  target  "2R" = 2 x risk | "low" = the lowest low from the BOS to the fill, only if >= 1R away (else no trade).
Every symbol of the export, M5-D1 (bt/xrun.py --export); exits on the finest bars, FTMO costs, coin flip per trade.
"""
import sys, numpy as np
sys.path.insert(0, "/home/claude/bt")
from smc import pivots
from xgrid import Fill

REGISTRY = {}


def rule(name):
    def deco(fn): REGISTRY[name] = fn; return fn
    return deco


def _trap(S, ctx, tgt_mode, n=3, window=48, buf=0.05):
    M = ctx["S_other"]; ph, pl = pivots(M.h, M.l, n); ti = M.t.view("i8"); bar = ctx["bar_ns"]; N = len(M.c); out = []
    stack = []                                             # usable swing highs, each lower than the one below it (monotonic):
    last_sl = np.nan                                       # stack[-1] = the latest swing high, stack[-2] = the latest one above it
    for m in range(N):
        q = m - 1 - n
        if q >= 0:
            if ph[q]:
                x = M.h[q]
                while stack and stack[-1] <= x: stack.pop()
                stack.append(x)
            if pl[q]: last_sl = M.l[q]
        if not (np.isfinite(last_sl) and M.c[m] < last_sl): continue
        last_sl = np.nan                                   # this swing low is used
        if len(stack) < 2: continue
        Hs = stack[-1]; lb = stack[-2]
        atr = M.atr[m] if hasattr(M, "atr") else np.nan
        if not np.isfinite(atr) or Hs <= M.c[m]: continue
        stop = lb + buf * atr; fill = None; low = M.l[m]
        for k in range(m + 1, min(m + 1 + window, N)):
            if M.o[k] >= stop: break                       # cancelled at the open
            if M.h[k] >= Hs: fill = k; break               # fill checked before anything else on this bar
            low = min(low, M.l[k])
            if M.c[k] >= stop: break
        if fill is None: continue
        e = max(Hs, M.o[fill]); risk = stop - e
        if risk <= 0: continue
        if tgt_mode == "2R": tgt = e - 2.0 * risk
        else:
            tgt = low
            if (e - tgt) < 1.0 * risk: continue
        out.append(Fill(ti[fill], bar, -e, -stop, -tgt, "limit"))   # short in M = long in S
    return out


@rule("#79 Marco trap 2R")
def marco_trap_2r(S, ctx): return _trap(S, ctx, "2R")


@rule("#79 Marco trap to the post-BOS low")
def marco_trap_low(S, ctx): return _trap(S, ctx, "low")
