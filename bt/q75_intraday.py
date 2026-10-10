"""Log #75 (pre-registered 10 Oct 2026 08:55 MYT): backlog #30 Dual Thrust and #31 R-Breaker on every symbol, session and bar size.

Engine + runner. Rules are fixed exactly as written in research/log.md #75 / the task brief; nothing here is tuned on results.

Data: the FTMO export via quant/universe.py; day x bar matrices via quant/sessions.Session (exchange sessions of
U.sessions_of(sym)); plus gold on the server day (00:00-23:55 server = 17:00-16:55 New York, built on a copy of the frame whose
index is shifted to server time, as in quant/mcpt_wvb.py) and BTCUSD on the UTC day (00:00-24:00 UTC).
Bar sizes: the finest file (M5; forex only has M15) and coarser bars made by joining consecutive columns from the session open
(M15 / M30 / H1). When the session length is not a multiple of the bar, the last partial bar is dropped and positions exit at the
close of the last full bar. Daily levels (Dual Thrust range, R-Breaker pivots) always come from the full session.

Fills (both rules): stop entries fill at the level, or at the bar's open if it opened beyond it; exits at a level fill at the
level, or at the bar's open if it gapped through; flat at the session close. Costs per trade = spread x 1.2 at the entry bar (round
trip, price units) + commission x (|entry| + |exit|). No swap (intraday).

#30 Dual Thrust (M. Chalek): N = 4 previous sessions: HH, LC, HC, LL; Range = max(HH - LC, HC - LL); BT = open + k Range,
  ST = open - k Range, k in (0.3, 0.5, 0.7). Stop-and-reverse inside the session: the first trigger touched opens the position;
  touching the opposite trigger closes it and opens the reverse. A bar that touches both triggers: the open position (or, when flat,
  the first position: the one whose trigger the bar opened beyond, else a long) is closed at the opposite trigger and NO reverse is
  opened on that bar. R = (P/L - costs) / (BT - ST).
#31 R-Breaker: from yesterday's session H, L, C: P = (H+L+C)/3; bB = H + 2(P - L) (break buy), sS = P + (H - L) (sell setup),
  sE = 2P - L (sell enter), bE = 2P - H (buy enter), bS = P - (H - L) (buy setup), sB = L - 2(H - P) (break sell).
  Trend: touch bB -> long, stop P; touch sB -> short, stop P. Reversal: once today's high > sS (on an earlier bar), a bar trading at
  or below sE -> short, stop = today's high so far (through the previous bar, or the entry bar's open if higher); once today's low
  < bS, a bar trading at or above bE -> long, stop = today's low so far. At most one long and one short per session; one position
  at a time; a reversal signal while in the opposite position closes it at the reversal level and opens the new one (SAR); flat at
  the close. R = (P/L - costs) / |entry - initial stop|.
  Same-bar conventions (intrabar order unknown -> the worse outcome): the stop is checked in the entry bar (a reversal trade's
  extreme-based stop counts only if the bar trades beyond it); after a stop-out no new entry on that bar; when both directions
  trigger on one bar while flat and the open does not tell which came first, one losing trade is booked (the side whose
  entry-then-first-adverse-exit is worse), that side counts as used and nothing else happens on that bar.
Baseline (coin flip): the opposite direction at the same entry moment and price, protective stop at the same distance on the other
side, out at the same exit moment (the real trade's exit price) unless its own stop is touched first (the entry and exit bars
count, worst case). coin = (R + R_opposite) / 2 = the expected R of a fair coin choosing the side.

python3 bt/q75_intraday.py run [--symbols A,B] [--ideas dt,rb]   -> results/q75_intraday_cells.csv (+ trades of primary cells)
python3 bt/q75_intraday.py summary                                -> results/q75_intraday_pooled.csv, printed tables
"""
import os, sys, time, copy, argparse, warnings
import numpy as np, pandas as pd
from numba import njit

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "quant")); sys.path.insert(0, HERE)
warnings.filterwarnings("ignore", category=RuntimeWarning)
import universe as U  # noqa: E402
from sessions import Session  # noqa: E402
from run_battery import intraday_frame  # noqa: E402

U.SESSIONS["server_day"] = ("UTC", "00:00", "23:55")     # on a frame whose index is server time (New York + 7 h)
U.SESSIONS["utc_day"] = ("UTC", "00:00", "24:00")

