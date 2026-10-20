"""
Item, icon and particle sprites. Every function returns a PIL image; generate_assets.py saves them.
"""
import math

from pixelart import (BRASS, CLEAR, CLOTH, COPPER, CYAN, IRON, LEATHER, OUTLINE, PAPER, STEAM, STONE, bevel_rect, disc,
                      gear, gradient_bg, inner_outline, line, new, noise, put, ramp, rect, rgb, stamp)

# Shared palette for hand-drawn grids
P = {
    "o": OUTLINE,
    "1": BRASS[1], "2": BRASS[2], "3": BRASS[3], "4": BRASS[4], "5": BRASS[5],
    "a": COPPER[1], "b": COPPER[2], "c": COPPER[3], "d": COPPER[4],
    "l": LEATHER[1], "m": LEATHER[2], "n": LEATHER[3], "p": LEATHER[4],
    "i": IRON[1], "j": IRON[2], "k": IRON[3], "q": IRON[4], "r": IRON[5],
    "x": CYAN[1], "y": CYAN[2], "z": CYAN[3], "w": CYAN[4],
    "s": STONE[1], "t": STONE[2], "u": STONE[3], "v": STONE[4],
    "e": CLOTH[1], "f": CLOTH[2], "g": CLOTH[3],
}


def check(rows, width):
    for r in rows:
        assert len(r) == width, (len(r), r)
    return rows


# ------------------------------------------------------------------------------------------- items

def arcane_cog():
    img = new(16)
    gear(img, 8, 8, 7.7, 5.9, 8, BRASS, angle=-math.pi / 16, hole=0, hub=(3.0, 3.9), spokes=4, tooth_width=0.5)
    disc(img, 8, 8, 2.2, CYAN, outline=True)
    put(img, 7, 7, CYAN[4])
    return img


def technomancy_rune():
    img = new(16)
    # Stone tablet, 12x14, same silhouette language as Iron's runes: lit top lip, dark lower edge, clipped corners
    x0, y0, x1, y1 = 2, 1, 13, 14
    rect(img, x0, y0, x1, y1, STONE[2])
    line(img, x0, y0, x1, y0, STONE[4])
    line(img, x0, y0 + 1, x1, y0 + 1, STONE[3])
    line(img, x0, y0, x0, y1, STONE[3])
    line(img, x1, y0, x1, y1, STONE[1])
    line(img, x0, y1, x1, y1, STONE[0])
    noise(img, x0, y0 + 2, x1 - 1, y1 - 1, 0.06, 11)
    for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        put(img, cx, cy, CLEAR)
    inner_outline(img)
    # recessed copper plate
    rect(img, 4, 4, 11, 11, COPPER[0])
    line(img, 4, 4, 11, 4, OUTLINE)
    line(img, 4, 4, 4, 11, OUTLINE)
    line(img, 5, 11, 11, 11, COPPER[2])
    line(img, 11, 5, 11, 11, COPPER[2])
    glyph = check([
        "..4.4..",
        ".44344.",
        "433x334",
        ".3xyx3.",
        "433x332",
        ".33332.",
        "..2.2..",
    ], 7)
    stamp(img, 4, 4, glyph, P)
    put(img, 7, 7, CYAN[4])
    return img


def upgrade_orb_layer_frames(frames=8):
    """Animated school layer drawn over Iron's dark orb base: a spinning brass cog with a glowing core."""
    sheet = new(16, 16 * frames)
    for f in range(frames):
        frame = new(16)
        gear(frame, 8, 8, 5.2, 3.9, 6, BRASS, angle=f * (2 * math.pi / 6) / frames, hub=None, tooth_width=0.5)
        disc(frame, 8, 8, 1.8, CYAN, outline=False)
        put(frame, 7, 7, CYAN[4])
        sheet.paste(frame, (0, 16 * f))
    return sheet


def scroll_technomancy():
    img = new(16)
    rows = check([
        "................",
        "..oooooooooooo..",
        ".o3444444444441o",
        ".o2333333333321o",
        "..oooooooooooo..",
        "...o32222222o...",
        "...o2bbbbbb2o...",
        "...o2b4334b2o...",
        "...o2b3xx3b2o...",
        "...o2b4334b2o...",
        "...o2bbbbbb2o...",
        "...o32222222o...",
        "..oooooooooooo..",
        ".o3444444444441o",
        ".o2333333333321o",
        "..oooooooooooo..",
    ], 16)
    stamp(img, 0, 0, rows, P)
    # parchment body
    paper = {"2": PAPER[2], "3": PAPER[3], "b": PAPER[1]}
    for y in range(5, 12):
        for x in range(4, 12):
            px = rows[y][x]
            if px in paper:
                put(img, x, y, paper[px])
    gear(img, 8, 8.5, 2.6, 1.9, 6, COPPER, hole=0, outline=False)
    put(img, 8, 8, CYAN[3])
    return img


