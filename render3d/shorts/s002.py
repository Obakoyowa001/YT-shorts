"""Short #002 — What If Everyone Printed Money? (see scripts/002_everyone_prints_money.md)

Each entry in SHOTS is one shot:
  text   narration spoken during the shot
  bg     ambience: day / night / interior / shop / sepia
  build  build(c): builds the 3D scene, animates it and adds the 2D graphics.
         c.dur is the shot length in seconds; c.w("word") is when that word is spoken.
  audio  audio(m, T, d, c): sound effects at absolute time T + offset (c.w() works here too)
  cut    "whip" (default, blurred whip-pan transition) or "cut" (hard cut)
"""
import math
import random

import kit as K
from kit import (CREAM, GOLD, INK, MONEY, MONEY_D, RED, WHITE, WOOD, WOOD_D, WOOD_L, box, cyl,
                 empty, key, mat, sphere, text)

VOICE = "en-US-GuyNeural"
RATE = "+28%"
MUSIC = False
GOLD_WORDS = {"millionaire", "gus", "million", "thousand", "inflation", "hyperinflation",
              "germany", "zimbabwe", "eggs", "chicken", "barter", "central", "bank", "slowly",
              "doubled", "towers", "wheelbarrow", "dollar", "first", "friday"}
VOCALS = {
    "woo": ("Woo hoo!", "en-US-GuyNeural", "+10%", "+20Hz"),
    "hm": ("Hmm.", "en-US-EricNeural", "+0%", "-10Hz"),
    "nope": ("Nope.", "en-US-EricNeural", "+0%", "-10Hz"),
    "cluck": ("Bawk! Bawk bawk!", "en-US-AnaNeural", "+30%", "+40Hz"),
    "aww": ("Awww.", "en-US-GuyNeural", "+0%", "+10Hz"),
}


# ================================================================ shared sets & props
def square(lit=False, presses=False, signs=None):
    (K.light_night if lit else K.light_day)()
    K.ground()
    K.street(signs=signs or {1: "BAKERY", 2: "BARBER"}, lit=lit)
    K.plant_pot((-3.4, 4.6, 0))
    K.plant_pot((3.6, 4.4, 0), 0.9)
    K.lamp_post((-4.6, 3.0, 0), lit)
    K.lamp_post((4.8, 2.6, 0), lit)
    K.hay_bale((5.3, 5.0, 0), 15)
    K.barrel((-5.2, 5.4, 0))
    if presses:
        for x in (-6.2, -2.1, 2.0, 6.1):
            K.printing_press((x + 1.1, 6.6, 0), 0, 0.7)


def bill(loc, rot=(0, 0, 0), s=1.0, parent=None):
    root = empty("bill", loc, rot, parent)
    box((0.5 * s, 0.24 * s, 0.01 * s), (0, 0, 0), mat(MONEY, 0.7), 0.003, root)
    box((0.36 * s, 0.14 * s, 0.004 * s), (0, 0, 0.006 * s), mat(MONEY_D, 0.7), 0.0, root)
    return root


def spray_bills(origin, t0, t1, n=14, spread=1.6, height=1.4, seed=1, s=1.0):
    """Bills shooting up out of a press and fluttering down."""
    rng = random.Random(seed)
    for i in range(n):
        ts = t0 + (t1 - t0) * i / n
        b = bill(origin, (0, 0, 0), s)
        key(b, "scale", max(0, ts - 0.01), (0, 0, 0), "CONSTANT")
        key(b, "scale", ts, (1, 1, 1), "CONSTANT")
        key(b, "location", ts, origin)
        dx, dy = rng.uniform(-spread, spread), rng.uniform(-spread * 0.6, spread * 0.3)
        peak = (origin[0] + dx * 0.5, origin[1] + dy * 0.5, origin[2] + height * rng.uniform(.7, 1.2))
        land = (origin[0] + dx, origin[1] + dy, 0.02 + rng.uniform(0, 0.05))
        key(b, "location", ts + 0.35, peak)
        key(b, "location", ts + 1.4, land)
        key(b, "rotation_euler", ts, (0, 0, 0))
        key(b, "rotation_euler", ts + 1.4, (rng.uniform(-40, 40), rng.uniform(-60, 60),
                                             rng.uniform(0, 360)))


def press_pump(press, t0, t1, rate=0.45):
    plate = K.bpy.data.objects[press["plate"]]
    wheel = K.bpy.data.objects[press["wheel"]]
    z = plate.location.z
    t, i = t0, 0
    while t < t1:
        key(plate, "location", t, (0, 0, z + (0.18 if i % 2 == 0 else 0)) )
        t += rate / 2
        i += 1
    key(wheel, "rotation_euler", t0, (0, 90, 0))
    key(wheel, "rotation_euler", t1, (360 * (t1 - t0) / 1.2, 90, 0), "LINEAR")


def shopkeeper(loc=(0, 0, 0), yaw=0.0):
    t = K.Toy("shopkeeper", loc, yaw, height=1.4, head=0.35, skin=(232, 186, 150),
              body=(210, 120, 80), body_w=1.3, legs=INK, arms=(230, 230, 222),
              nose=(220, 150, 120))
    box((t.body_r * 1.3, 0.05, 0.5), (0, -t.body_r * 0.83, 0.3), mat(WHITE, 0.7), 0.04, t.hips)
    R = t.R
    cyl(R * 0.75, R * 0.5, (0, 0, R * 1.85), mat(WHITE, 0.8), t.head_pivot)
    sphere(R * 0.8, (0, 0, R * 2.15), mat(WHITE, 0.8), t.head_pivot, scale=(1, 1, 0.6))
    K.mustache(t, (90, 60, 40), 0.9)
    t.expr(0, eyes="half", brows="flat", mouth="flat")
    return t