RES = os.path.join(ROOT, "results")
CELLS = os.path.join(RES, "q75_intraday_cells.csv")
PRIMARY_TRADES = os.path.join(RES, "q75_intraday_trades_primary.csv")
POOLED = os.path.join(RES, "q75_intraday_pooled.csv")
CUT = pd.Timestamp("2024-01-01")
SPM = 1.2
KS = (0.3, 0.5, 0.7)
BATCH2 = {"AMD", "AVGO", "BA", "CVX", "DIS", "INTC", "JNJ", "JPM", "KO", "MSTR", "NKE", "PLTR", "QCOM", "XOM"}
PRIMARY = {("dt", "XAUUSD", "server_day", 5, 0.5), ("dt", "US100.cash", "us_cash", 5, 0.5), ("dt", "US500.cash", "us_cash", 5, 0.5),
           ("dt", "BTCUSD", "utc_day", 5, 0.5),
           ("rb", "XAUUSD", "server_day", 5, 0.0), ("rb", "US100.cash", "us_cash", 5, 0.0), ("rb", "US500.cash", "us_cash", 5, 0.0)}
TF = {1: "M1", 5: "M5", 15: "M15", 30: "M30", 60: "H1"}


# ------------------------------------------------------------------------------------------------------------- sessions
def server_frame(d):
    s = d.copy()
    s.index = (d.index.tz_convert("America/New_York").tz_localize(None) + pd.Timedelta(hours=7)).tz_localize("UTC")
    return s[~s.index.duplicated()].sort_index()


def symbol_sessions(sym, cat):
    """[(session name, Session at the finest bar)], finest timeframe label."""
    d, tf = intraday_frame(sym, cat)
    if d is None or len(d) < 2000: return [], tf
    out = []
    for sess in U.sessions_of(sym):
        try: S = Session(d, sess)
        except Exception as e: print(f"  {sym} {sess}: {e!r}", flush=True); continue
        if len(S.days) >= 150: out.append((sess, S))
    if sym == "XAUUSD":
        S = Session(server_frame(d), "server_day", min_cov=0.7, edge_min=70)   # gold pauses 00:00-01:00 server
        out.append(("server_day", S))
    if sym == "BTCUSD":
        S = Session(d, "utc_day")
        if len(S.days) >= 150: out.append(("utc_day", S))
    return out, tf


