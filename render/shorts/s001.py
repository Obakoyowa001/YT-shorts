"""Short #001 — If You Opened a Bank in 1837 (see scripts/001_wildcat_banks_1837.md)."""
import math

from engine import (CREAM, GOLD, GREY, INK, MONEY, MUD, RED, STEEL, WHITE, WOOD, WOOD_D,
                    WOOD_L, badge, banknote, barrel, bear, book, cloud, coin, crowd_person,
                    dog, ease, floor, ground, hills, lerp, moon, person, pony, pop, press,
                    prog, shack, sign, sparkle, strongbox, sun, tree, wall_planks, wildcat)

VOICE = "en-US-GuyNeural"
RATE = "+40%"
GOLD_WORDS = {"michigan", "legally", "dog", "gold", "silver", "nobody", "wildcats",
              "wildcat", "inspector", "rich", "nails", "glass", "coins", "beautiful",
              "gus", "boots", "laughs", "cents", "town", "run", "money", "bank"}


def forest_bg(c, gy=1500, n=9, off=0, far=True):
    if far:
        hills(c, gy - 40, (150, 190, 130), off * 0.3)
        for i in range(-2, n):
            tree(c, i * 170 + 60 + (off * 0.5) % 170, gy - 30, 0.7, (90, 150, 100), (70, 128, 86))
    ground(c, gy)


# 1 ------------------------------------------------------------------------
def s01(c, t, d):
    c.cam(lerp(1.0, 1.12, ease(t / d)), 540, 1150)
    cloud(c, 160, 420, 1.0)
    cloud(c, 760, 330, 0.8)
    hills(c, 1460, (170, 206, 130))
    ground(c, 1500)
    shack(c, 130, 1500, 0.45, None)
    shack(c, 960, 1500, 0.42, None)
    shack(c, 520, 1560, 1.0, "BANK", sign_sc=pop(t, 0.25))
    sw = math.sin(t * 14) * 40
    person(c, 860, 1600, 1.0, "boss", t, arm_l=10, arm_r=130 + sw, mouth="grin",
           hold_r="hammer")
    s = pop(t, 0.6)
    if s:
        c.rect(110 - 90 * s, 1180 - 110 * s, 110 + 90 * s, 1180 + 110 * s, WHITE, r=10,
               outline=INK, w=5)
        c.rect(110 - 90 * s, 1180 - 110 * s, 110 + 90 * s, 1180 - 60 * s, RED, r=10,
               shadow=False)
        c.text(110, 1200, "1837", 64 * s, INK)


# 2 ------------------------------------------------------------------------
def s02(c, t, d):
    c.cam(lerp(1.0, 1.1, ease(t / d)), 540, 1050)
    wall_planks(c)
    s = pop(t, 0.1)
    if s:
        c.rect(540 - 360 * s, 520 - 120 * s, 540 + 360 * s, 520 + 120 * s, CREAM, r=20,
               outline=WOOD_D, w=6)
        c.text(540, 480, "MICHIGAN GENERAL", 50 * s, INK)
        c.text(540, 560, "BANKING LAW · 1837", 50 * s, INK)
    floor(c, 1500)
    press(c, 480, 1500, 1.0, t)
    for i in range(6):
        u = ((t * 1.3) - i * 0.35)
        if u < 0:
            continue
        u = u % 2.2
        banknote(c, 620 + u * 260, 1340 - u * 180 - math.sin(u * 3) * 40, 220)


# 3 ------------------------------------------------------------------------
def s03(c, t, d):
    c.cam(1.08, lerp(430, 650, ease(t / d)), 1120)
    wall_planks(c)
    c.rect(-200, 1250, 1300, 1330, WOOD_D)
    c.rect(-200, 1330, 1300, 2600, WOOD)
    banknote(c, 220, 1180, 300, "BANK OF YOU", "$5", "name", sc=pop(t, 0.05))
    banknote(c, 560, 1180, 300, "BANK OF YOU", "$5", "face", sc=pop(t, 0.6))
    banknote(c, 900, 1180, 300, "BANK OF YOU", "$10", "dog", sc=pop(t, 1.2))
    if t > 1.5:
        dog(c, 1120, 1250, 0.9 * pop(t, 1.5), t)


