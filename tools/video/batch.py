"""Process a batch of strategy videos (a folder or .zip of .mp4/.mov/.webm files) for research, with de-duplication against every
video already processed (research/videos/index.csv + transcripts/).

python3 -I tools/video/batch.py INPUT OUT_DIR [--index research/videos/index.csv]

For each video, in name order (resumable: a video with OUT_DIR/<name>/transcript.txt is skipped):
  1. sha1 of the file -> exact duplicate of an indexed video? Then no transcription, just the reference.
  2. transcript (tools/video/video_notes.py: SenseVoice + Silero VAD, offline) and contact sheets (frames every 2 s for clips under
     1 min, 10 s under 5 min, 30 s otherwise).
  3. near-duplicate check: overlap of the transcript's 5-character pieces (timestamps and punctuation removed) with every
     indexed transcript (>= 60% of the shorter one = duplicate; catches re-encodes and clips cut from a longer video), and for silent clips a perceptual hash of 3 frames (25/50/75%) against the indexed hashes.
  4. strategy keywords (FVG, order block, BOS/CHoCH, liquidity/sweep, Fibonacci, moving averages, RSI/MACD, volume profile,
     trendline, breakout/pullback, session, news, risk...) to sort the batch.
Writes OUT_DIR/batch_report.md (one row per video) and OUT_DIR/batch.csv. The index itself is updated only after the rules are
tested (one row per video: id, sha1, duration, author, title, log entry, verdict, hash, transcript file).
Untrusted input: zips are extracted into OUT_DIR/_input (a new, empty folder); run this with python3 -I."""
import os, sys, re, csv, glob, hashlib, zipfile, argparse, subprocess, traceback, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import video_notes as VN  # noqa: E402

EXT = (".mp4", ".mov", ".m4v", ".webm", ".mkv")
KEYWORDS = {
    "FVG / gap": ["fvg", "fair value gap", "公允价值缺口", "缺口", "失衡"],
    "order block": ["order block", "订单块", "ob"],
    "BOS / CHoCH": ["bos", "break of structure", "choch", "change of character", "结构突破", "结构转换", "mss", "市场结构"],
    "liquidity / sweep": ["liquidity", "流动性", "sweep", "扫", "猎杀", "诱多", "诱空", "inducement", "idm"],
    "Fibonacci / OTE": ["fibonacci", "斐波那契", "0.618", "0.705", "0.786", "ote", "黄金分割"],
    "moving average": ["均线", "moving average", "ema", "sma", "金叉", "死叉"],
    "RSI / MACD / oscillator": ["rsi", "macd", "kdj", "stochastic", "背离", "divergence"],
    "volume / profile": ["成交量", "volume", "value area", "价值区", "poc", "volume profile", "order flow", "订单流", "heatmap"],
    "trendline / channel": ["趋势线", "trendline", "trend line", "通道", "channel"],
    "breakout / pullback": ["突破", "breakout", "回调", "回撤", "pullback", "retest", "回踩"],
    "session / time": ["亚洲", "伦敦", "纽约", "asia", "london", "new york", "kill zone", "killzone", "开盘", "open"],
    "news": ["新闻", "非农", "cpi", "news", "fomc", "数据"],
    "risk / money mgmt": ["风控", "止损", "仓位", "risk", "盈亏比", "drawdown", "回撤控制", "资金管理"],
    "prop firm": ["prop", "ftmo", "自营", "考核", "funded", "payout", "出金"],
}


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()


def norm_text(txt):
    txt = re.sub(r"\[\d\d:\d\d\.\d\]", " ", txt)
    return re.sub(r"[\s\W_]+", "", txt.lower())


def shingles(t, n=5):
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def overlap(a, b):
    """Share of the shorter transcript's 5-character pieces found in the other: catches re-uploads, re-encodes and clips cut
    from a longer video (difflib's ratio misses those)."""
    sa, sb = shingles(a), shingles(b)
    if not sa or not sb: return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


def ahash_frames(path, dur):
    """64-bit average hash of 3 frames (25/50/75% of the clip), as one hex string."""
    import cv2
    out = []
    for q in (0.25, 0.5, 0.75):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{dur * q:.2f}", "-i", path, "-frames:v", "1", "-vf", "scale=8:8,format=gray",
                              "-f", "rawvideo", "-"], capture_output=True).stdout
        if len(raw) < 64: out.append("0" * 16); continue
        a = np.frombuffer(raw[:64], np.uint8).astype(float); bits = (a > a.mean()).astype(int)
        out.append("%016x" % int("".join(map(str, bits)), 2))
    return "".join(out)


def ham(a, b):
    if not a or not b or len(a) != len(b): return 999
    return sum(bin(int(a[i:i + 16], 16) ^ int(b[i:i + 16], 16)).count("1") for i in range(0, len(a), 16))


def load_index(path):
    if not os.path.exists(path): return []
    with open(path, encoding="utf-8") as f: return list(csv.DictReader(f))