def coarsen(S, g):
    """Bars of g consecutive columns from the session open; the last partial bar is dropped. Daily fields stay those of S."""
    if g == 1: return S
    n, K = S.O.shape; Kc = K // g; cut = Kc * g
    X = copy.copy(S)
    X.O = np.ascontiguousarray(S.O[:, 0:cut:g])
    X.H = S.H[:, :cut].reshape(n, Kc, g).max(2)
    X.L = S.L[:, :cut].reshape(n, Kc, g).min(2)
    X.C = np.ascontiguousarray(S.C[:, g - 1:cut:g])
    X.SP = S.SP[:, :cut].reshape(n, Kc, g).mean(2)          # typical spread inside the joined bar
    X.V = S.V[:, :cut].reshape(n, Kc, g).sum(2)
    X.K, X.bar, X.first = Kc, S.bar * g, (S.first // g).astype(np.int64)
    X.truncated = cut < K
    return X


def bar_sizes(base):
    return sorted({b for b in (base, 15, 30, 60) if b >= base and b % base == 0})


# -------------------------------------------------------------------------------------------------------------- kernels
@njit(cache=False)
def dt_kernel(O, H, L, C, first, BT, ST, cap):
    """Dual Thrust SAR. Returns trade arrays (day, entry col, exit col, dir, entry px, exit px, both-touch flag) and count."""
    n, K = O.shape
    t_i = np.empty(cap, np.int64); t_e = np.empty(cap, np.int64); t_x = np.empty(cap, np.int64)
    t_d = np.empty(cap, np.int64); t_ep = np.empty(cap); t_xp = np.empty(cap); t_b = np.zeros(cap, np.int64)
    m = 0
    for i in range(n):
        bt = BT[i]; st = ST[i]
        if not (np.isfinite(bt) and np.isfinite(st)) or bt <= st: continue
        pos = 0; ep = 0.0; ec = 0
        for j in range(first[i], K):
            o = O[i, j]; h = H[i, j]; l = L[i, j]
            up = h >= bt; dn = l <= st
            if pos == 0:
                if up and dn:                      # first position stopped at the opposite trigger, no reverse
                    if o <= st:
                        dd = -1; e = o; x = bt
                    else:
                        dd = 1; e = max(bt, o); x = st
                    if m >= cap: return t_i, t_e, t_x, t_d, t_ep, t_xp, t_b, -1
                    t_i[m] = i; t_e[m] = j; t_x[m] = j; t_d[m] = dd; t_ep[m] = e; t_xp[m] = x; t_b[m] = 1; m += 1
                elif up:
                    pos = 1; ep = max(bt, o); ec = j
                elif dn:
                    pos = -1; ep = min(st, o); ec = j
            elif pos == 1:
                if dn:
                    x = min(st, o)
                    if m >= cap: return t_i, t_e, t_x, t_d, t_ep, t_xp, t_b, -1
                    t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = 1; t_ep[m] = ep; t_xp[m] = x; t_b[m] = 1 if up else 0; m += 1
                    if up: pos = 0
                    else:
                        pos = -1; ep = x; ec = j
            else:
                if up:
                    x = max(bt, o)
                    if m >= cap: return t_i, t_e, t_x, t_d, t_ep, t_xp, t_b, -1
                    t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = -1; t_ep[m] = ep; t_xp[m] = x; t_b[m] = 1 if dn else 0; m += 1
                    if dn: pos = 0
                    else:
                        pos = 1; ep = x; ec = j
        if pos != 0:
            if m >= cap: return t_i, t_e, t_x, t_d, t_ep, t_xp, t_b, -1
            t_i[m] = i; t_e[m] = ec; t_x[m] = K - 1; t_d[m] = pos; t_ep[m] = ep; t_xp[m] = C[i, K - 1]; t_b[m] = 0; m += 1
    return t_i, t_e, t_x, t_d, t_ep, t_xp, t_b, m


@njit(cache=False)
def rb_kernel(O, H, L, C, first, PH, PL, PC):
    """R-Breaker. Returns (day, entry col, exit col, dir, entry px, exit px, initial stop, kind) and count.
    kind: 0 trend, 1 reversal, 2 same-bar two-sided loss (ambiguous order)."""
    n, K = O.shape
    cap = 2 * n + 2
    t_i = np.empty(cap, np.int64); t_e = np.empty(cap, np.int64); t_x = np.empty(cap, np.int64); t_d = np.empty(cap, np.int64)
    t_ep = np.empty(cap); t_xp = np.empty(cap); t_st = np.empty(cap); t_k = np.empty(cap, np.int64)
    m = 0
    for i in range(n):
        h0 = PH[i]; l0 = PL[i]; c0 = PC[i]
        if not (np.isfinite(h0) and np.isfinite(l0) and np.isfinite(c0)) or h0 <= l0: continue
        P = (h0 + l0 + c0) / 3.0
        bB = h0 + 2.0 * (P - l0); sS = P + (h0 - l0); sE = 2.0 * P - l0
        bE = 2.0 * P - h0; bS = P - (h0 - l0); sB = l0 - 2.0 * (h0 - P)
        pos = 0; ep = 0.0; ec = 0; stp = 0.0; kd = 0
        lu = False; su = False; s_arm = False; l_arm = False
        hs = -1e300; ls = 1e300
        for j in range(first[i], K):
            o = O[i, j]; h = H[i, j]; l = L[i, j]
            if pos == 0:
                has_l = False; has_s = False; tl = 0.0; ts = 0.0; kl = 0; ks = 0
                if not lu:
                    if l_arm:
                        tl = bE; kl = 1
                    else:
                        tl = bB; kl = 0
                    has_l = h >= tl
                if not su:
                    if s_arm:
                        ts = sE; ks = 1
                    else:
                        ts = sB; ks = 0
                    has_s = l <= ts
                fdir = 0          # 1 long first, -1 short first, 2 ambiguous, 0 nothing
                if has_l and has_s:
                    ol = o >= tl; osh = o <= ts            # trigger already satisfied at the bar's open
                    if ol and not osh: fdir = 1
                    elif osh and not ol: fdir = -1
                    elif ol and osh: fdir = 1              # both at the open (only when bE <= o <= sE): long first, then SAR
                    else: fdir = 2                         # neither at the open: order unknown
                elif has_l: fdir = 1
                elif has_s: fdir = -1
                if fdir == 2:
                    # long first: in at tl, out at its first adverse level going down (SAR level sE if the short is a
                    # reversal, else its stop; never below ts); short first: mirror. Book the worse one; no reverse.
                    stl = P if kl == 0 else min(ls, o)
                    xl = sE if ks == 1 else max(stl, ts)
                    rl = (xl - tl) / (tl - stl) if tl > stl else -1e9
                    sts = P if ks == 0 else max(hs, o)
                    xs = bE if kl == 1 else min(sts, tl)
                    rs = (ts - xs) / (sts - ts) if sts > ts else -1e9
                    if rl <= rs:
                        t_i[m] = i; t_e[m] = j; t_x[m] = j; t_d[m] = 1; t_ep[m] = tl; t_xp[m] = xl; t_st[m] = stl; t_k[m] = 2; m += 1
                        lu = True
                    else:
                        t_i[m] = i; t_e[m] = j; t_x[m] = j; t_d[m] = -1; t_ep[m] = ts; t_xp[m] = xs; t_st[m] = sts; t_k[m] = 2; m += 1
                        su = True
                elif fdir == 1:
                    ep = max(tl, o); ec = j; pos = 1; lu = True; kd = kl
                    stp = P if kl == 0 else min(ls, o)
                    at_open = o >= tl
                    # rest of the entry bar
                    if at_open and has_s and ks == 1:              # opened beyond the long trigger, then down to sE: SAR
                        x = min(sE, o)
                        t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = 1; t_ep[m] = ep; t_xp[m] = x; t_st[m] = stp; t_k[m] = kd; m += 1
                        pos = -1; ep = x; ec = j; su = True; kd = 1; stp = max(hs, o)
                        if h > stp:
                            t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = -1; t_ep[m] = ep; t_xp[m] = stp; t_st[m] = stp; t_k[m] = kd; m += 1
                            pos = 0
                    else:
                        hit = (l <= stp) if kd == 0 else (l < stp)
                        if hit:
                            t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = 1; t_ep[m] = ep; t_xp[m] = stp; t_st[m] = stp; t_k[m] = kd; m += 1
                            pos = 0
                elif fdir == -1:
                    ep = min(ts, o); ec = j; pos = -1; su = True; kd = ks
                    stp = P if ks == 0 else max(hs, o)
                    at_open = o <= ts
                    if at_open and has_l and kl == 1:
                        x = max(bE, o)
                        t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = -1; t_ep[m] = ep; t_xp[m] = x; t_st[m] = stp; t_k[m] = kd; m += 1
                        pos = 1; ep = x; ec = j; lu = True; kd = 1; stp = min(ls, o)
                        if l < stp:
                            t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = 1; t_ep[m] = ep; t_xp[m] = stp; t_st[m] = stp; t_k[m] = kd; m += 1
                            pos = 0
                    else:
                        hit = (h >= stp) if kd == 0 else (h > stp)
                        if hit:
                            t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = -1; t_ep[m] = ep; t_xp[m] = stp; t_st[m] = stp; t_k[m] = kd; m += 1
                            pos = 0
            elif pos == 1:
                if s_arm and (not su) and l <= sE:                  # reversal short while long: SAR at sE
                    x = min(sE, o)
                    t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = 1; t_ep[m] = ep; t_xp[m] = x; t_st[m] = stp; t_k[m] = kd; m += 1
                    pos = -1; ep = x; ec = j; su = True; kd = 1; stp = max(hs, o)
                    if h > stp:
                        t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = -1; t_ep[m] = ep; t_xp[m] = stp; t_st[m] = stp; t_k[m] = kd; m += 1
                        pos = 0
                elif l <= stp:
                    t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = 1; t_ep[m] = ep; t_xp[m] = min(stp, o); t_st[m] = stp; t_k[m] = kd; m += 1
                    pos = 0
            else:
                if l_arm and (not lu) and h >= bE:                  # reversal long while short: SAR at bE
                    x = max(bE, o)
                    t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = -1; t_ep[m] = ep; t_xp[m] = x; t_st[m] = stp; t_k[m] = kd; m += 1
                    pos = 1; ep = x; ec = j; lu = True; kd = 1; stp = min(ls, o)
                    if l < stp:
                        t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = 1; t_ep[m] = ep; t_xp[m] = stp; t_st[m] = stp; t_k[m] = kd; m += 1
                        pos = 0
                elif h >= stp:
                    t_i[m] = i; t_e[m] = ec; t_x[m] = j; t_d[m] = -1; t_ep[m] = ep; t_xp[m] = max(stp, o); t_st[m] = stp; t_k[m] = kd; m += 1
                    pos = 0
            if h > hs: hs = h
            if l < ls: ls = l
            if hs > sS: s_arm = True
            if ls < bS: l_arm = True
        if pos != 0:
            t_i[m] = i; t_e[m] = ec; t_x[m] = K - 1; t_d[m] = pos; t_ep[m] = ep; t_xp[m] = C[i, K - 1]; t_st[m] = stp; t_k[m] = kd; m += 1
    return t_i[:m], t_e[:m], t_x[:m], t_d[:m], t_ep[:m], t_xp[:m], t_st[:m], t_k[:m]


@njit(cache=False)
def opp_kernel(O, H, L, t_i, t_e, t_x, t_d, t_ep, t_xp, dist):
    """Exit price of the opposite-direction trade: same entry, stop at the same distance on the other side, out at the real
    exit unless its stop is touched first (entry and exit bars included = worst case)."""
    m = len(t_i); X = np.empty(m)
    for t in range(m):
        i = t_i[t]; od = -t_d[t]; e = t_ep[t]; st = e - od * dist[t]
        X[t] = t_xp[t]
        for j in range(t_e[t], t_x[t] + 1):
            if od == 1:
                if L[i, j] <= st:
                    X[t] = st if j == t_e[t] else min(st, O[i, j]); break
            else:
                if H[i, j] >= st:
                    X[t] = st if j == t_e[t] else max(st, O[i, j]); break
    return X


# ---------------------------------------------------------------------------------------------------------------- rules
def dt_levels(S, k, N=4):
    """Dual Thrust triggers from the previous N sessions (rows) of the full session; NaN when a gap > 5 days sits inside."""
    hi = pd.Series(S.high); lo = pd.Series(S.low); cl = pd.Series(S.close)
    HH = hi.rolling(N).max().shift(1).values; LL = lo.rolling(N).min().shift(1).values
    HC = cl.rolling(N).max().shift(1).values; LC = cl.rolling(N).min().shift(1).values
    rng = np.maximum(HH - LC, HC - LL)
    okgap = pd.Series(np.isfinite(S.prev_close).astype(float)).rolling(N).min().values == 1   # rows i-N+1..i chained without long gaps
    rng = np.where(okgap & (rng > 0), rng, np.nan)
    return S.open + k * rng, S.open - k * rng, rng


def rb_levels(S):
    ok = np.isfinite(S.prev_close)
    PH = np.where(ok, np.r_[np.nan, S.high[:-1]], np.nan); PL = np.where(ok, np.r_[np.nan, S.low[:-1]], np.nan)
    return PH, PL, np.where(ok, S.prev_close, np.nan)


def run_dt(S, X, k, comm):
    """S: full session (levels), X: the (possibly coarse) bar matrix. -> trades DataFrame."""
    BT, ST, rng = dt_levels(S, k)
    first = np.asarray(X.first, np.int64)
    cap = max(16 * len(S.days), 1000)
    t_i, t_e, t_x, t_d, t_ep, t_xp, t_b, m = dt_kernel(X.O, X.H, X.L, X.C, first, BT, ST, cap)
    if m < 0: raise RuntimeError("dt_kernel capacity exceeded")
    t_i, t_e, t_x, t_d, t_ep, t_xp, t_b = (a[:m] for a in (t_i, t_e, t_x, t_d, t_ep, t_xp, t_b))
    den = (BT - ST)[t_i]
    opp_trig = np.where(t_d == 1, ST[t_i], BT[t_i])
    dist = np.abs(t_ep - opp_trig)
    return _trades(S, X, t_i, t_e, t_x, t_d, t_ep, t_xp, den, dist, comm, extra=dict(both=t_b))


def run_rb(S, X, comm):
    PH, PL, PC = rb_levels(S)
    t_i, t_e, t_x, t_d, t_ep, t_xp, t_st, t_k = rb_kernel(X.O, X.H, X.L, X.C, np.asarray(X.first, np.int64), PH, PL, PC)
    dist = np.abs(t_ep - t_st)
    return _trades(S, X, t_i, t_e, t_x, t_d, t_ep, t_xp, dist, dist, comm, extra=dict(kind=t_k))


def _trades(S, X, t_i, t_e, t_x, t_d, t_ep, t_xp, den, dist, comm, extra):
    cost = X.SP[t_i, t_e] * SPM + comm * (np.abs(t_ep) + np.abs(t_xp))
    gross = t_d * (t_xp - t_ep)
    with np.errstate(invalid="ignore", divide="ignore"):
        R = (gross - cost) / den
        Xo = opp_kernel(X.O, X.H, X.L, t_i, t_e, t_x, t_d, t_ep, t_xp, dist)
        cost_o = X.SP[t_i, t_e] * SPM + comm * (np.abs(t_ep) + np.abs(Xo))
        Ro = (-t_d * (Xo - t_ep) - cost_o) / den
    T = pd.DataFrame(dict(day=S.days[t_i], i=t_i, e_col=t_e, x_col=t_x, d=t_d, e_px=t_ep, x_px=t_xp, den=den, R=R,
                          R_gross=gross / den, R_opp=Ro, cost_R=cost / den, **extra))
    T = T[np.isfinite(T.R) & (T.den > 0)]
    return T


# ---------------------------------------------------------------------------------------------------------------- stats
def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 3 or x.std() == 0: return np.nan
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x))