def kid(name, loc, yaw=0.0, seed=1):
    rng = random.Random(seed)
    t = K.Toy(name, loc, yaw, height=0.9, head=0.3, seed=seed,
              skin=rng.choice([K.SKIN, K.SKIN_TAN, (226, 176, 130)]),
              body=rng.choice([(200, 90, 70), (70, 120, 170), (90, 150, 90)]),
              legs=(70, 60, 50))
    K.hat_beanie(t, rng.choice([(90, 90, 100), (130, 80, 60)]))
    t.expr(0, eyes="open", mouth="grin")
    return t


def price_board(values, loc, yaw=0.0, size=0.42, w=2.0, h=1.1):
    """Board whose price text swaps over time. values: [(t, "text", (r, g, b)), ...]."""
    root = empty("pboard", loc, (0, 0, yaw))
    box((w + 0.14, 0.1, h + 0.14), (0, 0.02, 0), mat(WOOD_D, 0.6), 0.03, root)
    box((w, 0.1, h), (0, -0.01, 0), mat(CREAM, 0.8), 0.0, root)
    for i, (t, s, colr) in enumerate(values):
        o = text(s, (0, -0.08, 0), size, mat(colr, 0.6), parent=root, extrude=0.005,
                 fnt="Montserrat-Black")
        t_next = values[i + 1][0] if i + 1 < len(values) else 999
        key(o, "scale", 0, (0, 0, 0), "CONSTANT")
        key(o, "scale", t, (1, 1, 1), "CONSTANT")
        key(o, "scale", min(t_next, 998), (0, 0, 0), "CONSTANT")
    return root


def bank_building(loc=(0, 6.5, 0)):
    root = empty("bank", loc)
    stone = mat((236, 230, 214), 0.7)
    for i, z in enumerate((0.1, 0.3, 0.5)):
        box((7.4 - i * 0.5, 2.0 - i * 0.4, 0.2), (0, -1.2 + i * 0.2, z), stone, 0.02, root)
    box((7.0, 1.2, 4.0), (0, 0.4, 2.6), stone, 0.03, root)
    for i in range(6):
        x = -2.9 + i * 1.16
        cyl(0.24, 3.4, (x, -0.55, 2.3), mat((244, 240, 228), 0.6), root, seg=24)
        box((0.6, 0.6, 0.16), (x, -0.55, 4.05), stone, 0.02, root)
        box((0.6, 0.6, 0.16), (x, -0.55, 0.68), stone, 0.02, root)
    box((7.2, 1.6, 0.4), (0, -0.25, 4.3), stone, 0.03, root)
    K.prism(7.4, 1.3, 1.5, (0, -0.25, 4.5), stone, root)
    box((4.6, 0.12, 0.6), (0, -1.08, 4.32), mat((40, 50, 70), 0.5), 0.02, root)
    sign = text("CENTRAL BANK", (0, -1.16, 4.32), 0.42, mat(GOLD, 0.25, metal=0.8), parent=root,
                extrude=0.02)
    box((1.6, 0.1, 2.4), (0, -0.16, 1.85), mat((70, 50, 30), 0.5), 0.03, root)
    return root, sign


def balloon(loc, label="PRICES"):
    root = empty("balloon", loc)
    b = sphere(0.6, (0, 0, 0), mat(RED, 0.25, coat=0.6), root, scale=(1, 1, 1.15))
    cone(0.12, 0.18, (0, 0, -0.72), mat(RED, 0.3), root, rot=(180, 0, 0))
    text(label, (0, -0.58, 0.05), 0.24, mat(WHITE, 0.4), parent=root, extrude=0.01)
    cyl(0.006, 2.0, (0, 0, -1.8), mat(WHITE, 0.6), root, seg=6)
    return root, b


def cone(r, d, loc, m, parent=None, rot=(0, 0, 0)):
    return K.cone(r, d, loc, m, parent, rot)


def egg_basket(loc, parent=None):
    root = empty("eggs", loc, parent=parent)
    K.cyl(0.3, 0.22, (0, 0, 0.11), mat((180, 130, 70), 0.8), root, r2=0.36)
    K.torus(0.2, 0.02, (0, 0, 0.4), mat((150, 100, 50), 0.7), root, rot=(90, 0, 0), arc=180)
    for i, (x, y) in enumerate(((-0.12, 0), (0.1, 0.05), (0, -0.1), (0.14, -0.1), (-0.1, -0.12))):
        sphere(0.085, (x, y, 0.26 + (i % 2) * 0.03), mat((250, 240, 222), 0.5), root,
               scale=(0.85, 0.85, 1.1))
    return root


def calendar(loc, days, times, yaw=0.0):
    root = empty("cal", loc, (0, 0, yaw))
    box((0.9, 0.08, 1.1), (0, 0, 0), mat(WHITE, 0.7), 0.03, root)
    box((0.9, 0.1, 0.28), (0, -0.01, 0.42), mat(RED, 0.6), 0.03, root)
    text("DAY", (0, -0.08, 0.42), 0.16, mat(WHITE, 0.5), parent=root, extrude=0.003,
         fnt="Montserrat-Black")
    for i, (d, t) in enumerate(zip(days, times)):
        o = text(str(d), (0, -0.08, -0.1), 0.48, mat(INK, 0.6), parent=root, extrude=0.004,
                 fnt="Montserrat-Black")
        nxt = times[i + 1] if i + 1 < len(times) else 999
        key(o, "scale", 0, (0, 0, 0), "CONSTANT")
        key(o, "scale", t, (1, 1, 1), "CONSTANT")
        key(o, "scale", min(998, nxt), (0, 0, 0), "CONSTANT")
    return root


