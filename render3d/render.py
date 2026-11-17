"""3D Short renderer (Blender Cycles on CPU), split into stages so shots render in parallel.

  prep      voice (TTS) + word timings + sound mix + shot plan       -> work/plan.json, mix.wav
  shots     render this shard's shots: 3D frames -> graphics -> MP4 -> work/shotNN.mp4
  assemble  join shots, add the mix, loudness-normalise              -> final MP4
  all       everything locally

Quality presets (--quality):
  final    3D at 720x1280, 2 samples + denoise, 30 fps -> upscaled to 1080x1920 output
  preview  3D at 360x640, 2 samples, 15 fps            -> 540x960 output (fast check)

  python render3d/render.py all --short s002 --quality preview --out out/s002_preview.mp4
"""
import argparse
import importlib
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.append(os.path.join(ROOT, "render"))  # audio.py + sfx library live there

import numpy as np  # noqa: E402

import audio as A  # noqa: E402

QUALITY = {
    "final": dict(rw=720, rh=1280, width=1080, height=1920, fps=30, spp=2),
    "preview": dict(rw=360, rh=640, width=540, height=960, fps=15, spp=2),
}
AMBIENCE = {
    "day": [("wind", -38)], "night": [("crickets", -30), ("wind", -44)],
    "interior": [("room", -44)], "shop": [("room", -44)], "sepia": [("wind", -42)],
}


def load_short(name):
    return importlib.import_module(f"shorts.{name}")


def words_in(text):
    return [w for w in text.split() if A.norm(w)]


# ---------------------------------------------------------------- prep
def segment_starts(shots, words):
    counts = [len(words_in(s["text"])) for s in shots]
    total = sum(counts)
    if total != len(words):
        print(f"[warn] script has {total} words, TTS returned {len(words)}; scaling")
    starts, idx_ranges, cum = [], [], 0
    for n in counts:
        i0 = min(len(words) - 1, round(cum * len(words) / total))
        i1 = min(len(words), round((cum + n) * len(words) / total))
        starts.append(words[i0][0])
        idx_ranges.append((i0, i1))
        cum += n
    starts[0] = 0.0
    for i in range(1, len(starts)):
        starts[i] = max(starts[i] - 0.06, starts[i - 1] + 0.5)
    return starts, idx_ranges


def tts(short, text, work):
    pref = os.environ.get("TTS_ENGINE", "auto")
    if pref == "fake":  # silent placeholder voice for offline testing
        words, t = [], 0.3
        for w in text.split():
            words.append((t, t + 0.2, w))
            t += 0.25 + (0.15 if w[-1] in ",.?!" else 0)
        return np.zeros(int((t + 0.3) * A.SR), np.float32), words
    if pref in ("auto", "edge"):
        try:
            mp3 = os.path.join(work, "voice.mp3")
            words = A.tts_edge(text, mp3, short.VOICE, short.RATE)
            print("tts: edge")
            return A.decode(mp3), words
        except Exception as e:  # noqa: BLE001
            if pref == "edge":
                raise
            print(f"[warn] edge-tts failed ({type(e).__name__}: {e}); using Piper")
    model = os.environ.get("PIPER_MODEL", os.path.join(A.HERE, "voices", "en_US-ryan-high.onnx"))
    voice, words = A.tts_piper(short.SHOTS, work, model,
                               float(getattr(short, "PIPER_LENGTH_SCALE", 0.8)))
    print("tts: piper")
    return voice, words