# 4 ------------------------------------------------------------------------
def s04(c, t, d):
    c.cam(1.05, 540, 1050)
    wall_planks(c)
    sign(c, 540, 520, 420, 140, "ONE RULE", 76, sc=pop(t, 0.2))
    person(c, 760, 1340, 1.1, "boss", t, arm_l=20, arm_r=20, mouth="flat", look=-1)
    c.rect(-200, 1180, 1300, 1260, WOOD_D)
    c.rect(-200, 1260, 1300, 2600, WOOD)
    u = prog(t, 0.2, 1.6)
    hx = lerp(-120, 420, u)
    c.line([(-300, 1260), (hx - 60, 1205)], (90, 140, 170), 60)
    c.circle(hx - 40, 1200, 30, (241, 198, 160))
    banknote(c, hx + 80, 1150, 260)


# 5 ------------------------------------------------------------------------
def s05(c, t, d):
    c.cam(lerp(1.0, 1.1, ease(t / d)), 540, 1150)
    floor(c, 600, WOOD_L, WOOD)
    person(c, 540, 1000, 1.25, "boss", t, arm_l=40, arm_r=40, mouth="o", sweat=True)
    strongbox(c, 540, 1420, 1.5, "RESERVES", coins=0, t=t)
    coin(c, 540, 1225, 30)
    sparkle(c, 590, 1190, 22, t)


# 6 ------------------------------------------------------------------------
def s06(c, t, d):
    off = t * 160
    c.cam(1.0, 540, 1000)
    cloud(c, 200 - off * 0.2, 420)
    cloud(c, 900 - off * 0.2, 340, 0.7)
    hills(c, 1450, (170, 206, 130), -off * 0.4)
    ground(c, 1500)
    for i in range(-1, 8):
        x = (i * 260 - off) % 1820 - 300
        tree(c, x, 1520, 0.55)
    c.rect(150, 1505, 650, 1540, WOOD_D)  # sled runner
    shack(c, 400, 1505, 0.6, "BANK")
    hands = person(c, 860, 1600, 1.05, "boss", t, arm_l=95, arm_r=95, mouth="grin", walk=1.0)
    c.line([(650, 1500), hands["l"]], WOOD_D, 8)
    badge(c, t, "STEP 1", 0.05)


# 7 ------------------------------------------------------------------------
def s07(c, t, d):
    c.cam(1.0, lerp(330, 760, ease(t / d)), 1050)
    forest_bg(c, 1500, 12)
    bear(c, 200, 1520, 0.9, t)
    sign(c, 520, 1240, 330, 90, "TOWN ← 40 MI", 46, post=230)
    shack(c, 980, 1530, 0.7, "BANK")
    for i, (x, y) in enumerate(((870, 1170), (980, 1110), (1090, 1170))):
        wildcat(c, x, y + 40, 0.55 * pop(t, 0.6 + i * 0.25), t + i, 1 if i % 2 else -1)
    for x in (-150, 1300, 1450):
        tree(c, x, 1600, 1.2)


# 8 ------------------------------------------------------------------------
def s08(c, t, d):
    c.cam(lerp(1.0, 1.15, ease(t / d)), 540, 1150)
    forest_bg(c, 1500, 10)
    for x, s in ((60, 1.4), (1000, 1.5), (300, 1.0), (800, 1.1)):
        tree(c, x, 1560, s)
    k = 1 if int(t / 0.45) % 2 == 0 else -1
    hands = person(c, 540, 1620, 1.1, "folk2", t, arm_l=20, arm_r=120, mouth="o", look=k)
    banknote(c, hands["r"][0] + 40, hands["r"][1] - 60, 200)
    s = pop(t, 0.5)
    if s:
        c.text(700, 900, "?", 160 * s, WHITE, kind="cap", stroke=8)
        c.text(380, 950, "?", 110 * s, WHITE, kind="cap", stroke=6)


