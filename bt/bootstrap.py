"""Recreate the working data files the engines expect (/home/claude/data/*.pkl, /home/claude/news,
/home/claude/lab) from this repo. Run once per fresh session: python3 bt/bootstrap.py
Safe to re-run; skips files that already exist."""
import os, glob, shutil, sys, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
OUT = "/home/claude/data"
os.makedirs(OUT, exist_ok=True); os.makedirs("/home/claude/news", exist_ok=True)
os.makedirs("/home/claude/lab", exist_ok=True); os.makedirs("/home/claude/bt", exist_ok=True)

p = os.path.join(OUT, "gold_m1_utc.pkl")
if not os.path.exists(p):
    parts = [pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(D, "gold_m1", "*.parquet")))]
    g = pd.concat(parts).sort_index(); g.index.name = "utc"
    g.to_pickle(p); print("gold M1", g.shape, g.index[0], g.index[-1])

for s in ("gold", "TSLA", "AAPL", "US100", "US500"):
    p = os.path.join(OUT, f"{s}_m5.pkl")
    if not os.path.exists(p):
        b = pd.read_parquet(os.path.join(D, "ftmo", f"{s}_m5.parquet"))
        b.attrs["comm"] = {"gold": 0.000007, "TSLA": 0.00002, "AAPL": 0.00002, "US100": 0.0, "US500": 0.0}[s]
        b.to_pickle(p); print(s, "M5", b.shape)

shutil.copy(os.path.join(D, "news", "news_usd.csv"), "/home/claude/news/news_usd.csv")
for f in glob.glob(os.path.join(ROOT, "lab", "*.py")): shutil.copy(f, "/home/claude/lab/")
for f in glob.glob(os.path.join(ROOT, "bt", "*.py")): shutil.copy(f, "/home/claude/bt/")
print("ready: /home/claude/data, /home/claude/lab, /home/claude/bt")
