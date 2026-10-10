"""Transcript from BURNED-IN subtitles (added 2026-10-10, log #78-#81). RedNote reposts by 油管中文配音檔案館 (Chinese-dubbed YouTube
trading videos) carry two subtitle lines at the bottom of a 1920x1080 frame: Chinese at y ~ 820-865 and the original English at
y ~ 880-925. Reading them is faster and more accurate than speech-to-text on the dub, and the English line is the speaker's own words
(it is cut at the frame edges when it is long; the Chinese line is complete).

python3 -I tools/video/sub_ocr.py VIDEO OUT.txt [--fps 2] [--y0 818] [--zh 10:60] [--en 62:112] [--h 112]
  pip install --break-system-packages rapidocr_onnxruntime   (1.2.x bundles its ONNX models; no download needed)
Recognition only (no text detection) on fixed line crops: ~0.17 s a frame on 2 cores; frames whose subtitle band is unchanged
(mean abs diff < 3 on a 1/4-scale grey copy) reuse the previous result, so a 25-minute video takes ~2-5 minutes.
Output: one line per subtitle: "[mm:ss] English || Chinese" (low-confidence lines dropped, repeats merged).
Other layouts: check one frame first (ffmpeg -ss 300 -i VIDEO -frames:v 1 f.jpg) and pass the band's rows.
"""
import sys, json, argparse, difflib, subprocess
import numpy as np


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("out")
    ap.add_argument("--fps", type=float, default=2.0); ap.add_argument("--y0", type=int, default=818)
    ap.add_argument("--h", type=int, default=112); ap.add_argument("--zh", default="10:60"); ap.add_argument("--en", default="62:112")
    ap.add_argument("--width", type=int, default=1920)
    a = ap.parse_args()
    from rapidocr_onnxruntime import RapidOCR
    rec = RapidOCR().text_recognizer
    z0, z1 = map(int, a.zh.split(":")); e0, e1 = map(int, a.en.split(":"))
    W, H = a.width, a.h
    cmd = ["ffmpeg", "-v", "error", "-skip_frame", "noref", "-i", a.video, "-vf", f"fps={a.fps},crop={W}:{H}:0:{a.y0}",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    rows = []; last_small = None; last = None; n = 0
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        im = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        small = im[::4, ::4].astype(np.int16).mean(axis=2)
        if last_small is None or np.abs(small - last_small).mean() >= 3.0:
            r = rec([np.ascontiguousarray(im[z0:z1]), np.ascontiguousarray(im[e0:e1])]); r = r[0] if isinstance(r, tuple) else r
            last = [(str(x), float(c)) for x, c in r]; last_small = small
        rows.append(dict(t=n / a.fps, zh=last[0][0], zc=last[0][1], en=last[1][0], ec=last[1][1])); n += 1
    sim = lambda x, y: difflib.SequenceMatcher(None, x, y).ratio()
    segs = []
    for r in rows:
        en = r["en"].strip() if r["ec"] >= 0.6 else ""; zh = r["zh"].strip() if r["zc"] >= 0.6 else ""
        if len(en) < 3 and len(zh) < 2: continue
        if segs and (sim(en, segs[-1]["en"]) > 0.75 or (zh and sim(zh, segs[-1]["zh"]) > 0.7)):
            s = segs[-1]
            if r["ec"] > s["ec"] and en: s["en"], s["ec"] = en, r["ec"]
            if r["zc"] > s["zc"] and zh: s["zh"], s["zc"] = zh, r["zc"]
        else:
            segs.append(dict(t=r["t"], en=en, ec=r["ec"], zh=zh, zc=r["zc"]))
    with open(a.out, "w") as f:
        for s in segs:
            m, sec = divmod(int(s["t"]), 60); f.write(f"[{m:02d}:{sec:02d}] {s['en']}  ||  {s['zh']}\n")
    print(f"{a.video}: {n} frames, {len(segs)} subtitle lines -> {a.out}")


if __name__ == "__main__":
    main()