def cell_stats(T, n_days):
    """One row of statistics for a cell (T = trades with day, R, R_opp)."""
    R = T.R.values; day = pd.DatetimeIndex(T.day)
    out = dict(sessions=n_days, n=len(R))
    if len(R) == 0: return out
    is_ = day < CUT
    yr = pd.DataFrame(dict(R=R, y=day.year)).groupby("y").R.agg(["mean", "size"])
    yr10 = yr[yr["size"] >= 10]
    coin = 0.5 * (R + T.R_opp.values)
    out.update(mean=R.mean(), t=tstat(R), win=(R > 0).mean(), gross=T.R_gross.mean(), costR=T.cost_R.mean(),
               n_is=int(is_.sum()), mean_is=R[is_].mean() if is_.any() else np.nan,
               n_oos=int((~is_).sum()), mean_oos=R[~is_].mean() if (~is_).any() else np.nan,
               worst_year=int(yr10["mean"].idxmin()) if len(yr10) else np.nan, worst_mean=yr10["mean"].min() if len(yr10) else np.nan,
               pos_years=(yr10["mean"] > 0).mean() if len(yr10) else np.nan,
               coin=coin.mean(), opp=T.R_opp.mean(),
               by_year=" ".join(f"{y % 100:02d}:{v:+.3f}({c})" for y, (v, c) in yr.iterrows()),
               first=day.min().date(), last=day.max().date(), per_day=len(R) / max(n_days, 1),
               sumR=R.sum(), sumR2=(R ** 2).sum(), sumR_is=R[is_].sum(), sumR2_is=(R[is_] ** 2).sum(),
               sumR_oos=R[~is_].sum(), sumR2_oos=(R[~is_] ** 2).sum(), sum_coin=coin.sum())
    out["beats"] = bool(out["mean"] > out["coin"])
    out["passes"] = bool(out["n"] >= 200 and out["t"] >= 2 and out["mean"] >= 0.05 and out["mean_is"] > 0 and out["mean_oos"] > 0
                         and (not np.isfinite(out["worst_mean"]) or out["worst_mean"] >= -0.3) and out["beats"])
    if "both" in T: out["share_both"] = T.both.mean()
    if "kind" in T:
        for k, nm in ((0, "trend"), (1, "rev"), (2, "amb")):
            x = T.R[T.kind == k]; out[f"n_{nm}"] = len(x); out[f"mean_{nm}"] = x.mean() if len(x) else np.nan
    return out