# 9 ------------------------------------------------------------------------
def s09(c, t, d):
    c.cam(lerp(1.35, 1.0, ease(t / d)), 540, 1080)
    forest_bg(c, 1550, 10)
    shack(c, 540, 1560, 1.0, "WILDCAT BANK", sign_size=50)
    wildcat(c, 540, 1028, 0.7, t)
    for x in (-60, 1140):
        tree(c, x, 1620, 1.3)


# 10 -----------------------------------------------------------------------
def s10(c, t, d):
    c.cam(1.0, 540, 1050)
    forest_bg(c, 1500, 10)
    x = lerp(-250, 470, prog(t, 0.0, 1.8))
    run = 1.0 if t < 1.8 else 0.0
    pony(c, x, 1560, 1.25, t, (120, 90, 70), run)
    person(c, x - 10, 1360, 0.95, "pike", t, arm_l=40, arm_r=160, mouth="flat",
           hold_r="magnifier")
    s = pop(t, 1.0)
    if s:
        c.rect(800 - 150 * s, 1080 - 180 * s, 800 + 150 * s, 1080 + 180 * s, WOOD_L, r=12,
               outline=WOOD_D, w=6)
        c.rect(800 - 120 * s, 1080 - 140 * s, 800 + 120 * s, 1080 + 160 * s, WHITE,
               shadow=False)
        c.text(800, 1020, "GOLD", 56 * s, INK)
        c.text(800, 1100, "INSPECTION", 40 * s, INK)
    badge(c, t, "STEP 2", 0.05)


# 11 -----------------------------------------------------------------------
def s11(c, t, d):
    c.cam(1.0, 540, 1000)
    c.rect(-200, -200, 540, 2400, (214, 176, 126), shadow=False)
    c.rect(540, -200, 1300, 2400, (200, 190, 220), shadow=False)
    floor(c, 1500)
    c.rect(530, -200, 550, 2400, INK, shadow=False)
    strongbox(c, 270, 1340, 0.85, "EMPTY")
    mx, my = 270 + math.sin(t * 3) * 60, 1150 - t * 120
    flap = abs(math.sin(t * 20)) * 22
    c.ellipse(mx - 18, my, 20, 8 + flap * 0.4, GREY, shadow=False)
    c.ellipse(mx + 18, my, 20, 8 + flap * 0.4, GREY, shadow=False)
    strongbox(c, 800, 1340, 0.85, "GOLD", coins=14)
    pat = abs(math.sin(t * 8)) * 25
    person(c, 820, 1140, 0.8, "mo", t, arm_l=110 - pat, arm_r=20, mouth="grin")
    for i in range(3):
        sparkle(c, 700 + i * 90, 1150, 20, t, i)


# 12 -----------------------------------------------------------------------
def s12(c, t, d):
    mo_x = lerp(150, 1500, t / d)
    c.cam(1.0, mo_x - 80, 1050)
    off = 0
    forest_bg(c, 1500, 16, off)
    for i, txt in enumerate(("MONDAY", "TUESDAY", "WEDNESDAY")):
        sign(c, 500 + i * 650, 1300, 300, 80, txt, 40, post=190)
    seat = pony(c, mo_x, 1560, 0.9, t, (200, 160, 120), 1.0)
    person(c, seat[0] - 10, seat[1] + 120, 0.7, "mo", t, arm_l=150, arm_r=150, mouth="grin")
    strongbox(c, seat[0] - 10, seat[1] - 230, 0.35, "GOLD", coins=7)
    px = mo_x - 650
    pony(c, px, 1520, 0.5, t, (120, 90, 70), 0.6)
    person(c, px, 1440, 0.4, "pike", t, arm_l=30, arm_r=150, mouth="flat", hold_r="magnifier")


