"""
Iron's Technomancy 1.10: the Hextech Thunderforge (registry id clockwork_altar, the Tech Dragon's summoning altar) as
an animated GeckoLib block, "Premium Fantasy" preset (2 texels per model px, navy hextech plate, brass, cyan glow).

Studied for construction only (nothing copied): the Cataclysm altars (Altar of Fire / Void / Amethyst / Abyss) - a
one-block plinth with a working mechanism and the offering shown on top - and the Dragon Summoning Device.

- a stepped octagonal steel plinth with a brass trim ring;
- a navy hextech housing with a clock dial on the front (long and short hands turning) and a big cog on the back;
- a cog on each side, turning;
- four brass pylons at the corners crowned with cyan crystals (they pulse; arcs leap from them to the core);
- on top, a turning toothed brass ring around a cradle of three claws where the Overcharged Dynamo Core sits.

Animations: idle (slow cogs, the clock running, crystals breathing), charging (the summoning: everything spins up, the
claws open, crystals blaze).
"""
import math

from models import C, build, kf
from pixelart import BRASS, COPPER, OUTLINE, line, put, ramp, rgb
from staffs_v5 import ring_of
from turrets_v7 import HCYAN, NAVY, STEEL, brass, brass_dark, copper, gear, navy, octagon, shade, steel

CREAM = [rgb("8C7350"), rgb("B89C70"), rgb("DCC59A"), rgb("F2E4C2"), rgb("FFF8E6")]


def dial(img, x, y, w, h, face):
    """Clock face: cream disc in a brass bezel, twelve tick marks, a hextech glyph ring."""
    if face != "north":
        brass_dark(img, x, y, w, h, face)
        return
    cx, cy = (w - 1) / 2, (h - 1) / 2
    R = min(w, h) / 2
    for j in range(h):
        for i in range(w):
            d = math.hypot(i - cx, j - cy) / R
            a = math.atan2(j - cy, i - cx)
            if d > 1.0:
                put(img, x + i, y + j, ramp(NAVY, 0.4))
            elif d > 0.84:
                put(img, x + i, y + j, ramp(BRASS, 0.75 - 0.3 * (j / h)))
            elif d > 0.72 and abs(((a / (2 * math.pi) * 12) % 1.0) - 0.5) > 0.38:
                put(img, x + i, y + j, OUTLINE)
            elif 0.5 < d < 0.58:
                put(img, x + i, y + j, ramp(HCYAN, 0.6))
            else:
                put(img, x + i, y + j, ramp(CREAM, 0.75 - 0.25 * d))


def hand(img, x, y, w, h, face):
    shade(STEEL, img, x, y, w, h, 0.25, 0.2, 0, face)