def bakery_interior():
    K.light_day()
    K.sky((250, 230, 200), 0.6)
    K.room(wall=(236, 190, 150), floor=WOOD_L, pattern=False)
    K.counter((0, 1.2, 0), 3.4)
    shelf = empty("breadshelf", (0, 2.75, 0))
    box((3.6, 0.4, 0.08), (0, 0, 1.6), mat(WOOD_D, 0.6), 0.02, shelf)
    box((3.6, 0.4, 0.08), (0, 0, 2.2), mat(WOOD_D, 0.6), 0.02, shelf)
    for z in (1.72, 2.32):
        for i in range(7):
            K.bread((-1.5 + i * 0.5, 0, z), 0.9, shelf)
    text("BAKERY", (0, 2.86, 3.0), 0.5, mat(RED, 0.5), extrude=0.02)
    K.point_light((0, -1.5, 3.2), 180, (255, 220, 170), 0.6)


# ================================================================ shots
def s01(c):  # Imagine tomorrow, everyone is allowed to print their own money.
    square()
    K.sky((255, 200, 150), 0.6, horizon=(255, 230, 190))
    spots = [(-3.0, 3.6, 25), (-0.9, 4.6, 5), (1.3, 4.4, -5), (3.4, 3.4, -25)]
    for i, (x, y, yaw) in enumerate(spots):
        p = K.printing_press((x, y, 0), yaw, 0.85)
        press_pump(p, 0.2 + i * 0.15, c.dur, 0.45)
        spray_bills((x, y - 0.4, 1.3), 0.4 + i * 0.12, c.dur, 9, 1.3, 1.7, seed=i)
    cam = K.Cam(24, 2.8)
    cam.at(0, (0, -4.5, 6.5), (0, 3.8, 1.0))
    cam.at(c.dur, (0, -3.2, 1.8), (0, 3.8, 1.3))
    cam.drift(0, c.dur, 0.03)
    c.pop("TOMORROW", "w:tomorrow", c.dur, at=(0.5, 0.18), size=0.13)


def s02(c):  # Congratulations. You're a millionaire.
    square(presses=False)
    p = K.printing_press((0.9, 1.4, 0), -20, 0.85)
    press_pump(p, 0.0, c.dur, 0.4)
    spray_bills((0.9, 1.1, 1.3), 0.1, c.dur, 18, 1.4, 1.5)
    b = K.boss((-0.5, 0.4, 0), 20)
    K.cash_stack((0.35, -0.1, 0), 14, 1.0, grow=(0.2, c.dur))
    b.expr(c.w("millionaire") - 0.1, eyes="wide", brows="up", mouth="grin")
    b.hop(c.w("millionaire"), 0.18)
    b.idle(0, c.dur)
    cam = K.Cam(34, 1.6)
    cam.at(0, (-0.2, -3.6, 1.3), (-0.3, 0.4, 1.0))
    cam.at(c.dur, (-0.3, -2.8, 1.2), (-0.4, 0.4, 1.05))
    cam.drift(0, c.dur)
    c.pop("$1,000,000", "w:millionaire", c.dur, at=(0.5, 0.2), size=0.12)
    c.icon("$", c.anchor(b.top), "w:millionaire", c.dur, color="green")


def s03(c):  # So is your neighbour.
    square()
    m = K.mo((0.3, 0.6, 0), -15)
    K.cash_stack((1.0, 0.3, 0), 14)
    K.cash_stack((1.0, 0.65, 0), 10)
    m.expr(0.2, eyes="smug", brows="sly", mouth="smile")
    m.arm(0.5, 1, 40, -20)
    m.idle(0, c.dur)
    cam = K.Cam(30, 1.8)
    cam.at(0, (1.5, -3.6, 1.6), (0.6, 0.6, 1.3))
    cam.at(c.dur, (0.9, -3.2, 1.55), (0.6, 0.6, 1.35))
    cam.drift(0, c.dur)
    c.tag("YOUR NEIGHBOUR", (0.5, 0.14), "w:neighbour", c.dur)


def s04(c):  # So is Gus.
    square()
    g = K.gus((-0.35, 0.8, 0), 15)
    K.cash_stack((0.55, 0.75, 0), 20, 1.1, yaw=10)
    g.arm(0.0, 1, 75, -40)
    g.arm(0.0, 0, 30, -20)
    g.expr(0.2, eyes="closed", brows="up", mouth="grin")
    g.idle(0, c.dur, blinks=False)
    g.head_turn(0.6, -10, 10)
    g.head_turn(1.2, -10, -4)
    cam = K.Cam(30, 1.8)
    cam.at(0, (-0.3, -3.8, 1.3), (0.0, 0.7, 1.35))
    cam.at(c.dur, (-0.2, -3.2, 1.35), (0.0, 0.7, 1.45))
    cam.drift(0, c.dur)
    c.icon("heart", c.anchor(g.top), "w:gus", c.dur, offset=(0.12, -0.02))
    c.icon("heart", c.anchor(g.top), c.dur * 0.6, c.dur, offset=(-0.12, 0.0), size=0.06)
    c.tag("GUS", c.anchor(g.top), "w:gus", c.dur, offset=(-0.0, -0.1))


def s05(c):  # Step one, you print a million dollars and run to the store.
    square()
    b = K.boss((-5.0, 1.0, 0), -90)
    case = K.briefcase((0.0, -0.2, -0.45), 90, b.hand_tips[1])
    b.expr(0, eyes="wide", brows="up", mouth="grin")
    b.walk(0.2, c.dur, (4.5, 1.0, 0), -90, step=0.11, bounce=0.06)
    cam = K.Cam(26, 2.4)
    cam.at(0, (-4.5, -3.2, 1.0), (-4.5, 1.0, 0.9))
    cam.at(c.dur, (3.2, -3.2, 1.0), (3.6, 1.0, 0.9))
    cam.drift(0, c.dur, 0.04)
    c.badge([(0.0, "1", "yellow")], at=(0.5, 0.13))
    c.pop("STEP ONE", 0.0, c.dur * 0.55, at=(0.5, 0.24), size=0.1)
    c.tag("THE STORE", (0.83, 0.42), "w:store", c.dur, point="down")


