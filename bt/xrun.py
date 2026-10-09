"""Run rules from bt/xrules.py (and any module that registers into it) across every asset and timeframe in hand.
python3 xrun.py [rule-name-prefix ...] [--assets gold,fx,index,stock,crypto or symbols] [--tfs M5,H1,...] [--module xrules_video]
Writes /home/claude/bt/xgrid_results/<timestamp>_cells.csv and _trades.pkl, prints every cell and a per-rule summary."""
import sys, os, time, argparse, importlib, pandas as pd
sys.path.insert(0, "/home/claude/bt")
import xgrid as XG

ap = argparse.ArgumentParser(); ap.add_argument("rules", nargs="*"); ap.add_argument("--assets", default="")
ap.add_argument("--tfs", default=""); ap.add_argument("--module", action="append", default=["xrules"])
ap.add_argument("--export", action="store_true", help="use the full FTMO export (data/x) instead of the data in hand")
ap.add_argument("--h4-offset", type=int, default=0, help="phase check: start H4 bars this many hours after FTMO's (1-3)")
a = ap.parse_args()
XG.H4_OFFSET_H = a.h4_offset
reg = {}
for mod in a.module: reg.update(importlib.import_module(mod).REGISTRY)
names = [n for n in reg if not a.rules or any(n.startswith(p) for p in a.rules)]
which = [x for x in a.assets.split(",") if x] or None
tfs = tuple(x for x in a.tfs.split(",") if x) or None
t0 = time.time()
if a.export:
    groups = [x for x in (which or []) if x in ("gold", "fx", "index", "stock", "crypto", "metal", "energy", "soft")] or None
    syms = [x for x in (which or []) if x not in ("gold", "fx", "index", "stock", "crypto", "metal", "energy", "soft")] or None
    C, T = XG.run_many({n: reg[n] for n in names}, XG.datasets_export(groups, syms), tfs, verbose=True)
else:
    ds = XG.datasets(which); print(f"data: {[d.name for d in ds]} ({time.time() - t0:.0f}s)", flush=True)
    allC, allT = [], []
    for n in names:
        C, T = XG.run_rule(reg[n], n, ds, tfs); allC.append(C); allT.append(T)
        print(f"--- {n} done ({time.time() - t0:.0f}s)", flush=True)
    C = pd.concat(allC); T = pd.concat(allT)
os.makedirs("/home/claude/bt/xgrid_results", exist_ok=True); stamp = time.strftime("%Y%m%d_%H%M%S") + (f"_h4o{a.h4_offset}" if a.h4_offset else "")
C.to_csv(f"/home/claude/bt/xgrid_results/{stamp}_cells.csv", index=False); T.to_pickle(f"/home/claude/bt/xgrid_results/{stamp}_trades.pkl")
S = XG.summary(C, T)
print("\nper rule:"); print(S.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
print(f"done in {time.time() - t0:.0f}s -> xgrid_results/{stamp}_*")