# 13 -----------------------------------------------------------------------
def s13(c, t, d):
    k = min(2, int(t / (d / 3)))
    tl = t - k * d / 3
    names = ("BANK OF YOU", "MO'S BANK", "BANK OF BEARS")
    walls = ((214, 170, 118), (196, 186, 220), (190, 214, 170))
    c.cam(1.05, 540, 1050)
    wall_planks(c, col=walls[k], line=tuple(max(0, v - 30) for v in walls[k]))
    sign(c, 540, 500, 560, 120, names[k], 60)
    person(c, 830, 1200, 0.9, "pike", tl, arm_l=30, arm_r=150, mouth="smile",
           hold_r="magnifier")
    c.rect(-200, 1250, 1300, 1330, WOOD_D)
    c.rect(-200, 1330, 1300, 2600, WOOD)
    strongbox(c, 400, 1150, 0.7, None, coins=14)
    c.rect(520, 1110, 680, 1170, (250, 240, 120), r=6, shadow=False)
    c.text(600, 1140, "PROPERTY OF MO", 18, INK)
    s = pop(tl, 0.25)
    if s:
        c.rect(540 - 200 * s, 1450 - 60 * s, 540 + 200 * s, 1450 + 60 * s, None, r=10,
               outline=(40, 150, 70), w=10, shadow=False)
        c.text(540, 1452, "APPROVED", 66 * s, (40, 150, 70), kind="cap")


# 14 -----------------------------------------------------------------------
def s14(c, t, d):
    c.cam(lerp(1.0, 1.1, ease(t / d)), 540, 1150)
    forest_bg(c, 1450, 10)
    sink = prog(t, 0.0, d) * 90
    pony(c, 540, 1560 + sink, 1.1, t * 0.3, (200, 160, 120), 0.2)
    person(c, 500, 1420 + sink, 0.8, "mo", t, arm_l=150, arm_r=150, mouth="sad", sweat=True)
    strongbox(c, 780, 1520 + sink * 1.5, 0.4, "GOLD", coins=5)
    c.ellipse(540, 1640, 520, 120, MUD, shadow=False)
    c.ellipse(540, 1620, 470, 80, (130, 92, 58), shadow=False)
    badge(c, t, "STEP 3", 0.05)


# 15 -----------------------------------------------------------------------
def s15(c, t, d):
    c.cam(1.05, 540, 1150)
    wall_planks(c)
    floor(c, 1550)
    barrel(c, 460, 1400, 1.2, "GOLD")
    hands = person(c, 840, 1640, 1.0, "boss", t, arm_l=20, arm_r=150, mouth="grin")
    bx, by = 700, 950
    c.poly([(bx - 70, by - 60), (bx + 70, by - 60), (bx + 50, by + 60), (bx - 50, by + 60)], STEEL)
    for i in range(14):
        u = ((t * 1.6) + i * 0.13) % 1.0
        x = lerp(bx - 40, 460 + (i % 5 - 2) * 30, u)
        y = lerp(by + 40, 1100, u)
        if i % 3 == 0:
            c.poly([(x, y - 18), (x + 14, y + 10), (x - 12, y + 6)], (190, 230, 240, 220))
        else:
            c.line([(x - 4, y - 22), (x + 4, y + 22)], (120, 124, 134), 6)


# 16 -----------------------------------------------------------------------
def s16(c, t, d):
    c.cam(1.0, 540, 1050)
    floor(c, -200, WOOD_L, WOOD)
    c.circle(540, 1050, 420, WOOD_D)
    c.circle(540, 1050, 380, (80, 80, 90), shadow=False)
    for i in range(30):
        a, r = i * 2.4, 40 + (i * 37) % 300
        c.line([(540 + math.cos(a) * r, 1050 + math.sin(a) * r),
                (540 + math.cos(a) * r + 30, 1050 + math.sin(a) * r + 12)], (150, 154, 164), 7,
               shadow=False)
    n = 0
    for ring, cnt in ((0, 1), (110, 6), (220, 12), (320, 18)):
        for j in range(cnt):
            a = j / cnt * math.tau
            coin(c, 540 + math.cos(a) * ring, 1050 + math.sin(a) * ring, 52,
                 sc=pop(t, 0.05 + n * 0.045, 0.25))
            n += 1
    for i in range(5):
        sparkle(c, 300 + i * 120, 800 + (i % 2) * 450, 26, t, i)


