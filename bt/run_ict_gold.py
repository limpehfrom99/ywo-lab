import pandas as pd, numpy as np, time, ict, smc, json
g = pd.read_pickle("/home/claude/data/gold_m5.pkl")
rows = []
def row(d, lab):
    s = smc.stats(d, lab)
    if len(d) >= 10:
        e, l_ = d[d.t < "2020-01-01"], d[d.t >= "2020-01-01"]
        s["2012-19"] = round(e.R.mean(), 3) if len(e) else None; s["2020-26"] = round(l_.R.mean(), 3) if len(l_) else None
        s["gross R"] = round(d.R.mean() + d.cost_R.mean(), 3); s["exits"] = str(d.why.value_counts().to_dict())
    return s
t0 = time.time()
runs = [("2022 model: 4h bias, killzones, FVG limit, 2R", dict(bias="4h", windows="killzones", target="2R")),
        ("2022 model: 4h bias, killzones, FVG limit, target = draw (PDH/PDL)", dict(bias="4h", windows="killzones", target="draw")),
        ("2022 model: premium/discount bias, killzones, 2R", dict(bias="pd", windows="killzones", target="2R")),
        ("2022 model: both biases agree, killzones, 2R", dict(bias="both", windows="killzones", target="2R")),
        ("2022 model: 4h bias, market entry at the MSS, 2R", dict(bias="4h", windows="killzones", target="2R", entry="market")),
        ("2022 model: 4h bias, any time of day, 2R", dict(bias="4h", windows="all", target="2R")),
        ("Silver Bullet windows: 4h bias, FVG limit, 2R", dict(bias="4h", windows="silver", target="2R")),
        ("Silver Bullet windows: no bias, no sweep, first FVG after an MSS", dict(bias="none", windows="silver", target="2R", need_sweep=False)),
        ("baseline: 4h bias + MSS + FVG, no sweep required", dict(bias="4h", windows="killzones", target="2R", need_sweep=False)),
        ("baseline: same setups, coin-flip direction", dict(bias="4h", windows="killzones", target="2R", random_dir=True))]
for lab, kw in runs:
    d = ict.run(g, **kw); r = row(d, lab); r["sec"] = round(time.time() - t0); rows.append(r)
    pd.DataFrame(rows).to_csv("/home/claude/bt/ict_gold_results.csv", index=False)
    if lab.startswith("2022 model: 4h bias, killzones, FVG limit, 2R"): d.to_pickle("/home/claude/bt/ict_gold_base.pkl")
print("done", round(time.time() - t0))
