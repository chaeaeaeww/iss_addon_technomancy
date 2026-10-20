"""
Third content update sprites: Technomancer skin (64x64 player layout), Rocket Hand cable, Magnetic Field sigils,
icons for Rocket Grab / Magnetic Field / EMP Screech / Call the Tech Drake and the Short Circuit effect.
"""
import math

from pixelart import (BRASS, COPPER, CYAN, IRON, OUTLINE, CLEAR, disc, gear, gradient_bg, inner_outline, line, new, noise, put,
                      ramp, rect, rgb, stamp)
from sprites import _frame
from models_v2 import CRYSTAL, SKIN

RED = [rgb("3E0A0A"), rgb("6A1414"), rgb("8E1F1F"), rgb("B02A2A"), rgb("D04040")]
GOLD = [rgb("6A4A12"), rgb("9A7020"), rgb("C99A34"), rgb("E6C25A"), rgb("FFE59A")]
FACE = [rgb("9C8878"), rgb("BFAE9E"), rgb("D8C9B8"), rgb("ECE0D2")]
HAIR = [rgb("1E140F"), rgb("2E2018"), rgb("3B2A22"), rgb("54402F")]
NAVY = [rgb("14161F"), rgb("1E2130"), rgb("2A2E42"), rgb("383D55")]
GLOVE = [rgb("0E0E10"), rgb("1A1A1E"), rgb("26262C")]
LENS = [rgb("0E5A4C"), rgb("1FA88E"), rgb("4FE3C0"), rgb("B6FFF0")]


# ------------------------------------------------------------------------------------------- skin helpers

def box(img, u, v, w, h, d, paint):
    """paint(face, x, y, fw, fh) for the six faces of a box-UV part at (u, v)."""
    faces = {
        "top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d),
        "right": (u, v + d, d, h), "front": (u + d, v + d, w, h),
        "left": (u + d + w, v + d, d, h), "back": (u + 2 * d + w, v + d, w, h),
    }
    for face, (x, y, fw, fh) in faces.items():
        paint(face, x, y, fw, fh)


def fill(img, x, y, w, h, colors, base=0.55, seed=0, grain=0.05):
    for j in range(h):
        for i in range(w):
            t = base + 0.25 * (0.5 - j / max(1, h - 1)) * 0.6
            put(img, x + i, y + j, ramp(colors, t))
    if grain:
        noise(img, x, y, x + w - 1, y + h - 1, grain, seed)


