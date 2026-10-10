"""Selection-aware permutation test (PROTOCOL robustness 1) for GB4 (bt/q75_web_mql.py), whose pre-registered primary cell (XAUUSD
H4) cleared the CANDIDATE bar. Family = every cell of the idea that could clear the bar (>= 200 trades in the real run: 308 of 510
symbol x timeframe cells). Each shuffle permutes the finest bars of every symbol within their New York time-of-day slot
(robust.permute_bars algorithm: gaps and bar shapes shuffled separately, spread travels with the bar shape; re-implemented here
with the slot groups and logs precomputed once — identical output for the same generator, checked by --verify), rebuilds every
timeframe, reruns the rule with the same filters, costs and swaps, and records each cell's mean R and t.
p_alone = primary vs its own null; p_best = primary vs the best cell of each shuffle (t-stat; also mean R among cells with
>= 200 trades in that shuffle). python3 bt/q75_web_perm.py [--perms 200] [--symbols ...] [--verify]"""
import sys, os, time, zlib, argparse, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/ywo-lab/bt")
import q75_web_common as C
import q75_web_mql as M
import robust

SCR = M.SCR; OUT = M.OUT
PDIR = os.path.join(SCR, "q75_web_perm"); os.makedirs(PDIR, exist_ok=True)


def tf_groups(t, idx, tf):
    if tf in ("M5", "M15", "M30", "H1"):
        key = t // C.TF_NS[tf]
    else:
        key = C.to_server(idx).values.astype("datetime64[ns]").view("i8") // C.TF_NS[tf]
    starts = np.r_[0, np.flatnonzero(np.diff(key)) + 1]; ends = np.r_[starts[1:], len(key)]
    if tf == "D1":
        wd = (key[starts] + 3) % 7                      # day 0 = Thu 1 Jan 1970; Monday = 0
        keep = wd < 5; starts, ends = starts[keep], ends[keep]
    return starts, ends


class FastPerm:
    def __init__(self, o, h, l, c, slots, extra):
        self.lo = np.log(o); lh, ll, lc = np.log(h), np.log(l), np.log(c)
        self.gap = np.r_[0.0, self.lo[1:] - lc[:-1]]; self.hi = lh - self.lo; self.lw = ll - self.lo; self.cl = lc - self.lo
        order = np.argsort(slots, kind="stable"); ss = slots[order]
        self.groups = [g[g > 0] for g in np.split(order, np.flatnonzero(np.diff(ss)) + 1)]
        self.extra = extra

    def __call__(self, rng):
        n = len(self.lo); p1 = np.arange(n); p2 = np.arange(n)
        for m in self.groups:
            p1[m] = rng.permutation(m); p2[m] = rng.permutation(m)
        g = self.gap[p2]; g[0] = 0.0; cc = self.cl[p1]
        close = self.lo[0] + np.cumsum(g + cc); op = close - cc
        return [np.exp(op), np.exp(op + self.hi[p1]), np.exp(op + self.lw[p1]), np.exp(close)] + [e[p1] for e in self.extra]


