"""
Second generation 2D sprites: Clockwork Staff icon, staff modules, boss items, the Clockwork Codex spellbook, the
Clockwork Altar block, the module bench GUI and the boss spell icons.
"""
import math

from pixelart import (BRASS, CLEAR, COPPER, CYAN, IRON, LEATHER, OUTLINE, PAPER, bevel_rect, disc, gear, gradient_bg,
                      inner_outline, line, new, noise, put, ramp, rect, rgb, stamp)
from models_v2 import CRYSTAL, ORANGE, SKIN, VIOLET, WOOD

MODULE_COLORS = {
    "splitter": [rgb("5A2306"), rgb("A2470E"), rgb("E07A1E"), rgb("FFB45A"), rgb("FFE2B0")],
    "caliber": [rgb("4A0C10"), rgb("8E1C22"), rgb("D23A36"), rgb("FF7A66"), rgb("FFC8BC")],
    "assembler": [rgb("123A12"), rgb("246E26"), rgb("3FAE3C"), rgb("86E07A"), rgb("CFF8C4")],
    "capacitor": [rgb("4A3A06"), rgb("8E7410"), rgb("D8B428"), rgb("FFE36A"), rgb("FFF6C4")],
    "tesla": CYAN,
}


# ------------------------------------------------------------------------------------------- staff icon