def technomancer_skin():
    img = new(64)

    # ---- head: pale face, swept dark hair, brass goggles with teal lenses
    def head(face, x, y, w, h):
        fill(img, x, y, w, h, FACE, 0.6, seed=x + y, grain=0.03)
        if face in ("top", "back"):
            fill(img, x, y, w, h, HAIR, 0.55, seed=x * 3 + y, grain=0.08)
        elif face in ("left", "right"):
            fill(img, x, y, w, 4, HAIR, 0.55, seed=x + y * 5, grain=0.08)
            put(img, x + (w - 2 if face == "right" else 1), y + 4, HAIR[2])
            for i in range(w):
                put(img, x + i, y + 3, GOLD[2])  # goggle strap
        elif face == "front":
            fill(img, x, y, w, 2, HAIR, 0.55, seed=x + 9, grain=0.08)
            put(img, x + 1, y + 2, HAIR[2])
            put(img, x + 6, y + 2, HAIR[3])
            put(img, x + 7, y + 2, HAIR[2])
            # goggles on row 3-4
            for i in range(w):
                put(img, x + i, y + 3, GOLD[2])
            for gx in (x + 1, x + 5):
                put(img, gx, y + 3, GOLD[3])
                put(img, gx + 1, y + 3, GOLD[3])
                put(img, gx, y + 4, LENS[2])
                put(img, gx + 1, y + 4, LENS[3])
                put(img, gx - 1 if gx == x + 1 else gx + 2, y + 4, GOLD[1])
            put(img, x + 3, y + 4, GOLD[1])
            put(img, x + 4, y + 4, GOLD[1])
            # thin mouth, sharp chin
            put(img, x + 3, y + 6, FACE[0])
            put(img, x + 4, y + 6, FACE[0])
            put(img, x + 2, y + 5, FACE[1])
            put(img, x + 5, y + 5, FACE[1])
            put(img, x, y + 7, FACE[1])
            put(img, x + 7, y + 7, FACE[1])
        elif face == "bottom":
            fill(img, x, y, w, h, FACE, 0.35, grain=0)

    box(img, 0, 0, 8, 8, 8, head)

    # hat layer: hair volume on top/back
    def hat(face, x, y, w, h):
        if face == "top":
            for j in range(h):
                for i in range(w):
                    if j < 6 or i in (0, w - 1):
                        put(img, x + i, y + j, ramp(HAIR, 0.45 + 0.1 * ((i + j) % 3)))
        elif face == "front":
            for i in range(w):
                put(img, x + i, y, HAIR[3 if i % 3 else 2])
            put(img, x + 6, y + 1, HAIR[3])
            put(img, x + 7, y + 1, HAIR[2])
        elif face in ("left", "right", "back"):
            for i in range(w):
                put(img, x + i, y, HAIR[2])
                put(img, x + i, y + 1, HAIR[1] if (i % 2) else HAIR[2])

    box(img, 32, 0, 8, 8, 8, hat)

    # ---- torso: red coat, gold trim, cyan chest core
    def body(face, x, y, w, h):
        fill(img, x, y, w, h, RED, 0.5, seed=x * 7 + y)
        if face == "front":
            for j in range(h):
                put(img, x + 3, y + j, GOLD[2])
                put(img, x + 4, y + j, GOLD[3])
            for i in range(w):
                put(img, x + i, y, GOLD[3])
                put(img, x + i, y + 1, GOLD[1])
            put(img, x + 1, y + 5, CYAN[2])
            put(img, x + 2, y + 5, CYAN[3])
            put(img, x + 1, y + 6, CYAN[1])
            for i in range(w):
                put(img, x + i, y + 9, NAVY[1])  # belt
            put(img, x + 3, y + 9, GOLD[4])
            put(img, x + 4, y + 9, GOLD[3])
        elif face == "back":
            for i in range(w):
                put(img, x + i, y, GOLD[3])
                put(img, x + i, y + 9, NAVY[1])
            line(img, x + 2, y + 2, x + 5, y + 2, COPPER[2])
            line(img, x + 2, y + 2, x + 2, y + 7, COPPER[2])
        elif face in ("left", "right"):
            put(img, x + 1, y + 9, NAVY[1])
            put(img, x + 2, y + 9, NAVY[1])
        elif face == "top":
            fill(img, x, y, w, h, GOLD, 0.6, grain=0)

    box(img, 16, 16, 8, 12, 4, body)

    def jacket(face, x, y, w, h):
        # high gold collar and coat tails flare
        if face in ("front", "back", "left", "right"):
            for i in range(w):
                put(img, x + i, y, GOLD[4] if face != "back" else GOLD[3])
            for j in range(10, h):
                for i in range(w):
                    if face != "front" or i in (0, 1, w - 2, w - 1):
                        put(img, x + i, y + j, RED[2] if (i + j) % 2 else RED[3])

    box(img, 16, 32, 8, 12, 4, jacket)

    # ---- right arm: red sleeve, gold cuff, black glove
    def arm_r(face, x, y, w, h):
        fill(img, x, y, w, h, RED, 0.5, seed=x + y * 3)
        if face not in ("top", "bottom"):
            for i in range(w):
                put(img, x + i, y + 8, GOLD[3])
            fill(img, x, y + 9, w, 3, GLOVE, 0.5, grain=0)
            put(img, x, y + 1, GOLD[2])
        elif face == "bottom":
            fill(img, x, y, w, h, GLOVE, 0.5, grain=0)
        elif face == "top":
            fill(img, x, y, w, h, GOLD, 0.65, grain=0)

    box(img, 40, 16, 4, 12, 4, arm_r)

    def sleeve_r(face, x, y, w, h):
        if face in ("front", "back", "left", "right", "top"):
            for i in range(w):
                put(img, x + i, y, GOLD[4])
                put(img, x + i, y + 1, GOLD[2])
                if face != "top":
                    put(img, x + i, y + 2, GOLD[1])

    box(img, 40, 32, 4, 12, 4, sleeve_r)

    # ---- left arm: mechanical (blackened iron, brass joints, teal lights)
    def arm_l(face, x, y, w, h):
        fill(img, x, y, w, h, IRON, 0.35, seed=x * 5 + y)
        if face not in ("top", "bottom"):
            for j in (3, 7):
                for i in range(w):
                    put(img, x + i, y + j, BRASS[3])
            put(img, x + 1, y + 5, LENS[2])
            put(img, x + 2, y + 10, LENS[3])
            line(img, x + w - 1, y, x + w - 1, y + h - 1, IRON[1])
        elif face == "top":
            fill(img, x, y, w, h, BRASS, 0.6, grain=0)

    box(img, 32, 48, 4, 12, 4, arm_l)

    def sleeve_l(face, x, y, w, h):
        if face in ("front", "back", "left", "right", "top"):
            for i in range(w):
                put(img, x + i, y, GOLD[4])
                put(img, x + i, y + 1, RED[2])

    box(img, 48, 48, 4, 12, 4, sleeve_l)

    # ---- legs: navy trousers, black boots with gold buckle
    def leg(face, x, y, w, h):
        fill(img, x, y, w, h, NAVY, 0.55, seed=x + y * 7)
        if face not in ("top", "bottom"):
            fill(img, x, y + 8, w, 4, GLOVE, 0.5, grain=0)
            if face == "front":
                put(img, x + 1, y + 8, GOLD[3])
                put(img, x + 2, y + 8, GOLD[3])
        elif face == "bottom":
            fill(img, x, y, w, h, GLOVE, 0.3, grain=0)

    box(img, 0, 16, 4, 12, 4, leg)
    box(img, 16, 48, 4, 12, 4, leg)

    def coat_tail(face, x, y, w, h):
        if face in ("front", "back", "left", "right"):
            for j in range(0, 6):
                for i in range(w):
                    if face != "front" or i in (0, w - 1):
                        put(img, x + i, y + j, RED[2] if (i + j) % 2 else RED[3])
            if face != "front":
                for i in range(w):
                    put(img, x + i, y + 5, GOLD[3])

    box(img, 0, 32, 4, 12, 4, coat_tail)
    box(img, 0, 48, 4, 12, 4, coat_tail)
    return img


