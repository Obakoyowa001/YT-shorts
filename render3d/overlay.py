"""2D motion-graphics layer drawn on top of the rendered 3D frames (Pillow + numpy).

Everything is drawn at the final output size, so text stays sharp even when the 3D frames
were rendered smaller and upscaled.

Positions are either normalised (x, y) in 0..1 of the frame, or the name of an anchor (a
3D point that the Blender stage projected to the screen for every frame).
Times are seconds from the start of the shot.
"""
import math
import os
import re
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")

YELLOW = (255, 214, 10)
YELLOW_D = (150, 96, 0)
WHITE = (255, 255, 255)
INK = (24, 18, 16)
RED = (226, 54, 48)
GREEN = (56, 190, 90)
PURPLE = (150, 96, 230)
BLUE = (70, 160, 240)
PINK = (250, 90, 140)
COLORS = dict(yellow=YELLOW, white=WHITE, red=RED, green=GREEN, purple=PURPLE, blue=BLUE,
              pink=PINK)


@lru_cache(maxsize=64)
def font(size, name="Montserrat-ExtraBold"):
    return ImageFont.truetype(os.path.join(FONT_DIR, name + ".ttf"), int(size))


def ease_out_back(x, s=1.9):
    x = min(1.0, max(0.0, x)) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def pop_scale(t, t0, t1, din=0.2, dout=0.12):
    if t < t0 or t > t1:
        return 0.0
    if t < t0 + din:
        return max(0.0, ease_out_back((t - t0) / din))
    if t > t1 - dout:
        return max(0.0, (t1 - t) / dout)
    return 1.0


def col(c):
    return COLORS.get(c, c) if isinstance(c, str) else c


