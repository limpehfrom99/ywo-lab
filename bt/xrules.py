"""Rules for the cross-asset harness (bt/xgrid.py). Each rule(S, ctx) returns LONG fills in S's frame; the harness mirrors for shorts.
Rules first written for one side in their own scripts are wrapped by running that logic on the other frame (ctx['S_other']) and
negating the prices (a short at p in the mirrored frame is a long at -p in this one)."""
import sys, numpy as np
sys.path.insert(0, "/home/claude/bt")
from smc import pivots
import ob_strategies as O
import fvg_retest as F
from xgrid import Fill

REGISTRY = {}


def rule(name):
    def deco(fn): REGISTRY[name] = fn; return fn
    return deco


def _ti(S): return S.t.view("i8")


# ---------------------------------------------------------------- #33: gap retest after a break of structure, near target
# Fill order (fixed 2026-10-10 01:05 MYT, log #60): the original scripts checked "price ran through the stop" / "a close beyond the
# block" BEFORE the fill on the same bar, so a bar that filled the limit and then hit the stop (or closed beyond the block) was
# dropped instead of counted as a loss: look-ahead that removes losers. fill_first=True checks the fill first (a bar that OPENS
# beyond the stop is still skipped: a pending order can be cancelled at the open). fill_first=False reproduces the old numbers.
@rule("#33 gap retest after BOS, pullback target")
def r33(S, ctx, n=3, buf=0.05, window=48, min_rr=2.0, fill_first=True):
    M = ctx["S_other"]; ph, pl = pivots(M.h, M.l, n); out = []; ti = _ti(M); bar = ctx["bar_ns"]
    for bos_i, bot, top, leg_high, k in F.setups(M, n=n):
        a = max(bos_i, k) + 1; b = min(a + window, len(M.c))
        if a >= len(M.c): continue
        atr = M.atr[a]
        if not np.isfinite(atr): continue
        stop = leg_high + buf * atr; ent = bot; post_low = M.l[bos_i:a].min(); last_pl = None; fill = None
        for m in range(a, b):
            q = m - 1 - n
            if q > bos_i and pl[q]: last_pl = M.l[q]
            if fill_first:
                if M.o[m] >= stop: break
                if M.h[m] >= ent: e = max(ent, M.o[m]); fill = m; break
            else:
                if M.h[m] >= stop: break
                if M.h[m] >= ent: e = max(ent, M.o[m]); fill = m; break
            post_low = min(post_low, M.l[m])
        if fill is None: continue
        risk = stop - e
        if risk <= 0: continue
        tgt = last_pl if last_pl is not None else post_low
        if (e - tgt) / risk < min_rr: continue
        out.append(Fill(ti[fill], bar, -e, -stop, -tgt, "limit"))       # short in M = long in S
    return out


# ---------------------------------------------------------------- #35: breaker block retest, 2R
@rule("#35 breaker block retest 2R")
def r35(S, ctx, rr=2.0, life=100, fill_first=True):
    M, Mo = ctx["S_other"], S                                            # bullish OBs in M; their breakers are shorts in M
    raw_m = O.find_obs(M); raw_o = O.find_obs(Mo)
    obs = O.lifetimes(raw_m, raw_o, len(M.c))
    ph, pl = pivots(M.h, M.l, 3); sl = O.last_swing(M.l, pl, 3); ti = _ti(M); bar = ctx["bar_ns"]; out = []; N = len(M.c)
    for x in obs:
        bk = None
        for q in range(x["valid"], min(x["valid"] + life, N)):
            if M.c[q] < x["lo"]:
                bk = q if np.isfinite(sl[q]) and M.c[q] < sl[q] else None; break
        if bk is None or not np.isfinite(M.atr[bk]): continue
        stop = x["hi"] + 0.05 * M.atr[bk]; fill = None
        for r_ in range(bk + 1, min(bk + 1 + life, N)):
            if fill_first:
                if M.o[r_] >= stop: break
                if M.h[r_] >= x["lo"]: fill = r_; break
                if M.c[r_] > x["hi"]: break
            else:
                if M.c[r_] > x["hi"]: break
                if M.h[r_] >= x["lo"]: fill = r_; break
        if fill is None: continue
        e = max(x["lo"], M.o[fill])
        if stop <= e: continue
        tgt = e - rr * (stop - e)
        out.append(Fill(ti[fill], bar, -e, -stop, -tgt, "limit"))
    return out


@rule("#33 OLD fill order (same-bar stop skipped)")
def r33_old(S, ctx): return r33(S, ctx, fill_first=False)


@rule("#35 OLD fill order (same-bar close beyond block skipped)")
def r35_old(S, ctx): return r35(S, ctx, fill_first=False)
