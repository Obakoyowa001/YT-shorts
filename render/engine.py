"""Paper-craft 2D drawing engine for our Shorts.

All scene coordinates use a 1080x1920 "base" space and get scaled to the
output resolution (2160x3840 for 4K), so scenes are resolution-independent.
"""
import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

BASE_W, BASE_H = 1080, 1920
SCENE_LIFT = -200   # lift every scene so captions sit on empty ground below the action
CAPTION_Y = 1480    # ~77% down: clear of scene signs and of the Shorts UI
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
FONT_FILES = {"sign": "Rye-Regular.ttf", "cap": "LuckiestGuy-Regular.ttf"}
FALLBACKS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]

SHX, SHY = 7, 10                 # paper-cut drop shadow offset (base units)
SHADOW = (60, 35, 15, 70)

# Palette
SKIN = (241, 198, 160)
SKIN_D = (214, 160, 122)
INK = (45, 32, 28)
WHITE = (252, 248, 238)
CREAM = (246, 233, 205)
GOLD = (245, 192, 40)
GOLD_D = (196, 140, 20)
GREEN = (34, 139, 84)
EMERALD = (22, 120, 80)
MONEY = (168, 208, 150)
MONEY_D = (82, 140, 92)
WOOD = (170, 110, 62)
WOOD_D = (125, 76, 40)
WOOD_L = (206, 150, 92)
RED = (214, 64, 52)
PURPLE = (120, 72, 160)
GREY = (140, 140, 150)
GREY_D = (90, 92, 104)
STEEL = (110, 118, 130)
GRASS = (122, 178, 82)
GRASS_D = (92, 148, 64)
TREE = (54, 120, 70)
TREE_D = (36, 92, 54)
MUD = (110, 74, 44)


# ---------------------------------------------------------------- utilities
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def lerp(a, b, u):
    return a + (b - a) * u


def ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def prog(t, t0, t1):
    """Eased 0..1 progress of t between t0 and t1."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return ease((t - t0) / (t1 - t0))


def pop(t, t0, dur=0.35):
    """Ease-out-back pop-in scale: 0 before t0, overshoots, settles at 1."""
    if t < t0:
        return 0.0
    u = (t - t0) / dur
    if u >= 1:
        return 1.0
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


def mix(c1, c2, u):
    return tuple(int(lerp(a, b, clamp(u))) for a, b in zip(c1, c2))


@lru_cache(maxsize=1024)
def font(kind, px):
    px = max(4, int(px))
    for p in [os.path.join(FONT_DIR, FONT_FILES.get(kind, ""))] + FALLBACKS:
        if p and os.path.exists(p):
            return ImageFont.truetype(p, px)
    return ImageFont.load_default()


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, img, S):
        self.img = img
        self.S = S
        self.d = ImageDraw.Draw(img, "RGBA")
        self.z, self.fx, self.fy = 1.0, 540.0, 960.0
        self.shadows = True

    def cam(self, z=1.0, fx=540.0, fy=960.0):
        self.z, self.fx, self.fy = z, fx, fy

    def P(self, x, y):
        return (((x - self.fx) * self.z + 540) * self.S,
                ((y - self.fy) * self.z + 960 + SCENE_LIFT) * self.S)

    def L(self, v):
        return v * self.z * self.S

    def _box(self, x0, y0, x1, y1):
        a, b = self.P(x0, y0), self.P(x1, y1)
        return [min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])]

    def rect(self, x0, y0, x1, y1, fill, r=0, outline=None, w=0, shadow=True):
        if shadow and self.shadows:
            self._rect(x0 + SHX, y0 + SHY, x1 + SHX, y1 + SHY, SHADOW, r)
        self._rect(x0, y0, x1, y1, fill, r, outline, w)

    def _rect(self, x0, y0, x1, y1, fill, r=0, outline=None, w=0):
        box = self._box(x0, y0, x1, y1)
        if box[2] - box[0] < 1 or box[3] - box[1] < 1:
            return
        width = max(1, int(self.L(w))) if w else 0
        if r:
            rad = min(self.L(r), (box[2] - box[0]) / 2, (box[3] - box[1]) / 2)
            self.d.rounded_rectangle(box, radius=rad, fill=fill, outline=outline, width=width)
        else:
            self.d.rectangle(box, fill=fill, outline=outline, width=width)

    def ellipse(self, cx, cy, rx, ry, fill, outline=None, w=0, shadow=True):
        if shadow and self.shadows:
            self._ell(cx + SHX, cy + SHY, rx, ry, SHADOW)
        self._ell(cx, cy, rx, ry, fill, outline, w)

    def _ell(self, cx, cy, rx, ry, fill, outline=None, w=0):
        box = self._box(cx - rx, cy - ry, cx + rx, cy + ry)
        if box[2] - box[0] < 1 or box[3] - box[1] < 1:
            return
        self.d.ellipse(box, fill=fill, outline=outline,
                       width=max(1, int(self.L(w))) if w else 0)

    def circle(self, cx, cy, r, fill, outline=None, w=0, shadow=True):
        self.ellipse(cx, cy, r, r, fill, outline, w, shadow)

    def poly(self, pts, fill, outline=None, w=0, shadow=True):
        if shadow and self.shadows:
            self.d.polygon([self.P(x + SHX, y + SHY) for x, y in pts], fill=SHADOW)
        self.d.polygon([self.P(x, y) for x, y in pts], fill=fill, outline=outline,
                       width=max(1, int(self.L(w))) if w else 0)

    def line(self, pts, fill, w=6, shadow=False):
        if shadow and self.shadows:
            self.d.line([self.P(x + SHX, y + SHY) for x, y in pts], fill=SHADOW,
                        width=max(1, int(self.L(w))), joint="curve")
        self.d.line([self.P(x, y) for x, y in pts], fill=fill,
                    width=max(1, int(self.L(w))), joint="curve")

    def arc(self, cx, cy, rx, ry, start, end, fill, w=5):
        box = self._box(cx - rx, cy - ry, cx + rx, cy + ry)
        if box[2] - box[0] < 1 or box[3] - box[1] < 1:
            return
        self.d.arc(box, start, end, fill=fill, width=max(1, int(self.L(w))))

    def text(self, x, y, s, size, fill=INK, kind="sign", anchor="mm",
             stroke=0, stroke_fill=INK):
        f = font(kind, self.L(size))
        self.d.text(self.P(x, y), s, font=f, fill=fill, anchor=anchor,
                    stroke_width=int(self.L(stroke)) if stroke else 0,
                    stroke_fill=stroke_fill)


# ---------------------------------------------------------------- backdrops
SKIES = {
    "day": ((126, 192, 232), (214, 236, 244)),
    "forest": ((150, 200, 196), (226, 236, 210)),
    "dusk": ((82, 84, 150), (236, 160, 120)),
    "night": ((22, 30, 66), (60, 66, 112)),
    "interior": ((206, 168, 120), (232, 204, 160)),
    "shop": ((180, 196, 170), (220, 228, 200)),
    "modern": ((200, 212, 224), (236, 240, 244)),
}


@lru_cache(maxsize=16)
def sky(kind, W, H):
    top, bot = SKIES[kind]
    g = np.linspace(0, 1, H)[:, None]
    arr = np.zeros((H, 1, 3))
    for i in range(3):
        arr[:, :, i] = top[i] + (bot[i] - top[i]) * g
    arr = np.repeat(arr, W, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


@lru_cache(maxsize=4)
def paper_overlay(W, H, seed=7):
    """Multiply layer: paper grain + fibres + soft vignette."""
    rng = np.random.default_rng(seed)
    coarse = rng.normal(0, 1, (H // 24 + 1, W // 24 + 1)).astype(np.float32)
    coarse = np.array(Image.fromarray(coarse).resize((W, H), Image.BICUBIC))
    fine = rng.normal(0, 1, (H, W)).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = ((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2 * 0.8)
    val = 250 - coarse * 4 - fine * 5 - v * 95
    val = np.clip(val, 0, 255).astype(np.uint8)
    L = Image.fromarray(val, "L")
    return Image.merge("RGB", (L, L, L.point(lambda p: max(0, p - 4))))


def finish(img):
    return ImageChops.multiply(img, paper_overlay(img.width, img.height))


# ---------------------------------------------------------------- scenery
def ground(c, y, col=GRASS, col2=GRASS_D):
    c.rect(-900, y, 1980, 3000, col, shadow=False)
    c.rect(-900, y, 1980, y + 18, col2, shadow=False)


def floor(c, y, col=WOOD_L, line=WOOD):
    c.rect(-900, y, 1980, 3000, col, shadow=False)
    for i in range(-10, 30):
        c.line([(i * 120, y), (i * 120 - 60, y + 900)], line, 4)


def wall_planks(c, top=-900, bottom=1500, col=(214, 170, 118), line=(186, 140, 92)):
    c.rect(-900, top, 1980, bottom, col, shadow=False)
    for i in range(-10, 30):
        c.line([(i * 90, top), (i * 90, bottom)], line, 5)


def hills(c, y, col=(160, 200, 120), off=0):
    for i in range(-3, 6):
        cx = i * 420 + (off % 420)
        c.ellipse(cx, y, 330, 160, col, shadow=False)


def cloud(c, x, y, s=1.0):
    for dx, dy, r in ((0, 0, 60), (55, -25, 55), (110, 0, 58), (55, 15, 60)):
        c.circle(x + dx * s, y + dy * s, r * s, (255, 255, 255, 230), shadow=False)


def tree(c, x, y, s=1.0, col=TREE, col2=TREE_D):
    c.rect(x - 16 * s, y - 120 * s, x + 16 * s, y, WOOD_D)
    for i, (w, h) in enumerate(((120, 160), (100, 140), (75, 120))):
        top = y - 110 * s - i * 85 * s
        cc = col if i % 2 == 0 else col2
        c.poly([(x - w * s, top), (x + w * s, top), (x, top - h * s * 1.2)], cc)


def sun(c, x, y, r=70):
    c.circle(x, y, r * 1.35, (255, 230, 140, 90), shadow=False)
    c.circle(x, y, r, (255, 214, 90), shadow=False)


def moon(c, x, y, r=60):
    c.circle(x, y, r * 1.4, (240, 240, 220, 50), shadow=False)
    c.circle(x, y, r, (240, 240, 220), shadow=False)
    c.circle(x - r * 0.3, y - r * 0.2, r * 0.18, (210, 210, 190), shadow=False)
    c.circle(x + r * 0.25, y + r * 0.3, r * 0.12, (210, 210, 190), shadow=False)


def sign(c, x, y, w, h, txt, size=60, bg=CREAM, fg=INK, post=0, border=WOOD_D,
         kind="sign", sc=1.0):
    if sc <= 0.01:
        return
    w, h, size = w * sc, h * sc, size * sc
    if post:
        c.rect(x - 10, y + h / 2 - 5, x + 10, y + h / 2 + post, WOOD_D)
    c.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, bg, r=10, outline=border, w=6)
    c.text(x, y, txt, size, fg, kind=kind)


def badge(c, t, txt, t0=0.0, x=540, y=560):
    s = pop(t, t0)
    if s > 0:
        c.rect(x - 190 * s, y - 62 * s, x + 190 * s, y + 62 * s, RED, r=30 * s,
               outline=WHITE, w=8)
        c.text(x, y + 4 * s, txt, 74 * s, WHITE, kind="cap")


def shack(c, x, y, s=1.0, sign_txt="BANK", sign_sc=1.0, door_open=False,
          sign_size=None):
    w, h = 300 * s, 230 * s
    c.rect(x - w, y - h * 2, x + w, y, WOOD)
    for i in range(1, 8):
        yy = y - i * h * 2 / 8
        c.line([(x - w, yy), (x + w, yy)], WOOD_D, 4)
    c.poly([(x - w - 40 * s, y - h * 2), (x + w + 40 * s, y - h * 2),
            (x, y - h * 2 - 190 * s)], (150, 70, 52))
    # door
    c.rect(x - 60 * s, y - 210 * s, x + 60 * s, y, (40, 26, 18) if door_open else WOOD_D,
           shadow=False)
    if not door_open:
        c.circle(x + 35 * s, y - 100 * s, 8 * s, GOLD, shadow=False)
    # window
    c.rect(x + 110 * s, y - 330 * s, x + 230 * s, y - 220 * s, (180, 220, 236),
           outline=WOOD_D, w=6)
    c.rect(x - 230 * s, y - 330 * s, x - 110 * s, y - 220 * s, (180, 220, 236),
           outline=WOOD_D, w=6)
    if sign_txt:
        sign(c, x, y - h * 2 + 60 * s, 380 * s, 100 * s, sign_txt,
             sign_size or (66 * s), sc=sign_sc)
    return (x, y - h * 2 - 190 * s)  # roof apex


def banknote(c, x, y, w=300, label="BANK OF YOU", amount="$5", portrait="face",
             sc=1.0, col=MONEY):
    if sc <= 0.01:
        return
    w = w * sc
    h = w * 0.46
    c.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, col, r=8 * sc,
           outline=MONEY_D, w=5 * sc)
    c.rect(x - w / 2 + 12 * sc, y - h / 2 + 12 * sc, x + w / 2 - 12 * sc,
           y + h / 2 - 12 * sc, None, r=6 * sc, outline=MONEY_D, w=3 * sc, shadow=False)
    c.text(x - w * 0.33, y - h * 0.22, amount, 40 * w / 300, (30, 80, 40), kind="sign")
    c.text(x + w * 0.05, y + h * 0.28, label, 24 * w / 300, (30, 80, 40), kind="sign")
    px, py, pr = x + w * 0.18, y - h * 0.05, h * 0.27
    c.ellipse(px, py, pr * 1.1, pr, (226, 236, 210), outline=MONEY_D, w=3 * sc,
              shadow=False)
    if portrait == "face":
        c.circle(px, py + 2 * sc, pr * 0.55, SKIN, shadow=False)
        c.ellipse(px, py - pr * 0.45, pr * 0.55, pr * 0.22, (60, 40, 30), shadow=False)
        c.arc(px, py + pr * 0.1, pr * 0.25, pr * 0.15, 20, 160, INK, 2 * sc)
    elif portrait == "dog":
        c.circle(px, py + 2 * sc, pr * 0.55, (170, 120, 80), shadow=False)
        c.ellipse(px - pr * 0.5, py - pr * 0.1, pr * 0.18, pr * 0.35, (110, 70, 40),
                  shadow=False)
        c.ellipse(px + pr * 0.5, py - pr * 0.1, pr * 0.18, pr * 0.35, (110, 70, 40),
                  shadow=False)
        c.circle(px, py + pr * 0.15, pr * 0.12, INK, shadow=False)
    elif portrait == "name":
        c.text(px, py, "YOU", 22 * w / 300, (30, 80, 40))
    elif portrait == "modern":
        c.circle(px, py, pr * 0.55, (150, 160, 150), shadow=False)


def coin(c, x, y, r=26, sc=1.0):
    if sc <= 0.01:
        return
    r *= sc
    c.circle(x, y, r, GOLD, outline=GOLD_D, w=4 * sc)
    c.circle(x, y, r * 0.62, None, outline=GOLD_D, w=3 * sc, shadow=False)


def sparkle(c, x, y, r, t, phase=0.0):
    k = 0.5 + 0.5 * math.sin(t * 9 + phase)
    r = r * (0.5 + 0.7 * k)
    c.poly([(x, y - r), (x + r * 0.25, y - r * 0.25), (x + r, y), (x + r * 0.25, y + r * 0.25),
            (x, y + r), (x - r * 0.25, y + r * 0.25), (x - r, y), (x - r * 0.25, y - r * 0.25)],
           (255, 248, 200), shadow=False)


def strongbox(c, x, y, s=1.0, label="RESERVES", coins=0, t=0.0, lid=True):
    w, h = 260 * s, 170 * s
    if lid:
        c.poly([(x - w, y - h), (x + w, y - h), (x + w - 30 * s, y - h - 120 * s),
                (x - w + 30 * s, y - h - 120 * s)], (70, 74, 86))
    c.rect(x - w, y - h, x + w, y + h, (88, 92, 106), r=14 * s)
    c.rect(x - w + 24 * s, y - h + 6 * s, x + w - 24 * s, y - h + 50 * s, (40, 40, 48),
           shadow=False)
    for i in range(coins):
        cx = x - w + 70 * s + (i % 7) * 62 * s
        cy = y - h + 24 * s - (i // 7) * 26 * s
        coin(c, cx, cy, 28 * s)
    for bx in (-0.55, 0.55):
        c.rect(x + bx * w - 14 * s, y - h, x + bx * w + 14 * s, y + h, STEEL, shadow=False)
    if label:
        c.rect(x - 150 * s, y + 20 * s, x + 150 * s, y + 100 * s, CREAM, r=8 * s,
               shadow=False)
        c.text(x, y + 62 * s, label, 48 * s, INK)


def barrel(c, x, y, s=1.0, label="GOLD", top_fill=None):
    w, h = 170 * s, 250 * s
    c.poly([(x - w, y - h), (x + w, y - h), (x + w * 1.12, y), (x + w, y + h),
            (x - w, y + h), (x - w * 1.12, y)], WOOD)
    for k in (-0.6, 0.6):
        c.line([(x - w * 1.08, y + k * h), (x + w * 1.08, y + k * h)], STEEL, 14)
    c.ellipse(x, y - h, w, 40 * s, WOOD_D, shadow=False)
    c.ellipse(x, y - h, w - 16 * s, 30 * s, top_fill or (60, 40, 25), shadow=False)
    if label:
        c.text(x, y + 10 * s, label, 90 * s, (60, 36, 20))


def book(c, x, y, s=1.0, title="BANK NOTE REPORTER", open_u=0.0):
    w, h = 300 * s, 200 * s
    if open_u < 0.5:
        c.rect(x - w, y - h, x + w, y + h, (120, 40, 40), r=10 * s)
        c.rect(x - w + 20 * s, y - h + 20 * s, x + w - 20 * s, y + h - 20 * s, None,
               r=8 * s, outline=GOLD, w=5, shadow=False)
        c.text(x, y - 30 * s, "BANK NOTE", 52 * s, GOLD)
        c.text(x, y + 40 * s, "REPORTER", 52 * s, GOLD)
    else:
        c.rect(x - w * 1.9, y - h, x + w * 1.9, y + h, (120, 40, 40), r=10 * s)
        c.rect(x - w * 1.8, y - h + 14 * s, x - 6 * s, y + h - 14 * s, CREAM, shadow=False)
        c.rect(x + 6 * s, y - h + 14 * s, x + w * 1.8, y + h - 14 * s, CREAM, shadow=False)
        for i in range(6):
            yy = y - h + 60 * s + i * 50 * s
            c.line([(x - w * 1.7, yy), (x - 40 * s, yy)], (170, 160, 140), 4)
            c.line([(x + 40 * s, yy), (x + w * 1.7, yy)], (170, 160, 140), 4)


# ---------------------------------------------------------------- characters
KINDS = {
    #        legs torsoH torsoW headR  coat         pants          shirt
    "boss": (70, 125, 160, 64, EMERALD, (70, 60, 70), WHITE),
    "gus": (115, 185, 220, 72, RED, (70, 90, 140), RED),
    "mo": (125, 140, 104, 56, PURPLE, (60, 50, 70), WHITE),
    "pike": (150, 200, 104, 54, GREY, GREY_D, WHITE),
    "shop": (95, 140, 140, 60, (90, 120, 160), (80, 70, 60), WHITE),
    "folk1": (95, 135, 140, 58, (180, 120, 60), (80, 70, 90), WHITE),
    "folk2": (95, 135, 140, 58, (90, 140, 170), (70, 60, 50), WHITE),
    "folk3": (95, 135, 140, 58, (200, 170, 90), (90, 70, 60), WHITE),
    "folk4": (95, 135, 140, 58, (150, 90, 120), (60, 70, 80), WHITE),
    "modern": (115, 185, 220, 72, (70, 110, 170), (50, 60, 90), WHITE),
}


def person(c, x, y, s=1.0, kind="boss", t=0.0, arm_l=15, arm_r=15, mouth="smile",
           walk=0.0, look=0.0, blink=True, sweat=False, boots=False, hold_r=None,
           hold_l=None):
    legs, th, tw, hr, coat, pants, shirt = KINDS[kind]
    legs, th, tw, hr = legs * s, th * s, tw * s, hr * s
    bob = abs(math.sin(t * 9)) * 8 * s if walk else math.sin(t * 2.5) * 2 * s
    y0 = y - bob
    # legs
    sw = math.sin(t * 9) * 22 * s * walk
    lw = (24 if kind not in ("mo", "pike") else 16) * s
    for dx, k in ((-tw * 0.22, 1), (tw * 0.22, -1)):
        fx = x + dx + sw * k
        c.line([(x + dx, y0 - legs), (fx, y0 - 6 * s)], pants, lw * 1.6)
        if kind in ("gus",) and not boots:
            c.ellipse(fx + 10 * s, y0 - 4 * s, 26 * s, 12 * s, SKIN)
        else:
            c.ellipse(fx + 10 * s, y0 - 6 * s, 30 * s, 14 * s, (50, 36, 30))
    top = y0 - legs - th
    # torso
    if kind == "pike":
        c.poly([(x - tw / 2, top), (x + tw / 2, top), (x + tw * 0.7, y0 - legs * 0.4),
                (x - tw * 0.7, y0 - legs * 0.4)], coat)
    else:
        c.rect(x - tw / 2, top, x + tw / 2, y0 - legs + 10 * s, coat, r=tw * 0.35)
    if kind == "boss":
        c.poly([(x - tw * 0.18, top + 4 * s), (x + tw * 0.18, top + 4 * s),
                (x, top + th * 0.55)], shirt, shadow=False)
        c.line([(x - tw * 0.3, top + th * 0.55), (x, top + th * 0.68),
                (x + tw * 0.3, top + th * 0.55)], GOLD, 5 * s)
        for i in range(3):
            c.circle(x, top + th * (0.62 + i * 0.12), 6 * s, GOLD_D, shadow=False)
    elif kind == "gus":
        for i in range(1, 5):
            c.line([(x - tw / 2 + 8 * s, top + i * th / 5), (x + tw / 2 - 8 * s, top + i * th / 5)],
                   (150, 36, 30), 6 * s)
        for i in range(1, 4):
            c.line([(x - tw / 2 + i * tw / 4, top + 10 * s), (x - tw / 2 + i * tw / 4, y0 - legs)],
                   (150, 36, 30), 6 * s)
    elif kind in ("mo", "pike", "shop"):
        c.poly([(x - tw * 0.16, top + 4 * s), (x + tw * 0.16, top + 4 * s),
                (x, top + th * 0.4)], shirt, shadow=False)
        if kind == "shop":
            c.rect(x - tw * 0.38, top + th * 0.35, x + tw * 0.38, y0 - legs + 6 * s,
                   (236, 230, 214), r=10 * s, shadow=False)
    elif kind == "modern":
        c.poly([(x - tw * 0.2, top + 4 * s), (x + tw * 0.2, top + 4 * s),
                (x, top + th * 0.3)], shirt, shadow=False)
    # arms
    alen = th * 0.85
    hands = {}
    for side, ang, hold in ((-1, arm_l, hold_l), (1, arm_r, hold_r)):
        sx, sy = x + side * tw * 0.42, top + 26 * s
        a = math.radians(ang)
        hx, hy = sx + side * math.sin(a) * alen, sy + math.cos(a) * alen
        c.line([(sx, sy), (hx, hy)], coat, 26 * s if kind == "gus" else 20 * s)
        c.circle(hx, hy, 15 * s if kind != "gus" else 19 * s, SKIN)
        hands["l" if side < 0 else "r"] = (hx, hy)
    # head
    hx, hy = x, top - hr * 0.85
    c.circle(hx, hy, hr, SKIN)
    if kind == "gus":
        c.ellipse(hx, hy + hr * 0.55, hr * 0.85, hr * 0.5, (150, 90, 50), shadow=False)
        c.ellipse(hx, hy - hr * 0.55, hr * 1.02, hr * 0.62, RED, shadow=False)
        c.rect(hx - hr * 1.02, hy - hr * 0.42, hx + hr * 1.02, hy - hr * 0.22, (170, 40, 34),
               r=6 * s, shadow=False)
        c.circle(hx, hy - hr * 1.15, hr * 0.2, WHITE, shadow=False)
    elif kind == "boss":
        c.ellipse(hx - hr * 0.1, hy - hr * 0.62, hr * 0.95, hr * 0.48, (60, 40, 30),
                  shadow=False)
    elif kind == "mo":
        c.ellipse(hx, hy - hr * 0.7, hr * 0.9, hr * 0.4, (40, 30, 30), shadow=False)
    elif kind == "pike":
        c.rect(hx - hr * 0.75, hy - hr * 1.9, hx + hr * 0.75, hy - hr * 0.6, (60, 62, 70),
               r=4 * s, shadow=False)
        c.rect(hx - hr * 1.15, hy - hr * 0.72, hx + hr * 1.15, hy - hr * 0.55, (60, 62, 70),
               shadow=False)
    elif kind == "shop":
        c.ellipse(hx, hy - hr * 0.7, hr * 0.8, hr * 0.35, (200, 200, 200), shadow=False)
    elif kind.startswith("folk"):
        c.ellipse(hx, hy - hr * 0.68, hr * 1.25, hr * 0.28, (110, 80, 50), shadow=False)
        c.rect(hx - hr * 0.7, hy - hr * 1.2, hx + hr * 0.7, hy - hr * 0.65, (110, 80, 50),
               r=8 * s, shadow=False)
    elif kind == "modern":
        c.ellipse(hx, hy - hr * 0.55, hr * 1.02, hr * 0.62, (230, 120, 40), shadow=False)
    # face
    closed = blink and (t % 3.1) < 0.12
    ex = hr * 0.36
    for side in (-1, 1):
        if closed:
            c.line([(hx + side * ex - 8 * s, hy - 4 * s), (hx + side * ex + 8 * s, hy - 4 * s)],
                   INK, 4 * s)
        else:
            c.circle(hx + side * ex + look * 5 * s, hy - 4 * s, 8 * s, INK, shadow=False)
    c.circle(hx - hr * 0.62, hy + hr * 0.25, hr * 0.16, (240, 150, 140, 150), shadow=False)
    c.circle(hx + hr * 0.62, hy + hr * 0.25, hr * 0.16, (240, 150, 140, 150), shadow=False)
    my = hy + hr * 0.38
    if kind == "mo":
        for side in (-1, 1):
            c.ellipse(hx + side * hr * 0.45, my - hr * 0.12, hr * 0.5, hr * 0.14, (40, 30, 30),
                      shadow=False)
            c.circle(hx + side * hr * 0.92, my - hr * 0.26, hr * 0.12, (40, 30, 30),
                     shadow=False)
    elif kind == "pike":
        c.ellipse(hx, my - hr * 0.1, hr * 0.38, hr * 0.1, (110, 110, 110), shadow=False)
    if mouth == "smile":
        c.arc(hx, my - hr * 0.05, hr * 0.3, hr * 0.2, 15, 165, INK, 5 * s)
    elif mouth == "grin":
        c.ellipse(hx, my, hr * 0.32, hr * 0.2, (120, 30, 40), shadow=False)
        c.rect(hx - hr * 0.26, my - hr * 0.18, hx + hr * 0.26, my - hr * 0.05, WHITE,
               shadow=False)
    elif mouth == "o":
        c.circle(hx, my + hr * 0.04, hr * 0.13, (120, 30, 40), shadow=False)
    elif mouth == "flat":
        c.line([(hx - hr * 0.22, my), (hx + hr * 0.22, my)], INK, 5 * s)
    elif mouth == "sad":
        c.arc(hx, my + hr * 0.15, hr * 0.26, hr * 0.16, 200, 340, INK, 5 * s)
    elif mouth == "laugh":
        c.ellipse(hx, my + hr * 0.02, hr * 0.34, hr * 0.26, (120, 30, 40), shadow=False)
    if sweat:
        dy = (t * 120) % (hr * 1.2)
        c.ellipse(hx + hr * 0.95, hy - hr * 0.3 + dy, 9 * s, 14 * s, (140, 200, 240),
                  shadow=False)
    if hold_r == "magnifier" and "r" in hands:
        mx, my2 = hands["r"]
        c.line([(mx, my2), (mx + 30 * s, my2 - 70 * s)], WOOD_D, 12 * s)
        c.circle(mx + 50 * s, my2 - 120 * s, 62 * s, (200, 230, 245, 170), outline=(150, 120, 60),
                 w=12 * s)
    if hold_r == "hammer" and "r" in hands:
        mx, my2 = hands["r"]
        c.line([(mx, my2), (mx + 10 * s, my2 - 70 * s)], WOOD_D, 10 * s)
        c.rect(mx - 20 * s, my2 - 92 * s, mx + 40 * s, my2 - 62 * s, STEEL, r=4 * s)
    if hold_r == "axe" and "r" in hands:
        mx, my2 = hands["r"]
        c.line([(mx, my2), (mx + 20 * s, my2 - 120 * s)], WOOD_D, 12 * s)
        c.poly([(mx + 20 * s, my2 - 120 * s), (mx + 75 * s, my2 - 135 * s),
                (mx + 70 * s, my2 - 85 * s), (mx + 22 * s, my2 - 95 * s)], STEEL)
    if hold_l == "lantern" and "l" in hands:
        mx, my2 = hands["l"]
        c.circle(mx, my2 + 30 * s, 45 * s, (255, 210, 100, 80), shadow=False)
        c.rect(mx - 14 * s, my2 + 12 * s, mx + 14 * s, my2 + 50 * s, (255, 220, 120),
               outline=INK, w=3 * s, shadow=False)
    return hands


def bear(c, x, y, s=1.0, t=0.0, wave=True):
    col, col2 = (130, 84, 52), (100, 62, 38)
    c.ellipse(x, y - 120 * s, 95 * s, 125 * s, col)
    c.ellipse(x, y - 100 * s, 55 * s, 70 * s, (176, 130, 90), shadow=False)
    c.circle(x, y - 270 * s, 70 * s, col)
    c.circle(x - 55 * s, y - 325 * s, 24 * s, col2)
    c.circle(x + 55 * s, y - 325 * s, 24 * s, col2)
    c.ellipse(x, y - 250 * s, 30 * s, 22 * s, (176, 130, 90), shadow=False)
    c.circle(x, y - 262 * s, 9 * s, INK, shadow=False)
    c.circle(x - 25 * s, y - 290 * s, 7 * s, INK, shadow=False)
    c.circle(x + 25 * s, y - 290 * s, 7 * s, INK, shadow=False)
    a = math.radians(150 + (math.sin(t * 10) * 25 if wave else -110))
    sx, sy = x + 80 * s, y - 190 * s
    c.line([(sx, sy), (sx + math.sin(a) * 110 * s, sy + math.cos(a) * 110 * s)], col, 40 * s)


def wildcat(c, x, y, s=1.0, t=0.0, flip=1):
    col, str_ = (214, 150, 80), (150, 90, 40)
    c.ellipse(x, y - 45 * s, 90 * s, 45 * s, col)
    for i in range(-2, 3):
        c.line([(x + i * 30 * s, y - 85 * s), (x + i * 30 * s, y - 60 * s)], str_, 6 * s)
    tail = math.sin(t * 4) * 20 * s
    c.line([(x - flip * 85 * s, y - 50 * s), (x - flip * 130 * s, y - 100 * s + tail)], col,
           16 * s)
    hx = x + flip * 80 * s
    c.circle(hx, y - 95 * s, 45 * s, col)
    c.poly([(hx - 40 * s, y - 120 * s), (hx - 30 * s, y - 165 * s), (hx - 8 * s, y - 132 * s)], col)
    c.poly([(hx + 40 * s, y - 120 * s), (hx + 30 * s, y - 165 * s), (hx + 8 * s, y - 132 * s)], col)
    c.circle(hx - 16 * s, y - 100 * s, 7 * s, INK, shadow=False)
    c.circle(hx + 16 * s, y - 100 * s, 7 * s, INK, shadow=False)
    c.line([(hx - 30 * s, y - 82 * s), (hx - 60 * s, y - 86 * s)], INK, 2 * s)
    c.line([(hx + 30 * s, y - 82 * s), (hx + 60 * s, y - 86 * s)], INK, 2 * s)


def dog(c, x, y, s=1.0, t=0.0):
    col = (170, 120, 80)
    c.ellipse(x, y - 60 * s, 70 * s, 60 * s, col)
    c.circle(x + 10 * s, y - 150 * s, 55 * s, col)
    c.ellipse(x - 35 * s, y - 150 * s, 18 * s, 40 * s, (110, 70, 40))
    c.ellipse(x + 55 * s, y - 150 * s, 18 * s, 40 * s, (110, 70, 40))
    c.circle(x - 5 * s, y - 160 * s, 7 * s, INK, shadow=False)
    c.circle(x + 25 * s, y - 160 * s, 7 * s, INK, shadow=False)
    c.circle(x + 10 * s, y - 135 * s, 10 * s, INK, shadow=False)
    wag = math.sin(t * 14) * 25 * s
    c.line([(x - 65 * s, y - 70 * s), (x - 110 * s, y - 110 * s + wag)], col, 14 * s)


def pony(c, x, y, s=1.0, t=0.0, col=(200, 160, 120), run=0.0, flip=1):
    bob = abs(math.sin(t * 12)) * 10 * s * run
    yb = y - bob
    for i, lx in enumerate((-70, -40, 40, 70)):
        sw = math.sin(t * 12 + i * 1.6) * 30 * s * run
        c.line([(x + lx * s, yb - 120 * s), (x + lx * s + sw, y)], (150, 110, 80), 18 * s)
    c.ellipse(x, yb - 150 * s, 120 * s, 60 * s, col)
    hx = x + flip * 120 * s
    c.line([(x + flip * 80 * s, yb - 170 * s), (hx, yb - 250 * s)], col, 44 * s)
    c.ellipse(hx + flip * 25 * s, yb - 260 * s, 50 * s, 30 * s, col)
    c.line([(x + flip * 70 * s, yb - 200 * s), (hx - flip * 10 * s, yb - 280 * s)],
           (90, 60, 40), 14 * s)
    c.circle(hx + flip * 25 * s, yb - 268 * s, 6 * s, INK, shadow=False)
    c.line([(x - flip * 115 * s, yb - 160 * s), (x - flip * 150 * s, yb - 100 * s)],
           (90, 60, 40), 16 * s)
    return (x, yb - 210 * s)  # saddle point


def press(c, x, y, s=1.0, t=0.0):
    c.rect(x - 200 * s, y - 420 * s, x + 200 * s, y, (70, 70, 80), r=12 * s)
    c.rect(x - 170 * s, y - 380 * s, x + 170 * s, y - 250 * s, (50, 50, 58), shadow=False)
    ang = t * 6
    cx, cy = x + 240 * s, y - 300 * s
    c.circle(cx, cy, 70 * s, STEEL)
    c.line([(cx, cy), (cx + math.cos(ang) * 70 * s, cy + math.sin(ang) * 70 * s)], GREY_D, 12 * s)
    ry = y - 300 * s + abs(math.sin(t * 6)) * 60 * s
    c.rect(x - 140 * s, ry, x + 140 * s, ry + 40 * s, STEEL)
    c.rect(x - 220 * s, y - 140 * s, x + 220 * s, y - 100 * s, (90, 90, 100))


def crowd_person(c, x, y, s, t, i, lantern=False, sign_txt=None):
    k = ["folk1", "folk2", "folk3", "folk4"][i % 4]
    hands = person(c, x, y, s, k, t + i * 0.37, arm_l=25, arm_r=160 if sign_txt else 30,
                   mouth="o" if i % 2 else "flat", walk=1.0, hold_l="lantern" if lantern else None)
    if sign_txt:
        hx, hy = hands["r"]
        c.line([(hx, hy), (hx, hy - 120 * s)], WOOD_D, 10 * s)
        sign(c, hx, hy - 170 * s, 300 * s, 90 * s, sign_txt, 44 * s)


# ---------------------------------------------------------------- captions
def draw_caption(img, S, word, age, gold):
    """Single-word karaoke caption, centre ~57% down the frame."""
    d = ImageDraw.Draw(img, "RGBA")
    sc = 0.6 + 0.4 * pop(age, 0.0, 0.18)
    size = 104 * S * sc
    f = font("cap", size)
    x, y = 540 * S, CAPTION_Y * S
    d.text((x + 6 * S, y + 9 * S), word, font=f, fill=(0, 0, 0, 120), anchor="mm",
           stroke_width=int(11 * S), stroke_fill=(0, 0, 0, 120))
    d.text((x, y), word, font=f, fill=(255, 215, 0) if gold else (255, 255, 255),
           anchor="mm", stroke_width=int(11 * S), stroke_fill=(0, 0, 0))
