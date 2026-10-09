"""Check bt/robust.py against Timothy Masters' C++ originals on identical inputs.
Needs the book code built first: bash tools/get_masters.sh  (binaries in $VENDOR/bin, default /home/claude/vendor).
  CSCV: robust.cscv_pbo vs CSCV_CORE.CPP (criterion = mean) -> must match exactly.
  BCa : robust.bca_bounds vs boot_conf_BCa (BOOT_CONF.CPP)  -> must agree within bootstrap noise.
"""
import os, subprocess, sys, tempfile
import numpy as np
sys.path.insert(0, "/home/claude/bt")
import robust

BIN = os.path.join(os.environ.get("VENDOR", "/home/claude/vendor"), "bin")


def c_cscv(M, n_blocks):
    T, N = M.shape
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(f"{T} {N} {n_blocks}\n")
        for j in range(N):                                   # one row per system, cases fastest
            f.write(" ".join(f"{v:.17g}" for v in M[:, j]) + "\n")
    out = subprocess.run([os.path.join(BIN, "verify_cscv"), f.name], capture_output=True, text=True).stdout
    os.unlink(f.name)
    return float(out.split()[-1])


def c_bca(x, nboot):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(f"{len(x)}\n" + "\n".join(f"{v:.17g}" for v in x) + "\n")
    out = subprocess.run([os.path.join(BIN, "verify_bca"), f.name, str(nboot)], capture_output=True, text=True).stdout
    os.unlink(f.name)
    l2, h2, l5, h5, l10, h10 = map(float, out.split())
    return {0.025: (l2, h2), 0.05: (l5, h5), 0.10: (l10, h10)}


def main():
    rng = np.random.default_rng(11)
    ok = True
    print("CSCV (probability of backtest overfitting), Python vs C++:")
    cases = [("noise 1000x50, 10 blocks", rng.normal(0, 1, (1000, 50)), 10),
             ("noise 1003x40, 8 blocks (uneven blocks)", rng.normal(0, 1, (1003, 40)), 8),
             ("5 real edges among 30, 12 blocks", np.c_[rng.normal(0.08, 1, (1200, 5)), rng.normal(0, 1, (1200, 25))], 12),
             ("sparse trades 900x16, 16 blocks", rng.normal(0, 1, (900, 16)) * (rng.random((900, 16)) < 0.3), 16)]
    for name, M, nb in cases:
        py = robust.cscv_pbo(M, nb)["pbo"]; c = c_cscv(M, nb)
        same = abs(py - c) < 1e-9          # C++ prints 10 decimals
        ok &= same
        print(f"  {name:42s} python {py:.6f}  C++ {c:.6f}  {'MATCH' if same else 'DIFFERENT'}")
    print("BCa bounds for the mean (200,000 resamples each side), Python vs C++:")
    for name, x in (("skewed sample n=400", rng.lognormal(0, 1, 400) - 1.4),
                    ("trade-like R n=1100", np.where(rng.random(1100) < 0.38, rng.exponential(1.6, 1100), -1.0))):
        py = robust.bca_bounds(x, "mean", B=200_000, rng=1)
        c = c_bca(x, 200_000)
        se = x.std(ddof=1) / np.sqrt(len(x))
        for a in (0.025, 0.05, 0.10):
            dl = (py["low"][a] - c[a][0]) / se; dh = (py["high"][a] - c[a][1]) / se
            good = abs(dl) < 0.03 and abs(dh) < 0.03
            ok &= good
            print(f"  {name:22s} {a:5.3f}: low py {py['low'][a]:+.5f} C {c[a][0]:+.5f} | high py {py['high'][a]:+.5f} "
                  f"C {c[a][1]:+.5f} | diff {dl:+.3f}/{dh:+.3f} std errors  {'OK' if good else 'CHECK'}")
    print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
