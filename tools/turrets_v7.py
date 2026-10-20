"""
Iron's Technomancy 1.10 turrets (Deploy Brass Sentry), "Premium Fantasy" preset.

- brass_sentry: a small clockwork gun turret on three brass-shod legs: a riveted brass gun housing with a cyan visor
  slit, a banded iron barrel with a muzzle brake, a cog on each side and one at the back turning, and a copper steam
  stack with a cap rising behind the housing (it vents steam);
- siege_sentry (overdriven, "Grand Cannon"): a fixed emplacement in the spirit of a big coastal gun - an octagonal
  armoured plinth with four buttresses, a turning brass collar, a heavy navy turret with sloped armour, and ONE long
  heavy barrel ringed with glowing hextech coils ending in a big muzzle brake; a hextech capacitor glows at the back.

Both assemble out of the ground when summoned (spawn: plinth/base rises, legs unfold, the housing drops onto it and
locks, the barrel runs out, the cogs spin up, a puff of steam) and fold away when they expire (despawn). Bone names
stay those the Java code and the old animations used.
"""
import math

from models import C, build, kf
from pixelart import BRASS, COPPER, IRON, OUTLINE, line, put, ramp, rgb

NAVY = [rgb("070C20"), rgb("0F1834"), rgb("18264E"), rgb("22366C"), rgb("31498C"), rgb("4566B0")]
HCYAN = [rgb("0A3A70"), rgb("1670C8"), rgb("38B4FF"), rgb("8AE0FF"), rgb("D8F8FF"), rgb("FFFFFF")]
STEEL = [rgb("15171E"), rgb("252A33"), rgb("3A414D"), rgb("566070"), rgb("7C8899"), rgb("AEB9C8")]


def shade(colors, img, x, y, w, h, base, spread, seed=0, face="north"):
    """Top-lit gradient with a soft bevel (lighter top/left edge, darker bottom/right) and a little grain."""
    lit = {"up": 0.1, "north": 0.04, "east": 0.0, "west": -0.02, "south": -0.06, "down": -0.16}.get(face, 0)
    for j in range(h):
        for i in range(w):
            t = base + lit + spread * (0.5 - j / max(1, h)) * 0.8 + ((i * 7 + j * 13 + seed) % 5 - 2) * 0.018
            if i == 0 or j == 0:
                t += 0.1
            elif i == w - 1 or j == h - 1:
                t -= 0.1
            put(img, x + i, y + j, ramp(colors, t))


def rivets(img, x, y, w, h, colors):
    if w >= 5 and h >= 5:
        for cx, cy in ((x + 1, y + 1), (x + w - 2, y + 1), (x + 1, y + h - 2), (x + w - 2, y + h - 2)):
            put(img, cx, cy, colors[-1])
            put(img, cx + 1 if cx + 1 < x + w else cx, cy + 1 if cy + 1 < y + h else cy, colors[1])


def brass(img, x, y, w, h, face):
    shade(BRASS, img, x, y, w, h, 0.6, 0.5, x + y * 3, face)
    line(img, x, y, x + w - 1, y, BRASS[5])
    rivets(img, x, y, w, h, BRASS)


def brass_dark(img, x, y, w, h, face):
    shade(BRASS, img, x, y, w, h, 0.36, 0.4, x + y, face)


def copper(img, x, y, w, h, face):
    shade(COPPER, img, x, y, w, h, 0.58, 0.5, x + y, face)
    if face in ("north", "south", "east", "west") and h >= 4:
        for k in range(1, h, 3):
            line(img, x, y + k, x + w - 1, y + k, COPPER[1])


def iron(img, x, y, w, h, face):
    shade(IRON, img, x, y, w, h, 0.48, 0.45, x * 3 + y * 7, face)
    rivets(img, x, y, w, h, IRON)


def steel(img, x, y, w, h, face):
    shade(STEEL, img, x, y, w, h, 0.5, 0.45, x + y * 5, face)


def navy(img, x, y, w, h, face):
    shade(NAVY, img, x, y, w, h, 0.55, 0.45, x * 3 + y, face)
    rivets(img, x, y, w, h, NAVY)
    if w >= 8 and h >= 4 and face in ("north", "east", "west", "south"):
        # a brass trim line along the top edge
        line(img, x + 1, y + 1, x + w - 2, y + 1, BRASS[3])