# ------------------------------------------------------------------------------------------- effect textures

def cable():
    img = new(16)
    for y in range(16):
        for x in range(16):
            t = 0.65 - abs(x - 7.5) / 8 * 0.6
            put(img, x, y, ramp([rgb("141418"), rgb("22222A"), rgb("33333E"), rgb("454552")], t))
    for y in (0, 1, 8, 9):
        for x in range(16):
            put(img, x, y, ramp(COPPER, 0.7 - abs(x - 7.5) / 8 * 0.5))
    return img


def magnetic_sigil(size=128, inner=False):
    img = new(size)
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            dx, dy = x - c, y - c
            r = math.hypot(dx, dy) / c
            a = math.atan2(dy, dx)
            alpha = 0
            col = CYAN[2]
            if not inner:
                if 0.94 <= r <= 0.99:
                    alpha = 230
                    col = CYAN[3]
                elif 0.86 <= r <= 0.9 and (a * 24 / math.pi) % 2 < 1.2:
                    alpha = 200  # cog teeth ring
                elif 0.70 <= r <= 0.72:
                    alpha = 150
                elif 0.72 < r < 0.86 and abs(((a * 8 / math.pi) % 2) - 1) < 0.06:
                    alpha = 170  # spokes / field lines
                elif r < 0.94:
                    alpha = int(40 * (1 - r) + 25 * r)
                    col = CYAN[1]
            else:
                if 0.9 <= r <= 0.97:
                    alpha = 220
                    col = CYAN[3]
                elif r < 0.9:
                    swirl = (a * 3 + r * 9) % (2 * math.pi)
                    if swirl < 0.5:
                        alpha = 200
                        col = CYAN[4] if r < 0.5 else CYAN[2]
                    else:
                        alpha = int(30 * (1 - r))
                        col = CYAN[1]
            if alpha:
                put(img, x, y, (col[0], col[1], col[2], alpha))
    return img