def s06(c):  # But Gus printed ten million, and he got there first.
    bakery_interior()
    g = K.gus((-0.9, 0.5, 0), 115)
    sk = shopkeeper((0.7, 1.9, 0), -35)
    for i, (x, y) in enumerate(((-1.9, 0.9), (-1.5, 1.4), (-2.3, 1.5), (-2.0, 0.2))):
        K.cash_stack((x, y, 0), 16 + i * 3, 1.0, yaw=i * 25)
    g.expr(0.1, eyes="closed", mouth="grin")
    g.idle(0, c.dur)
    sk.expr(c.w("ten"), eyes="wide", brows="up", mouth="open")
    b = K.boss((1.6, -0.5, 0), 30)
    b.expr(0, eyes="open", mouth="smile")
    b.expr(c.w("first"), eyes="wide", brows="sad", mouth="frown")
    cam = K.Cam(26, 2.0)
    cam.at(0, (-0.5, -4.0, 1.6), (-0.2, 0.8, 1.0))
    cam.at(c.dur, (-0.6, -3.5, 1.55), (-0.3, 0.8, 1.05))
    cam.drift(0, c.dur)
    c.pop("$10,000,000", "w:ten", c.dur, at=(0.5, 0.15), size=0.11)
    c.icon("sweat", c.anchor(b.top), "w:first", c.dur, offset=(0.08, 0.0))
    c.tag("FIRST!", c.anchor(g.top), "w:first", c.dur, color="green")


def s07(c):  # The shopkeeper isn't dumb.
    bakery_interior()
    sk = shopkeeper((0, 1.9, 0), 0)
    sk.expr(0.1, eyes="squint", brows="sly", mouth="smile")
    sk.arm(0.4, 1, 150, 0)
    sk.head_turn(0.5, 0, 10)
    sk.idle(0, c.dur)
    cam = K.Cam(36, 1.4)
    cam.at(0, (0.2, -1.6, 1.3), (0, 1.9, 1.1))
    cam.at(c.dur, (0.1, -1.2, 1.3), (0, 1.9, 1.15))
    c.tag("SHOPKEEPER", c.anchor(sk.top), "w:shopkeeper", c.dur, offset=(0, -0.05))
    c.icon("bulb", c.anchor(sk.top), "w:dumb", c.dur, offset=(0.14, 0.02))


def s08(c):  # If everyone has a million, a loaf of bread isn't worth one dollar anymore.
    bakery_interior()
    K.bread((0, 1.0, 0.92), 1.5)
    tag = K.price_tag("$1", (0.3, 0.72, 1.0), 1.0)
    key(tag, "rotation_euler", 0, (0, 0, 0))
    key(tag, "rotation_euler", c.dur, (0, -6, 0))
    cam = K.Cam(40, 1.2)
    cam.at(0, (0.5, -1.6, 1.4), (0, 0.9, 1.1))
    cam.at(c.dur, (0.25, -1.2, 1.35), (0, 0.9, 1.12))
    cam.drift(0, c.dur, 0.01)
    c.badge([("w:million", "$1", "green")], at=(0.82, 0.14), size=0.1)


def s09(c):  # It's worth a thousand.
    bakery_interior()
    K.bread((0, 1.0, 0.92), 1.5)
    t_thousand = c.w("thousand")
    old = K.price_tag("$1", (0.3, 0.72, 1.0), 1.0)
    new = K.price_tag("$1,000", (0.3, 0.72, 1.0), 1.0)
    key(old, "scale", 0, (1, 1, 1), "CONSTANT")
    key(old, "scale", t_thousand, (0, 0, 0), "CONSTANT")
    key(new, "scale", 0, (0, 0, 0), "CONSTANT")
    key(new, "scale", t_thousand, (1.3, 1.3, 1.3))
    key(new, "scale", t_thousand + 0.15, (1, 1, 1))
    cam = K.Cam(40, 1.2)
    cam.at(0, (0.25, -1.2, 1.35), (0, 0.9, 1.12))
    cam.at(c.dur, (0.1, -0.9, 1.32), (0, 0.9, 1.14))
    cam.shake(t_thousand, 0.03)
    c.flash(t_thousand, strength=0.5)
    c.mark("x", t_thousand, c.dur, at=(0.32, 0.35), size=0.12)


def s10(c):  # This is called inflation.
    square(signs={1: "BAKERY", 2: "BARBER"})
    bal, ball = balloon((-1.2, 4.0, 3.2))
    key(bal, "scale", 0, (0.5, 0.5, 0.5))
    key(bal, "scale", c.dur, (2.0, 2.0, 2.0))
    key(bal, "location", c.dur, (-1.2, 4.0, 3.8))
    cam = K.Cam(26, 3.0)
    cam.at(0, (-0.6, -3.0, 1.4), (-1.2, 4.0, 3.0))
    cam.at(c.dur, (-0.7, -2.4, 1.4), (-1.2, 4.0, 3.4))
    cam.drift(0, c.dur)
    c.pop("INFLATION", "w:inflation", c.dur, at=(0.5, 0.78), size=0.13)