# 17 -----------------------------------------------------------------------
def s17(c, t, d):
    c.cam(1.05, 540, 1100)
    wall_planks(c)
    floor(c, 1550)
    barrel(c, 360, 1400, 1.0, "GOLD", top_fill=GOLD)
    person(c, 760, 1640, 1.0, "pike", t, arm_l=20, arm_r=160 if t < 0.8 else 120,
           mouth="flat" if t < 0.8 else "smile", hold_r="magnifier")
    s = pop(t, 0.75)
    if s:
        c.rect(540 - 220 * s, 700 - 70 * s, 540 + 220 * s, 700 + 70 * s, None, r=10,
               outline=(40, 150, 70), w=12, shadow=False)
        c.text(540, 702, "APPROVED", 74 * s, (40, 150, 70), kind="cap")


# 18 -----------------------------------------------------------------------
def s18(c, t, d):
    c.cam(1.0, 540, 1100)
    forest_bg(c, 1550, 10)
    c.rect(200, 1480, 380, 1560, WOOD)
    c.circle(290, 1480, 40, WOOD_L)
    swing = 0 if t > 0.9 else abs(math.sin(t * 7)) * 90
    hands = person(c, 360, 1620, 1.0, "gus", t, arm_l=20, arm_r=60 + swing,
                   mouth="grin" if t > 1.2 else "smile", hold_r="axe" if t < 0.9 else None)
    bh = person(c, 820, 1620, 0.95, "boss", t, arm_l=15, arm_r=80, mouth="grin", look=-1)
    u = prog(t, 0.9, 1.5)
    nx = lerp(bh["l"][0], hands["r"][0] + 40, u)
    ny = lerp(bh["l"][1], hands["r"][1] - 40, u)
    banknote(c, nx, ny, 220, "WILDCAT BANK", "$5")


# 19 -----------------------------------------------------------------------
def s19(c, t, d):
    u = t / d
    phase = (u * 2) % 1.0
    night = 0.5 - 0.5 * math.cos(u * 2 * math.tau)
    c.cam(1.0, 540, 1000)
    top = tuple(int(lerp(a, b, night)) for a, b in zip((126, 192, 232), (22, 30, 66)))
    c.rect(-600, -400, 1700, 1500, top, shadow=False)
    ang = math.pi * (1 - phase)
    bx, by = 540 + math.cos(ang) * 420, 900 - math.sin(ang) * 520
    (moon if int(u * 2) % 2 else sun)(c, bx, by)
    off = t * 220
    hills(c, 1400, (120, 170, 110), -off * 0.6)
    ground(c, 1500)
    sign(c, (900 - off) % 1600 - 200, 1300, 300, 80, "CITY → 2 DAYS", 38, post=200)
    person(c, 520, 1640, 1.0, "gus", t, arm_l=25, arm_r=25, mouth="smile", walk=1.0)


# 20 -----------------------------------------------------------------------
def s20(c, t, d):
    c.cam(lerp(1.0, 1.08, ease(t / d)), 540, 1100)
    wall_planks(c, col=(196, 206, 176), line=(170, 182, 150))
    for row in range(2):
        c.rect(-100, 560 + row * 260, 1200, 590 + row * 260, WOOD_D)
        for i in range(6):
            x = 60 + i * 190
            c.poly([(x, 550 + row * 260), (x + 40, 550 + row * 260), (x + 40, 470 + row * 260),
                    (x + 20, 450 + row * 260), (x, 450 + row * 260)], (90, 60, 40))
            c.rect(x, 520 + row * 260, x + 90, 550 + row * 260, (90, 60, 40), r=10)
    person(c, 540, 1250, 1.0, "shop", t, arm_l=120, arm_r=120, mouth="flat")
    c.rect(-200, 1250, 1300, 1330, WOOD_D)
    c.rect(-200, 1330, 1300, 2600, WOOD)
    book(c, 540, 1180, 0.8, open_u=prog(t, 1.2, 1.5))
    if t > 1.3:
        for i in range(8):
            a = i / 8 * math.tau
            r = (t - 1.3) * 400
            c.circle(540 + math.cos(a) * r, 1150 + math.sin(a) * r * 0.5, 40 - (t - 1.3) * 20,
                     (220, 210, 190, max(0, int(180 - (t - 1.3) * 160))), shadow=False)