# ---------------------------------------------------------------------------------------------------------------- runner
def impute_stock_spread(S):
    """Cost-sensitivity only (not the pre-registered run): FTMO's export has spread 0 on stock CFD bars for the second batch
    2021-25, NVDA 2021-23 and MCD 2024-25; fill zero spreads with 0.02 (before 2025) / 0.10 (from 2025), the typical
    first-batch stock spreads in price units."""
    yr = pd.DatetimeIndex(S.days).year.values[:, None]
    S.SP = np.where(S.SP > 0, S.SP, np.where(yr < 2025, 0.02, 0.10))
    return S


def run_symbol(sym, cat, ideas=("dt", "rb"), impute=False):
    rows, prim = [], []
    t0 = time.time()
    sessions, tf = symbol_sessions(sym, cat)
    if impute and U.group_of(sym) == "stock": sessions = [(ss, impute_stock_spread(S)) for ss, S in sessions]
    comm = U.commission_of(sym); grp = U.group_of(sym)
    for sess, S in sessions:
        for b in bar_sizes(S.bar):
            X = coarsen(S, b // S.bar)
            jobs = []
            if "dt" in ideas: jobs += [("dt", k) for k in KS]
            if "rb" in ideas: jobs += [("rb", 0.0)]
            for idea, k in jobs:
                T = run_dt(S, X, k, comm) if idea == "dt" else run_rb(S, X, comm)
                st = cell_stats(T, len(S.days))
                key = (idea, sym, sess, b, k)
                st.update(idea=idea, symbol=sym, group=grp, batch2=sym in BATCH2, session=sess, bar=b, tf=TF.get(b, f"{b}m"),
                          variant=f"k={k}" if idea == "dt" else "RB", k=k, primary=key in PRIMARY,
                          truncated=bool(getattr(X, "truncated", False)), base_tf=TF.get(S.bar))
                rows.append(st)
                if key in PRIMARY:
                    prim.append(T.assign(idea=idea, symbol=sym, session=sess, bar=b, k=k))
    print(f"{sym}: {len(sessions)} sessions ({', '.join(f'{s}:{len(S.days)}' for s, S in sessions)}), base {tf}, "
          f"{len(rows)} cells, {time.time() - t0:.0f}s", flush=True)
    return rows, prim


LEAD = ["idea", "symbol", "group", "batch2", "session", "tf", "bar", "variant", "k", "primary", "truncated", "base_tf", "sessions",
        "n", "per_day", "mean", "t", "win", "gross", "costR", "n_is", "mean_is", "n_oos", "mean_oos", "worst_year", "worst_mean",
        "pos_years", "coin", "opp", "beats", "passes", "by_year", "first", "last", "share_both", "n_trend", "mean_trend", "n_rev",
        "mean_rev", "n_amb", "mean_amb", "sumR", "sumR2", "sumR_is", "sumR2_is", "sumR_oos", "sumR2_oos", "sum_coin"]


def cmd_run(a):
    cells_path, trades_path = CELLS, PRIMARY_TRADES
    cat = U.catalog()
    syms = a.symbols.split(",") if a.symbols else sorted({s for s, _ in cat if U.sessions_of(s)})
    ideas = tuple(a.ideas.split(","))
    if a.impute_stock_spread:                        # sensitivity run: own cells file, no primary trades written
        cells_path, trades_path = os.path.join(RES, "q75_intraday_cells_stock_spread_imputed.csv"), None
        syms = [s for s in syms if U.group_of(s) == "stock"]
        if os.path.exists(cells_path): os.remove(cells_path)
    done = set()
    if a.resume and os.path.exists(cells_path):
        done = set(pd.read_csv(cells_path, usecols=["symbol"]).symbol)
    elif os.path.exists(cells_path) and not a.symbols:
        os.remove(cells_path)
        if trades_path and os.path.exists(trades_path): os.remove(trades_path)
    t0 = time.time()
    for s in syms:
        if s in done: continue
        rows, prim = run_symbol(s, cat, ideas, impute=a.impute_stock_spread)
        if rows:
            D = pd.DataFrame(rows).reindex(columns=LEAD)
            D.to_csv(cells_path, mode="a", header=not os.path.exists(cells_path), index=False, float_format="%.5g")
        if prim and trades_path:
            P = pd.concat(prim, ignore_index=True)
            P = P.reindex(columns=["idea", "symbol", "session", "bar", "k", "day", "e_col", "x_col", "d", "e_px", "x_px", "den", "R",
                                   "R_gross", "R_opp", "cost_R", "both", "kind"])
            P.to_csv(trades_path, mode="a", header=not os.path.exists(trades_path), index=False, float_format="%.6g")
        print(f"  [{(time.time() - t0) / 60:.1f} min]", flush=True)


# --------------------------------------------------------------------------------------------------------------- summary
def pool(g):
    n = g.n.sum(); s = g.sumR.sum(); s2 = g.sumR2.sum()
    mean = s / n if n else np.nan
    var = (s2 - n * mean ** 2) / (n - 1) if n > 1 else np.nan
    t = mean / np.sqrt(var / n) if n > 1 and var > 0 else np.nan
    nis = g.n_is.sum(); noos = g.n_oos.sum()
    return pd.Series(dict(cells=len(g), n=int(n), mean=mean, t=t, coin=g.sum_coin.sum() / n if n else np.nan,
                          mean_is=g.sumR_is.sum() / nis if nis else np.nan, mean_oos=g.sumR_oos.sum() / noos if noos else np.nan,
                          pos_share=(g["mean"] > 0).mean(), passing=int(g.passes.sum())))


def cmd_summary(a):
    C = pd.read_csv(CELLS)
    C = C[C.n > 0]
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500); pd.set_option("display.max_columns", 50)
    out = []
    for idea, G in C.groupby("idea"):
        print(f"\n===== {idea}: {len(G)} cells, {G.symbol.nunique()} symbols, {G.n.sum():,} trades =====")
        big = G[G.n >= 200]
        print(f"cells positive: {(G['mean'] > 0).mean():.1%}; cells with n >= 200: {len(big)}, passing the CANDIDATE bar: "
              f"{int(G.passes.sum())} (luck ~2.5% = {0.025 * len(big):.1f}); positive among n>=200: {(big['mean'] > 0).mean():.1%}")
        prim = G[G.primary]
        print("primary cells:")
        print(prim[["symbol", "session", "tf", "variant", "n", "mean", "t", "win", "mean_is", "mean_oos", "worst_year", "worst_mean",
                    "coin", "beats", "passes", "by_year"]].round(3).to_string(index=False))
        for keys, lab in ((["variant", "group", "tf"], "group x bar"), (["variant", "tf"], "all groups x bar")):
            P = G.groupby(keys).apply(pool, include_groups=False).reset_index()
            P.insert(0, "idea", idea); P.insert(1, "scope", lab); out.append(P)
        nc = G[G.group != "crypto"]
        P = nc.groupby(["variant", "tf"]).apply(pool, include_groups=False).reset_index()
        P.insert(0, "idea", idea); P.insert(1, "scope", "no crypto x bar"); out.append(P)
        Pv = G.groupby(["variant"]).apply(pool, include_groups=False).reset_index(); Pv.insert(0, "idea", idea); Pv.insert(1, "scope", "all")
        out.append(Pv)
        Pv = nc.groupby(["variant"]).apply(pool, include_groups=False).reset_index(); Pv.insert(0, "idea", idea); Pv.insert(1, "scope", "no crypto")
        out.append(Pv)
        print("passing cells:")
        print(G[G.passes][["symbol", "session", "tf", "variant", "n", "mean", "t", "mean_is", "mean_oos", "worst_mean", "coin"]]
              .round(3).to_string(index=False) or "none")
    Pall = pd.concat(out, ignore_index=True)
    Pall.to_csv(POOLED, index=False, float_format="%.5g")
    for idea in Pall.idea.unique():
        X = Pall[Pall.idea == idea]
        print(f"\n----- {idea} pooled -----")
        print(X[X.scope.isin(["all", "no crypto"])].round(4).to_string(index=False))
        print(X[X.scope.isin(["all groups x bar", "no crypto x bar"])].round(4).to_string(index=False))
        piv = X[X.scope == "group x bar"].pivot_table(index=["variant", "group"], columns="tf", values="mean")
        print(piv.round(3).to_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "summary"])
    ap.add_argument("--symbols", default=""); ap.add_argument("--ideas", default="dt,rb"); ap.add_argument("--resume", action="store_true")
    ap.add_argument("--impute-stock-spread", action="store_true", help="cost sensitivity: fill zero stock spreads (see impute_stock_spread)")
    a = ap.parse_args()
    cmd_run(a) if a.cmd == "run" else cmd_summary(a)


if __name__ == "__main__":
    main()
