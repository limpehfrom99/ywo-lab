"""Turn a trading video (RedNote / YouTube / Instagram download or a screen recording) into notes Claude can read:
a timestamped transcript of the speech and contact sheets of frames (charts, on-screen rules, burned-in subtitles).

python3 video_notes.py VIDEO [OUT_DIR] [--every SECONDS]
Speech: SenseVoice (Mandarin, English, Cantonese, Japanese, Korean; auto-detected) via sherpa-onnx, fully offline,
cut into utterances by Silero VAD. Models live in /home/claude/models (see setup() for where they come from).
Frames: one every N seconds (default: enough for ~100 frames, at least every 2 s), 3x3 contact sheets with timestamps.
Single full-size frames: python3 video_notes.py VIDEO OUT --frame 83.5  (seconds)
"""
import os, sys, json, subprocess, argparse
import numpy as np

MODELS = "/home/claude/models"
SV = os.path.join(MODELS, "sensevoice")
VAD = os.path.join(MODELS, "silero_vad.onnx")
REL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models"


def setup():
    """Download the speech models if the container was reset (GitHub release assets; pip install sherpa-onnx)."""
    os.makedirs(MODELS, exist_ok=True)
    if not os.path.exists(VAD):
        subprocess.run(["curl", "-sSL", "-o", VAD, f"{REL}/silero_vad.onnx"], check=True)
    if not os.path.exists(os.path.join(SV, "model.int8.onnx")):
        tb = os.path.join(MODELS, "sv.tar.bz2"); d = "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
        subprocess.run(["curl", "-sSL", "-o", tb, f"{REL}/{d}.tar.bz2"], check=True)
        subprocess.run(["tar", "-xjf", tb, "-C", MODELS, f"{d}/model.int8.onnx", f"{d}/tokens.txt"], check=True)
        os.rename(os.path.join(MODELS, d), SV); os.remove(tb)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def audio(path, sr=16000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def fmt(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def transcribe(samples, sr=16000):
    import sherpa_onnx
    rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(model=os.path.join(SV, "model.int8.onnx"),
                                                         tokens=os.path.join(SV, "tokens.txt"), num_threads=2,
                                                         use_itn=True, language="auto")
    cfg = sherpa_onnx.VadModelConfig(); cfg.silero_vad.model = VAD; cfg.silero_vad.min_silence_duration = 0.4
    cfg.silero_vad.max_speech_duration = 25; cfg.sample_rate = sr
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=120)
    lines = []; w = cfg.silero_vad.window_size

    def drain():
        while not vad.empty():
            seg = vad.front; s = rec.create_stream(); s.accept_waveform(sr, np.asarray(seg.samples, dtype=np.float32))
            rec.decode_stream(s); txt = s.result.text.strip()
            if txt: lines.append((seg.start / sr, txt))
            vad.pop()
    for i in range(0, len(samples), w):
        vad.accept_waveform(samples[i:i + w]); drain()
    vad.flush(); drain()
    return lines


def size(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]; return int(s["width"]), int(s["height"])


def frames(path, out, every, dur):
    """Contact sheets: landscape video -> 3x3 frames 640 px wide; phone (portrait) video -> 2x2 frames 540 px wide."""
    import cv2
    w0, h0 = size(path); portrait = h0 > w0
    W, cols = (540, 2) if portrait else (640, 3); per = cols * cols
    fdir = os.path.join(out, "frames"); os.makedirs(fdir, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vf", f"fps=1/{every},scale={W}:-2", "-q:v", "3",
                    os.path.join(fdir, "f_%04d.jpg")], check=True)
    files = sorted(f for f in os.listdir(fdir) if f.endswith(".jpg"))
    sdir = os.path.join(out, "sheets"); os.makedirs(sdir, exist_ok=True)
    sheets = []
    for k in range(0, len(files), per):
        imgs = []
        for j, f in enumerate(files[k:k + per]):
            im = cv2.imread(os.path.join(fdir, f)); t = (k + j) * every + every / 2
            cv2.rectangle(im, (0, 0), (112, 26), (0, 0, 0), -1)
            cv2.putText(im, fmt(t), (5, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            imgs.append(im)
        h, w = imgs[0].shape[:2]
        imgs = [cv2.resize(i, (w, h)) for i in imgs] + [np.zeros((h, w, 3), np.uint8)] * (per - len(imgs))
        grid = np.vstack([np.hstack(imgs[r * cols:r * cols + cols]) for r in range(cols)])
        p = os.path.join(sdir, f"sheet_{k // per + 1:02d}.jpg"); cv2.imwrite(p, grid, [cv2.IMWRITE_JPEG_QUALITY, 85]); sheets.append(p)
    return len(files), sheets


def one_frame(path, out, t):
    p = os.path.join(out, f"frame_{t:07.1f}s.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", path, "-frames:v", "1", p], check=True)
    return p


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("out", nargs="?")
    ap.add_argument("--every", type=float, default=None); ap.add_argument("--frame", type=float, default=None)
    a = ap.parse_args()
    out = a.out or os.path.splitext(a.video)[0] + "_notes"; os.makedirs(out, exist_ok=True)
    if a.frame is not None: print(one_frame(a.video, out, a.frame)); return
    setup()
    dur = duration(a.video)
    every = a.every or max(2.0, round(dur / 100, 1))
    lines = transcribe(audio(a.video))
    with open(os.path.join(out, "transcript.txt"), "w", encoding="utf-8") as f:
        for t, txt in lines: f.write(f"[{fmt(t)}] {txt}\n")
    n, sheets = frames(a.video, out, every, dur)
    print(f"{dur:.0f}s video: {len(lines)} speech segments -> {out}/transcript.txt; {n} frames every {every}s -> {len(sheets)} sheets in {out}/sheets")


if __name__ == "__main__":
    main()
