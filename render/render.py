"""Render a Short to MP4: TTS voice + word captions + music + paper-craft scenes.

Usage:
  python render/render.py --short s001 --width 2160 --height 3840 --out out/short.mp4
  python render/render.py --short s001 --width 270 --height 480 --fps 12 --out preview.mp4
"""
import argparse
import asyncio
import importlib
import json
import math
import multiprocessing as mp
import os
import re
import subprocess
import sys
import wave

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E  # noqa: E402

SR = 44100


# ---------------------------------------------------------------- voice
def tts(text, mp3_path, voice, rate):
    import edge_tts

    async def run():
        try:
            comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
        except TypeError:  # older edge-tts: word boundaries are the default
            comm = edge_tts.Communicate(text, voice, rate=rate)
        words = []
        with open(mp3_path, "wb") as f:
            async for ch in comm.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    st = ch["offset"] / 1e7
                    words.append((st, st + ch["duration"] / 1e7, ch["text"]))
        return words

    return asyncio.run(run())


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


# ---------------------------------------------------------------- music + sfx
def pluck(freq, dur, amp=1.0):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 7.0)
    sig = sum(np.sin(2 * np.pi * freq * h * t) / h ** 1.3 for h in range(1, 6))
    return sig * env * amp


def music(duration, bpm=128):
    out = np.zeros(int((duration + 2) * SR), np.float32)
    beat = 60 / bpm
    eighth = beat / 2
    # G  C  D  G  (banjo-ish arpeggios over a walking bass)
    chords = [(196.0, 246.9, 293.7, 392.0), (261.6, 329.6, 392.0, 523.3),
              (293.7, 370.0, 440.0, 587.3), (196.0, 246.9, 293.7, 392.0)]
    bass = [98.0, 130.8, 146.8, 98.0]
    pattern = [0, 2, 1, 3, 2, 1, 3, 2]
    t = 0.0
    bar = 0
    while t < duration + 1:
        ch = chords[bar % 4]
        for i in range(8):
            st = int((t + i * eighth) * SR)
            n = pluck(ch[pattern[i]], 0.6, 0.35 if i % 2 else 0.5)
            out[st:st + len(n)] += n[: max(0, len(out) - st)]
            if i % 4 == 0:
                b = pluck(bass[bar % 4] if i == 0 else bass[bar % 4] * 1.5, 0.9, 0.8)
                out[st:st + len(b)] += b[: max(0, len(out) - st)]
        t += 8 * eighth
        bar += 1
    out /= np.max(np.abs(out)) + 1e-9
    return out


def whoosh(dur=0.22):
    n = int(dur * SR)
    rng = np.random.default_rng(3)
    x = rng.normal(0, 1, n).astype(np.float32)
    x = np.convolve(x, np.ones(30) / 30, mode="same")
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return x * env / (np.max(np.abs(x)) + 1e-9)


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- timing
def norm(w):
    return re.sub(r"[^a-z0-9$¢]", "", w.lower())


def segment_starts(segments, words):
    counts = [len([w for w in seg["text"].split() if norm(w)]) for seg in segments]
    total = sum(counts)
    if total != len(words):
        print(f"[warn] script has {total} words, TTS returned {len(words)}; scaling")
    starts, cum = [], 0
    for n in counts:
        idx = min(len(words) - 1, round(cum * len(words) / total))
        starts.append(words[idx][0])
        cum += n
    starts[0] = 0.0
    for i in range(1, len(starts)):
        starts[i] = max(starts[i] - 0.05, starts[i - 1] + 0.4)
    return starts


# ---------------------------------------------------------------- video
def render_shot(job):
    (short_name, idx, f0, f1, t_start, t_end, W, H, fps, words, out) = job
    short = importlib.import_module(f"shorts.{short_name}")
    seg = short.SEGMENTS[idx]
    S = W / E.BASE_W
    dur = t_end - t_start
    gold_words = set(getattr(short, "GOLD_WORDS", []))
    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264",
         "-preset", os.environ.get("X264_PRESET", "fast"), "-crf", "18",
         "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    wi = 0
    for f in range(f0, f1):
        tg = f / fps
        tl = tg - t_start
        img = E.sky(seg.get("bg", "day"), W, H).copy()
        c = E.Canvas(img, S)
        seg["draw"](c, tl, dur)
        img = E.finish(img)
        while wi + 1 < len(words) and words[wi + 1][0] <= tg:
            wi += 1
        if words and words[wi][0] <= tg:
            nxt = words[wi + 1][0] if wi + 1 < len(words) else words[wi][1] + 0.5
            if tg < max(nxt, words[wi][1] + 0.15) or tg < words[wi][0] + 0.6:
                raw = words[wi][2]
                txt = re.sub(r"^[\"'(]+|[\"'),.!?;:]+$", "", raw)
                gold = (norm(raw) in gold_words or any(ch.isdigit() for ch in raw)
                        or "$" in raw)
                E.draw_caption(img, S, txt, tg - words[wi][0], gold)
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--short", default="s001")
    ap.add_argument("--width", type=int, default=2160)
    ap.add_argument("--height", type=int, default=3840)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", default="out/short.mp4")
    ap.add_argument("--work", default="out/work")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args()

    os.makedirs(args.work, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    short = importlib.import_module(f"shorts.{args.short}")
    text = " ".join(s["text"] for s in short.SEGMENTS)

    # 1. voice + word timings
    mp3 = os.path.join(args.work, "voice.mp3")
    words = tts(text, mp3, short.VOICE, short.RATE)
    voice = decode(mp3)
    vdur = len(voice) / SR
    print(f"voice: {vdur:.1f}s, {len(words)} words, {len(words) / vdur * 60:.0f} WPM")
    json.dump(words, open(os.path.join(args.work, "words.json"), "w"), indent=0)

    starts = segment_starts(short.SEGMENTS, words)
    total = vdur + 0.7
    ends = starts[1:] + [total]

    # 2. audio mix: voice + music bed (-24 dB) + whooshes on cuts
    bed = music(total)[: int(total * SR)]
    mixd = np.zeros(int(total * SR), np.float32)
    mixd[: len(voice)] += voice
    mixd[: len(bed)] += bed * 10 ** (-24 / 20) * 2.2
    wh = whoosh()
    for st in starts[1:]:
        i = int(st * SR)
        seg = wh[: max(0, len(mixd) - i)]
        mixd[i:i + len(seg)] += seg * 10 ** (-30 / 20)
    mixd /= max(1.0, np.max(np.abs(mixd)) / 0.89)
    wav = os.path.join(args.work, "mix.wav")
    write_wav(wav, mixd)

    # 3. video, one shot per worker
    jobs = []
    for i, (a, b) in enumerate(zip(starts, ends)):
        f0, f1 = round(a * args.fps), round(b * args.fps)
        jobs.append((args.short, i, f0, f1, f0 / args.fps, f1 / args.fps, args.width,
                     args.height, args.fps, words, os.path.join(args.work, f"shot{i:02d}.mp4")))
    with mp.get_context("spawn").Pool(args.jobs) as pool:
        for done in pool.imap_unordered(render_shot, jobs):
            print("rendered", os.path.basename(done), flush=True)

    lst = os.path.join(args.work, "shots.txt")
    with open(lst, "w") as f:
        for j in jobs:
            f.write(f"file '{os.path.abspath(j[-1])}'\n")
    silent = os.path.join(args.work, "video.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", silent], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-movflags", "+faststart", "-shortest", args.out],
                   check=True)
    print("done:", args.out)


if __name__ == "__main__":
    main()