def affinity_ring():
    img = new(16)
    # band
    for py in range(16):
        for px in range(16):
            dx, dy = (px + 0.5 - 8) / 5.6, (py + 0.5 - 10) / 4.6
            d = math.hypot(dx, dy)
            if 0.62 <= d <= 1.0:
                t = 0.5 + 0.45 * (-(dx) - (dy)) / (d or 1)
                put(img, px, py, ramp(BRASS, t))
    inner_outline(img)
    gear(img, 8, 5, 4.4, 3.3, 8, COPPER, hub=None, tooth_width=0.5)
    disc(img, 8, 5, 1.9, CYAN)
    return img


def clockwork_scepter():
    """32x32 handheld staff: blackened iron haft with brass bands, gear head clutching a cyan crystal."""
    img = new(32)
    # haft from bottom-left to the head
    for i in range(22):
        x, y = 3 + i, 29 - i
        put(img, x, y, IRON[3])
        put(img, x + 1, y, IRON[2])
        put(img, x, y - 1, IRON[4])
        put(img, x + 1, y - 1, IRON[3])
        put(img, x + 2, y, IRON[1])
        put(img, x - 1, y - 1, IRON[5])
    # brass bands and pommel
    for k in (4, 10, 16):
        x, y = 3 + k, 29 - k
        for dx, dy, c in ((0, 0, BRASS[3]), (1, 0, BRASS[2]), (0, -1, BRASS[4]), (1, -1, BRASS[3]), (-1, 0, BRASS[2]), (0, 1, BRASS[2])):
            put(img, x + dx, y + dy, c)
    disc(img, 3.5, 29.5, 2.2, BRASS, outline=False)
    # piston running along the haft
    for i in range(8, 15):
        put(img, 5 + i, 29 - i - 2, COPPER[3] if i % 3 else COPPER[1])
    inner_outline(img)
    # head: big cog + crystal
    gear(img, 23.5, 8.5, 8.2, 6.4, 10, BRASS, angle=0.2, hub=(3.4, 4.3), tooth_width=0.45)
    crystal = check([
        "..o..",
        ".owo.",
        "owzyo",
        "ozyxo",
        ".oxo.",
        "..o..",
    ], 5)
    stamp(img, 21, 6, crystal, P)
    return img


def armor_icon(slot):
    if slot == "helmet":
        rows = check([
            "................",
            ".....oooooo.....",
            "....oggfffeo....",
            "....ogffffeo....",
            "....ogffffeo....",
            "...ooooffoooo...",
            "..o4zyo33o4zyo..",
            "..o3yxo22o3yxo..",
            "...oooo11oooo...",
            "..oooooooooooo..",
            ".olnnnnnnnnnnmo.",
            "..oooooooooooo..",
            "................",
            "................",
            "................",
            "................",
        ], 16)
    elif slot == "chestplate":
        rows = [
            "................",
            "..oooo....oooo..",
            ".o4332oooo2334o.",
            ".o3321nnnn1233o.",
            ".oooonmlmmnoooo.",
            "..onnm4ml4mnno..",
            "..onnmnmlmnnno..",
            "..onnm4ml4mnno..",
            "..onnmnmlmnnno..",
            "..o11111111111o.",
            "..o3ii3443ii3o..",
            "..onnm4ml4mnno..",
            "..onnmnmlmnnno..",
            "..onnn.ml.nnno..",
            "..ooooo..ooooo..",
            "................",
        ]
        rows = [r[:16].ljust(16, ".") for r in rows]
    elif slot == "leggings":
        rows = [
            "................",
            "...oooooooooo...",
            "...o34421112o...",
            "...offfffffgo...",
            "...offffgffgo...",
            "...offfoofffo...",
            "...offgo.ofgfo..",
            "...o343o.o343o..",
            "...o232o.o232o..",
            "...offgo.offgo..",
            "...offgo.offgo..",
            "...offgo.offgo..",
            "...offgo.offgo..",
            "...ooooo.ooooo..",
            "................",
            "................",
        ]
        rows = [r[:16].ljust(16, ".") for r in rows]
    else:
        rows = [
            "................",
            "................",
            "................",
            "..oooo....oooo..",
            "..ommo....ommo..",
            "..o34o....o34o..",
            "..ommo....ommo..",
            "..omno....omno..",
            "..o23o....o23o..",
            "..ommoo...ommoo.",
            "..ommmmo..ommmmo",
            "..o44443o.o44443",
            "..oooooo..oooooo",
            "................",
            "................",
            "................",
        ]
        rows = [r[:16].ljust(16, ".") for r in rows]
    img = new(16)
    stamp(img, 0, 0, rows, P)
    return img