# ------------------------------------------------------------------------------------------- icons

def icon_rocket_grab():
    img = gradient_bg(new(16), (110, 70, 24), (30, 16, 8))
    for y in (5, 8, 11):
        line(img, 1, y, 5, y, rgb("E6C25A"))
    fist = [
        "..oooooo.",
        ".o3343331",
        "o33433331",
        "o22222221",
        "o222oo221",
        ".o22oo221",
        "..o11111.",
    ]
    stamp(img, 6, 4, fist, {"o": OUTLINE, "1": BRASS[1], "2": BRASS[2], "3": BRASS[3], "4": BRASS[4]})
    put(img, 9, 8, CYAN[3])
    put(img, 10, 8, CYAN[2])
    _frame(img, BRASS[4])
    return img


def icon_magnetic_field():
    img = gradient_bg(new(16), (20, 60, 80), (6, 14, 24))
    for r, col in ((6.5, CYAN[2]), (4.5, CYAN[1])):
        for k in range(48):
            a = k * math.pi / 24
            put(img, round(7.5 + math.cos(a) * r), round(7.5 + math.sin(a) * r * 0.6 + 1), col)
    magnet = [
        "r..b",
        "r..b",
        "r..b",
        "rrbb",
        ".rb.",
    ]
    stamp(img, 6, 3, magnet, {"r": rgb("D04040"), "b": rgb("4060D0")})
    put(img, 6, 3, rgb("F0F0F0"))
    put(img, 9, 3, rgb("F0F0F0"))
    for x, y in ((3, 12), (12, 12), (7, 14)):
        put(img, x, y, CYAN[4])
    _frame(img, CYAN[3])
    return img


def icon_emp_screech():
    img = gradient_bg(new(16), (40, 24, 70), (10, 6, 22))
    for r in (3, 6, 9):
        for k in range(-6, 7):
            a = k * 0.12
            put(img, round(2 + math.cos(a) * r), round(8 + math.sin(a) * r), CYAN[3] if r < 9 else CYAN[2])
    for x, y in ((9, 4), (10, 5), (9, 6), (10, 7), (11, 8)):
        put(img, x, y, rgb("FFF2A0"))
    put(img, 2, 8, CYAN[4])
    _frame(img, CYAN[3])
    return img


def icon_summon_drake():
    img = gradient_bg(new(16), (24, 30, 80), (6, 6, 20))
    head = [
        "....cc......",
        "...cwc......",
        "..oggggo....",
        ".ogsgggggo..",
        "oggggegggggo",
        "ossssssggggo",
        ".ottttsssso.",
        "..oooooooo..",
    ]
    stamp(img, 2, 4, head, {"o": OUTLINE, "g": rgb("D9AD55"), "s": SKIN[3], "t": rgb("F3EEE2"), "e": CYAN[4], "c": CRYSTAL[3], "w": CRYSTAL[4]})
    _frame(img, CRYSTAL[3])
    return img


def effect_short_circuit():
    img = new(18)
    disc(img, 9, 9, 8, [rgb("0E3A4A"), rgb("17607A"), rgb("2A8FB0"), rgb("4FC8E8")], outline=True)
    bolt = [
        "....yy",
        "...yy.",
        "..yyyy",
        "...yy.",
        "..yy..",
        ".yy...",
    ]
    stamp(img, 5, 5, bolt, {"y": rgb("FFF2A0")})
    for x, y in ((3, 4), (14, 13), (4, 14)):
        put(img, x, y, CYAN[4])
    return img