def s11(c):  # Step two, everyone prints more to keep up.
    square(lit=True, presses=True)
    presses = [o for o in K.bpy.data.objects if o.name.startswith("press")]
    for i, p in enumerate(presses):
        press_pump(p, i * 0.1, c.dur, 0.3)
        spray_bills((p.location.x, p.location.y - 0.3, 1.2), 0.1 + i * 0.1, c.dur, 10, 1.2, 1.4,
                    seed=10 + i)
    cam = K.Cam(22, 3.0)
    cam.at(0, (-3, -3.5, 3.0), (0, 6, 1.5))
    cam.at(c.dur, (2.5, -3.5, 2.6), (0.5, 6, 1.5))
    cam.drift(0, c.dur, 0.03)
    c.badge([(0.0, "2", "purple")], at=(0.5, 0.13))
    c.pop("STEP TWO", 0.0, c.dur * 0.55, at=(0.5, 0.24), size=0.1, color="white")
    c.meter([(0, 0.2), (c.dur, 0.75)], 0.2, c.dur, label="PRINTING")


def s12(c):  # The printers run all night.
    square(lit=True)
    p = K.printing_press((0.6, 1.2, 0), -25, 0.9)
    press_pump(p, 0, c.dur, 0.25)
    spray_bills((0.6, 0.9, 1.3), 0.0, c.dur, 16, 1.3, 1.3, seed=4)
    b = K.boss((-0.6, 0.6, 0), 25)
    b.expr(0, eyes="half", brows="sad", mouth="flat")
    b.idle(0, c.dur, blinks=False)
    b.head_turn(0.6, 0, 0, 12, 0.4)
    cam = K.Cam(34, 1.6)
    cam.at(0, (-0.1, -3.2, 1.3), (0, 0.9, 1.0))
    cam.at(c.dur, (-0.2, -2.6, 1.25), (-0.1, 0.9, 1.05))
    cam.drift(0, c.dur)
    c.icon("zzz", c.anchor(b.top), 0.4, c.dur, color="white", size=0.07)
    c.tag("ALL NIGHT", (0.5, 0.15), "w:night", c.dur, color="purple")


def s13(c):  # By Friday, one loaf costs a wheelbarrow of cash.
    square()
    b = K.boss((-4.5, 0.5, 0), -90)
    wb = K.wheelbarrow((-3.6, 0.5, 0), 0)
    b.expr(0, eyes="half", brows="sad", mouth="frown")
    b.walk(0.0, c.dur, (1.0, 0.5, 0), -90, step=0.22)
    key(wb, "location", 0, (-3.6, 0.5, 0))
    key(wb, "location", c.dur, (1.9, 0.5, 0), "LINEAR")
    K.bread((3.0, 0.4, 1.0), 1.0)
    K.counter((3.1, 0.6, 0), 1.0, 90)
    cam = K.Cam(28, 2.4)
    cam.at(0, (-3.2, -3.4, 1.4), (-3.4, 0.5, 0.8))
    cam.at(c.dur, (1.4, -3.4, 1.4), (1.6, 0.5, 0.8))
    cam.drift(0, c.dur)
    c.card("FRIDAY", "w:friday", c.dur, at=(0.5, 0.15), color="red")
    c.icon("sweat", c.anchor(b.top), 0.5, c.dur, offset=(0.07, 0))


def s14(c):  # This is called hyperinflation, and it really happened.
    bakery_interior()
    K.bread((0, 1.0, 0.92), 1.5)
    vals = ["$1,000", "$40,000", "$800,000", "$1,000,000"]
    t_h = c.w("hyperinflation")
    tags = [K.price_tag(v, (0.3, 0.72, 1.0), 1.0) for v in vals]
    for i, tg in enumerate(tags):
        ta = 0 if i == 0 else t_h + 0.18 * i
        tb = t_h + 0.18 * (i + 1) if i < len(tags) - 1 else 99
        key(tg, "scale", 0, (0, 0, 0) if i else (1, 1, 1), "CONSTANT")
        key(tg, "scale", ta, (1, 1, 1), "CONSTANT")
        key(tg, "scale", tb, (0, 0, 0), "CONSTANT")
    cam = K.Cam(40, 1.2)
    cam.at(0, (0.0, -1.9, 1.35), (0, 0.9, 1.12))
    cam.at(c.dur, (0.0, -1.4, 1.32), (0, 0.9, 1.14))
    cam.roll(0, 0)
    cam.roll(c.dur, 4)
    c.pop("HYPERINFLATION", "w:hyperinflation", c.dur, at=(0.5, 0.2), size=0.085)
    c.stamp("REAL", "w:really", c.dur, at=(0.72, 0.72), angle=14)


def s15(c):  # In Germany in 1923, kids built towers out of money.
    K.light_day()
    K.sky((200, 180, 150), 0.8)
    K.ground(material=K.mat_cobble((190, 170, 140), (120, 100, 80)))
    K.street(signs={1: "BÄCKEREI", 2: "BANK"}, seed=7)
    kids = [kid("kid1", (-0.9, 0.4, 0), 30, 1), kid("kid2", (0.95, 0.3, 0), -30, 2),
            kid("kid3", (0.1, 1.3, 0), 0, 3)]
    for i, k in enumerate(kids):
        k.idle(0, c.dur)
        k.arm(0.3 + i * 0.2, i % 2, 120, -30)
    tw = empty("tower", (0, 0.4, 0))
    t_t = c.w("towers")
    for j in range(16):
        layer = K.cash_stack((0, 0, j * 0.16), 2, 0.9, tw, yaw=(j % 2) * 90)
        ta = max(0.0, t_t - 1.2 + j * 0.12)
        key(layer, "scale", 0, (0, 0, 0), "CONSTANT")
        key(layer, "scale", ta, (1, 1, 1), "CONSTANT")
    cam = K.Cam(30, 1.8)
    cam.at(0, (0.0, -3.2, 0.7), (0, 0.5, 1.0))
    cam.at(c.dur, (0.0, -3.0, 1.0), (0, 0.5, 1.6))
    cam.drift(0, c.dur)
    c.ov.add("grade", t0=0, t1=99, mode="sepia")
    c.vignette(0, None, strength=0.7)
    c.pop("1923", "w:1923", c.dur, at=(0.5, 0.15), size=0.15)
    c.tag("GERMANY", (0.5, 0.27), "w:germany", c.dur, color="white")


