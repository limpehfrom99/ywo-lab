import sys; sys.path.insert(0,'/home/claude/bt')
import sr_diag, pandas as pd
g = sr_diag.load(); d, atr = sr_diag.daily_atr(g); lv = sr_diag.build_levels(g, d, atr)
for k, tr, hold in ((0.1, 2.0, 1440), (0.2, 2.0, 2880), (0.3, 1.5, 2880)):
    df = sr_diag.simulate(g, lv, atr, stop_atr_k=k, target_r=tr, hold=hold)
    df = df[df.touch == 1]
    print(sr_diag.stats(df, f"first touch, stop {k} ATR, {tr}R, {hold//60}h"), flush=True)
    print(df.groupby('year').R.agg(['count','mean']).round(2).T.to_string(), flush=True)
