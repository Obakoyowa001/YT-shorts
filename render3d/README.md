# 3D Short renderer (Blender, cloud)

Renders a Short as real 3D animation on GitHub's servers, using **Blender as a Python module** (`bpy`, the Cycles renderer on CPU). Nothing renders on your own computer, so everything can be run from a phone.

The target look is described in [`analysis/04_reference_style_3d.md`](../analysis/04_reference_style_3d.md): toy-figure characters, a reused hero set, a camera that keeps moving, whip-pan transitions, pop-up graphics and karaoke captions.

## How a render runs

1. **Prep** (1 job): narrator voice (Microsoft Edge neural voice, with an offline Piper voice as backup), word timings, sound effects and ambience, giving `mix.wav` and a shot plan.
2. **Shots** (several parallel jobs): each job builds its shots in Blender, renders the 3D frames, upscales them, then draws the graphics layer (captions, pop-up words, labels, badges, meters, stamps and whip-pan blur) and encodes MP4 segments.
3. **Assemble** (1 job): joins the shots, adds the audio, normalises loudness to −14 LUFS, and publishes the MP4 to the repo's **Releases** page (one release per Short and quality, for example `s002-preview`, replaced on every render) so it plays straight in a browser.

**Watch the latest render:** https://github.com/Obakoyowa001/YT-shorts/releases

| Quality | 3D render | Output | FPS | Shards | Use |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `preview` | 360×640, 2 samples | 540×960 | 15 | 4 | Check staging and timing. Cheap. |
| `final` | 720×1280, 2 samples + denoise | 1080×1920 | 30 | 16 | The video you upload. |

## Triggering

- **Automatic preview:** any push that changes `render3d/**`.
- **Final render:** start the commit message with `[final]`.
- **Manual:** Actions → *Render Short (3D)* → *Run workflow*, then choose the Short and quality. This only works once the workflow is on `main`.

> **GitHub minutes:** this repo is public, so GitHub Actions minutes on its standard machines are free and unlimited. A preview of a one-minute Short takes roughly 30 minutes of wall time; a final render takes longer (it is split across 16 parallel machines). If the repo ever goes private again, renders count against the private-repo minute allowance.

## Files

| File | What it is |
| :--- | :--- |
| `kit.py` | The 3D toolkit: materials (toy plastic, cobblestones, stripes, plaid, polka dots), primitives, 3D text, the `Toy` character class (eyes, lids, brows, mouths, arms, legs, walk, hop, talk, blink), the cast (`boss`, `gus`, `mo`, `pike`, `townsfolk`), sets (`street`, `facade`, `room`), props, lighting presets (`light_day`, `light_night`, `light_amber`) and the `Cam` camera rig. |
| `overlay.py` | The 2D graphics layer drawn on top of the frames. |
| `render.py` | The prep → shots → assemble pipeline. |
| `shorts/s002.py` | Short #002, *What If Everyone Printed Money?* |
| `fonts/` | Bundled open-licence fonts (see `fonts/LICENSES.md`). |

Sound effects and the TTS helpers are shared with the old 2D renderer in `render/` (`render/audio.py`, `render/sfx/`).

## Making a new Short

Copy `shorts/s002.py` to `shorts/s003.py`. Each entry in `SHOTS` is one shot:

```python
dict(text="narration for this shot", bg="day", build=s01, audio=a01, cut="whip")
```

`build(c)` builds and animates the scene. Times are in seconds from the start of the shot, and `c.w("word")` returns when a word is spoken:

```python
def s01(c):
    square()                                   # town-square set + daylight
    g = K.gus((0, 0.8, 0), yaw=0)              # a character
    g.expr(c.w("money"), eyes="wide", mouth="grin")
    g.walk(0.2, c.dur, (2, 0.8, 0), yaw=-90)
    cam = K.Cam(lens=30, fstop=1.8)            # lower fstop = blurrier background
    cam.at(0, (0, -3.5, 1.2), (0, 0.8, 1.1))   # position, look-at point
    cam.at(c.dur, (0, -2.8, 1.2), (0, 0.8, 1.2))
    cam.drift(0, c.dur)                        # handheld float
    c.pop("$1,000,000", "w:money", at=(0.5, 0.2))          # big pop-up word
    c.tag("GUS", c.anchor(g.top), "w:gus")                 # label that follows Gus
    c.icon("?", c.anchor(g.top), 1.0)                      # ? ! heart sweat bulb zzz $
    c.badge([(0, "1", "yellow"), ("w:two", "2", "green")]) # counter badge
    c.meter([(0, 0.1), (c.dur, 0.9)], label="TENSION")     # filling meter
    c.stamp("NO TRICK", "w:nothing")                       # rubber stamp
    c.card("MEANWHILE...", 0)                              # slide-in title card
```

`audio(m, T, d, c)` cues sounds at absolute time `T + offset`, for example `m.sfx("coins", T + c.w("cash"))`. Sound names are listed in `render/audio.py` (`LIB`).

## Local testing

```bash
pip install -r render3d/requirements.txt
TTS_ENGINE=fake python render3d/render.py all --short s002 --quality preview --out out/test.mp4
```

`TTS_ENGINE=fake` skips the voice so it runs offline. `--only 3,4` renders just those shots (after a `prep`).