def prep(args):
    short = load_short(args.short)
    q = dict(QUALITY[args.quality])
    work = args.work
    os.makedirs(work, exist_ok=True)
    text = " ".join(s["text"] for s in short.SHOTS)
    voice, words = tts(short, text, work)
    vdur = len(voice) / A.SR
    print(f"voice: {vdur:.1f}s, {len(words)} words, {len(words) / vdur * 60:.0f} WPM")
    starts, ranges = segment_starts(short.SHOTS, words)
    total = vdur + float(getattr(short, "TAIL", 0.6))
    ends = starts[1:] + [total]

    m = A.Mixer(total)
    m.whoosh = A.whoosh()
    m.chime = A.chime()
    m.vox = {}
    for tag, (txt, v, rate, pitch) in getattr(short, "VOCALS", {}).items():
        try:
            m.vox[tag] = A.vocal(txt, v, work, tag, rate, pitch)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] vocal {tag} failed: {e}")
            m.vox[tag] = np.zeros(int(0.3 * A.SR), np.float32)
    gens = {"wind": A.wind, "crickets": A.crickets, "room": A.room}
    shots = []
    for i, (seg, a, b, (i0, i1)) in enumerate(zip(short.SHOTS, starts, ends, ranges)):
        d = b - a
        rel = [(w0 - a, w1 - a, w) for w0, w1, w in words[i0:i1]]
        for name, g in AMBIENCE.get(seg.get("bg", "day"), []):
            x = gens[name](d + 0.1)
            fade = min(len(x) // 2, int(0.05 * A.SR))
            x[:fade] *= np.linspace(0, 1, fade)
            x[-fade:] *= np.linspace(1, 0, fade)
            m.add(x, a, g)
        if seg.get("audio"):
            seg["audio"](m, a, d, Cue(rel, d))
        if i and seg.get("cut", "whip") == "whip":
            m.add(m.whoosh, a - 0.12, -24)
        f0, f1 = round(a * q["fps"]), round(b * q["fps"])
        shots.append(dict(idx=i, f0=f0, f1=f1, words=rel))
    sfx = m.buf[: int(total * A.SR)]
    vpad = np.zeros(len(sfx), np.float32)
    vpad[: min(len(voice), len(vpad))] = voice[: len(vpad)]
    mix = vpad + sfx
    if getattr(short, "MUSIC", False):
        bed = A.music(total)[: len(sfx)] * 10 ** (-22 / 20)
        mix += A.duck(bed, vpad, -8)
    mix /= max(1.0, float(np.max(np.abs(mix))) / 0.89)
    A.write_wav(os.path.join(work, "mix.wav"), mix)

    loads = [0] * args.shards
    for sh in sorted(shots, key=lambda s: s["f1"] - s["f0"], reverse=True):
        k = loads.index(min(loads))
        sh["shard"] = k
        loads[k] += sh["f1"] - sh["f0"]
    plan = dict(short=args.short, quality=args.quality, shards=args.shards, shots=shots,
                words=words, total=total, **q)
    json.dump(plan, open(os.path.join(work, "plan.json"), "w"))
    print(f"plan: {len(shots)} shots, {round(total * q['fps'])} frames @ {q['fps']} fps, "
          f"shard loads {loads}")


class Cue:
    """Word lookup for one shot: c.w('hoof') -> seconds from the shot start."""

    def __init__(self, words, dur):
        self.words, self.dur = words, dur

    def w(self, word, nth=1, end=False, default=None):
        target = A.norm(word)
        k = 0
        for a, b, w in self.words:
            if A.norm(w) == target or A.norm(w).startswith(target):
                k += 1
                if k == nth:
                    return max(0.0, b if end else a)
        if default is not None:
            return default
        print(f"[warn] cue word {word!r} not found in shot; using middle")
        return self.dur / 2

    def t(self, v):
        """Accept seconds, a word cue 'w:hoof', 'w:hoof:2', or 'end-0.3'."""
        if isinstance(v, (int, float)):
            return float(v)
        if v.startswith("w:"):
            parts = v[2:].split(":")
            return self.w(parts[0], int(parts[1]) if len(parts) > 1 else 1)
        if v.startswith("end"):
            return self.dur + float(v[3:] or 0)
        raise ValueError(v)


class Ctx(Cue):
    """Passed to each shot's build(c): timing, overlays and screen anchors."""

    def __init__(self, words, dur, ov):
        super().__init__(words, dur)
        self.ov = ov
        self.anchor_objs = {}

    def anchor(self, obj, local=(0, 0, 0), name=None):
        name = name or f"{obj.name}@{local}"
        self.anchor_objs[name] = (obj, tuple(local))
        return name

    def _add(self, kind, t0, t1, **kw):
        t0 = self.t(t0)
        t1 = self.dur + 0.5 if t1 is None else self.t(t1)
        self.ov.add(kind, t0=t0, t1=t1, **kw)

    def pop(self, text, t0=0.0, t1=None, **kw):
        self._add("pop", t0, t1, text=text, **kw)

    def tag(self, text, at, t0=0.0, t1=None, **kw):
        self._add("tag", t0, t1, text=text, at=at, **kw)

    def icon(self, icon, at, t0=0.0, t1=None, **kw):
        self._add("icon", t0, t1, icon=icon, at=at, **kw)

    def badge(self, steps, t1=None, **kw):
        steps = [(self.t(a), b, c) for a, b, c in steps]
        self.ov.add("badge", steps=steps, t1=self.dur + 1 if t1 is None else self.t(t1), **kw)

    def meter(self, keys, t0=0.0, t1=None, **kw):
        keys = [(self.t(a), v) for a, v in keys]
        self._add("meter", t0, t1, keys=keys, **kw)

    def stamp(self, text, t0, t1=None, **kw):
        self._add("stamp", t0, t1, text=text, **kw)

    def card(self, text, t0=0.0, t1=None, **kw):
        self._add("card", t0, t1, text=text, **kw)

    def mark(self, mark, t0, t1=None, **kw):
        self._add("mark", t0, t1, mark=mark, **kw)

    def flash(self, t0, **kw):
        self._add("flash", t0, None, **kw)

    def vignette(self, t0=0.0, t1=None, **kw):
        self._add("vignette", t0, t1, **kw)


# ---------------------------------------------------------------- one shot (Blender)
def render_shot(plan, idx, work):
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    from PIL import Image

    import kit as K
    import overlay as O

    short = load_short(plan["short"])
    seg = short.SHOTS[idx]
    sh = plan["shots"][idx]
    fps, W, H = plan["fps"], plan["width"], plan["height"]
    n = max(1, sh["f1"] - sh["f0"])
    dur = n / fps
    t_start = time.time()

    sc = K.new_scene(plan["rw"], plan["rh"], fps, plan["spp"])
    ov = O.Overlay(W, H, fps)
    ctx = Ctx(sh["words"], dur, ov)
    seg["build"](ctx)
    sc.frame_end = n
    fdir = os.path.join(work, f"frames{idx:02d}")
    os.makedirs(fdir, exist_ok=True)
    sc.render.filepath = os.path.join(fdir, "f_")
    t_build = time.time()
    bpy.ops.render.render(animation=True)
    t_render = time.time()

    cam = sc.camera
    for name, (obj, local) in ctx.anchor_objs.items():
        seq = []
        for fr in range(1, n + 1):
            sc.frame_set(fr)
            p = world_to_camera_view(sc, cam, obj.matrix_world @ Vector(local))
            seq.append((p.x, 1 - p.y, p.z > 0))
        ov.anchors[name] = seq

    gold = set(getattr(short, "GOLD_WORDS", set()))
    groups = O.caption_groups(plan["words"], gold)
    out = os.path.join(work, f"shot{idx:02d}.mp4")
    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
         "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
         "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    cut_in = seg.get("cut", "whip") == "whip" and idx > 0
    nxt = short.SHOTS[idx + 1] if idx + 1 < len(short.SHOTS) else None
    cut_out = nxt is not None and nxt.get("cut", "whip") == "whip"
    wdir = seg.get("whip_dir", 1 if idx % 2 else -1)
    wn = max(2, round(0.13 * fps))
    for i in range(n):
        img = Image.open(os.path.join(fdir, f"f_{i + 1:04d}.png")).convert("RGB")
        if img.size != (W, H):
            img = img.resize((W, H), Image.LANCZOS)
        if cut_in and i < wn:
            img = O.whip(img, (1 - i / wn) ** 1.5, wdir)
        if cut_out and i >= n - wn:
            img = O.whip(img, ((i - (n - wn)) / wn) ** 1.5, -wdir)
        frame = img.convert("RGBA")
        t = i / fps
        ov.draw(frame, t, i)
        O.draw_caption(frame, groups, (sh["f0"] + i) / fps, W, H, getattr(short, "CAPTION_Y", 0.6))
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    ff.wait()
    if ff.returncode:
        raise RuntimeError("ffmpeg failed")
    t_done = time.time()
    print(f"shot {idx:02d}: {n} frames | build {t_build - t_start:.1f}s | 3D "
          f"{t_render - t_build:.1f}s ({(t_render - t_build) / n:.2f}s/frame) | graphics "
          f"{t_done - t_render:.1f}s", flush=True)
    if not os.environ.get("KEEP_FRAMES"):
        for fn in os.listdir(fdir):
            os.remove(os.path.join(fdir, fn))
        os.rmdir(fdir)
    return out


def shots(args):
    plan = json.load(open(os.path.join(args.work, "plan.json")))
    mine = [s["idx"] for s in plan["shots"]
            if (args.shard is None or s["shard"] == args.shard)
            and (not args.only or s["idx"] in args.only)]
    for idx in mine:  # one process per shot keeps memory clean
        r = subprocess.run([sys.executable, __file__, "shot", "--idx", str(idx), "--work",
                            args.work], capture_output=True, text=True)
        tail = [ln for ln in r.stdout.splitlines() if ln.startswith(("shot ", "[warn]"))]
        print("\n".join(tail), flush=True)
        if r.returncode:
            print(r.stdout[-3000:], r.stderr[-3000:])
            raise SystemExit(f"shot {idx} failed")


def check(args):
    """Build every shot's scene without rendering, to catch script errors in seconds."""
    import traceback

    import kit as K
    import overlay as O
    short = load_short(args.short)
    bad = 0
    for i, seg in enumerate(short.SHOTS):
        words = [(0.2 + 0.3 * k, 0.4 + 0.3 * k, w) for k, w in enumerate(seg["text"].split())]
        dur = 0.4 + 0.3 * len(words)
        K.new_scene(64, 112, 15, 1)
        try:
            seg["build"](Ctx(words, dur, O.Overlay(64, 112, 15)))
            m = A.Mixer(dur + 1)
            m.whoosh = m.chime = np.zeros(10, np.float32)
            m.vox = {k: np.zeros(10, np.float32) for k in getattr(short, "VOCALS", {})}
            if seg.get("audio"):
                seg["audio"](m, 0.0, dur, Cue(words, dur))
            print(f"ok   shot {i:02d}")
        except Exception:  # noqa: BLE001
            bad += 1
            print(f"FAIL shot {i:02d}\n{traceback.format_exc()}")
    if bad:
        raise SystemExit(f"{bad} shot(s) failed")


# ---------------------------------------------------------------- assemble
def assemble(args):
    plan = json.load(open(os.path.join(args.work, "plan.json")))
    lst = os.path.join(args.work, "shots.txt")
    with open(lst, "w") as f:
        for s in plan["shots"]:
            f.write("file '%s'\n" % os.path.abspath(os.path.join(args.work,
                                                                  "shot%02d.mp4" % s["idx"])))
    silent = os.path.join(args.work, "video.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", silent], check=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent,
                    "-i", os.path.join(args.work, "mix.wav"), "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-movflags", "+faststart", "-shortest", args.out],
                   check=True)
    print("done:", args.out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["prep", "shots", "shot", "assemble", "all", "check"])
    ap.add_argument("--short", default="s002")
    ap.add_argument("--quality", choices=list(QUALITY), default="final")
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--shard", type=int, default=None)
    ap.add_argument("--idx", type=int, default=None)
    ap.add_argument("--only", type=lambda s: [int(x) for x in s.split(",")], default=None,
                    help="render only these shot numbers (comma-separated)")
    ap.add_argument("--work", default="out/work")
    ap.add_argument("--out", default="out/short.mp4")
    args = ap.parse_args()
    if args.stage == "shot":
        plan = json.load(open(os.path.join(args.work, "plan.json")))
        render_shot(plan, args.idx, args.work)
        return
    if args.stage == "check":
        check(args)
        return
    if args.stage in ("prep", "all"):
        prep(args)
    if args.stage in ("shots", "all"):
        shots(args)
    if args.stage in ("assemble", "all") and not args.only:
        assemble(args)


if __name__ == "__main__":
    main()