def technomancy_gem():
    img = new(16)
    gear(img, 8, 8, 7.0, 5.6, 12, BRASS, hub=None, tooth_width=0.5)
    # faceted cyan gem
    gem = check([
        "...oo...",
        "..owzo..",
        ".owzzyo.",
        "owzzyyxo",
        "ozyyyxxo",
        ".oyyxxo.",
        "..oxxo..",
        "...oo...",
    ], 8)
    stamp(img, 4, 4, gem, P)
    return img


# ------------------------------------------------------------------------------------------- spell icons (16x16, full bleed)

def _frame(img, accent):
    w, h = img.size
    for x in range(w):
        put(img, x, 0, OUTLINE)
        put(img, x, h - 1, OUTLINE)
    for y in range(h):
        put(img, 0, y, OUTLINE)
        put(img, w - 1, y, OUTLINE)
    for c in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
        put(img, c[0], c[1], accent)


def icon_gear_barrage():
    img = gradient_bg(new(16), (120, 74, 30), (34, 18, 8))
    # motion streaks trailing to the lower-left
    for x, y in ((1, 13), (2, 10), (4, 14)):
        line(img, x, y, x + 3, y - 3, (190, 130, 60, 255))
    gear(img, 5, 11, 3.9, 2.9, 7, COPPER, hub=None)
    gear(img, 10.5, 5.5, 5.0, 3.8, 8, BRASS, hub=(1.6, 2.2), angle=0.2)
    put(img, 5, 11, OUTLINE)
    put(img, 13, 1, BRASS[5])
    put(img, 14, 2, BRASS[4])
    _frame(img, BRASS[4])
    return img