def s16(c):  # In Zimbabwe, prices doubled every day.
    bakery_interior()
    t0 = c.w("doubled")
    times = [0.0] + [t0 + i * 0.3 for i in range(1, 6)]
    price_board([(t, f"${2 ** i:,}", RED) for i, t in enumerate(times)], (0.05, 1.0, 1.55),
                0, 0.5, 1.6, 0.9)
    calendar((-1.2, 1.0, 1.55), list(range(1, 7)), times, 12)
    sk = shopkeeper((1.6, 1.8, 0), -25)
    sk.expr(t0, eyes="wide", brows="up", mouth="open")
    cam = K.Cam(28, 1.6)
    cam.at(0, (0.0, -3.0, 1.5), (0.0, 1.0, 1.5))
    cam.at(c.dur, (0.0, -2.5, 1.5), (0.0, 1.0, 1.52))
    cam.drift(0, c.dur, 0.01)
    c.tag("ZIMBABWE", (0.5, 0.14), "w:zimbabwe", c.dur, color="white")
    c.badge([(t0, "x2", "red")], at=(0.82, 0.62), size=0.12)


def s17(c):  # Step three, the shopkeeper stops taking money at all.
    bakery_interior()
    sk = shopkeeper((0, 1.9, 0), 0)
    stack = K.cash_stack((0.2, 1.2, 0.86), 6)
    t_s = c.w("stops")
    key(stack, "location", t_s, (0.2, 1.2, 0.86))
    key(stack, "location", t_s + 0.35, (0.2, 0.3, 0.86))
    key(stack, "location", t_s + 0.6, (0.2, -0.3, 0.0))
    sk.arm(t_s, 0, 40, -70)
    sk.expr(t_s, eyes="squint", brows="angry", mouth="frown")
    sk.shake(t_s + 0.2, min(c.dur, t_s + 1.0))
    cam = K.Cam(30, 1.6)
    cam.at(0, (0.5, -2.2, 1.35), (0.1, 1.5, 1.0))
    cam.at(c.dur, (0.4, -1.8, 1.35), (0.1, 1.5, 1.05))
    c.badge([(0.0, "3", "red")], at=(0.5, 0.13))
    c.pop("STEP THREE", 0.0, c.dur * 0.5, at=(0.5, 0.24), size=0.1)
    c.mark("x", "w:money", c.dur, at=(0.6, 0.62), size=0.14)


def s18(c):  # He wants eggs.
    bakery_interior()
    sk = shopkeeper((0, 1.9, 0), 0)
    egg_basket((0.45, 1.05, 0.86))
    sk.expr(0, eyes="closed", brows="up", mouth="grin")
    sk.arm(0.2, 1, 60, -60)
    sk.idle(0, c.dur, blinks=False)
    cam = K.Cam(32, 1.4)
    cam.at(0, (0.4, -1.8, 1.35), (0, 1.5, 1.05))
    cam.at(c.dur, (0.3, -1.4, 1.3), (0, 1.5, 1.05))
    c.icon("heart", c.anchor(sk.top), "w:eggs", c.dur)
    c.tag("EGGS", (0.5, 0.75), "w:eggs", c.dur, point="down")


def s19(c):  # Gus pays for a haircut with a chicken.
    K.light_day()
    K.sky((220, 230, 240), 0.6)
    K.room(wall=(120, 170, 200), floor=(230, 230, 230), pattern=True)
    box((2.0, 0.1, 1.4), (0, 2.85, 2.0), mat((200, 220, 235), 0.05, metal=0.6), 0.02)
    text("BARBER", (0, 2.78, 3.1), 0.4, mat(RED, 0.5), extrude=0.02)
    seat = empty("chair", (0.0, 0.9, 0))
    cyl(0.1, 0.5, (0, 0, 0.25), mat((180, 180, 186), 0.3, metal=0.8), seat)
    box((0.9, 0.8, 0.2), (0, 0, 0.6), mat(RED, 0.4), 0.06, seat)
    box((0.9, 0.2, 0.8), (0, 0.4, 1.0), mat(RED, 0.4), 0.06, seat)
    g = K.gus((0.0, 0.8, 0.45), 0)
    g.expr(0, eyes="open", mouth="grin")
    barber = K.townsfolk("barber", (1.4, 0.6, 0), -110, 5)
    barber.expr(0, eyes="open", mouth="smile")
    barber.expr(c.w("chicken"), eyes="wide", brows="up", mouth="open")
    ch = K.chicken((0.55, 0.3, 1.0), -60, 1.0)
    key(ch, "location", 0, (0.55, 0.3, 1.0))
    key(ch, "location", c.w("chicken"), (1.05, 0.35, 1.05))
    g.arm(0.1, 1, 60, -50)
    cam = K.Cam(30, 1.6)
    cam.at(0, (0.6, -2.8, 1.6), (0.5, 0.7, 1.2))
    cam.at(c.dur, (0.7, -2.3, 1.55), (0.6, 0.7, 1.25))
    cam.drift(0, c.dur)
    c.icon("?", c.anchor(barber.top), "w:chicken", c.dur)
    c.tag("HAIRCUT", c.anchor(g.top), "w:haircut", c.dur, offset=(-0.05, -0.08))


