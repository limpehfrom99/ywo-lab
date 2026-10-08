import pandas as pd, numpy as np, time, ict, smc
rows = []
def row(d, lab):
    s = smc.stats(d, lab)
    if len(d) >= 10:
        s["gross R"] = round(d.R.mean() + d.cost_R.mean(), 3); s["exits"] = str(d.why.value_counts().to_dict())
        kz = d.groupby("kz").R.mean().round(2).to_dict(); s["by zone"] = str(kz)
    return s
t0 = time.time()
for sym in ["US100", "US500", "TSLA", "AAPL"]:
    b = pd.read_pickle(f"/home/claude/data/{sym}_m5.pkl"); ict._CACHE.clear()
    for lab, kw in [("2022 model: 4h bias, killzones, FVG limit, 2R", dict(bias="4h", windows="killzones", target="2R")),
                    ("2022 model: 4h bias, target = draw", dict(bias="4h", windows="killzones", target="draw")),
                    ("2022 model: both biases, 2R", dict(bias="both", windows="killzones", target="2R")),
                    ("2022 model: 4h bias, market entry", dict(bias="4h", windows="killzones", target="2R", entry="market")),
                    ("Silver Bullet: 4h bias, FVG limit, 2R", dict(bias="4h", windows="silver", target="2R")),
                    ("Silver Bullet: no bias, no sweep, first FVG after MSS", dict(bias="none", windows="silver", target="2R", need_sweep=False)),
                    ("baseline: 4h bias + MSS + FVG, no sweep", dict(bias="4h", windows="killzones", target="2R", need_sweep=False))]:
        d = ict.run(b, **kw); r = row(d, f"{sym}: {lab}"); rows.append(r)
        pd.DataFrame(rows).to_csv("/home/claude/bt/ict_others_results.csv", index=False)
print("done", round(time.time() - t0))
