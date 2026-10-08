import sys; sys.path.insert(0,'/home/claude/bt')
import sr_diag, pandas as pd
g = sr_diag.load(); d, atr = sr_diag.daily_atr(g); lv = sr_diag.build_levels(g, d, atr)
rd = sr_diag.simulate(g, lv, atr, random_dir=True); rd.to_pickle('/home/claude/bt/sr_diag_random.pkl')
print(sr_diag.stats(rd, "random direction (benchmark)"))