def tags_of(txt):
    t = txt.lower(); found = []
    for k, words in KEYWORDS.items():
        n = sum(t.count(w) for w in words if len(w) > 2 or not w.isascii())
        if n: found.append(f"{k} ({n})")
    return found


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("out")
    ap.add_argument("--index", default=os.path.join(HERE, "..", "..", "research", "videos", "index.csv"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True); VN.setup()
    src = a.input
    if src.lower().endswith(".zip"):
        dst = os.path.join(a.out, "_input"); os.makedirs(dst, exist_ok=True)
        with zipfile.ZipFile(src) as z:
            for m in z.infolist():
                name = os.path.basename(m.filename)
                if not name or not name.lower().endswith(EXT): continue
                with z.open(m) as fi, open(os.path.join(dst, name), "wb") as fo: fo.write(fi.read())
        src = dst
    vids = sorted(p for p in glob.glob(os.path.join(src, "**", "*"), recursive=True) if p.lower().endswith(EXT))
    index = load_index(a.index); idx_dir = os.path.dirname(os.path.abspath(a.index))
    known_txt = {}
    for r in index:
        p = os.path.join(idx_dir, r.get("transcript_file", ""))
        if r.get("transcript_file") and os.path.exists(p):
            known_txt[r["id"]] = norm_text(open(p, encoding="utf-8").read())
    by_sha = {r["sha1"]: r["id"] for r in index if r.get("sha1")}
    rows = []; seen_new = {}
    log = open(os.path.join(a.out, "batch.log"), "a", encoding="utf-8")
    for k, v in enumerate(vids, 1):
        name = f"{k:03d}_{os.path.splitext(os.path.basename(v))[0][:40]}"
        od = os.path.join(a.out, name); os.makedirs(od, exist_ok=True)
        t0 = time.time()
        try:
            h = sha1(v); dur = VN.duration(v)
            row = {"n": k, "file": os.path.basename(v), "folder": name, "sha1": h, "duration_s": round(dur, 1)}
            if h in by_sha:
                row.update(dup=f"same file as {by_sha[h]}", tags="", first=""); rows.append(row)
                print(f"[{k}/{len(vids)}] {row['file']}: exact duplicate of {by_sha[h]}", file=log, flush=True); continue
            if h in seen_new:
                row.update(dup=f"same file as #{seen_new[h]} in this batch", tags="", first=""); rows.append(row); continue
            seen_new[h] = k
            tp = os.path.join(od, "transcript.txt")
            if not os.path.exists(tp):
                lines = VN.transcribe(VN.audio(v))
                with open(tp, "w", encoding="utf-8") as f:
                    for t, txt in lines: f.write(f"[{VN.fmt(t)}] {txt}\n")
                every = 2.0 if dur < 60 else (10.0 if dur < 300 else 30.0)
                VN.frames(v, od, every, dur)
            txt = open(tp, encoding="utf-8").read(); nt = norm_text(txt)
            row["ahash"] = ahash_frames(v, dur)
            dup = ""
            if len(nt) >= 30:
                best = max(((overlap(nt, kt), kid) for kid, kt in known_txt.items()), default=(0, ""))
                if best[0] >= 0.6: dup = f"near duplicate of {best[1]} (text {best[0]:.0%})"
            else:
                best = min(((ham(row["ahash"], r.get("ahash", "")), r["id"]) for r in index), default=(999, ""))
                if best[0] <= 12: dup = f"probably the same clip as {best[1]} (frames)"
            known_txt[f"batch#{k}"] = nt
            row.update(dup=dup, tags="; ".join(tags_of(txt)), first=re.sub(r"\[\d\d:\d\d\.\d\]\s*", "", txt)[:160].replace("\n", " "))
            rows.append(row)
            print(f"[{k}/{len(vids)}] {row['file']} {dur:.0f}s done in {time.time() - t0:.0f}s {dup}", file=log, flush=True)
        except Exception:
            print(f"[{k}/{len(vids)}] {v} FAILED\n{traceback.format_exc()}", file=log, flush=True)
            rows.append({"n": k, "file": os.path.basename(v), "folder": name, "dup": "FAILED (see batch.log)"})
    keys = ["n", "file", "folder", "duration_s", "sha1", "ahash", "dup", "tags", "first"]
    with open(os.path.join(a.out, "batch.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader(); [w.writerow(r) for r in rows]
    with open(os.path.join(a.out, "batch_report.md"), "w", encoding="utf-8") as f:
        f.write(f"# Video batch: {len(vids)} files\n\n| # | file | length | duplicate? | topics | opening words |\n|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['n']} | {r['file']} | {r.get('duration_s', '')}s | {r.get('dup', '')} | {r.get('tags', '')} | {r.get('first', '')} |\n")
    print(f"{len(vids)} videos -> {a.out}/batch_report.md")


if __name__ == "__main__":
    main()
