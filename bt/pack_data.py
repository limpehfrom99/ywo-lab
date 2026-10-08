"""Pack the working data into the repo as compressed parquet (one gold M1 file per year so every
file stays far below GitHub's 100 MB limit), plus the raw broker exports gzipped and the news CSV.
Run from the repo root: python3 bt/pack_data.py"""
import os, gzip, shutil, glob, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
for sub in ("gold_m1", "ftmo", "raw", "news"):
    os.makedirs(os.path.join(D, sub), exist_ok=True)

g = pd.read_pickle("/home/claude/data/gold_m1_utc.pkl")
for y, part in g.groupby(g.index.year):
    part.to_parquet(os.path.join(D, "gold_m1", f"{y}.parquet"), compression="zstd")

for s in ("gold", "TSLA", "AAPL", "US100", "US500"):
    b = pd.read_pickle(f"/home/claude/data/{s}_m5.pkl")
    b.to_parquet(os.path.join(D, "ftmo", f"{s}_m5.parquet"), compression="zstd")

for f in glob.glob("/home/claude/data/assets/*.csv") + glob.glob("/home/claude/data/mt4/XAUUSD_*.csv"):
    with open(f, "rb") as src, gzip.open(os.path.join(D, "raw", os.path.basename(f) + ".gz"), "wb") as dst:
        shutil.copyfileobj(src, dst)

shutil.copy("/home/claude/news/news_usd.csv", os.path.join(D, "news", "news_usd.csv"))

total = 0
for root, _, files in os.walk(D):
    for f in files:
        total += os.path.getsize(os.path.join(root, f))
print(f"data folder: {total/1e6:.0f} MB")