# 21 -----------------------------------------------------------------------
def s21(c, t, d):
    c.cam(1.0, 540, 1000)
    c.rect(-200, -200, 1300, 2400, (120, 40, 40), shadow=False)
    c.rect(60, 300, 1020, 1350, CREAM, r=10)
    rows = (("BANK OF MICHIGAN", "GOOD"), ("MO'S BANK", "50¢"), ("FARMERS BANK", "80¢"),
            ("WILDCAT BANK", "3¢"))
    for i, (n, v) in enumerate(rows):
        y = 430 + i * 230
        c.text(110, y, n, 50, INK, anchor="lm")
        c.text(960, y, v, 56, RED if i == 3 else INK, anchor="rm")
        c.line([(100, y + 70), (980, y + 70)], (190, 180, 160), 4)
    s = pop(t, 0.3)
    if s:
        c.ellipse(540, 1120, 470 * s, 100 * s, None, outline=RED, w=12, shadow=False)
    if t > 0.9:
        c.text(800, 440, "HA HA!", 90 * pop(t, 0.9), WHITE, kind="cap", stroke=8)
    gx, gy = 540, 1560
    c.circle(gx, gy + 60, 120, (241, 198, 160))
    shrink = prog(t, 1.6, 2.4)
    if shrink < 1:
        banknote(c, gx, gy - 40, 320 * (1 - shrink) + 1, "WILDCAT BANK", "$5")
    else:
        for i in range(3):
            coin(c, gx - 50 + i * 50, gy - 20 - i * 6, 22, sc=0.6)


# 22 -----------------------------------------------------------------------
def s22(c, t, d):
    c.cam(1.0, 540, 1050)
    moon(c, 860, 360)
    forest_bg(c, 1500, 10)
    shack(c, 1100, 1520, 0.8, "WILDCAT BANK", sign_size=40)
    march = t * 90
    order = [(-250, 1.0, False, None), (-60, 0.9, True, None), (120, 0.95, False, "WE WANT GOLD"),
             (300, 0.85, True, None), (-420, 0.85, True, "GOLD!"), (470, 0.8, False, None)]
    for i, (x, s, lan, txt) in sorted(enumerate(order), key=lambda p: p[1][1]):
        crowd_person(c, x + march, 1600 + (1 - s) * -150, s, t, i, lan, txt)
    person(c, 520 + march, 1680, 1.05, "gus", t, arm_l=150, arm_r=25, mouth="o", walk=1.0)


# 23 -----------------------------------------------------------------------
def s23(c, t, d):
    c.cam(1.25, 540, 1150)
    wall_planks(c)
    person(c, 700, 1500, 1.2, "boss", t, arm_l=60, arm_r=60, mouth="o", sweat=True, look=-1)
    barrel(c, 400, 1450, 1.1, None, top_fill=(130, 134, 144))
    y = lerp(900, 1180, prog(t, 0.1, 0.5))
    c.line([(420, y - 30), (426, y + 30)], (120, 124, 134), 8)