def s20(c):  # This is called barter.
    K.light_day()
    K.sky((220, 230, 240), 0.6)
    K.room(wall=(120, 170, 200), floor=(230, 230, 230), pattern=True)
    ch = K.chicken((0.0, 0.6, 0.0), -10, 1.6)
    t_b = c.w("barter")
    key(ch, "location", t_b - 0.05, (0, 0.6, 0))
    key(ch, "location", t_b + 0.15, (0, 0.6, 0.3))
    key(ch, "location", t_b + 0.35, (0, 0.6, 0))
    cam = K.Cam(40, 1.4)
    cam.at(0, (0.0, -3.4, 1.0), (0, 0.6, 0.6))
    cam.at(c.dur, (0.0, -2.8, 0.95), (0, 0.6, 0.65))
    c.pop("BARTER", "w:barter", c.dur, at=(0.5, 0.25), size=0.15)
    c.tag("1 CHICKEN = 1 HAIRCUT", (0.5, 0.75), "w:barter", c.dur, size=0.038, color="white")


def s21(c):  # So countries made one rule.
    K.light_day()
    K.ground()
    bank_building((0, 6.5, 0))
    K.facade((-6.5, 7.0, 0), 0, 4.0, 3, seed=3)
    K.facade((6.5, 7.0, 0), 0, 4.0, 3, seed=4)
    K.lamp_post((-3.5, 3.4, 0))
    K.lamp_post((3.5, 3.4, 0))
    cam = K.Cam(22, 4.0)
    cam.at(0, (0, -6.5, 1.0), (0, 5, 3.2))
    cam.at(c.dur, (0, -4.8, 1.3), (0, 5, 3.3))
    cam.drift(0, c.dur, 0.02)
    c.pop("ONE RULE", "w:rule", c.dur, at=(0.5, 0.18), size=0.12)


def s22(c):  # Only one bank gets to print money, and it has to print slowly.
    K.light_amber()
    K.room(wall=(60, 70, 90), floor=(120, 110, 100), pattern=False)
    p = K.printing_press((0, 1.4, 0), 0, 1.0)
    press_pump(p, 0.0, c.dur, 2.4)
    for x in (-1.6, 1.6):
        box((0.12, 0.12, 2.4), (x, 0.4, 1.2), mat(GOLD, 0.3, metal=1), 0.02)
    box((3.32, 0.12, 0.12), (0, 0.4, 2.4), mat(GOLD, 0.3, metal=1), 0.02)
    for x in (-1.6, 1.6):
        cyl(0.05, 1.1, (x, 0.2, 0.55), mat(GOLD, 0.3, metal=1), seg=12)
    pike = K.pike((1.8, -0.2, 0), 210)
    pike.expr(0, eyes="squint", brows="flat", mouth="flat")
    pike.idle(0, c.dur)
    cam = K.Cam(30, 1.8)
    cam.at(0, (-0.8, -3.6, 1.6), (0.2, 1.2, 1.2))
    cam.at(c.dur, (-0.4, -3.0, 1.5), (0.2, 1.2, 1.25))
    cam.drift(0, c.dur)
    c.badge([("w:one", "1", "yellow")], at=(0.5, 0.13))
    c.tag("SLOWLY", (0.5, 0.8), "w:slowly", c.dur, color="green")


def s23(c):  # This is called a central bank.
    K.light_day()
    K.ground()
    bank_building((0, 6.5, 0))
    cam = K.Cam(30, 3.0)
    cam.at(0, (0, -2.0, 2.0), (0, 5.4, 4.0))
    cam.at(c.dur, (0, 0.6, 3.1), (0, 5.4, 4.3))
    c.pop("CENTRAL BANK", "w:central", c.dur, at=(0.5, 0.75), size=0.1)


def s24(c):  # Gus still has the chicken.
    K.light_amber()
    K.room(wall=(140, 90, 70), floor=WOOD_L, pattern=True)
    sofa = empty("sofa", (0, 1.2, 0))
    box((2.2, 0.9, 0.5), (0, 0, 0.35), mat((90, 120, 80), 0.8), 0.12, sofa)
    box((2.2, 0.3, 0.9), (0, 0.35, 0.8), mat((90, 120, 80), 0.8), 0.12, sofa)
    g = K.gus((0, 1.1, 0.35), 0)
    g.expr(0, eyes="closed", brows="up", mouth="smile")
    ch = K.chicken((0.55, 0.65, 0.85), 20, 0.9)
    key(ch, "rotation_euler", 0, (0, 0, 20))
    key(ch, "rotation_euler", c.dur, (0, 0, -10))
    g.idle(0, c.dur, blinks=False)
    K.bookshelf((-2.4, 2.6, 0))
    cam = K.Cam(32, 1.6)
    cam.at(0, (0.3, -2.4, 1.3), (0, 1.0, 1.1))
    cam.at(c.dur, (0.2, -1.9, 1.3), (0, 1.0, 1.1))
    cam.drift(0, c.dur)
    c.icon("heart", c.anchor(g.top), 0.3, c.dur, offset=(0.1, 0))


def s25(c):  # And that's basically why you're not allowed to print your own money.
    square(presses=True)
    K.sky((255, 200, 150), 0.6, horizon=(255, 230, 190))
    b = K.boss((0, 0.6, 0), 0)
    b.expr(0, eyes="smug", brows="sly", mouth="smile")
    b.idle(0, c.dur)
    cam = K.Cam(30, 3.0)
    cam.at(0, (0, -2.6, 1.3), (0, 0.6, 1.0))
    cam.at(c.dur, (0, -6, 7), (0, 5, 1.5))
    c.pop("NOT ALLOWED", "w:not", c.dur, at=(0.5, 0.2), size=0.11, color="red")