def clockwork_staff_icon():
    img = new(32)
    # twisted shaft from bottom-left to the head
    for i in range(21):
        x, y = 4 + i, 28 - i
        twist = (i // 2) % 2
        put(img, x, y, WOOD[3 if twist else 2])
        put(img, x + 1, y, WOOD[2 if twist else 1])
        put(img, x, y - 1, WOOD[4 if twist else 3])
        put(img, x - 1, y - 1, WOOD[4])
        put(img, x + 1, y + 1, WOOD[0])
    for k in (3, 9, 15):
        x, y = 4 + k, 28 - k
        for dx, dy, c in ((0, 0, BRASS[3]), (1, 0, BRASS[2]), (0, -1, BRASS[4]), (1, -1, BRASS[3]), (-1, 0, BRASS[2]), (0, 1, BRASS[1]), (-1, -1, BRASS[4])):
            put(img, x + dx, y + dy, c)
    for k in range(5, 8):
        put(img, 4 + k, 28 - k, LEATHER[3])
        put(img, 5 + k, 28 - k, LEATHER[2])
    disc(img, 3.5, 28.5, 1.8, BRASS, outline=False)
    inner_outline(img)
    # head: cog ring around a cyan core
    gear(img, 22.5, 9.5, 8.6, 7.0, 12, BRASS, angle=0.1, hole=4.6, tooth_width=0.45)
    disc(img, 22.5, 9.5, 2.6, CYAN, outline=True)
    put(img, 21, 8, CYAN[4])
    # spokes
    for a in (0.5, 2.6, 4.7):
        for r in range(3, 5):
            put(img, round(22.5 + math.cos(a) * r - 0.5), round(9.5 + math.sin(a) * r - 0.5), IRON[2])
    # orange lightning hand to the upper right
    for x, y in ((24, 8), (25, 7), (26, 6), (25, 5), (26, 4), (27, 3), (28, 2)):
        put(img, x, y, ORANGE[3])
    for x, y in ((28, 1), (29, 1), (29, 2), (27, 2)):
        put(img, x, y, ORANGE[4])
    # orbiting orbs
    disc(img, 12.5, 6.5, 1.6, VIOLET, outline=True)
    disc(img, 30, 14, 1.2, VIOLET, outline=False)
    return img


# ------------------------------------------------------------------------------------------- modules

def _module_frame(img, colors, tier):
    """16x16 cartridge: iron casing, brass connector pins, coloured core window, tier pips."""
    bevel_rect(img, 3, 2, 12, 12, IRON[1:5])
    for x in (5, 7, 9, 11):
        put(img, x, 13, BRASS[3])
        put(img, x, 14, BRASS[2])
    rect(img, 4, 3, 11, 9, colors[0])
    rect(img, 5, 4, 10, 8, colors[1])
    for i in range(tier):
        put(img, 5 + i * 3, 11, BRASS[5])
        put(img, 6 + i * 3, 11, BRASS[3])
    put(img, 3, 2, IRON[5])


def module_icon(kind, tier):
    img = new(16)
    c = MODULE_COLORS[kind]
    _module_frame(img, c, tier)
    if kind == "splitter":
        for x, y in ((6, 6), (7, 6), (8, 6)):
            put(img, x, y, c[3])
        line(img, 8, 6, 10, 4, c[4])
        line(img, 8, 6, 10, 6, c[4])
        line(img, 8, 6, 10, 8, c[4])
    elif kind == "caliber":
        rect(img, 6, 5, 9, 7, c[3])
        put(img, 10, 6, c[4])
        rect(img, 5, 5, 5, 7, BRASS[3])
        put(img, 6, 5, c[4])
    elif kind == "assembler":
        gear(img, 7.5, 6.5, 2.8, 2.0, 6, [c[1], c[2], c[3], c[4]], hole=0.7, outline=False)
        put(img, 7, 6, c[0])
    elif kind == "capacitor":
        rect(img, 6, 4, 9, 8, c[2])
        rect(img, 7, 3, 8, 3, BRASS[4])
        for y in (5, 6, 7):
            line(img, 6, y, 9, y, c[3] if y % 2 else c[4])
    elif kind == "tesla":
        for x, y in ((8, 4), (7, 5), (8, 6), (7, 7), (6, 8)):
            put(img, x, y, CYAN[4])
        put(img, 9, 4, CYAN[3])
        put(img, 9, 5, CYAN[2])
    return img


# ------------------------------------------------------------------------------------------- boss items

def dragon_core():
    img = new(16)
    # brass cage
    disc(img, 8, 8, 6.4, BRASS, outline=True)
    disc(img, 8, 8, 4.6, [rgb("0B1430"), rgb("101C44"), rgb("162658"), rgb("1E3270")], outline=False)
    # crystal heart
    heart = [
        "..o.o..",
        ".ozozo.",
        "ozwzyzo",
        "ozyzyxo",
        ".oyzxo.",
        "..oxo..",
        "...o...",
    ]
    stamp(img, 5, 4, heart, {"o": OUTLINE, "w": CRYSTAL[4], "z": CRYSTAL[3], "y": CRYSTAL[2], "x": CRYSTAL[1]})
    for x, y in ((8, 1), (8, 14), (1, 8), (14, 8)):
        put(img, x, y, BRASS[5])
    return img


def dynamo_core():
    """Summoning item: overcharged dynamo sphere crackling with lightning inside a brass gimbal."""
    img = new(16)
    gear(img, 8, 8, 7.6, 6.3, 10, BRASS, hole=4.9, tooth_width=0.45)
    disc(img, 8, 8, 4.4, [rgb("2A1640"), rgb("3E2066"), rgb("5A33A0"), rgb("7A4CD0"), rgb("A88AF0")], outline=True)
    for x, y in ((9, 5), (8, 6), (9, 7), (7, 8), (8, 9), (7, 10)):
        put(img, x, y, CYAN[4])
    put(img, 10, 6, CYAN[3])
    put(img, 6, 9, CYAN[3])
    return img


def codex_icon():
    """Clockwork Codex: indigo leather tome with brass corners and a cog clasp."""
    img = new(16)
    rect(img, 2, 2, 12, 14, SKIN[2])
    for y in range(2, 15):
        put(img, 2, y, SKIN[4])
        put(img, 3, y, SKIN[3])
    rect(img, 13, 3, 13, 13, PAPER[2])
    rect(img, 13, 3, 13, 3, PAPER[3])
    for (x, y) in ((2, 2), (12, 2), (2, 14), (12, 14)):
        put(img, x, y, BRASS[4])
    put(img, 3, 2, BRASS[3])
    put(img, 2, 3, BRASS[3])
    put(img, 11, 14, BRASS[2])
    put(img, 12, 13, BRASS[2])
    gear(img, 7.5, 8.5, 3.6, 2.7, 8, BRASS, hole=0, hub=(1.0, 1.6), outline=False)
    put(img, 7, 8, CRYSTAL[3])
    put(img, 8, 8, CRYSTAL[2])
    inner_outline(img)
    return img


def codex_model_texture():
    """64x64 sheet for irons_spellbooks:item/template_spell_book_model (+ _open): only the top-left 32x32 is used."""
    img = new(64)
    # covers (outside: 0..10 x 9..16, inside: 11..21 x 9..16)
    for y in range(64):
        for x in range(64):
            put(img, x, y, SKIN[2])
    noise(img, 0, 0, 63, 63, 0.06, 77)
    rect(img, 0, 9, 10, 15, SKIN[3])
    for x in range(0, 11):
        put(img, x, 9, SKIN[4])
        put(img, x, 15, SKIN[1])
    for (x, y) in ((0, 9), (10, 9), (0, 15), (10, 15)):
        put(img, x, y, BRASS[4])
    put(img, 5, 12, BRASS[4])
    put(img, 4, 12, BRASS[3])
    put(img, 6, 12, BRASS[3])
    put(img, 5, 11, BRASS[3])
    put(img, 5, 13, BRASS[2])
    put(img, 5, 12, CRYSTAL[3])
    rect(img, 11, 9, 21, 15, SKIN[1])
    # pages
    rect(img, 12, 16, 29, 20, PAPER[2])
    for x in range(12, 30, 2):
        put(img, x, 18, PAPER[1])
    rect(img, 20, 8, 23, 15, PAPER[3])
    # spine
    rect(img, 10, 21, 13, 30, BRASS[2])
    for y in range(21, 31, 3):
        line(img, 10, y, 13, y, BRASS[4])
    rect(img, 0, 31, 9, 31, BRASS[3])
    return img


# ------------------------------------------------------------------------------------------- altar block

def altar_top():
    img = new(16)
    rect(img, 0, 0, 15, 15, IRON[2])
    noise(img, 0, 0, 15, 15, 0.06, 5)
    for i in range(16):
        put(img, i, 0, IRON[4])
        put(img, 0, i, IRON[3])
        put(img, i, 15, IRON[0])
        put(img, 15, i, IRON[1])
    gear(img, 8, 8, 6.8, 5.2, 10, BRASS, hole=2.4, hub=(2.6, 3.3), outline=True)
    disc(img, 8, 8, 2.2, CYAN, outline=False)
    put(img, 7, 7, CYAN[4])
    return img


def altar_side():
    img = new(16)
    rect(img, 0, 0, 15, 15, IRON[1])
    noise(img, 0, 0, 15, 15, 0.07, 9)
    rect(img, 0, 0, 15, 2, BRASS[2])
    line(img, 0, 0, 15, 0, BRASS[4])
    rect(img, 0, 13, 15, 15, BRASS[1])
    line(img, 0, 13, 15, 13, BRASS[3])
    for x in (3, 12):
        rect(img, x, 3, x + 1, 12, COPPER[2])
        line(img, x, 3, x, 12, COPPER[3])
    rect(img, 6, 5, 9, 10, IRON[0])
    rect(img, 7, 6, 8, 9, CYAN[2])
    put(img, 7, 6, CYAN[4])
    for (x, y) in ((1, 4), (14, 4), (1, 11), (14, 11)):
        put(img, x, y, BRASS[4])
    return img


def altar_bottom():
    img = new(16)
    rect(img, 0, 0, 15, 15, IRON[1])
    noise(img, 0, 0, 15, 15, 0.08, 13)
    return img


# ------------------------------------------------------------------------------------------- module bench GUI

def module_gui():
    """256x256 sheet, 176x166 window: three module sockets around a staff silhouette, then the player inventory."""
    img = new(256)
    W, H = 176, 166
    bevel_rect(img, 1, 1, W - 2, H - 2, [rgb("2A1E12"), rgb("4A3520"), rgb("6A4C2C"), rgb("8E6A40"), rgb("B08A58")], outline=OUTLINE)
    noise(img, 2, 2, W - 3, H - 3, 0.05, 31)
    # inner brass-trimmed panel
    rect(img, 7, 15, W - 8, 70, rgb("1C140C"))
    for x in range(7, W - 7):
        put(img, x, 15, BRASS[1])
        put(img, x, 70, BRASS[3])
    for y in range(15, 71):
        put(img, 7, y, BRASS[1])
        put(img, W - 8, y, BRASS[3])
    # cog heart wired to the three sockets
    for (tx, ty) in ((52, 43), (88, 52), (124, 43)):
        line(img, 88, 27, tx, ty, COPPER[2])
        line(img, 88, 28, tx, ty + 1, COPPER[0])
    gear(img, 88, 27, 10, 8, 12, BRASS, hole=5.5, tooth_width=0.45, outline=True)
    disc(img, 88, 27, 3.2, CYAN, outline=True)

    def slot(x, y):
        rect(img, x, y, x + 17, y + 17, rgb("8B8B8B"))
        line(img, x, y, x + 16, y, rgb("373737"))
        line(img, x, y, x, y + 16, rgb("373737"))
        line(img, x + 1, y + 17, x + 17, y + 17, rgb("FFFFFF"))
        line(img, x + 17, y + 1, x + 17, y + 17, rgb("FFFFFF"))

    # module sockets (slot origins are 1px up-left of the item position used by the menu)
    for sx, sy in ((43, 34), (79, 52), (115, 34)):
        rect(img, sx - 2, sy - 2, sx + 19, sy + 19, BRASS[2])
        line(img, sx - 2, sy - 2, sx + 19, sy - 2, BRASS[4])
        slot(sx, sy)
    for row in range(3):
        for col in range(9):
            slot(7 + col * 18, 83 + row * 18)
    for col in range(9):
        slot(7 + col * 18, 141)
    return img


# ------------------------------------------------------------------------------------------- spawn egg free icons

def boss_bar_none():
    return new(16)