# 24 -----------------------------------------------------------------------
def s24(c, t, d):
    c.cam(1.0, 540, 1050)
    wall_planks(c)
    floor(c, 1550)
    c.rect(60, 1000, 300, 1550, (40, 26, 18), shadow=False)  # back door open
    sign(c, 820, 700, 300, 100, "CLOSED", 60, bg=RED, fg=WHITE, sc=pop(t, 0.15))
    bx = lerp(700, -200, prog(t, 0.1, 1.2))
    person(c, bx, 1640, 1.0, "boss", t, arm_l=80, arm_r=80, mouth="o", walk=1.0, look=-1)
    for i in range(4):
        x = lerp(1400, 900 - i * 120, prog(t, 0.3 + i * 0.1, 1.5))
        crowd_person(c, x, 1660, 0.9, t, i, i % 2 == 0)
    badge(c, t, "BANK RUN", 0.2)


# 25 -----------------------------------------------------------------------
def s25(c, t, d):
    if t > d - 0.7:  # match-cut back to the opening for the loop
        s01(c, 0.0, 3.0)
        return
    c.cam(lerp(1.25, 1.0, ease(t / (d - 0.7))), 540, 1100)
    c.rect(-600, -400, 1700, 2600, (230, 236, 240), shadow=False)
    c.rect(-600, 1550, 1700, 2600, (180, 186, 196), shadow=False)
    press(c, 300, 1550, 1.0, t)
    for i in range(4):
        u = ((t * 1.2) - i * 0.4) % 2.0
        banknote(c, 420 + u * 160, 1350 - u * 120, 160, "", "$1", "modern", col=(200, 214, 196))
    hands = person(c, 780, 1680, 1.05, "gus", t, arm_l=20, arm_r=140, mouth="grin", boots=True)
    banknote(c, hands["r"][0] + 20, hands["r"][1] - 70, 220, "", "$1", "modern",
             col=(200, 214, 196))


SEGMENTS = [
    dict(text="If you opened a bank in Michigan in 1837, congratulations.", bg="day", draw=s01),
    dict(text="You're legally allowed to print your own money.", bg="interior", draw=s02),
    dict(text="Your name, your face, a picture of your dog. Anything.", bg="interior", draw=s03),
    dict(text="There's just one rule. If someone brings your paper money back,", bg="interior",
         draw=s04),
    dict(text="you have to swap it for real gold or silver.", bg="interior", draw=s05),
    dict(text="So, step one, you build your bank where nobody can find it.", bg="day", draw=s06),
    dict(text="Deep in the woods, past the bears, right next to the wildcats.", bg="forest",
         draw=s07),
    dict(text="Nobody can cash out if nobody can find the door.", bg="forest", draw=s08),
    dict(text="This is called a wildcat bank.", bg="forest", draw=s09),
    dict(text="Step two, the inspector is coming to count your gold.", bg="forest", draw=s10),
    dict(text="You don't have any gold. But the bank next door does.", bg="interior", draw=s11),
    dict(text="So one box of gold rides through the forest, one day ahead of the inspector.",
         bg="forest", draw=s12),
    dict(text="Every bank he visits looks rich.", bg="interior", draw=s13),
    dict(text="Step three, the box doesn't show up.", bg="forest", draw=s14),
    dict(text="So you fill a barrel with nails and broken glass,", bg="interior", draw=s15),
    dict(text="and put one layer of coins on top.", bg="interior", draw=s16),
    dict(text="The inspector opens it. Beautiful.", bg="interior", draw=s17),
    dict(text="Then Gus gets paid in your money.", bg="forest", draw=s18),
    dict(text="He walks two days into the city to buy boots.", bg="day", draw=s19),
    dict(text="The shopkeeper opens a giant book listing every bank in America,", bg="shop",
         draw=s20),
    dict(text="finds yours, and laughs. Gus's dollar is now worth a few cents.", bg="shop",
         draw=s21),
    dict(text="Then the whole town shows up at once, wanting their gold.", bg="night", draw=s22),
    dict(text="You have nails.", bg="interior", draw=s23),
    dict(text="This is called a bank run.", bg="interior", draw=s24),
    dict(text="And that's basically why you're not allowed to print your own money anymore.",
         bg="modern", draw=s25),
]