# ================================================================ sound
def a_press(m, T, d, c):
    t = 0.2
    while t < d:
        m.sfx("press", T + t, -6)
        m.sfx("paper", T + t + 0.1, -4)
        t += 0.45


def a_coins(m, T, d, c):
    m.sfx("coins", T + 0.1)
    m.sfx("paper", T + 0.4)


def a_ding(m, T, d, c, word=None):
    m.sfx("ding", T + (c.w(word) if word else 0.1))


def a_step(m, T, d, c):
    m.steps(T + 0.2, T + d, 0.16, "wood", -4)


SHOTS = [
    dict(text="Imagine tomorrow, everyone is allowed to print their own money.", bg="day",
         build=s01, audio=a_press, cut="cut"),
    dict(text="Congratulations. You're a millionaire.", bg="day", build=s02,
         audio=lambda m, T, d, c: (a_press(m, T, d, c), m.add(m.vox["woo"], T + c.w("millionaire") + 0.2, -6))),
    dict(text="So is your neighbour.", bg="day", build=s03,
         audio=lambda m, T, d, c: m.sfx("coins", T + 0.2)),
    dict(text="So is Gus.", bg="day", build=s04,
         audio=lambda m, T, d, c: (m.sfx("paper", T + 0.1), m.add(m.vox["aww"], T + 0.5, -8))),
    dict(text="Step one, you print a million dollars and run to the store.", bg="day",
         build=s05, audio=lambda m, T, d, c: (m.sfx("pop", T + 0.05), a_step(m, T, d, c))),
    dict(text="But Gus printed ten million, and he got there first.", bg="shop", build=s06,
         audio=lambda m, T, d, c: (m.sfx("coins", T + c.w("ten")), m.sfx("huh", T + c.w("first")))),
    dict(text="The shopkeeper isn't dumb.", bg="shop", build=s07,
         audio=lambda m, T, d, c: m.add(m.vox["hm"], T + 0.4, -6)),
    dict(text="If everyone has a million, a loaf of bread isn't worth one dollar anymore.",
         bg="shop", build=s08, audio=lambda m, T, d, c: m.sfx("paper", T + 0.2)),
    dict(text="It's worth a thousand.", bg="shop", build=s09, cut="cut",
         audio=lambda m, T, d, c: (m.sfx("stamp", T + c.w("thousand")), m.add(m.chime, T + c.w("thousand"), -14))),
    dict(text="This is called inflation.", bg="day", build=s10,
         audio=lambda m, T, d, c: (m.sfx("creak", T + 0.2, -4), m.sfx("pop", T + c.w("inflation")))),
    dict(text="Step two, everyone prints more to keep up.", bg="night", build=s11,
         audio=a_press),
    dict(text="The printers run all night.", bg="night", build=s12, audio=a_press),
    dict(text="By Friday, one loaf costs a wheelbarrow of cash.", bg="day", build=s13,
         audio=lambda m, T, d, c: (m.steps(T, T + d, 0.44, "wood", -6), m.sfx("creak", T + 0.6, -6))),
    dict(text="This is called hyperinflation, and it really happened.", bg="shop", build=s14,
         audio=lambda m, T, d, c: [m.sfx("clink", T + c.w("hyperinflation") + 0.18 * i) for i in range(4)] + [m.sfx("stamp", T + c.w("really"))]),
    dict(text="In Germany in 1923, kids built towers out of money.", bg="sepia", build=s15,
         audio=lambda m, T, d, c: [m.sfx("paper", T + max(0, c.w("towers") - 1.2 + j * 0.12), -6) for j in range(0, 16, 2)]),
    dict(text="In Zimbabwe, prices doubled every day.", bg="shop", build=s16,
         audio=lambda m, T, d, c: [m.sfx("book_flip", T + c.w("doubled") + i * 0.3, -4) for i in range(1, 6)]),
    dict(text="Step three, the shopkeeper stops taking money at all.", bg="shop", build=s17,
         audio=lambda m, T, d, c: (m.sfx("pop", T + 0.05), m.sfx("plank", T + c.w("stops") + 0.3), m.add(m.vox["nope"], T + c.w("money"), -6))),
    dict(text="He wants eggs.", bg="shop", build=s18,
         audio=lambda m, T, d, c: m.sfx("ding", T + c.w("eggs"))),
    dict(text="Gus pays for a haircut with a chicken.", bg="interior", build=s19,
         audio=lambda m, T, d, c: m.add(m.vox["cluck"], T + c.w("chicken"), -4)),
    dict(text="This is called barter.", bg="interior", build=s20,
         audio=lambda m, T, d, c: (m.add(m.vox["cluck"], T + c.w("barter") + 0.1, -6), m.sfx("pop", T + c.w("barter")))),
    dict(text="So countries made one rule.", bg="day", build=s21,
         audio=lambda m, T, d, c: m.sfx("stamp", T + c.w("rule"), -4)),
    dict(text="Only one bank gets to print money, and it has to print slowly.", bg="interior",
         build=s22, audio=lambda m, T, d, c: [m.sfx("press", T + 0.3 + 1.2 * i, -8) for i in range(int(d / 1.2))]),
    dict(text="This is called a central bank.", bg="day", build=s23,
         audio=lambda m, T, d, c: (m.add(m.chime, T + c.w("central"), -12), m.sfx("latch", T + c.w("bank")))),
    dict(text="Gus still has the chicken.", bg="interior", build=s24, cut="cut",
         audio=lambda m, T, d, c: m.add(m.vox["cluck"], T + 0.8, -10)),
    dict(text="And that's basically why you're not allowed to print your own money.", bg="day",
         build=s25, audio=lambda m, T, d, c: m.sfx("stamp", T + c.w("not"), -6)),
]