def crystal(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            put(img, x + i, y + j, ramp(HCYAN, 0.98 - 0.5 * j / max(1, h - 1) + (0.08 if i == 0 else 0)))
    put(img, x, y, HCYAN[5])


def plate_glyph(img, x, y, w, h, face):
    """Navy plate with a glowing hextech glyph line (the housing's sides)."""
    navy(img, x, y, w, h, face)
    if face in ("east", "west", "south") and w >= 8 and h >= 8:
        cx = x + w // 2
        for j in range(2, h - 2):
            put(img, cx, y + j, HCYAN[2])
        for i in range(2, w - 2):
            put(img, x + i, y + h // 2, HCYAN[2])
        put(img, cx, y + h // 2, HCYAN[4])


def hextech_forge():
    bones = [("root", None, [0, 0, 0], None), ("base", "root", [0, 0, 0], None),
             ("hand_long", "base", [0, 8.5, -5.25], None), ("hand_short", "base", [0, 8.5, -5.2], None),
             ("gear_l", "base", [5.3, 8, 0], None), ("gear_r", "base", [-5.3, 8, 0], None), ("gear_back", "base", [0, 8, 5.2], None),
             ("ring", "base", [0, 12.6, 0], None), ("socket", "base", [0, 12.4, 0], None)]
    for k in range(4):
        bones.append(("crystal_%d" % (k + 1), "base", [(6 if k in (0, 3) else -6), 14.2, (6 if k < 2 else -6)], None))
    for k in range(3):
        bones.append(("claw_%d" % (k + 1), "socket", [0, 12.4, 0], [0, k * 120, 0]))
    cubes = []
    octagon(cubes, "base", 0, 8, 2.5, steel, "plinth")
    octagon(cubes, "base", 2.5, 7.2, 1.0, brass, "trim")
    cubes += [
        C("base", [-5, 3.5, -5], [10, 8.5, 10], plate_glyph, name="housing"),
        C("base", [-5.5, 11.6, -5.5], [11, 1, 11], brass, name="cornice"),
        C("base", [-5.5, 3.4, -5.5], [11, 0.8, 11], brass_dark, name="skirt"),
        C("base", [-3.6, 4.9, -5.2], [7.2, 7.2, 0.4], dial, name="dial"),
        C("hand_long", [-0.3, 8.5, -5.45], [0.6, 3.2, 0.25], hand, name="hand_l"),
        C("hand_short", [-0.35, 8.5, -5.4], [0.7, 2.2, 0.2], hand, name="hand_s"),
        C("base", [-0.5, 8.0, -5.55], [1, 1, 0.3], brass, name="hub"),
        C("gear_l", [5, 4.5, -3.5], [0.8, 7, 7], gear, name="cog"),
        C("gear_l", [5, 4.5, -3.5], [0.8, 7, 7], gear, share="cog", rotation=[45, 0, 0], pivot=[5.4, 8, 0]),
        C("gear_r", [-5.8, 4.5, -3.5], [0.8, 7, 7], gear, share="cog"),
        C("gear_r", [-5.8, 4.5, -3.5], [0.8, 7, 7], gear, share="cog", rotation=[45, 0, 0], pivot=[-5.4, 8, 0]),
        C("gear_back", [-3.5, 4.5, 5], [7, 7, 0.8], gear, name="cog_b"),
        C("gear_back", [-3.5, 4.5, 5], [7, 7, 0.8], gear, share="cog_b", rotation=[0, 0, 45], pivot=[0, 8, 5.4]),
        # the cradle seat on top
        C("socket", [-2.2, 12.6, -2.2], [4.4, 0.8, 4.4], navy, name="seat"),
        C("socket", [-1.4, 13.2, -1.4], [2.8, 0.4, 2.8], crystal, glow=True, name="seat_glow"),
    ]
    # corner pylons with crystal crowns, copper conduits into the housing
    for k in range(4):
        sx = 6 if k in (0, 3) else -6
        sz = 6 if k < 2 else -6
        first = k == 0
        cubes.append(C("base", [sx - 1, 3.5, sz - 1], [2, 9.5, 2], brass, name="post" if first else None, share=None if first else "post"))
        cubes.append(C("base", [sx - 1.3, 12.8, sz - 1.3], [2.6, 0.8, 2.6], brass_dark, name="post_cap" if first else None, share=None if first else "post_cap"))
        cubes.append(C("base", [sx - 0.5 if sx > 0 else sx - 0.5, 7, sz * 0.5 - 0.5], [1, 1, abs(sz) * 0.4], copper,
                       name="conduit" if first else None, share=None if first else "conduit"))
        b = "crystal_%d" % (k + 1)
        # a pointed crystal: a turned shaft, a narrower crown, a sharp tip
        cubes.append(C(b, [sx - 0.8, 13.6, sz - 0.8], [1.6, 2.2, 1.6], crystal, glow=True, name="cry" if first else None, share=None if first else "cry",
                       rotation=[0, 45, 0], pivot=[sx, 15, sz]))
        cubes.append(C(b, [sx - 0.55, 15.8, sz - 0.55], [1.1, 1.2, 1.1], crystal, glow=True, name="cry2" if first else None, share=None if first else "cry2",
                       rotation=[0, 45, 0], pivot=[sx, 16.4, sz]))
        cubes.append(C(b, [sx - 0.3, 17.0, sz - 0.3], [0.6, 0.9, 0.6], crystal, glow=True, name="cry3" if first else None, share=None if first else "cry3",
                       rotation=[0, 45, 0], pivot=[sx, 17.4, sz]))
    # the turning toothed ring around the cradle
    ring_of(cubes, "ring", 12.9, 4.3, 12, 0.9, 0.7, brass, teeth=12, tooth_mat=brass_dark, plane="xz", name="ring")
    # three claws (one shape, turned 0/120/240 by their bones)
    for k in range(3):
        b = "claw_%d" % (k + 1)
        first = k == 0
        cubes.append(C(b, [-0.6, 12.4, -3.0], [1.2, 2.6, 1.0], brass, name="claw_a" if first else None, share=None if first else "claw_a",
                       rotation=[-18, 0, 0], pivot=[0, 12.4, -2.5]))
        cubes.append(C(b, [-0.5, 14.6, -2.6], [1.0, 1.8, 0.9], brass_dark, name="claw_b" if first else None, share=None if first else "claw_b",
                       rotation=[22, 0, 0], pivot=[0, 14.8, -2.2]))
    geo, img, glow = build("hextech_thunderforge", 160, bones, cubes, (2, 2, 0.5), density=2.0, bedrock_sides=True)

    L = 12.0
    idle = {"hand_long": {"rotation": {"0.0": kf([0, 0, 0]), str(L): kf([0, 0, -1440])}},
            "hand_short": {"rotation": {"0.0": kf([0, 0, 0]), str(L): kf([0, 0, -360])}},
            "gear_l": {"rotation": {"0.0": kf([0, 0, 0]), str(L): kf([720, 0, 0])}},
            "gear_r": {"rotation": {"0.0": kf([0, 0, 0]), str(L): kf([-720, 0, 0])}},
            "gear_back": {"rotation": {"0.0": kf([0, 0, 0]), str(L): kf([0, 0, 720])}},
            "ring": {"rotation": {"0.0": kf([0, 0, 0]), str(L): kf([0, 360, 0])}}}
    for k in range(4):
        ph = k * L / 4
        idle["crystal_%d" % (k + 1)] = {"scale": {"0.0": kf([1, 1, 1]), "%.2f" % (L / 8): kf([1.12, 1.18, 1.12], "easeInOutSine"),
                                                   "%.2f" % (L / 4): kf([1, 1, 1], "easeInOutSine"), str(L): kf([1, 1, 1])},
                                         "position": {"0.0": kf([0, 0, 0]), "%.2f" % (L / 2): kf([0, 0.4, 0], "easeInOutSine"), str(L): kf([0, 0, 0], "easeInOutSine")}}
    C2 = 1.0
    charging = {"hand_long": {"rotation": {"0.0": kf([0, 0, 0]), str(C2): kf([0, 0, -720])}},
                "hand_short": {"rotation": {"0.0": kf([0, 0, 0]), str(C2): kf([0, 0, -360])}},
                "gear_l": {"rotation": {"0.0": kf([0, 0, 0]), str(C2): kf([360, 0, 0])}},
                "gear_r": {"rotation": {"0.0": kf([0, 0, 0]), str(C2): kf([-360, 0, 0])}},
                "gear_back": {"rotation": {"0.0": kf([0, 0, 0]), str(C2): kf([0, 0, 360])}},
                "ring": {"rotation": {"0.0": kf([0, 0, 0]), str(C2): kf([0, 360, 0])},
                         "position": {"0.0": kf([0, 0.6, 0]), "0.5": kf([0, 0.9, 0]), str(C2): kf([0, 0.6, 0])}},
                "socket": {"position": {"0.0": kf([0, 0.4, 0])}}}
    for k in range(3):
        charging["claw_%d" % (k + 1)] = {"rotation": {"0.0": kf([0, k * 120, 0])}, "position": {"0.0": kf([0, 0.3, 0])}}
    for k in range(4):
        charging["crystal_%d" % (k + 1)] = {"scale": {"0.0": kf([1.3, 1.4, 1.3]), "0.25": kf([1.5, 1.7, 1.5]), "0.5": kf([1.3, 1.4, 1.3]),
                                                       "0.75": kf([1.5, 1.7, 1.5]), str(C2): kf([1.3, 1.4, 1.3])},
                                             "position": {"0.0": kf([0, 0.8, 0])}}
    # the claws spread open while charging (rotate the claw cubes outward via the bone's x tilt)
    for k in range(3):
        charging["claw_%d" % (k + 1)]["rotation"] = {"0.0": kf([-25, 0, 0])}
    anims = {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": {
        "idle": {"loop": True, "animation_length": L, "bones": idle},
        "charging": {"loop": True, "animation_length": C2, "bones": charging},
    }}
    return geo, img, glow, anims