def cell_run(sym, t, o, h, l, c, sp, send, cal, comm, base_ns, starts):
    Fh = np.maximum.reduceat(h, starts); Fl = np.minimum.reduceat(l, starts)
    ends = np.r_[starts[1:], len(t)]; Fc = c[ends - 1]
    sig, dist = M.gb4_signals(pd.DataFrame({"high": Fh, "low": Fl, "close": Fc}))
    i = np.flatnonzero(sig[:-1]); k0 = starts[i + 1]; ds = dist[i]
    ok = np.isfinite(ds) & (ds >= 2e-5 * np.abs(o[k0])) & ((sp[k0] / 1.2) <= 0.10 * np.nan_to_num(ds, nan=0.0)) & ((send[k0] - t[k0]) > 15 * C.NS)
    k0, ds = k0[ok].astype(np.int64), ds[ok]
    if not len(k0): return 0, np.nan, np.nan, np.array([])
    tk, xi, xp, why = C.sim_bracket(t, o, h, l, c, k0, ds, np.full(len(k0), 2.0), 1, True, M.MAXHOLD)
    k0, ds, xi, xp, why = k0[tk], ds[tk], xi[tk], xp[tk], why[tk]
    t_out = np.where(why == 3, t[xi] + base_ns - 1, t[xi] + base_ns // 2)
    R, _, _ = C.trade_R(sym, 1, o[k0], xp, ds, sp[k0], t[k0], t_out, cal, comm)
    return len(R), R.mean(), C.tstat(R), R


def main(a):
    real = pd.read_csv(os.path.join(OUT, "q75_web_mql_cells.csv"))
    fam = real[real.n >= 200][["asset", "tf", "n", "avgR", "t"]]
    want = {s: set(x.tf) for s, x in fam.groupby("asset")}
    symbols = [x for x in a.symbols.split(",") if x] or None
    order = ["XAUUSD"] + sorted(s for s in want if s != "XAUUSD")
    if symbols: order = [s for s in order if s in symbols]
    t0 = time.time()
    for sym in order:
        f = os.path.join(PDIR, f"{sym}.npz")
        if os.path.exists(f) and not a.verify: continue
        got = next(C.datasets(symbols=[sym]), None)
        if got is None: continue
        _, grp, base_tf, d = got
        t = C.ns(d.index); o, h, l, c, sp = (d[k].values.astype(float) for k in ("open", "high", "low", "close", "sp"))
        if min(o.min(), l.min()) <= 0: print(f"{sym}: non-positive prices, skipped", flush=True); continue
        comm = C.U.commission_of(sym); base_ns = C.TF_NS[base_tf]; cal = C.swap_calendar(sym, t[0], t[-1])
        send = C.session_end(t, base_ns, (30 if base_tf in ("M1", "M5") else 45) * C.NS)
        ny = d.index.tz_localize("UTC").tz_convert("America/New_York"); slots = (ny.hour * 60 + ny.minute).values.astype(np.int64)
        tfs = [tf for tf in M.TFS if tf in want[sym]]
        G = {tf: tf_groups(t, d.index, tf)[0] for tf in tfs}
        fp = FastPerm(o, h, l, c, slots, (sp,))
        if a.verify:
            r1 = robust.permute_bars(o, h, l, c, slots, np.random.default_rng(7), extra=(sp,)); r2 = fp(np.random.default_rng(7))
            print(sym, "FastPerm == robust.permute_bars:", all(np.allclose(x, y, rtol=1e-12, atol=0) for x, y in zip(r1, r2)), flush=True)
        rv = {tf: cell_run(sym, t, o, h, l, c, sp, send, cal, comm, base_ns, G[tf])[:3] for tf in tfs}
        print(f"{sym} real (same code path): " + " ".join(f"{tf}:{n}/{m:+.3f}/t{tt:+.2f}" for tf, (n, m, tt) in rv.items()), flush=True)
        if a.verify: continue
        rng = np.random.default_rng(zlib.crc32(f"q75web|{sym}".encode()))
        nm = np.full((a.perms, len(tfs)), np.nan); nt = nm.copy(); nn = np.zeros((a.perms, len(tfs)), np.int64)
        for p in range(a.perms):
            po, ph, pl, pc, psp = fp(rng)
            for j, tf in enumerate(tfs):
                nn[p, j], nm[p, j], nt[p, j], _ = cell_run(sym, t, po, ph, pl, pc, psp, send, cal, comm, base_ns, G[tf])
        np.savez(f, tfs=np.array(tfs), real_n=np.array([rv[x][0] for x in tfs]), real_m=np.array([rv[x][1] for x in tfs]),
                 real_t=np.array([rv[x][2] for x in tfs]), null_n=nn, null_m=nm, null_t=nt)
        print(f"{sym} {base_tf} {len(tfs)} cells x {a.perms} shuffles done ({time.time() - t0:.0f}s)", flush=True)
        del d, fp
    if a.verify: return
    summarize(a.perms)


def summarize(perms):
    cols, real_t, real_m, NT, NM, NN = [], [], [], [], [], []
    for f in sorted(os.listdir(PDIR)):
        z = np.load(os.path.join(PDIR, f))
        if z["null_t"].shape[0] < perms: continue
        sym = f[:-4]
        for j, tf in enumerate(z["tfs"]):
            cols.append(f"{sym} {tf}"); real_t.append(z["real_t"][j]); real_m.append(z["real_m"][j])
            NT.append(z["null_t"][:perms, j]); NM.append(z["null_m"][:perms, j]); NN.append(z["null_n"][:perms, j])
    NT, NM, NN = np.array(NT).T, np.array(NM).T, np.array(NN).T
    NMe = np.where(NN >= 200, NM, np.nan)
    res_t = robust.mcpt_select(pd.Series(real_t, index=cols), NT)
    res_m = robust.mcpt_select(pd.Series(real_m, index=cols), NMe)
    out = res_t.add_suffix("_t").join(res_m.add_suffix("_m"))
    out.insert(0, "n_cells", len(cols)); out.insert(1, "perms", perms)
    out.to_csv(os.path.join(OUT, "q75_web_mql_perm.csv"))
    pd.set_option("display.width", 250)
    print(f"family: {len(cols)} cells x {perms} shuffles; null best t avg {res_t.attrs['null_best_avg']:+.2f} (95th pct "
          f"{res_t.attrs['null_best_q95']:+.2f}); null best mean R avg {res_m.attrs['null_best_avg']:+.3f}")
    print(out.sort_values("real_t", ascending=False).head(12).to_string(float_format=lambda v: f"{v:+.3f}"))
    if "XAUUSD H4" in out.index: print("PRIMARY:\n", out.loc[["XAUUSD H4"]].T.to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--perms", type=int, default=200); ap.add_argument("--symbols", default=""); ap.add_argument("--verify", action="store_true")
    ap.add_argument("--summarize", action="store_true")
    a = ap.parse_args()
    summarize(a.perms) if a.summarize else main(a)
