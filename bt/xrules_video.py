"""Rules from the second video batch (K线之下 series, 熊猫教练 SB structure), for the cross-asset harness (bt/xgrid.py). Every rule is
written LONG in its frame; the harness mirrors prices for the short side. Fixed before running; stops/targets as the videos give them
(mostly "stop just beyond the level, target 2x the stop"). Indicators use closed bars only; market entries are at the next bar's open.
"Daily ATR" = S.atr (known before the bar's day); "bar ATR" = ATR(14) of this timeframe's bars up to the previous bar."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from smc import pivots
import ob_strategies as O
from xgrid import Fill

REGISTRY = {}
BUF = 0.05


def rule(name):
    def deco(fn): REGISTRY[name] = fn; return fn
    return deco


# ------------------------------------------------------------------------------------------------ indicators (closed bars)
def ema(x, n): return pd.Series(x).ewm(span=n, adjust=False).mean().values
def sma(x, n): return pd.Series(x).rolling(n).mean().values


def rsi(c, n=14):
    d = np.diff(c, prepend=c[0]); up = pd.Series(np.clip(d, 0, None)).ewm(alpha=1 / n, adjust=False).mean().values
    dn = pd.Series(np.clip(-d, 0, None)).ewm(alpha=1 / n, adjust=False).mean().values
    with np.errstate(divide="ignore", invalid="ignore"): return 100 - 100 / (1 + up / dn)


def bar_atr(S, n=14):
    pc = np.r_[S.c[0], S.c[:-1]]
    tr = np.maximum(S.h - S.l, np.maximum(np.abs(S.h - pc), np.abs(S.l - pc)))
    return pd.Series(tr).rolling(n).mean().shift(1).values


def heikin_ashi(S):
    hc = (S.o + S.h + S.l + S.c) / 4; ho = np.empty_like(hc); ho[0] = (S.o[0] + S.c[0]) / 2
    for i in range(1, len(hc)): ho[i] = (ho[i - 1] + hc[i - 1]) / 2
    hh = np.maximum(S.h, np.maximum(ho, hc)); hl = np.minimum(S.l, np.minimum(ho, hc))
    return ho, hh, hl, hc


def macd(c, f=12, s=26, sig=9):
    m = ema(c, f) - ema(c, s); return m, ema(m, sig)


def stoch(S, n=14, d=3):
    hh = pd.Series(S.h).rolling(n).max().values; ll = pd.Series(S.l).rolling(n).min().values
    with np.errstate(divide="ignore", invalid="ignore"): k = 100 * (S.c - ll) / (hh - ll)
    return k, pd.Series(k).rolling(d).mean().values


def vix_fix(S, pd_=22, bbl=20, mult=2.0, lb=50, ph=0.85):
    hc = pd.Series(S.c).rolling(pd_).max().values
    with np.errstate(divide="ignore", invalid="ignore"): w = (hc - S.l) / np.abs(hc) * 100
    mid = sma(w, bbl); sd = pd.Series(w).rolling(bbl).std(ddof=0).values
    rng = pd.Series(w).rolling(lb).max().values * ph
    return (w >= mid + mult * sd) | (w >= rng)


def swing_lows(S, n=3):
    _, pl = pivots(S.h, S.l, n); return np.flatnonzero(pl)


def recent_swing_low(S, i, n=3, back=30):
    """Lowest confirmed swing low among those usable at bar i (pivot j with j + n + 1 <= i) within `back` bars, else the low of the
    last 10 bars."""
    lo = S.l[max(0, i - back):i - n].min(initial=np.inf) if i - n > 0 else np.inf
    return lo if np.isfinite(lo) else S.l[max(0, i - 10):i + 1].min()


def mk(S, ctx, i_sig, stop, rr=2.0, tag=""):
    """Market entry at the open of bar i_sig + 1."""
    j = i_sig + 1
    if j >= len(S.c): return None
    e = S.o[j]
    if not (np.isfinite(stop) and e > stop): return None
    return Fill(S.t.view("i8")[j], ctx["bar_ns"], e, stop, e + rr * (e - stop), "market", tag=tag)


# ================================================================================================ Heikin Ashi (K线之下)
@rule("HA flip alone (3+ red then green no lower wick)")
def ha0(S, ctx):
    ho, hh, hl, hc = heikin_ashi(S); out = []; red = 0
    green_nowick = (hc > ho) & (np.abs(ho - hl) <= 1e-9 * np.maximum(1, np.abs(ho)))
    for i in range(30, len(S.c) - 1):
        if green_nowick[i] and red >= 3 and np.isfinite(S.atr[i]):
            f = mk(S, ctx, i, S.l[i - 5:i + 1].min() - BUF * S.atr[i])
            if f: out.append(f)
        red = red + 1 if hc[i] < ho[i] else 0
    return out


@rule("HA at support (rejected level, HA turns green)")
def ha1(S, ctx, n=3, look=300):
    ho, hh, hl, hc = heikin_ashi(S); A = bar_atr(S); _, pl = pivots(S.h, S.l, n); N = len(S.c); out = []
    green_nowick = (hc > ho) & (np.abs(ho - hl) <= 1e-9 * np.maximum(1, np.abs(ho))); red = hc < ho
    for j in np.flatnonzero(pl):
        c0 = j + n + 1
        if c0 >= N - 1 or not np.isfinite(A[c0]): continue
        L = S.l[j]; a = A[c0]; e_ = min(c0 + look, N - 1)
        brk = np.flatnonzero(S.c[c0:e_] < L); end = c0 + (brk[0] if len(brk) else e_ - c0)
        hmax = np.maximum.accumulate(S.h[j:end]) if end > j else np.array([])
        r = np.flatnonzero(hmax - L >= 2 * a)
        if not len(r): continue
        r0 = max(j + r[0] + 1, c0)
        t = np.flatnonzero(S.l[r0:end] <= L + 0.5 * a)
        if not len(t): continue
        touch = r0 + t[0]; w_end = min(touch + 21, end)
        reds = np.cumsum(red[touch:w_end]) > 0
        g = np.flatnonzero(green_nowick[touch + 1:w_end] & reds[:-1][:max(0, w_end - touch - 1)]) if w_end - touch > 1 else []
        if not len(g): continue
        i = touch + 1 + g[0]
        if np.isfinite(S.atr[i]):
            f = mk(S, ctx, i, min(L, S.l[touch:i + 1].min()) - BUF * S.atr[i])
            if f: out.append(f)
    return out


# ================================================================================================ fair value gaps (K线之下)
@rule("FVG inversion (bearish gap broken up, retest)")
def fvg_inv(S, ctx, life=100):
    N = len(S.c); out = []; ti = S.t.view("i8")
    for k in np.flatnonzero(S.h[2:] < S.l[:-2]) + 2:                  # bearish gap [h[k], l[k-2]]
        if k >= N - 2: continue
        bot, top = S.h[k], S.l[k - 2]
        b = np.flatnonzero(S.c[k + 1:k + 1 + life] > top)
        if not len(b): continue
        brk = k + 1 + b[0]; seg_c = S.c[brk + 1:brk + 1 + life]; seg_l = S.l[brk + 1:brk + 1 + life]
        dead = np.flatnonzero(seg_c < bot); tch = np.flatnonzero(seg_l <= top)
        if not len(tch) or (len(dead) and dead[0] < tch[0]): continue
        r_ = brk + 1 + tch[0]; atr = S.atr[r_]
        if not np.isfinite(atr): continue
        e = min(top, S.o[r_]); stop = bot - BUF * atr
        if e > stop: out.append(Fill(ti[r_], ctx["bar_ns"], e, stop, e + 2 * (e - stop), "limit"))
    return out


def up_legs(S, n=3):
    h, l = S.h, S.l; ph, pl = pivots(h, l, n); H = np.flatnonzero(ph); Lw = np.flatnonzero(pl); out = []
    for a_, j in zip(H[:-1], H[1:]):
        if not h[j] > h[a_]: continue
        lows = Lw[(Lw > a_) & (Lw < j)]
        if len(lows) == 0: continue
        s = lows[np.argmin(l[lows])]; out.append((s, j, j + n + 1))
    return out


@rule("FVG nearest the 61.8% retracement")
def fvg_fib(S, ctx, window=48):
    N = len(S.c); out = []; ti = S.t.view("i8")
    for s, j, conf in up_legs(S):
        if conf >= N: continue
        lo, hi = S.l[s], S.h[j]; f618 = hi - 0.618 * (hi - lo); best = None
        for k in range(s + 2, j + 1):
            if S.l[k] > S.h[k - 2] and S.l[k + 1:conf].min(initial=np.inf) > S.h[k - 2]:
                mid = (S.l[k] + S.h[k - 2]) / 2
                if best is None or abs(mid - f618) < abs(best[2] - f618): best = (S.h[k - 2], S.l[k], mid)
        if best is None: continue
        bot, top, _ = best
        for m in range(conf, min(conf + window, N)):
            if S.h[m] > hi or S.c[m] < lo: break
            if S.l[m] <= top:
                atr = S.atr[m]
                if np.isfinite(atr):
                    e = min(top, S.o[m]); stop = bot - BUF * atr
                    if e > stop: out.append(Fill(ti[m], ctx["bar_ns"], e, stop, e + 2 * (e - stop), "limit"))
                break
    return out


@rule("FVG + EMA200 trend + MACD cross on the retest")
def fvg_ema_macd(S, ctx, life=100):
    e200 = ema(S.c, 200); m, sg = macd(S.c); N = len(S.c); out = []
    xup = np.r_[False, (m[1:] > sg[1:]) & (m[:-1] <= sg[:-1])]
    for k in np.flatnonzero((S.l[2:] > S.h[:-2])) + 2:
        if k < 201 or k >= N - 2 or not S.c[k] > e200[k]: continue    # untested bullish gap in an uptrend
        bot, top = S.h[k - 2], S.l[k]
        seg_l, seg_c = S.l[k + 1:k + 1 + life], S.c[k + 1:k + 1 + life]
        tch = np.flatnonzero(seg_l <= top)
        if not len(tch): continue
        touch = k + 1 + tch[0]; w = slice(touch + 1, min(touch + 11, N - 1))
        dead = np.flatnonzero(S.c[w] < bot); cr = np.flatnonzero(xup[w])
        if not len(cr) or (len(dead) and dead[0] <= cr[0]) or S.c[touch] < bot: continue
        q = touch + 1 + cr[0]
        if np.isfinite(S.atr[q]):
            f = mk(S, ctx, q, min(bot, S.l[touch:q + 1].min()) - BUF * S.atr[q])
            if f: out.append(f)
    return out


# ================================================================================================ pullbacks (K线之下 回调交易法)
def _bull_reject(S, i):
    """Bullish engulfing of a bearish body, or a hammer (lower wick >= 2x body, close in the top third)."""
    body = abs(S.c[i] - S.o[i]); rng = S.h[i] - S.l[i]
    eng = S.c[i] > S.o[i] and S.c[i - 1] < S.o[i - 1] and S.c[i] >= S.o[i - 1] and S.o[i] <= S.c[i - 1]
    ham = rng > 0 and (min(S.o[i], S.c[i]) - S.l[i]) >= 2 * body and (S.c[i] - S.l[i]) >= 2 / 3 * rng
    return eng or ham


def _ma_pullbacks(S, ctx, confirm):
    s50 = sma(S.c, 50); r = rsi(S.c); A = bar_atr(S); N = len(S.c); out = []; i = 60
    while i < N - 1:
        up = S.c[i - 1] > s50[i - 1] and s50[i - 1] > s50[i - 11]
        if not (up and S.l[i] <= s50[i] and np.isfinite(A[i])): i += 1; continue
        touch = i; q = i
        while q < min(i + 10, N - 1):
            if S.c[q] < s50[q] - A[i]: break                            # a decisive close below the average: no pullback
            ok = _bull_reject(S, q) if confirm == "candle" else (r[q] > 50 and r[q - 1] <= 50)
            if ok and np.isfinite(S.atr[q]):
                f = mk(S, ctx, q, S.l[touch:q + 1].min() - BUF * S.atr[q])
                if f: out.append(f)
                break
            q += 1
        i = q + 1
        while i < N - 1 and S.l[i] <= s50[i]: i += 1                    # wait for price to leave the average again
    return out


@rule("Pullback to SMA50 + rejection candle")
def pb_ma_candle(S, ctx): return _ma_pullbacks(S, ctx, "candle")


@rule("Pullback to SMA50 + RSI crosses 50")
def pb_ma_rsi(S, ctx): return _ma_pullbacks(S, ctx, "rsi")


@rule("Broken resistance retest + RSI crosses 50")
def pb_flip_rsi(S, ctx, n=3):
    r = rsi(S.c); A = bar_atr(S); ph, _ = pivots(S.h, S.l, n); N = len(S.c); out = []; sh = None; used = set()
    for i in range(1, N - 1):
        j = i - 1 - n
        if j >= 0 and ph[j]: sh = j
        if sh is None or sh in used or not (S.c[i] > S.h[sh] and S.c[i - 1] <= S.h[sh]): continue
        used.add(sh); lvl = S.h[sh]; touch = None
        for q in range(i + 1, min(i + 31, N - 1)):
            if not np.isfinite(A[q]) or S.c[q] < lvl - A[q]: break
            if touch is None:
                if S.l[q] <= lvl + 0.1 * A[q]: touch = q
                continue
            if r[q] > 50 and r[q - 1] <= 50 and np.isfinite(S.atr[q]):
                f = mk(S, ctx, q, S.l[touch:q + 1].min() - BUF * S.atr[q])
                if f: out.append(f)
                break
    return out


# ================================================================================================ bottoms (K线之下 底部反转)
@rule("Williams VIX Fix + Stochastic cross")
def vixfix_stoch(S, ctx):
    g = vix_fix(S); k, d = stoch(S); N = len(S.c); out = []; last_green = -999; i = 30
    while i < N - 1:
        if g[i]: last_green = i
        if i - last_green <= 10 and k[i] > d[i] and k[i - 1] <= d[i - 1] and np.nanmin(k[max(0, i - 3):i + 1]) <= 20 and np.isfinite(S.atr[i]):
            f = mk(S, ctx, i, S.l[max(0, i - 10):i + 1].min() - BUF * S.atr[i])
            if f: out.append(f); last_green = -999
        i += 1
    return out


# ================================================================================================ liquidity (K线之下 流动性交易)
@rule("Equal lows above a demand zone, limit at zone top")
def liq_demand(S, ctx, n=3):
    obs = O.lifetimes(O.find_obs(S), O.find_obs(ctx["S_other"]), len(S.c)); ph, pl = pivots(S.h, S.l, n); out = []; ti = S.t.view("i8")
    for x in obs:
        lows = []; fill = None
        for q in range(x["valid"], x["end"]):
            j = q - 1 - n
            if j >= x["valid"] and pl[j] and S.l[j] > x["hi"]: lows.append(S.l[j])
            eq = any(abs(lows[a] - lows[b]) <= 0.1 * S.atr[q] for a in range(len(lows)) for b in range(a + 1, len(lows))) if np.isfinite(S.atr[q]) else False
            if S.l[q] <= x["hi"]:
                fill = q if eq else None; break
        if fill is None or not np.isfinite(S.atr[fill]): continue
        e = min(x["hi"], S.o[fill]); stop = x["lo"] - BUF * S.atr[fill]
        if e > stop: out.append(Fill(ti[fill], ctx["bar_ns"], e, stop, e + 2 * (e - stop), "limit"))
    return out


# ================================================================================================ moving-average cross (K线之下)
def _cross_trades(S):
    """Every SMA20/SMA50 cross: side, entry bar, stop (nearest swing beyond, else 10-bar extreme), 2R target, and the bar where the
    trade resolved on this timeframe (stop first). Used for the 'last two crosses won' filter."""
    f, s = sma(S.c, 20), sma(S.c, 50); N = len(S.c); tr = []
    for i in range(51, N - 1):
        up = f[i] > s[i] and f[i - 1] <= s[i - 1]; dn = f[i] < s[i] and f[i - 1] >= s[i - 1]
        if not (up or dn) or not np.isfinite(S.atr[i]): continue
        d = 1 if up else -1; e = S.o[i + 1]
        st = (S.l[max(0, i - 10):i + 1].min() - BUF * S.atr[i]) if d == 1 else (S.h[max(0, i - 10):i + 1].max() + BUF * S.atr[i])
        risk = d * (e - st)
        if risk <= 0: continue
        tg = e + d * 2 * risk; res = None; win = None
        for q in range(i + 1, N):
            hit_s = S.l[q] <= st if d == 1 else S.h[q] >= st; hit_t = S.h[q] >= tg if d == 1 else S.l[q] <= tg
            if hit_s: res, win = q, False; break
            if hit_t: res, win = q, True; break
        tr.append((i, d, e, st, tg, res, win))
    return tr


@rule("SMA20/50 cross (every signal)")
def ma_cross(S, ctx):
    return [Fill(S.t.view("i8")[i + 1], ctx["bar_ns"], e, st, tg, "market") for i, d, e, st, tg, res, win in _cross_trades(S) if d == 1]


@rule("SMA20/50 cross, only after two winning crosses")
def ma_cross_filtered(S, ctx):
    tr = _cross_trades(S); out = []
    for k, (i, d, e, st, tg, res, win) in enumerate(tr):
        if d != 1 or k < 2: continue
        prev = tr[k - 2:k]
        if all(p[5] is not None and p[5] < i and p[6] for p in prev):    # both resolved before this cross, both winners
            out.append(Fill(S.t.view("i8")[i + 1], ctx["bar_ns"], e, st, tg, "market"))
    return out


# ================================================================================================ SB structure (熊猫教练, second breakout)
def _signal_bar(S, i):
    rng = S.h[i] - S.l[i]
    if rng <= 0: return False
    strong = S.c[i] > S.o[i] and (S.c[i] - S.l[i]) >= 2 / 3 * rng
    pin = (min(S.o[i], S.c[i]) - S.l[i]) >= 2 * abs(S.c[i] - S.o[i]) and (S.c[i] - S.l[i]) >= 0.5 * rng
    return strong or pin


@rule("SB second breakout (small double bottom, buy stop over H1)")
def sb_double_bottom(S, ctx):
    A = bar_atr(S); e20 = ema(S.c, 20); N = len(S.c); out = []; ti = S.t.view("i8"); i = 25
    while i < N - 3:
        # 1) after a decline: a new 10-bar low, a bullish signal bar, below the 20 EMA
        if not (np.isfinite(A[i]) and S.l[i] <= S.l[i - 10:i].min() and S.c[i] < e20[i] and _signal_bar(S, i)): i += 1; continue
        low1 = S.l[i]; h1 = None; sig2 = None; q = i + 1
        while q < min(i + 30, N - 2):
            if S.l[q] < low1 - 0.5 * A[i]: break                         # fell well through the first low: no double bottom
            if h1 is None or S.h[q] > h1: h1 = S.h[q] if sig2 is None else h1
            if q >= i + 2 and sig2 is None and abs(S.l[q] - low1) <= 0.25 * A[i] and _signal_bar(S, q) and h1 is not None and h1 > S.h[q] and h1 - low1 >= 0.5 * A[i]:
                sig2 = q
            elif sig2 is not None:
                if S.h[q] >= h1 + 1e-12 and np.isfinite(S.atr[q]):          # 4) second breakout through H1: buy stop at H1
                    stop = min(low1, S.l[i:q + 1].min()) - BUF * S.atr[q]; e = max(h1, S.o[q])
                    if e > stop: out.append(Fill(ti[q], ctx["bar_ns"], e, stop, e + 2 * (e - stop), "stop"))
                    break
                if q - sig2 > 10: break
            q += 1
        i = q + 1
    return out


# ================================================================================================ manipulation + inversion gap (K线之下 超短线)
@rule("Sweep of an obvious low + inversion FVG close")
def sweep_ifvg(S, ctx, n=3, look=300):
    A = bar_atr(S); _, pl = pivots(S.h, S.l, n); N = len(S.c); out = []; used = set()
    bear_gap = np.r_[False, False, S.h[2:] < S.l[:-2]]
    for j in np.flatnonzero(pl):
        c0 = j + n + 1
        if c0 >= N - 1 or not np.isfinite(A[c0]): continue
        L = S.l[j]; a = A[c0]; e_ = min(c0 + look, N - 1)
        hmax = np.maximum.accumulate(S.h[j:e_]); r = np.flatnonzero(hmax - L >= 2 * a)
        if not len(r): continue
        r0 = max(j + r[0] + 1, c0)
        sw = np.flatnonzero(S.l[r0:e_] < L)
        if not len(sw): continue
        i = r0 + sw[0]
        if S.c[r0:i].min(initial=np.inf) < L: continue                 # it closed below before: not an intact level
        gaps = [k for k in range(max(2, i - 10), min(i + 6, N)) if bear_gap[k]]
        for q in range(i, min(i + 11, N - 1)):
            hit = [k for k in gaps if k <= q and S.c[q] > S.l[k - 2] and S.c[q - 1] <= S.l[k - 2]]
            if hit and np.isfinite(S.atr[q]):
                k = hit[-1]
                if (q, k) not in used:
                    used.add((q, k)); f = mk(S, ctx, q, S.h[k] - BUF * S.atr[q])
                    if f: out.append(f)
                break
    return out


# ================================================================================================ trendline + stochastic (K线之下)
@rule("Trendline touch + Stochastic(5,3,3) cross from oversold")
def tl_stoch(S, ctx, n=3, life=100):
    A = bar_atr(S); _, pl = pivots(S.h, S.l, n); N = len(S.c); out = []
    raw = 100 * (S.c - pd.Series(S.l).rolling(5).min().values) / np.maximum(pd.Series(S.h).rolling(5).max().values - pd.Series(S.l).rolling(5).min().values, 1e-12)
    k = pd.Series(raw).rolling(3).mean().values; d = pd.Series(k).rolling(3).mean().values
    xup = np.r_[False, (k[1:] > d[1:]) & (k[:-1] <= d[:-1])]
    lows = np.flatnonzero(pl)
    for a_, b_ in zip(lows[:-1], lows[1:]):
        if not S.l[b_] > S.l[a_]: continue
        slope = (S.l[b_] - S.l[a_]) / (b_ - a_); start = b_ + n + 1
        for i in range(start, min(start + life, N - 1)):
            line = S.l[b_] + slope * (i - b_)
            if not np.isfinite(A[i]) or S.c[i] < line - 0.5 * A[i]: break      # the line broke
            near = S.l[i] <= line + 0.25 * A[i]
            if near and xup[i] and np.nanmin(k[max(0, i - 3):i + 1]) <= 20 and np.isfinite(S.atr[i]):
                f = mk(S, ctx, i, min(S.l[max(0, i - 5):i + 1].min(), line) - BUF * S.atr[i])
                if f: out.append(f)
                break
    return out