# ---------------------------------------------------------------- sprite helpers
def _text_sprite(txt, size, fill, stroke=INK, stroke_w=None, fnt="Montserrat-ExtraBold",
                 extrude=0, extrude_col=None, shadow=True):
    """Render a text sprite (RGBA) with outline, optional 3D-style extrusion and soft shadow."""
    f = font(size, fnt)
    sw = int(size * 0.09) if stroke_w is None else stroke_w
    l, t, r, b = f.getbbox(txt, stroke_width=sw)
    pad = int(size * 0.35) + extrude
    W, H = r - l + pad * 2, b - t + pad * 2
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ox, oy = pad - l, pad - t
    if extrude:
        ec = extrude_col or tuple(int(c * 0.55) for c in fill[:3])
        for i in range(extrude, 0, -1):
            d.text((ox, oy + i), txt, font=f, fill=ec, stroke_width=sw, stroke_fill=stroke)
    d.text((ox, oy), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        a = img.split()[3].point(lambda v: int(v * 0.55))
        sh.putalpha(a)
        sh = sh.filter(ImageFilter.GaussianBlur(size * 0.06))
        out = Image.new("RGBA", img.size, (0, 0, 0, 0))
        out.alpha_composite(sh, (0, int(size * 0.06)))
        out.alpha_composite(img)
        img = out
    return img


def _paste(frame, sprite, cx, cy, scale=1.0, angle=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    w, h = sprite.size
    s = sprite
    if abs(scale - 1) > 1e-3:
        s = s.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BICUBIC)
    if angle:
        s = s.rotate(angle, Image.BICUBIC, expand=True)
    if alpha < 1:
        a = s.split()[3].point(lambda v: int(v * alpha))
        s = s.copy()
        s.putalpha(a)
    frame.alpha_composite(s, (int(cx - s.size[0] / 2), int(cy - s.size[1] / 2)))


@lru_cache(maxsize=256)
def _cached_text(txt, size, fill, stroke, fnt, extrude, shadow):
    return _text_sprite(txt, size, fill, stroke, None, fnt, extrude, None, shadow)


def _round_rect_sprite(w, h, r, fill, outline=INK, ow=6):
    img = Image.new("RGBA", (w + ow * 2 + 8, h + ow * 2 + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((ow + 4, ow + 4, ow + 4 + w, ow + 4 + h), r, fill=fill, outline=outline,
                        width=ow)
    return img


# ---------------------------------------------------------------- overlay items
class Overlay:
    """Collects overlay items for one shot and draws them on frames."""

    def __init__(self, W, H, fps):
        self.W, self.H, self.fps = W, H, fps
        self.items = []
        self.anchors = {}  # name -> list of (x, y, visible) per frame (normalised)

    def pos(self, at, frame_idx, dx=0.0, dy=0.0):
        if isinstance(at, str):
            seq = self.anchors.get(at)
            if not seq:
                return self.W * 0.5, self.H * 0.3
            x, y, _ = seq[min(frame_idx, len(seq) - 1)]
            return (x + dx) * self.W, (y + dy) * self.H
        return (at[0] + dx) * self.W, (at[1] + dy) * self.H

    def add(self, kind, **kw):
        kw["kind"] = kind
        self.items.append(kw)

    # ---- drawing
    def draw(self, frame, t, fi):
        for it in sorted(self.items, key=lambda i: i["kind"] not in ("grade", "vignette")):
            getattr(self, "_" + it["kind"])(frame, t, fi, it)

    def _grade(self, fr, t, fi, it):
        if not it["t0"] <= t <= it["t1"]:
            return
        if it.get("mode") == "sepia":
            a = np.asarray(fr).astype(np.float32)
            g = a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11
            out = a.copy()
            out[..., 0] = np.clip(g * 1.08 + 18, 0, 255)
            out[..., 1] = np.clip(g * 0.92 + 8, 0, 255)
            out[..., 2] = np.clip(g * 0.72, 0, 255)
            fr.paste(Image.fromarray(out.astype(np.uint8), "RGBA"))

    def _pop(self, fr, t, fi, it):
        s = pop_scale(t, it["t0"], it["t1"])
        if not s:
            return
        size = int(it.get("size", 0.13) * self.W)
        spr = _cached_text(it["text"], size, col(it.get("color", "yellow")), INK,
                           it.get("font", "LuckiestGuy"), max(2, size // 14), True)
        x, y = self.pos(it.get("at", (0.5, 0.2)), fi)
        wob = math.sin((t - it["t0"]) * 3.0) * it.get("wobble", 2.0)
        _paste(fr, spr, x, y, s, it.get("angle", 0) + wob)

    def _tag(self, fr, t, fi, it):
        """Yellow label with a pointer toward an anchor (or a fixed position)."""
        s = pop_scale(t, it["t0"], it["t1"])
        if not s:
            return
        size = int(it.get("size", 0.042) * self.W)
        f = font(size, "Montserrat-Black")
        lines = it["text"].split("\n")
        tw = max(f.getbbox(ln)[2] for ln in lines)
        th = int(size * 1.15 * len(lines))
        pw, ph = tw + size, th + int(size * 0.6)
        x, y = self.pos(it["at"], fi, *it.get("offset", (0.0, -0.08)))
        layer = Image.new("RGBA", (pw + size * 3, ph + size * 3), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        ox, oy = size * 1.5, size * 1.5
        d.rounded_rectangle((ox, oy, ox + pw, oy + ph), size * 0.25, fill=col(it.get("color",
                                                                                     "yellow")),
                            outline=INK, width=max(3, size // 9))
        tip = it.get("point", "down")
        cx = ox + pw / 2
        if tip == "down":
            d.polygon([(cx - size * 0.4, oy + ph - 2), (cx + size * 0.4, oy + ph - 2),
                       (cx, oy + ph + size * 0.7)], fill=col(it.get("color", "yellow")),
                      outline=INK)
        elif tip == "left":
            d.polygon([(ox + 2, oy + ph / 2 - size * 0.4), (ox + 2, oy + ph / 2 + size * 0.4),
                       (ox - size * 0.7, oy + ph / 2)], fill=col(it.get("color", "yellow")),
                      outline=INK)
        for i, ln in enumerate(lines):
            lw = f.getbbox(ln)[2]
            d.text((ox + (pw - lw) / 2, oy + size * 0.3 + i * size * 1.15 - f.getbbox(ln)[1] * 0.5),
                   ln, font=f, fill=INK)
        _paste(fr, layer, x, y, s, it.get("angle", 0))

    def _icon(self, fr, t, fi, it):
        s = pop_scale(t, it["t0"], it["t1"])
        if not s:
            return
        kind = it["icon"]
        size = int(it.get("size", 0.085) * self.W)
        bob = math.sin((t - it["t0"]) * 6) * size * 0.06
        x, y = self.pos(it["at"], fi, *it.get("offset", (0.0, -0.05)))
        if kind in ("?", "!", "?!", "zzz", "$", "!!"):
            spr = _cached_text(kind, size, col(it.get("color", "yellow")), INK, "LuckiestGuy",
                               max(2, size // 12), True)
        else:
            spr = _icon_sprite(kind, size)
        _paste(fr, spr, x, y + bob, s, math.sin((t - it["t0"]) * 4) * 6)

    def _badge(self, fr, t, fi, it):
        """Round counter badge. steps: [(t, text, colour), ...]."""
        cur = None
        for st in it["steps"]:
            if t >= st[0]:
                cur = st
        if cur is None or t > it.get("t1", 1e9):
            return
        size = int(it.get("size", 0.11) * self.W)
        since = t - cur[0]
        s = 1.0 + 0.25 * max(0.0, 1 - since / 0.15)
        x, y = self.pos(it.get("at", (0.5, 0.12)), fi)
        spr = _badge_sprite(cur[1], size, col(cur[2]))
        _paste(fr, spr, x, y, s)

    def _meter(self, fr, t, fi, it):
        """Vertical meter (e.g. TENSION). keys: [(t, value 0..1), ...]."""
        if t < it["t0"] or t > it["t1"]:
            return
        keys = it["keys"]
        v = keys[0][1]
        for (ta, va), (tb, vb) in zip(keys, keys[1:]):
            if ta <= t <= tb:
                v = va + (vb - va) * ease_out((t - ta) / max(1e-3, tb - ta))
                break
            if t > tb:
                v = vb
        W = self.W
        x, y = self.pos(it.get("at", (0.88, 0.32)), fi)
        mw, mh = int(W * 0.05), int(W * 0.34)
        layer = Image.new("RGBA", (mw + 80, mh + 160), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        ox, oy = 40, 70
        lab = font(int(W * 0.028), "Montserrat-Black")
        label = it.get("label", "TENSION")
        lw = lab.getbbox(label)[2]
        d.text((ox + mw / 2 - lw / 2, 20), label, font=lab, fill=WHITE, stroke_width=3,
               stroke_fill=INK)
        d.rounded_rectangle((ox, oy, ox + mw, oy + mh), mw // 2, fill=(250, 250, 250),
                            outline=INK, width=6)
        fill_c = GREEN if v < 0.4 else (YELLOW if v < 0.7 else RED)
        fh = int((mh - 16) * v)
        if fh > 4:
            d.rounded_rectangle((ox + 8, oy + mh - 8 - fh, ox + mw - 8, oy + mh - 8), mw // 2 - 8,
                                fill=fill_c)
        for i in range(1, 5):
            yy = oy + mh * i / 5
            d.line((ox + 6, yy, ox + mw * 0.45, yy), fill=INK, width=4)
        s = pop_scale(t, it["t0"], it["t1"], 0.2, 0.15)
        _paste(fr, layer, x, y, s)

    def _stamp(self, fr, t, fi, it):
        if t < it["t0"] or t > it["t1"]:
            return
        k = (t - it["t0"]) / 0.14
        s = 2.2 - 1.2 * ease_out(k) if k < 1 else 1.0
        a = min(1.0, k * 2)
        size = int(it.get("size", 0.09) * self.W)
        spr = _stamp_sprite(it["text"], size, col(it.get("color", "red")))
        x, y = self.pos(it.get("at", (0.5, 0.35)), fi)
        _paste(fr, spr, x, y, s, it.get("angle", 12), a)

    def _card(self, fr, t, fi, it):
        s = pop_scale(t, it["t0"], it["t1"], 0.18, 0.15)
        if not s:
            return
        size = int(it.get("size", 0.075) * self.W)
        spr = _cached_text(it["text"], size, col(it.get("color", "purple")), WHITE,
                           "LuckiestGuy", max(2, size // 14), True)
        x, y = self.pos(it.get("at", (0.5, 0.16)), fi)
        slide = (1 - ease_out((t - it["t0"]) / 0.25)) * -self.W * 0.6
        _paste(fr, spr, x + slide, y, 1.0, it.get("angle", -4))

    def _mark(self, fr, t, fi, it):
        s = pop_scale(t, it["t0"], it["t1"], 0.16, 0.1)
        if not s:
            return
        size = int(it.get("size", 0.16) * self.W)
        spr = _mark_sprite(it["mark"], size)
        x, y = self.pos(it.get("at", (0.5, 0.4)), fi, *it.get("offset", (0, 0)))
        _paste(fr, spr, x, y, s)

    def _flash(self, fr, t, fi, it):
        dt = t - it["t0"]
        if 0 <= dt < 0.18:
            a = int(255 * (1 - dt / 0.18) * it.get("strength", 0.8))
            fr.alpha_composite(Image.new("RGBA", fr.size, (255, 255, 255, a)))

    def _vignette(self, fr, t, fi, it):
        if it["t0"] <= t <= it["t1"]:
            fr.alpha_composite(_vignette_sprite(self.W, self.H, it.get("strength", 0.55)))


@lru_cache(maxsize=4)
def _vignette_sprite(W, H, strength):
    y, x = np.ogrid[:H, :W]
    d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
    a = np.clip((d - 0.45) / 0.55, 0, 1) ** 1.6 * 255 * strength
    img = np.zeros((H, W, 4), np.uint8)
    img[..., 3] = a.astype(np.uint8)
    return Image.fromarray(img, "RGBA")


@lru_cache(maxsize=64)
def _badge_sprite(txt, size, color):
    img = Image.new("RGBA", (size + 20, size + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((10, 14, size + 10, size + 14), fill=(0, 0, 0, 90))
    d.ellipse((10, 10, size + 10, size + 10), fill=color, outline=INK, width=max(4, size // 16))
    f = font(int(size * 0.55), "LuckiestGuy")
    l, t_, r, b = f.getbbox(txt)
    d.text((10 + size / 2 - (r + l) / 2, 10 + size / 2 - (b + t_) / 2), txt, font=f, fill=WHITE,
           stroke_width=max(3, size // 22), stroke_fill=INK)
    return img


@lru_cache(maxsize=32)
def _stamp_sprite(txt, size, color):
    f = font(size, "Montserrat-Black")
    l, t, r, b = f.getbbox(txt)
    w, h = r - l + size, b - t + size * 0.7
    img = Image.new("RGBA", (int(w + 20), int(h + 20)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((10, 10, 10 + w, 10 + h), size * 0.15, outline=color,
                        width=max(6, size // 9))
    d.text((10 + size / 2 - l, 10 + size * 0.35 - t), txt, font=f, fill=color)
    return img


@lru_cache(maxsize=16)
def _mark_sprite(kind, size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w = int(size * 0.16)
    if kind == "x":
        for a, b in (((0.2, 0.2), (0.8, 0.8)), ((0.8, 0.2), (0.2, 0.8))):
            d.line((a[0] * size, a[1] * size, b[0] * size, b[1] * size), fill=INK, width=w + 10)
        for a, b in (((0.2, 0.2), (0.8, 0.8)), ((0.8, 0.2), (0.2, 0.8))):
            d.line((a[0] * size, a[1] * size, b[0] * size, b[1] * size), fill=RED, width=w)
    else:
        pts = [(0.18 * size, 0.55 * size), (0.42 * size, 0.78 * size), (0.84 * size, 0.24 * size)]
        d.line(pts, fill=INK, width=w + 10, joint="curve")
        d.line(pts, fill=GREEN, width=w, joint="curve")
    return img


@lru_cache(maxsize=32)
def _icon_sprite(kind, size):
    img = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size
    ow = max(3, size // 14)
    if kind == "heart":
        r = size * 0.32
        d.ellipse((c - r * 2, c - r * 1.6, c, c + r * 0.4), fill=PINK, outline=INK, width=ow)
        d.ellipse((c, c - r * 1.6, c + r * 2, c + r * 0.4), fill=PINK, outline=INK, width=ow)
        d.polygon([(c - r * 1.95, c - r * 0.3), (c + r * 1.95, c - r * 0.3), (c, c + r * 2.0)],
                  fill=PINK, outline=INK)
        d.ellipse((c - r * 1.75, c - r * 1.4, c - r * 0.2, c + r * 0.2), fill=PINK)
        d.ellipse((c + r * 0.2, c - r * 1.4, c + r * 1.75, c + r * 0.2), fill=PINK)
    elif kind == "sweat":
        r = size * 0.28
        d.polygon([(c, c - r * 2.2), (c - r, c), (c + r, c)], fill=BLUE, outline=INK)
        d.ellipse((c - r, c - r, c + r, c + r), fill=BLUE, outline=INK, width=ow)
        d.polygon([(c, c - r * 2.0), (c - r * 0.85, c - r * 0.2), (c + r * 0.85, c - r * 0.2)],
                  fill=BLUE)
        d.ellipse((c - r * 0.45, c - r * 0.5, c - r * 0.05, c - r * 0.05), fill=WHITE)
    elif kind == "bulb":
        r = size * 0.4
        d.ellipse((c - r, c - r * 1.4, c + r, c + r * 0.6), fill=YELLOW, outline=INK, width=ow)
        d.rectangle((c - r * 0.45, c + r * 0.5, c + r * 0.45, c + r * 1.0), fill=(170, 170, 170),
                    outline=INK, width=ow)
        for a in range(-60, 61, 30):
            rad = math.radians(a - 90)
            d.line((c + math.cos(rad) * r * 1.3, c - r * 0.4 + math.sin(rad) * r * 1.3,
                    c + math.cos(rad) * r * 1.7, c - r * 0.4 + math.sin(rad) * r * 1.7),
                   fill=YELLOW, width=ow * 2)
    elif kind == "anger":
        r = size * 0.35
        for a in (45, 135, 225, 315):
            rad = math.radians(a)
            d.line((c + math.cos(rad) * r * 0.3, c + math.sin(rad) * r * 0.3,
                    c + math.cos(rad) * r, c + math.sin(rad) * r), fill=RED, width=ow * 3)
    return img


# ---------------------------------------------------------------- captions
def caption_sprite(word, W, gold):
    size = int(W * 0.068)
    fill = YELLOW if gold else WHITE
    return _cached_text(word, size, fill, INK, "Montserrat-ExtraBold", 0, True)


def caption_groups(words, gold_words, group=2):
    """Split timed words [(t0, t1, text)] into caption groups of up to `group` words,
    breaking after punctuation. Returns [(start, end, [(text, gold), ...]), ...]."""
    groups, cur = [], []
    for i, (a, b, raw) in enumerate(words):
        cur.append((a, b, raw))
        if len(cur) >= group or re.search(r"[,.!?;:]$", raw) or i == len(words) - 1:
            groups.append(cur)
            cur = []
    out = []
    for gi, g in enumerate(groups):
        start = g[0][0]
        nxt = groups[gi + 1][0][0] if gi + 1 < len(groups) else g[-1][1] + 0.5
        end = min(nxt, max(g[-1][1] + 0.35, start + 0.5))
        out.append((start, end, [(re.sub(r"^[\"'(]+|[\"'),;:]+$", "", w[2]),
                                  _is_gold(w[2], gold_words)) for w in g]))
    return out


def draw_caption(frame, groups, tg, W, H, y=0.6):
    for start, end, toks in groups:
        if start <= tg < end:
            t_in = tg - start
            s = ease_out_back(min(1.0, t_in / 0.12), 2.2) if t_in < 0.12 else 1.0
            sprites = [caption_sprite(tx, W, g) for tx, g in toks]
            size = int(W * 0.068)
            overlap = int(size * 0.35) * 2 - int(size * 0.3)  # sprite padding minus a space
            total = sum(sp.size[0] for sp in sprites) - overlap * (len(sprites) - 1)
            x = W / 2 - total / 2
            for sp in sprites:
                _paste(frame, sp, x + sp.size[0] / 2, H * y, max(0.3, s))
                x += sp.size[0] - overlap
            return


def _is_gold(raw, gold_words):
    w = re.sub(r"[^a-z0-9$,]", "", raw.lower()).strip(",")
    return w in gold_words or any(ch.isdigit() for ch in raw) or "$" in raw


# ---------------------------------------------------------------- whip transition
def whip(frame_rgb, amount, direction=1):
    """Horizontal motion blur + slide for whip-pan transitions. amount 0..1."""
    if amount <= 0.01:
        return frame_rgb
    a = np.asarray(frame_rgb).astype(np.float32)
    H, W = a.shape[:2]
    blur = int(W * 0.14 * amount)
    n = 12
    acc = np.zeros_like(a)
    for i in range(n):
        acc += np.roll(a, int(blur * i / n) * direction, axis=1)
    acc /= n
    shift = int(W * 0.3 * amount * amount) * direction
    acc = np.roll(acc, shift, axis=1)
    return Image.fromarray(acc.clip(0, 255).astype(np.uint8))