def icon_arc_welder():
    img = gradient_bg(new(16), (14, 40, 52), (6, 10, 16))
    # welding torch
    rows = check([
        "..........",
        "..........",
        "...oo.....",
        "..o34o....",
        ".o3iio....",
        "o2ijio....",
        "oo2iio....",
        ".oo2o.....",
        "..ooo.....",
        "..........",
    ], 10)
    stamp(img, 1, 6, rows, P)
    # jagged arc
    pts = [(6, 9), (8, 7), (8, 6), (10, 5), (11, 3), (13, 2)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        line(img, x0, y0, x1, y1, CYAN[3])
    for x, y in pts[1:-1]:
        put(img, x + 1, y, CYAN[2])
    put(img, 13, 2, CYAN[4])
    for x, y in ((12, 1), (14, 3), (14, 1), (12, 3)):
        put(img, x, y, BRASS[4])
    _frame(img, CYAN[3])
    return img


def icon_deploy_sentry():
    img = gradient_bg(new(16), (60, 40, 22), (20, 12, 8))
    rows = check([
        "..............",
        "..............",
        "....oooo......",
        "...o4433oooooo",
        "...o3zy2kqqqqo",
        "...o32212jjjjo",
        "...o2221oooooo",
        "....oooo......",
        "....o23o......",
        "...o1oo1o.....",
        "..oio..oio....",
        ".oio....oio...",
        ".oo......oo...",
        "..............",
    ], 14)
    stamp(img, 1, 1, rows, P)
    # cog sigil under the tripod
    for x in range(2, 14):
        if x % 2 == 0:
            put(img, x, 14, BRASS[2])
    _frame(img, BRASS[4])
    return img


def icon_steam_vent():
    img = gradient_bg(new(16), (40, 54, 66), (12, 14, 18))
    puffs = ((6.5, 9.5, 2.6), (9.5, 6.5, 3.3), (12.5, 3.5, 2.7), (12.8, 8.5, 2.0), (7.5, 4.5, 1.8))
    for cx, cy, r in puffs:
        disc(img, cx, cy, r + 0.9, [STEAM[0]] * 3, outline=False, highlight=False)
    for cx, cy, r in puffs:
        disc(img, cx, cy, r, STEAM, outline=False, highlight=False)
        put(img, int(cx - r * 0.4), int(cy - r * 0.4), (255, 255, 255, 255))
    rows = check([
        "oooo..",
        "o34o..",
        "o23ooo",
        "o2iiio",
        "o1iijo",
        "oooooo",
    ], 6)
    stamp(img, 1, 9, rows, P)
    _frame(img, STEAM[1])
    return img


def icon_overdrive():
    img = gradient_bg(new(16), (90, 30, 12), (24, 8, 4))
    gear(img, 8, 8, 6.6, 5.0, 10, BRASS, hub=(2.6, 3.4), tooth_width=0.45)
    # upward chevrons = upgrade
    chev = check([
        "...o...",
        "..ozo..",
        ".ozyzo.",
        "ozyoyzo",
        "oyo.oyo",
        "o.....o",
    ], 7)
    stamp(img, 5, 5, chev, P)
    for x, y in ((2, 2), (13, 2), (2, 13), (13, 13)):
        put(img, x, y, rgb("FF8A3A"))
    _frame(img, rgb("FF8A3A"))
    return img


def icon_assemble_automaton():
    img = gradient_bg(new(16), (40, 52, 46), (10, 14, 12))
    rows = check([
        "....oooooo....",
        "...o344321o...",
        "...o3zo0zo1o..",
        "...o2222221o..",
        "....oo11oo....",
        "..oo3444421oo.",
        ".o4o3bbcb2o3o.",
        ".o3o2bxxb2o2o.",
        ".o2o2bbbb1o1o.",
        ".oioo2112ooio.",
        "..o..oiio..o..",
        "....oio.oio...",
        "....oo...oo...",
    ], 14)
    rows = [r.replace("0", "o") for r in rows]
    stamp(img, 1, 1, rows, P)
    _frame(img, CYAN[2])
    return img


def effect_overdrive():
    img = new(18)
    gear(img, 9, 9, 8.0, 6.2, 10, BRASS, hub=(3.0, 3.9), tooth_width=0.45)
    chev = check([
        "...o...",
        "..ozo..",
        ".ozyzo.",
        "ozyoyzo",
        "oyo.oyo",
    ], 7)
    stamp(img, 6, 6, chev, P)
    return img


# ------------------------------------------------------------------------------------------- particles

def particle_brass_spark(n):
    img = new(8)
    sizes = [(3.5, 3.5, 1.1), (3.5, 3.5, 1.6), (3.5, 3.5, 2.2)]
    cx, cy, r = sizes[n]
    for y in range(8):
        for x in range(8):
            d = math.hypot(x + 0.5 - cx - 0.5, y + 0.5 - cy - 0.5)
            if d <= r:
                put(img, x, y, (255, 255, 255, 255 if d < r * 0.6 else 170))
    return img


def particle_steam(n):
    img = new(16)
    import random
    rnd = random.Random(7 + n)
    for _ in range(4):
        cx, cy = rnd.uniform(5, 11), rnd.uniform(5, 11)
        r = 2.5 + n * 0.9 + rnd.uniform(-0.5, 0.5)
        for y in range(16):
            for x in range(16):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d <= r:
                    a = int(230 * (1 - (d / r) ** 2)) - n * 30
                    if a > img.getpixel((x, y))[3]:
                        put(img, x, y, (255, 255, 255, max(0, a)))
    return img


def particle_arc_mote(n):
    img = new(8)
    for i in range(8):
        a = 140 + n * 60 if i in (3, 4) else 90
        put(img, i, 3, (255, 255, 255, int(a // (1 + abs(i - 3.5) // 2))))
        put(img, 3, i, (255, 255, 255, int(a // (1 + abs(i - 3.5) // 2))))
    for x, y in ((3, 3), (4, 3), (3, 4), (4, 4)):
        put(img, x, y, (255, 255, 255, 255))
    return img


def particle_cog_sigil():
    img = new(32)
    layer = new(32)
    gear(layer, 16, 16, 15.2, 12.6, 16, [(255, 255, 255, 255)] * 6, hole=10.8, outline=False, tooth_width=0.45)
    img.alpha_composite(layer)
    for r_in, r_out, alpha in ((6.0, 7.0, 255), (2.0, 2.8, 200)):
        for y in range(32):
            for x in range(32):
                d = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
                if r_in <= d <= r_out:
                    put(img, x, y, (255, 255, 255, alpha))
    for k in range(6):
        a = k * math.pi / 3
        line(img, 16 + 7.5 * math.cos(a), 16 + 7.5 * math.sin(a), 16 + 10.5 * math.cos(a), 16 + 10.5 * math.sin(a), (255, 255, 255, 220))
    return img