def barrel_iron(img, x, y, w, h, face):
    shade(STEEL, img, x, y, w, h, 0.45, 0.5, x + y, face)
    if face == "north" and w >= 3 and h >= 3:
        for j in range(1, h - 1):
            for i in range(1, w - 1):
                put(img, x + i, y + j, OUTLINE)
    elif face in ("east", "west", "up", "down") and w >= 5:
        for k in range(2, w, 4):
            line(img, x + k, y, x + k, y + h - 1, STEEL[1])


def brake(img, x, y, w, h, face):
    shade(BRASS, img, x, y, w, h, 0.45, 0.45, x, face)
    if face == "north" and w >= 3 and h >= 3:
        for j in range(1, h - 1):
            for i in range(1, w - 1):
                put(img, x + i, y + j, OUTLINE)
    elif face in ("east", "west", "up", "down") and h >= 3:
        line(img, x + w // 2, y + 1, x + w // 2, y + h - 2, OUTLINE)


def gear(img, x, y, w, h, face):
    shade(BRASS, img, x, y, w, h, 0.62, 0.5, 0, face)
    if face in ("north", "south", "east", "west") and w >= 3 and h >= 3:
        for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
            put(img, cx, cy, (0, 0, 0, 0))
        put(img, x + w // 2, y + h // 2, OUTLINE)
        if w >= 5 and h >= 5:
            for cx, cy in ((x + w // 2, y + 1), (x + w // 2, y + h - 2), (x + 1, y + h // 2), (x + w - 2, y + h // 2)):
                put(img, cx, cy, BRASS[1])


def visor(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            put(img, x + i, y + j, ramp(HCYAN, 0.85 - 0.35 * j / max(1, h - 1)))
    line(img, x, y, x + w - 1, y, HCYAN[5])


def coil(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            put(img, x + i, y + j, ramp(HCYAN, 0.72 + 0.2 * math.sin((i + j) * 1.3)))
    put(img, x, y, HCYAN[5])


def capacitor(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            t = 0.95 - 0.5 * (j / max(1, h - 1)) + (0.12 if i in (0, w - 1) else 0)
            put(img, x + i, y + j, ramp(HCYAN, t))


def octagon(cubes, bone, y, r, h, mat, name):
    """A stepped octagonal slab of half-width r: a cross of two slabs and a square turned 45 degrees filling the
    corners (its corners stay inside the flats, so no star points)."""
    w = r * 1.25
    cubes.append(C(bone, [-r, y, -w / 2], [2 * r, h, w], mat, name=name))
    cubes.append(C(bone, [-w / 2, y, -r], [w, h, 2 * r], mat, share=name))
    s = r * 1.38
    cubes.append(C(bone, [-s / 2, y, -s / 2], [s, h, s], mat, name=name + "_d", rotation=[0, 45, 0], pivot=[0, y, 0]))


# ------------------------------------------------------------------------------------------- Brass Sentry

def brass_sentry():
    bones = [("root", None, [0, 0, 0], None), ("base", "root", [0, 8, 0], None)]
    cubes = [
        C("base", [-3.5, 6.5, -3.5], [7, 4.5, 7], copper, name="drum"),
        C("base", [-4, 10.5, -4], [8, 1, 8], brass_dark, name="drum_rim"),
        C("base", [-2.5, 5.5, -2.5], [5, 1, 5], iron, name="drum_foot"),
    ]
    for i, yaw in enumerate((0, 120, 240)):
        bones.append(("leg_mount_%d" % (i + 1), "base", [0, 8, 0], [0, yaw, 0]))
        bones.append(("leg_%d" % (i + 1), "leg_mount_%d" % (i + 1), [0, 8, 3], [28, 0, 0]))
        cubes.append(C("leg_%d" % (i + 1), [-1, 0, 2], [2, 8.5, 2], iron, name="leg" if i == 0 else None, share=None if i == 0 else "leg"))
        cubes.append(C("leg_%d" % (i + 1), [-1.25, 4, 1.75], [2.5, 1, 2.5], brass, name="knee" if i == 0 else None, share=None if i == 0 else "knee"))
        cubes.append(C("leg_%d" % (i + 1), [-1.5, 0, 1.5], [3, 1, 3], brass, name="foot" if i == 0 else None, share=None if i == 0 else "foot"))
    bones += [
        ("head", "base", [0, 12, 0], None),
        ("barrel", "head", [0, 14.5, -3.5], None),
        ("muzzle", "barrel", [0, 14.5, -11.5], None),
        ("coil", "head", [0, 18, -0.5], None),
        ("gear_l", "head", [3.6, 14.5, 0], None),
        ("gear_r", "head", [-3.6, 14.5, 0], None),
        ("gear_back", "head", [0, 14, 3.4], None),
        ("vent", "head", [1.8, 16, 2.6], None),
    ]
    cubes += [
        C("head", [-3, 11, -3.5], [6, 6.5, 7], brass, name="housing"),
        C("head", [-3.3, 16.5, -3.8], [6.6, 1, 7.6], brass_dark, name="roof"),
        C("head", [-2.6, 12.3, -4], [5.2, 2.4, 0.6], iron, name="mantlet"),
        C("head", [-2, 15, -3.9], [4, 1, 0.4], visor, glow=True, name="visor"),
        C("barrel", [-0.9, 13.6, -11], [1.8, 1.8, 7.5], barrel_iron, name="barrel"),
        C("barrel", [-1.15, 13.35, -7], [2.3, 2.3, 0.8], brass, name="band"),
        C("barrel", [-1.15, 13.35, -9.5], [2.3, 2.3, 0.8], brass, share="band"),
        C("muzzle", [-1.4, 13.1, -12.4], [2.8, 2.8, 1.4], brake, name="brake"),
        C("coil", [-1.5, 17.5, -2], [3, 1.5, 3], coil, glow=True, name="coil"),
        C("gear_l", [3, 12, -2.5], [1, 5, 5], gear, name="cog"),
        C("gear_l", [3, 12, -2.5], [1, 5, 5], gear, share="cog", rotation=[45, 0, 0], pivot=[3.5, 14.5, 0]),
        C("gear_r", [-4, 12, -2.5], [1, 5, 5], gear, share="cog"),
        C("gear_r", [-4, 12, -2.5], [1, 5, 5], gear, share="cog", rotation=[45, 0, 0], pivot=[-3.5, 14.5, 0]),
        C("gear_back", [-2, 12, 3.4], [4, 4, 0.8], gear, name="cog_b"),
        C("gear_back", [-2, 12, 3.4], [4, 4, 0.8], gear, share="cog_b", rotation=[0, 0, 45], pivot=[0, 14, 3.8]),
        # the steam stack: a copper pipe up the back with a flared cap
        C("vent", [1.1, 13, 2.2], [1.4, 6.5, 1.4], copper, name="stack"),
        C("vent", [0.75, 19.5, 1.85], [2.1, 1, 2.1], brass, name="cap"),
        C("vent", [0.9, 13.6, 1.3], [1.8, 1, 1.0], brass_dark, name="clamp"),
    ]
    geo, img, glow = build("brass_sentry", 64, bones, cubes, (2, 2.5, 0.75), density=1.0, bedrock_sides=True)
    legs = ["leg_1", "leg_2", "leg_3"]
    # summon: the base climbs out of the ground (0-0.45 s), the legs swing down and plant (0.3-0.75), the housing
    # drops onto it and locks (0.6-0.95), the barrel runs out (0.95-1.15), the cogs spin up, the stack puffs (1.2)
    spawn = {"root": {"position": {"0.0": kf([0, -11, 0]), "0.45": kf([0, 1, 0], "easeOutBack"), "0.6": kf([0, 0, 0], "easeInOutSine")}},
             "head": {"position": {"0.0": kf([0, 9, 0]), "0.6": kf([0, 9, 0]), "0.85": kf([0, -0.6, 0], "easeInQuad"), "0.95": kf([0, 0, 0], "easeOutSine")},
                      "scale": {"0.0": kf([0, 0, 0]), "0.55": kf([0, 0, 0]), "0.62": kf([1, 1, 1], "easeOutBack"), "0.85": kf([1.06, 0.9, 1.06]), "1.0": kf([1, 1, 1])}},
             "barrel": {"position": {"0.0": kf([0, 0, 6]), "0.95": kf([0, 0, 6]), "1.15": kf([0, 0, -0.5], "easeOutBack"), "1.25": kf([0, 0, 0])}},
             "gear_l": {"rotation": {"0.0": kf([0, 0, 0]), "0.9": kf([0, 0, 0]), "1.4": kf([540, 0, 0], "easeInQuad")}},
             "gear_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.9": kf([0, 0, 0]), "1.4": kf([-540, 0, 0], "easeInQuad")}},
             "vent": {"scale": {"0.0": kf([1, 0.2, 1]), "1.0": kf([1, 0.2, 1]), "1.2": kf([1.2, 1.15, 1.2], "easeOutBack"), "1.4": kf([1, 1, 1])}}}
    despawn = {"barrel": {"position": {"0.0": kf([0, 0, 0]), "0.2": kf([0, 0, 6], "easeInSine")}},
               "head": {"rotation": {"0.0": kf([0, 0, 0]), "0.35": kf([20, 0, 0], "easeInSine")},
                        "scale": {"0.0": kf([1, 1, 1]), "0.3": kf([1, 1, 1]), "0.6": kf([0.4, 0.4, 0.4], "easeInBack")}},
               "root": {"position": {"0.0": kf([0, 0, 0]), "0.4": kf([0, 1, 0], "easeOutSine"), "1.0": kf([0, -11, 0], "easeInBack")}}}
    for leg in legs:
        spawn[leg] = {"rotation": {"0.0": kf([-80, 0, 0]), "0.3": kf([-80, 0, 0]), "0.75": kf([0, 0, 0], "easeOutBounce")}}
        despawn[leg] = {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([0, 0, 0]), "0.8": kf([-80, 0, 0], "easeInSine")}}
    anims = {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": {
        "spawn": {"animation_length": 1.4, "bones": spawn},
        "idle": {"loop": True, "animation_length": 2.0, "bones": {
            "gear_l": {"rotation": {"0.0": kf([0, 0, 0]), "2.0": kf([360, 0, 0])}},
            "gear_r": {"rotation": {"0.0": kf([0, 0, 0]), "2.0": kf([-360, 0, 0])}},
            "gear_back": {"rotation": {"0.0": kf([0, 0, 0]), "2.0": kf([0, 0, 360])}},
            "coil": {"scale": {"0.0": kf([1, 1, 1]), "1.0": kf([1.1, 1.0, 1.1], "easeInOutSine"), "2.0": kf([1, 1, 1], "easeInOutSine")}},
            "vent": {"scale": {"0.0": kf([1, 1, 1]), "1.7": kf([1, 1, 1]), "1.8": kf([1.15, 1.05, 1.15]), "2.0": kf([1, 1, 1])}}}},
        "overclock": {"loop": True, "animation_length": 0.6667, "bones": {
            "gear_l": {"rotation": {"0.0": kf([0, 0, 0]), "0.6667": kf([360, 0, 0])}},
            "gear_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.6667": kf([-360, 0, 0])}},
            "gear_back": {"rotation": {"0.0": kf([0, 0, 0]), "0.6667": kf([0, 0, 360])}},
            "coil": {"scale": {"0.0": kf([1, 1, 1]), "0.1667": kf([1.25, 1.15, 1.25]), "0.3333": kf([1, 1, 1]), "0.5": kf([1.25, 1.15, 1.25]), "0.6667": kf([1, 1, 1])}},
            "vent": {"scale": {"0.0": kf([1, 1, 1]), "0.3333": kf([1.15, 1.2, 1.15]), "0.6667": kf([1, 1, 1])}}}},
        "shoot": {"animation_length": 0.25, "bones": {
            "barrel": {"position": {"0.0": kf([0, 0, 0]), "0.05": kf([0, 0, 1.6], "easeOutQuad"), "0.25": kf([0, 0, 0], "easeInOutSine")}},
            "muzzle": {"scale": {"0.0": kf([1, 1, 1]), "0.05": kf([1.4, 1.4, 1.4]), "0.2": kf([1, 1, 1])}}}},
        "despawn": {"animation_length": 1.0, "loop": "hold_on_last_frame", "bones": despawn},
    }}
    return geo, img, glow, anims


# ------------------------------------------------------------------------------------------- Grand Cannon

def siege_sentry():
    bones = [("root", None, [0, 0, 0], None), ("base", "root", [0, 4, 0], None)]
    cubes = []
    octagon(cubes, "base", 0, 7.6, 2.5, steel, "plinth")
    octagon(cubes, "base", 2.5, 6.4, 1.5, navy, "deck")
    cubes.append(C("base", [-4.8, 2.6, -4.8], [9.6, 1.2, 9.6], brass_dark, name="deck_trim", rotation=[0, 22.5, 0], pivot=[0, 3, 0]))
    for i, yaw in enumerate((45, 135, 225, 315)):
        mount = "leg_mount_%d" % (i + 1)
        bones.append((mount, "base", [0, 2, 0], [0, yaw, 0]))
        bones.append(("leg_%d" % (i + 1), mount, [0, 2.5, 6], None))
        cubes.append(C("leg_%d" % (i + 1), [-1.5, 0, 5.5], [3, 3.5, 4], navy, name="buttress" if i == 0 else None, share=None if i == 0 else "buttress"))
        cubes.append(C("leg_%d" % (i + 1), [-2, 0, 8.5], [4, 1.2, 2.5], brass, name="pad" if i == 0 else None, share=None if i == 0 else "pad"))
    bones += [
        ("collar", "base", [0, 4, 0], None),
        ("head", "base", [0, 7, 0], None),
        ("armor_l", "head", [5, 9, 0], None),
        ("armor_r", "head", [-5, 9, 0], None),
        ("barrel", "head", [0, 10, -4], None),
        ("muzzle", "barrel", [0, 10, -21], None),
        ("coil", "head", [0, 14.5, 3], None),
        ("gear_back", "head", [0, 10, 5.6], None),
        ("exhaust", "head", [0, 12, 4], None),
    ]
    cubes += [
        C("collar", [-5, 4, -5], [10, 1.4, 10], brass, name="collar"),
        C("collar", [-5, 4, -5], [10, 1.4, 10], brass, share="collar", rotation=[0, 45, 0], pivot=[0, 4.7, 0]),
        C("head", [-5, 5.4, -4.5], [10, 7, 9.5], navy, name="housing"),
        C("head", [-4, 12.4, -3.5], [8, 2, 7.5], navy, name="roof"),
        C("head", [-4.5, 6.4, -6.6], [9, 5, 2.4], steel, name="glacis", rotation=[-25, 0, 0], pivot=[0, 9, -5]),
        C("head", [-2.4, 9.4, -6.9], [4.8, 1, 0.6], visor, glow=True, name="slit"),
        C("armor_l", [4.6, 5.8, -3.5], [1.4, 6.4, 8], steel, name="side"),
        C("armor_r", [-6, 5.8, -3.5], [1.4, 6.4, 8], steel, share="side"),
        # the one heavy barrel: a thick recoil sleeve, a long tube banded with hextech coils, a big muzzle brake
        C("barrel", [-2.2, 7.8, -9], [4.4, 4.4, 5], navy, name="sleeve"),
        C("barrel", [-1.5, 8.5, -21], [3, 3, 12.5], barrel_iron, name="tube"),
        C("barrel", [-1.9, 8.1, -11.5], [3.8, 3.8, 0.8], coil, glow=True, name="ring"),
        C("barrel", [-1.9, 8.1, -15], [3.8, 3.8, 0.8], coil, glow=True, share="ring"),
        C("barrel", [-1.9, 8.1, -18.5], [3.8, 3.8, 0.8], brass, name="bandb"),
        C("muzzle", [-2.4, 7.6, -24], [4.8, 4.8, 3.2], brake, name="brake"),
        C("coil", [-1.6, 12.4, 1.4], [3.2, 4, 3.2], capacitor, glow=True, name="cap"),
        C("coil", [-2, 16.3, 1], [4, 0.8, 4], brass, name="cap_top"),
        C("coil", [-2, 12.2, 1], [4, 0.6, 4], brass, share="cap_top"),
        C("gear_back", [-3.5, 6.5, 5.2], [7, 7, 0.9], gear, name="gear"),
        C("gear_back", [-3.5, 6.5, 5.2], [7, 7, 0.9], gear, share="gear", rotation=[0, 0, 45], pivot=[0, 10, 5.6]),
        C("exhaust", [3, 12, 2.5], [1.3, 4.5, 1.3], copper, name="pipe"),
        C("exhaust", [-4.3, 12, 2.5], [1.3, 4.5, 1.3], copper, share="pipe"),
    ]
    geo, img, glow = build("siege_sentry", 96, bones, cubes, (3.5, 3, 0.75), density=1.0, bedrock_sides=True)
    legs = ["leg_%d" % i for i in range(1, 5)]
    spawn = {"root": {"position": {"0.0": kf([0, -12, 0]), "0.55": kf([0, 1.2, 0], "easeOutBack"), "0.7": kf([0, 0, 0], "easeInOutSine")}},
             "head": {"position": {"0.0": kf([0, 10, 0]), "0.7": kf([0, 10, 0]), "0.95": kf([0, -0.8, 0], "easeInQuad"), "1.05": kf([0, 0, 0], "easeOutSine")},
                      "scale": {"0.0": kf([0, 0, 0]), "0.65": kf([0, 0, 0]), "0.72": kf([1, 1, 1], "easeOutBack"), "0.95": kf([1.06, 0.9, 1.06]), "1.1": kf([1, 1, 1])}},
             "collar": {"rotation": {"0.0": kf([0, 0, 0]), "0.6": kf([0, 0, 0]), "1.1": kf([0, 180, 0], "easeOutSine")}},
             "barrel": {"position": {"0.0": kf([0, 0, 11]), "1.1": kf([0, 0, 11]), "1.45": kf([0, 0, -0.6], "easeOutBack"), "1.55": kf([0, 0, 0])},
                        "rotation": {"0.0": kf([30, 0, 0]), "1.1": kf([30, 0, 0]), "1.5": kf([0, 0, 0], "easeOutBack")}},
             "coil": {"scale": {"0.0": kf([0.2, 0.2, 0.2]), "1.2": kf([0.2, 0.2, 0.2]), "1.45": kf([1.3, 1.3, 1.3], "easeOutBack"), "1.6": kf([1, 1, 1])}}}
    despawn = {"barrel": {"position": {"0.0": kf([0, 0, 0]), "0.3": kf([0, 0, 11], "easeInSine")},
                          "rotation": {"0.0": kf([0, 0, 0]), "0.35": kf([30, 0, 0], "easeInSine")}},
               "coil": {"scale": {"0.0": kf([1, 1, 1]), "0.3": kf([0.2, 0.2, 0.2], "easeInBack")}},
               "head": {"scale": {"0.0": kf([1, 1, 1]), "0.35": kf([1, 1, 1]), "0.65": kf([0.3, 0.3, 0.3], "easeInBack")}},
               "root": {"position": {"0.0": kf([0, 0, 0]), "0.45": kf([0, 1, 0], "easeOutSine"), "1.0": kf([0, -12, 0], "easeInBack")}}}
    for leg in legs:
        spawn[leg] = {"rotation": {"0.0": kf([-80, 0, 0]), "0.35": kf([-80, 0, 0]), "0.8": kf([0, 0, 0], "easeOutBounce")}}
        despawn[leg] = {"rotation": {"0.0": kf([0, 0, 0]), "0.45": kf([0, 0, 0]), "0.85": kf([-80, 0, 0], "easeInSine")}}
    anims = {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": {
        "spawn": {"animation_length": 1.6, "bones": spawn},
        "idle": {"loop": True, "animation_length": 3.0, "bones": {
            "gear_back": {"rotation": {"0.0": kf([0, 0, 0]), "3.0": kf([0, 0, 360])}},
            "coil": {"scale": {"0.0": kf([1, 1, 1]), "1.5": kf([1.08, 1.12, 1.08], "easeInOutSine"), "3.0": kf([1, 1, 1], "easeInOutSine")}},
            "exhaust": {"scale": {"0.0": kf([1, 1, 1]), "2.6": kf([1, 1, 1]), "2.75": kf([1.15, 1.1, 1.15]), "3.0": kf([1, 1, 1])}}}},
        "overclock": {"loop": True, "animation_length": 0.75, "bones": {
            "gear_back": {"rotation": {"0.0": kf([0, 0, 0]), "0.75": kf([0, 0, 360])}},
            "coil": {"scale": {"0.0": kf([1, 1, 1]), "0.1875": kf([1.3, 1.3, 1.3]), "0.375": kf([1, 1, 1]), "0.5625": kf([1.3, 1.3, 1.3]), "0.75": kf([1, 1, 1])}},
            "head": {"position": {"0.0": kf([0, 0, 0]), "0.05": kf([0.1, 0, 0]), "0.1": kf([-0.1, 0, 0]), "0.15": kf([0, 0, 0])}}}},
        # one heavy shot: the barrel slams back into the sleeve, the turret rocks, the brake flares
        "shoot": {"animation_length": 0.6, "bones": {
            "barrel": {"position": {"0.0": kf([0, 0, 0]), "0.04": kf([0, 0, 4.0], "easeOutQuad"), "0.5": kf([0, 0, 0], "easeInOutSine")}},
            "muzzle": {"scale": {"0.0": kf([1, 1, 1]), "0.04": kf([1.5, 1.5, 1.5]), "0.25": kf([1, 1, 1])}},
            "head": {"rotation": {"0.0": kf([0, 0, 0]), "0.06": kf([-4, 0, 0], "easeOutQuad"), "0.4": kf([0, 0, 0], "easeInOutSine")}}}},
        "despawn": {"animation_length": 1.0, "loop": "hold_on_last_frame", "bones": despawn},
    }}
    return geo, img, glow, anims
