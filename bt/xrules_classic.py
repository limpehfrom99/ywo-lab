"""Classic book rules from the nightly loop, ported unchanged to the cross-asset harness so they run on every export symbol and
timeframe (Shen's standing instruction; log #71). LONG in the frame, mirrored for shorts by the harness.
  Holy Grail (Raschke; log #54 rules): ADX(14) > 30 and rising on the previous bar, +DI > -DI; the bar's low touches the 20-EMA after
  the previous low stayed above it (first pullback) -> buy stop at that bar's high, valid 3 bars and lowered to each new bar's high;
  stop = the lowest low from the setup bar to the bar before the fill; target = the highest high of the 20 bars before the setup.
  Only if the target is above the entry. Fill bar: the harness counts the stop, not the target, inside the fill bar."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/bt")
from xgrid import Fill

REGISTRY = {}


def rule(name):
    def deco(fn): REGISTRY[name] = fn; return fn
    return deco


def adx(h, l, c, n=14):
    up = np.diff(h, prepend=h[0]); dn = -np.diff(l, prepend=l[0])
    pdm = np.where((up > dn) & (up > 0), up, 0.0); mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    pc = np.r_[c[0], c[:-1]]; tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    w = lambda x: pd.Series(x).ewm(alpha=1 / n, adjust=False).mean().values
    atr = w(tr)
    with np.errstate(divide="ignore", invalid="ignore"):
        pdi = 100 * w(pdm) / atr; mdi = 100 * w(mdm) / atr
        dx = 100 * np.abs(pdi - mdi) / (pdi + mdi)
    return w(np.nan_to_num(dx)), pdi, mdi


@rule("Holy Grail (ADX>30 rising, first pullback to EMA20, buy stop, 20-bar high target)")
def holy_grail(S, ctx):
    h, l, c, o = S.h, S.l, S.c, S.o; N = len(c); ti = S.t.view("i8"); bar = ctx["bar_ns"]
    E = pd.Series(c).ewm(span=20, adjust=False).mean().values
    A, PDI, MDI = adx(h, l, c)
    out = []; t = 25
    while t < N - 1:
        if A[t - 1] > 30 and A[t - 1] > A[t - 2] and PDI[t - 1] > MDI[t - 1] and l[t] <= E[t] and l[t - 1] > E[t - 1]:
            tgt = h[t - 20:t].max(); lvl = h[t]; ext = l[t]; fill = None
            for u in range(t + 1, min(t + 4, N)):
                if h[u] >= lvl:
                    fill = (u, max(lvl, o[u])); break
                ext = min(ext, l[u]); lvl = min(lvl, h[u])
            if fill is not None:
                u, e = fill
                if tgt > e and e > ext: out.append(Fill(ti[u], bar, e, ext, tgt, "stop"))
                t = u + 1; continue
        t += 1
    return out
