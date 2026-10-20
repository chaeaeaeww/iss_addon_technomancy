"""
Second generation GeckoLib models for Iron's Technomancy:

* Clockwork Automaton (robot): boxy servo-driven construct with a chest window full of spinning cogs, piston limbs,
  claw hands, twin smokestacks and a shoulder cog launcher. Its animations are deliberately "servo jerky": moves are
  split into held poses and fast snaps (and GeckoLib "step" easing) so it reads like a machine, not a creature.
* Automaton Mk.II (overdrive): a spherical brass steam golem with huge fists, a glowing top turbine, a lightning bolt
  chest emblem and spiked feet. It shares the entity (and animation names) with the normal automaton.
* Tech Dragon: the Technomancy boss. Indigo scaled hide under brass armor, blue crystal crest, brass-boned wings with
  glowing gem "eyes", segmented tail ending in a brass blade.
* Clockwork Staff: GeckoLib item model. Twisted dark shaft with brass bands, a spinning cog ring around a cyan core,
  an orange lightning clock hand and two orbiting orbs.

Every builder returns (geo json, texture, glowmask, animations) like tools/models.py.
"""
import math

from PIL import Image

import armor
from models import C, build, kf as _kf, iron_plate, dark_iron, brass, brass_dark, copper, glow_core, grill, gear_face, barrel
from pixelart import BRASS, COPPER, CYAN, IRON, OUTLINE, CLEAR, line, noise, put, ramp, rect, rgb

SKIN = [rgb("140F2A"), rgb("1F1840"), rgb("2B2258"), rgb("3A2F73"), rgb("4D4192"), rgb("6658B0")]
MEMBRANE = [rgb("220F36"), rgb("341A52"), rgb("48256E"), rgb("5E338C"), rgb("7745A8")]
CRYSTAL = [rgb("0A3470"), rgb("1458B8"), rgb("2A86EE"), rgb("6CC0FF"), rgb("CBEDFF")]
BONE = [rgb("7D7566"), rgb("ABA28E"), rgb("D6CDB8"), rgb("F3EEE2")]
CLAW = [rgb("1B1626"), rgb("2D2640"), rgb("463D5E"), rgb("62587E")]
WOOD = [rgb("1A0E1E"), rgb("2A182E"), rgb("3B2240"), rgb("4E2E52"), rgb("643C66")]
ORANGE = [rgb("6A2A08"), rgb("A8460E"), rgb("DE6A18"), rgb("F59A3C"), rgb("FFC97A")]
VIOLET = [rgb("2A0E3A"), rgb("4A1A66"), rgb("6E2C94"), rgb("9A4CC4"), rgb("D29AF0")]
RUBBER = [rgb("121216"), rgb("1E1E24"), rgb("2C2C34"), rgb("3C3C46")]


def kf(vector, easing=None, args=None):
    if easing == "step" and (not args or args[0] < 2):
        raise ValueError("GeckoLib step easing needs at least 2 steps")
    k = _kf(vector, easing)
    if args is not None:
        k["easingArgs"] = args
    return k


def rot(x=0, y=0, z=0):
    return [x, y, z]


# ------------------------------------------------------------------------------------------- materials

def shade(colors, img, x, y, w, h, base=0.55, spread=0.4, seed=0, grain=0.05):
    armor.shade_v(colors, x, y, w, h, img, base, spread=spread, seed=seed, grain=grain)


def machinery(img, x, y, w, h, face):
    """Dark recess behind the chest window: pipes and bolts."""
    shade(IRON, img, x, y, w, h, 0.18, 0.2, seed=x + y, grain=0.05)
    for k in range(1, h, 3):
        line(img, x, y + k, x + w - 1, y + k, IRON[1])
    for k in range(2, w, 4):
        line(img, x + k, y, x + k, y + h - 1, COPPER[0])


def eye_glow(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            put(img, x + i, y + j, CYAN[3])
    put(img, x, y, CYAN[4])


def white_eye(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            put(img, x + i, y + j, rgb("F4FBFF"))
    if w >= 2 and h >= 2:
        put(img, x + w - 1, y + h - 1, CYAN[3])


def hose(img, x, y, w, h, face):
    shade(RUBBER, img, x, y, w, h, 0.5, 0.4, grain=0.03)
    for k in range(0, max(w, h), 2):
        if h >= w:
            line(img, x, y + k, x + w - 1, y + k, RUBBER[0])
        else:
            line(img, x + k, y, x + k, y + h - 1, RUBBER[0])


def emblem_bolt(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            put(img, x + i, y + j, CYAN[2] if (i + j) % 3 else CYAN[3])


def scales(img, x, y, w, h, face):
    """Indigo dragon hide with staggered scale rows."""
    base = 0.62 if face == "up" else (0.25 if face == "down" else 0.45)
    shade(SKIN, img, x, y, w, h, base, 0.45, seed=x * 3 + y * 11, grain=0.06)
    for j in range(h):
        for i in range(w):
            if (i + (j // 2) * 2) % 4 == 0 and j % 2 == 0:
                put(img, x + i, y + j, SKIN[1])
            elif (i + (j // 2) * 2) % 4 == 1 and j % 2 == 0:
                put(img, x + i, y + j, SKIN[4] if face != "down" else SKIN[2])


def belly(img, x, y, w, h, face):
    shade(SKIN, img, x, y, w, h, 0.55, 0.3, seed=x + y, grain=0.04)
    for j in range(0, h, 3):
        line(img, x, y + j, x + w - 1, y + j, SKIN[2])


def membrane(img, x, y, w, h, face):
    shade(MEMBRANE, img, x, y, w, h, 0.5, 0.5, seed=x * 7 + y, grain=0.05)
    if face in ("up", "down") and w > 6:
        for k in range(0, w, max(3, w // 5)):
            line(img, x + k, y, x + max(0, k - h // 3), y + h - 1, MEMBRANE[1])
        line(img, x, y + h - 1, x + w - 1, y + h - 1, MEMBRANE[0])


def crystal(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            t = 0.35 + 0.6 * (1 - j / max(1, h - 1)) * (0.6 + 0.4 * ((i + j) % 2))
            put(img, x + i, y + j, ramp(CRYSTAL, t))
    put(img, x, y, CRYSTAL[4])


def gem(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            edge = i in (0, w - 1) or j in (0, h - 1)
            put(img, x + i, y + j, CRYSTAL[1] if edge and w > 2 and h > 2 else CRYSTAL[3])
    put(img, x + w // 2, y + h // 2, CRYSTAL[4])


def bone_white(img, x, y, w, h, face):
    shade(BONE, img, x, y, w, h, 0.65, 0.4, grain=0.03)


def claw(img, x, y, w, h, face):
    shade(CLAW, img, x, y, w, h, 0.5, 0.5, grain=0.03)
    put(img, x, y, CLAW[3])


def armor_plate(img, x, y, w, h, face):
    """Dragon brass armor: worn gold with a darker inset and a blue gem stripe on large faces."""
    armor.paint_brass_plate(img, x, y, w, h, face)
    if w >= 8 and h >= 6 and face in ("up", "north", "south", "east", "west"):
        armor.border(img, x + 2, y + 2, w - 4, h - 4, BRASS[2])
    if w >= 10 and h >= 4 and face == "up":
        cx = x + w // 2
        line(img, cx, y + 2, cx, y + h - 3, CRYSTAL[2])


def wood(img, x, y, w, h, face):
    shade(WOOD, img, x, y, w, h, 0.5, 0.5, seed=x * 13 + y, grain=0.06)
    for j in range(h):
        put(img, x + (j * 2) % max(1, w), y + j, WOOD[4])


def orange_bolt(img, x, y, w, h, face):
    shade(ORANGE, img, x, y, w, h, 0.65, 0.5, grain=0.02)
    line(img, x, y, x + w - 1, y, ORANGE[4])


def violet_orb(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            put(img, x + i, y + j, ramp(VIOLET, 0.8 - 0.5 * (i + j) / max(1, w + h - 2)))
    put(img, x, y, VIOLET[4])


def leather_grip(img, x, y, w, h, face):
    from pixelart import LEATHER
    shade(LEATHER, img, x, y, w, h, 0.5, 0.3, grain=0.06)
    for j in range(0, h, 2):
        line(img, x, y + j, x + w - 1, y + j, LEATHER[1])


# ------------------------------------------------------------------------------------------- helpers

def mirror(c, bone, share=True, name=None):
    """Mirror cube c across x=0 into another bone."""
    x, y, z = c.origin
    w, h, d = c.size
    rotation = None
    if c.rotation:
        rotation = [c.rotation[0], -c.rotation[1], -c.rotation[2]]
    pivot = None
    if c.pivot:
        pivot = [-c.pivot[0], c.pivot[1], c.pivot[2]]
    return C(bone, [-(x + w), y, z], [w, h, d], c.material, inflate=c.inflate, glow=c.glow, faces=c.faces,
             share=c.name if share else None, name=name, rotation=rotation, pivot=pivot)


def sym(cubes, bone_r, bone_l, origin, size, material, name, **kw):
    """Adds a right-side cube (at origin, negative x) and its mirrored left copy sharing UVs."""
    c = C(bone_r, origin, size, material, name=name, **kw)
    cubes.append(c)
    cubes.append(mirror(c, bone_l))
    return c


def gear_disc(cubes, bone, cx, cy, z, radius, depth, name, material=gear_face, axis="z"):
    """Octagonal cog made of a square disc and a 45 degree rotated copy (sharing UVs)."""
    s = radius * 2
    if axis == "z":
        a = C(bone, [cx - radius, cy - radius, z], [s, s, depth], material, name=name)
        b = C(bone, [cx - radius, cy - radius, z], [s, s, depth], material, share=name, rotation=[0, 0, 45], pivot=[cx, cy, z + depth / 2])
    else:  # facing x
        a = C(bone, [z, cy - radius, cx - radius], [depth, s, s], material, name=name)
        b = C(bone, [z, cy - radius, cx - radius], [depth, s, s], material, share=name, rotation=[45, 0, 0], pivot=[z + depth / 2, cy, cx])
    cubes += [a, b]


def octagon(cubes, bone, cx, cz, y0, y1, r, material, name):
    """Octagonal prism between y0 and y1 with apothem r, as four rectangles r x 0.414r rotated 0/90/45/-45 degrees."""
    h = y1 - y0
    t = r * 0.4142
    cubes.append(C(bone, [cx - r, y0, cz - t], [2 * r, h, 2 * t], material, name=name + "_a"))
    cubes.append(C(bone, [cx - t, y0, cz - r], [2 * t, h, 2 * r], material, name=name + "_b"))
    cubes.append(C(bone, [cx - r, y0, cz - t], [2 * r, h, 2 * t], material, share=name + "_a", rotation=[0, 45, 0], pivot=[cx, y0, cz]))
    cubes.append(C(bone, [cx - r, y0, cz - t], [2 * r, h, 2 * t], material, share=name + "_a", rotation=[0, -45, 0], pivot=[cx, y0, cz]))


def hull_plate(img, x, y, w, h, face):
    """Smooth riveted brass for the Mk.II hull (no plate borders so stacked slices read as one sphere)."""
    shade(BRASS, img, x, y, w, h, 0.62 if face != "down" else 0.35, 0.35, seed=x * 3 + y, grain=0.035)
    if face in ("north", "south", "east", "west") and h >= 3:
        for i in range(1, w - 1, 3):
            put(img, x + i, y + 1, BRASS[5])
            put(img, x + i, y + h - 1, BRASS[1])


def anims(d):
    return {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": d}


def spin(axis, length, turns=1, reverse=False):
    v = 360 * turns * (-1 if reverse else 1)
    end = [v if axis == "x" else 0, v if axis == "y" else 0, v if axis == "z" else 0]
    return {"rotation": {"0.0": kf([0, 0, 0]), "%g" % length: kf(end)}}


# =========================================================================================== Clockwork Automaton (robot)

def automaton_robot():
    bones = [
        ("root", None, [0, 0, 0], None),
        ("leg_r", "root", [-2.5, 11, 0], None),
        ("shin_r", "leg_r", [-2.5, 6.5, 0], None),
        ("leg_l", "root", [2.5, 11, 0], None),
        ("shin_l", "leg_l", [2.5, 6.5, 0], None),
        ("body", "root", [0, 11, 0], None),
        ("torso", "body", [0, 13, 0], None),
        ("gear_big", "torso", [0, 17.5, -2], None),
        ("gear_a", "torso", [2.4, 20.2, -1.6], None),
        ("gear_b", "torso", [-2.5, 20.3, -1.6], None),
        ("gear_c", "torso", [2.7, 14.9, -1.6], None),
        ("boiler", "torso", [0, 18, 4], None),
        ("chimney_r", "boiler", [-2.25, 22, 5.25], None),
        ("chimney_l", "boiler", [2.25, 22, 5.25], None),
        ("launcher", "torso", [3.75, 23.5, 1.5], None),
        ("head", "torso", [0, 23.5, 0], None),
        ("antenna", "head", [1.5, 29.5, 0], None),
        ("arm_r", "torso", [-6.5, 21.5, 0], None),
        ("shoulder_gear_r", "arm_r", [-9.2, 21.25, 0], None),
        ("elbow_r", "arm_r", [-7.25, 15, 0], None),
        ("claw_r", "elbow_r", [-7.25, 8.5, 0], None),
        ("arm_l", "torso", [6.5, 21.5, 0], None),
        ("shoulder_gear_l", "arm_l", [9.2, 21.25, 0], None),
        ("elbow_l", "arm_l", [7.25, 15, 0], None),
        ("claw_l", "elbow_l", [7.25, 8.5, 0], None),
    ]
    cubes = []
    # legs
    sym(cubes, "leg_r", "leg_l", [-4.25, 9.25, -1.75], [3.5, 2.5, 3.5], dark_iron, "hip")
    sym(cubes, "leg_r", "leg_l", [-3.75, 6.25, -1.25], [2.5, 3.5, 2.5], iron_plate, "thigh")
    sym(cubes, "leg_r", "leg_l", [-3.5, 6.75, 1.25], [1, 3, 1], copper, "thigh_piston")
    gear_disc(cubes, "shin_r", 0, 6.5, -4.75, 1.6, 0.6, "knee_gear_r", axis="x")
    cubes.append(mirror(cubes[-2], "shin_l"))
    cubes.append(mirror(cubes[-2], "shin_l"))
    sym(cubes, "shin_r", "shin_l", [-4.25, 1.5, -1.75], [3.5, 5, 3.5], brass, "shin")
    sym(cubes, "shin_r", "shin_l", [-3.25, 2, 1.75], [1.5, 4, 0.75], grill, "calf_vent")
    sym(cubes, "shin_r", "shin_l", [-4.75, 0, -3.25], [4.5, 1.5, 5.5], brass_dark, "foot")
    sym(cubes, "shin_r", "shin_l", [-4.75, 0, -4.25], [1.25, 1, 1], dark_iron, "toe_a")
    sym(cubes, "shin_r", "shin_l", [-1.5, 0, -4.25], [1.25, 1, 1], dark_iron, "toe_b")
    # pelvis
    cubes.append(C("body", [-4.5, 10.5, -2.5], [9, 2.5, 5], dark_iron, name="pelvis"))
    cubes.append(C("body", [-1.5, 9.5, -2.75], [3, 1.5, 0.75], brass, name="belt_buckle"))
    # torso shell with a recessed chest window
    cubes.append(C("torso", [-5.5, 13, -0.5], [11, 10, 4], brass, name="torso_back", faces=("east", "south", "west", "up", "down")))
    cubes.append(C("torso", [-3.5, 14.5, -0.6], [7, 6.5, 0.1], machinery, name="window_back", faces=("north",)))
    sym(cubes, "torso", "torso", [-5.5, 13, -3.5], [2, 10, 3], brass, "side_wall")
    cubes.append(C("torso", [-3.5, 21, -3.5], [7, 2, 3], brass, name="window_top"))
    cubes.append(C("torso", [-3.5, 13, -3.5], [7, 1.5, 3], brass, name="window_bottom"))
    cubes.append(C("torso", [-4, 21, -3.9], [8, 0.8, 0.5], iron_plate, name="frame_top"))
    cubes.append(C("torso", [-4, 14, -3.9], [8, 0.8, 0.5], iron_plate, name="frame_bottom"))
    sym(cubes, "torso", "torso", [-4, 14, -3.9], [0.8, 7.8, 0.5], iron_plate, "frame_side")
    cubes.append(C("torso", [-6.5, 22.5, -3], [13, 1.5, 6.5], brass_dark, name="yoke"))
    cubes.append(C("torso", [-4, 23.25, -2.5], [8, 0.75, 5], dark_iron, name="collar"))
    # inner cogs
    gear_disc(cubes, "gear_big", 0, 17.5, -2.3, 2.6, 0.6, "gear_big")
    cubes.append(C("gear_big", [-0.75, 16.75, -2.7], [1.5, 1.5, 0.45], glow_core, glow=True, name="core"))
    gear_disc(cubes, "gear_a", 2.4, 20.2, -1.9, 1.15, 0.5, "gear_a")
    gear_disc(cubes, "gear_b", -2.5, 20.3, -1.9, 1.3, 0.5, "gear_b")
    gear_disc(cubes, "gear_c", 2.7, 14.9, -1.9, 1.0, 0.5, "gear_c")
    # boiler and stacks
    cubes.append(C("boiler", [-3.5, 14, 3.5], [7, 8, 3], copper, name="tank"))
    cubes.append(C("boiler", [-3.75, 17, 3.25], [7.5, 1, 3.5], brass, name="tank_band"))
    cubes.append(C("boiler", [-1, 15, 6.5], [2, 2, 0.5], gear_face, name="valve"))
    cubes.append(C("chimney_r", [-3, 22, 4.5], [1.5, 5, 1.5], dark_iron, name="stack"))
    cubes.append(C("chimney_r", [-3.25, 26.5, 4.25], [2, 0.75, 2], brass, name="stack_cap"))
    cubes.append(C("chimney_l", [1.5, 22, 4.5], [1.5, 4, 1.5], dark_iron, share="stack"))
    cubes.append(C("chimney_l", [1.25, 25.5, 4.25], [2, 0.75, 2], brass, share="stack_cap"))
    # shoulder cog launcher
    cubes.append(C("launcher", [2.75, 23.25, 0.5], [2, 1.5, 2], dark_iron, name="launcher_base"))
    cubes.append(C("launcher", [3, 23.5, -2.5], [1.5, 1.5, 4], barrel, name="launcher_barrel"))
    cubes.append(C("launcher", [2.85, 23.35, -2.75], [1.8, 1.8, 0.6], brass, name="launcher_ring"))
    # head
    cubes.append(C("head", [-1.5, 23.5, -1.5], [3, 1.5, 3], dark_iron, name="neck"))
    cubes.append(C("head", [-3.5, 24.5, -3], [7, 5, 6], iron_plate, name="skull"))
    cubes.append(C("head", [-3, 25, -3.4], [6, 4, 0.5], brass_dark, name="face_plate"))
    sym(cubes, "head", "head", [-2.6, 26.4, -3.65], [1.6, 1.6, 0.35], eye_glow, "eye", glow=True)
    cubes.append(C("head", [-1.5, 25.2, -3.6], [3, 0.8, 0.3], grill, name="mouth"))
    sym(cubes, "head", "head", [-4.1, 25.75, -1], [0.6, 2, 2], brass, "ear_bolt")
    cubes.append(C("head", [-3, 29.5, -2.5], [6, 0.6, 5], brass, name="head_cap"))
    cubes.append(C("antenna", [1.25, 30, -0.25], [0.5, 2.6, 0.5], dark_iron, name="antenna_rod"))
    cubes.append(C("antenna", [1, 32.5, -0.5], [1, 1, 1], glow_core, glow=True, name="antenna_bulb"))
    # arms
    sym(cubes, "arm_r", "arm_l", [-9, 19.5, -2], [3, 3.5, 4], brass_dark, "shoulder")
    gear_disc(cubes, "shoulder_gear_r", 0, 21.25, -9.7, 1.75, 0.6, "shoulder_gear", axis="x")
    for c in cubes[-2:]:
        cubes.append(mirror(c, "shoulder_gear_l"))
    sym(cubes, "arm_r", "arm_l", [-8.25, 14.5, -1], [2, 5.5, 2], iron_plate, "upper_arm")
    sym(cubes, "arm_r", "arm_l", [-6.8, 15, 1], [0.7, 4.5, 0.7], copper, "arm_piston")
    sym(cubes, "elbow_r", "elbow_l", [-8.5, 13.75, -1.25], [2.5, 2.5, 2.5], dark_iron, "elbow")
    sym(cubes, "elbow_r", "elbow_l", [-9, 8.5, -1.75], [3.5, 5.5, 3.5], brass, "forearm")
    sym(cubes, "elbow_r", "elbow_l", [-9.35, 9.5, -1], [0.4, 3, 2], grill, "forearm_vent")
    sym(cubes, "claw_r", "claw_l", [-8.75, 6.5, -1.5], [3, 2, 3], dark_iron, "palm")
    sym(cubes, "claw_r", "claw_l", [-8.5, 4, -1.75], [2.5, 2.5, 0.8], iron_plate, "finger_front")
    sym(cubes, "claw_r", "claw_l", [-8.5, 4, 0.95], [2.5, 2.5, 0.8], iron_plate, "finger_back")
    geo, img, glow = build("clockwork_automaton", 128, bones, cubes, (2.5, 3, 1.2))

    # ---------------------------------------------------------------------------------- animations
    hold = None
    a = {}
    # constant machinery: cogs, shoulder gears and knee gears
    a["gears"] = {"loop": True, "animation_length": 3.0, "bones": {
        "gear_big": spin("z", 3.0),
        "gear_a": spin("z", 1.5, reverse=True),
        "gear_b": spin("z", 1.5, reverse=True),
        "gear_c": spin("z", 1.0, reverse=True),
        "shoulder_gear_r": spin("x", 3.0),
        "shoulder_gear_l": spin("x", 3.0, reverse=True),
        "antenna": {"scale": {"0.0": kf([1, 1, 1]), "1.4": kf([1, 1, 1]), "1.45": kf([1, 1.15, 1]), "1.55": kf([1, 1, 1])}},
    }}
    # idle: head scans in servo steps, body settles with a tiny hydraulic dip
    a["idle"] = {"loop": True, "animation_length": 4.0, "bones": {
        "head": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([0, 0, 0]), "1.12": kf([0, 25, 0], "step", [3]),
                              "2.2": kf([0, 25, 0]), "2.32": kf([5, -20, 0], "step", [3]), "3.4": kf([5, -20, 0]), "3.52": kf([0, 0, 0], "step", [3]), "4.0": kf([0, 0, 0])}},
        "body": {"position": {"0.0": kf([0, 0, 0]), "1.9": kf([0, 0, 0]), "2.0": kf([0, -0.4, 0], "step", [2]), "2.6": kf([0, -0.4, 0]), "2.7": kf([0, 0, 0], "step", [2])}},
        "arm_r": {"rotation": {"0.0": kf([0, 0, 0]), "2.8": kf([0, 0, 0]), "2.9": kf([-8, 0, 0], "step", [2]), "3.3": kf([-8, 0, 0]), "3.4": kf([0, 0, 0], "step", [2])}},
        "claw_l": {"rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([0, 0, 0]), "0.55": kf([0, -20, 0]), "0.8": kf([0, -20, 0]), "0.85": kf([0, 0, 0])}},
    }}
    # walk: stiff mechanical gait - legs snap to their next pose then hold, the torso jolts on every footfall
    L = 1.2
    a["walk"] = {"loop": True, "animation_length": L, "bones": {
        # legs: constant-speed linear sweeps with hard reversals (servo), knees kick on the forward swing
        "leg_r": {"rotation": {"0.0": kf([26, 0, 0]), "0.6": kf([-26, 0, 0]), "1.2": kf([26, 0, 0])}},
        "leg_l": {"rotation": {"0.0": kf([-26, 0, 0]), "0.6": kf([26, 0, 0]), "1.2": kf([-26, 0, 0])}},
        "shin_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.6": kf([0, 0, 0]), "0.75": kf([28, 0, 0]), "0.95": kf([0, 0, 0]), "1.2": kf([0, 0, 0])}},
        "shin_l": {"rotation": {"0.0": kf([0, 0, 0]), "0.15": kf([28, 0, 0]), "0.35": kf([0, 0, 0]), "1.2": kf([0, 0, 0])}},
        "arm_r": {"rotation": {"0.0": kf([-18, 0, 0]), "0.6": kf([18, 0, 0], "step", [3]), "1.2": kf([-18, 0, 0], "step", [3])}},
        "arm_l": {"rotation": {"0.0": kf([18, 0, 0]), "0.6": kf([-18, 0, 0], "step", [3]), "1.2": kf([18, 0, 0], "step", [3])}},
        "body": {"position": {"0.0": kf([0, -0.6, 0]), "0.05": kf([0, 0.1, 0]), "0.3": kf([0, 0.5, 0]), "0.6": kf([0, -0.6, 0]), "0.65": kf([0, 0.1, 0]), "0.9": kf([0, 0.5, 0]), "1.2": kf([0, -0.6, 0])},
                 "rotation": {"0.0": kf([0, 4, 0]), "0.6": kf([0, -4, 0], "step", [2]), "1.2": kf([0, 4, 0], "step", [2])}},
        "head": {"rotation": {"0.0": kf([2, -3, 0]), "0.1": kf([0, -3, 0]), "0.6": kf([2, 3, 0]), "0.7": kf([0, 3, 0]), "1.2": kf([2, -3, 0])}},
        "boiler": {"position": {"0.0": kf([0, -0.3, 0]), "0.1": kf([0, 0, 0]), "0.6": kf([0, -0.3, 0]), "0.7": kf([0, 0, 0]), "1.2": kf([0, -0.3, 0])}},
    }}
    # attack: arm ratchets up in three servo clicks, holds, snaps forward, then ratchets back
    a["attack"] = {"animation_length": 0.8, "bones": {
        "arm_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.24": kf([50, 0, 15], "step", [3]), "0.32": kf([50, 0, 15]), "0.38": kf([-95, 0, -5], "easeOutBack"),
                               "0.52": kf([-95, 0, -5]), "0.8": kf([0, 0, 0], "step", [3])}},
        "elbow_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.24": kf([-45, 0, 0], "step", [3]), "0.32": kf([-45, 0, 0]), "0.38": kf([0, 0, 0]), "0.8": kf([0, 0, 0])}},
        "claw_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.3": kf([0, 0, 0]), "0.36": kf([0, 90, 0]), "0.6": kf([0, 90, 0]), "0.7": kf([0, 0, 0], "step", [2])}},
        "torso": {"rotation": {"0.0": kf([0, 0, 0]), "0.24": kf([0, -18, 0], "step", [3]), "0.32": kf([0, -18, 0]), "0.38": kf([6, 22, 0], "easeOutBack"),
                               "0.52": kf([6, 22, 0]), "0.8": kf([0, 0, 0], "step", [3])}},
        "head": {"rotation": {"0.0": kf([0, 0, 0]), "0.38": kf([0, 0, 0]), "0.4": kf([0, 0, 8]), "0.46": kf([0, 0, -6]), "0.52": kf([0, 0, 0])}},
        "boiler": {"scale": {"0.0": kf([1, 1, 1]), "0.36": kf([1, 1, 1]), "0.4": kf([1.08, 1.1, 1.08]), "0.55": kf([1, 1, 1])}},
    }}
    # volley: plants its feet, chest cogs overspin, launcher pivots up and kicks three times
    a["volley"] = {"animation_length": 1.0, "bones": {
        "launcher": {"rotation": {"0.0": kf([0, 0, 0]), "0.2": kf([-25, 0, 0], "step", [2]), "0.55": kf([-25, 0, 0]), "0.9": kf([0, 0, 0], "step", [2])},
                     "position": {"0.0": kf([0, 0, 0]), "0.2": kf([0, 1, 0], "step", [2]), "0.6": kf([0, 1, 0]), "0.62": kf([0, 1, 1.2]), "0.68": kf([0, 1, 0]),
                                  "0.7": kf([0, 1, 1.2]), "0.76": kf([0, 1, 0]), "0.78": kf([0, 1, 1.2]), "0.84": kf([0, 1, 0]), "0.95": kf([0, 0, 0], "step", [2])}},
        "gear_big": {"rotation": {"0.0": kf([0, 0, 0]), "0.6": kf([0, 0, 1080], "easeInQuad"), "1.0": kf([0, 0, 1440], "easeOutQuad")}},
        "arm_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.2": kf([-30, 0, 20], "step", [2]), "0.85": kf([-30, 0, 20]), "1.0": kf([0, 0, 0], "step", [2])}},
        "arm_l": {"rotation": {"0.0": kf([0, 0, 0]), "0.2": kf([-30, 0, -20], "step", [2]), "0.85": kf([-30, 0, -20]), "1.0": kf([0, 0, 0], "step", [2])}},
        "body": {"position": {"0.0": kf([0, 0, 0]), "0.2": kf([0, -1, 0], "step", [2]), "0.85": kf([0, -1, 0]), "1.0": kf([0, 0, 0], "step", [2])}},
        "torso": {"rotation": {"0.0": kf([0, 0, 0]), "0.6": kf([0, 0, 0]), "0.62": kf([4, 0, 0]), "0.68": kf([0, 0, 0]), "0.7": kf([4, 0, 0]), "0.76": kf([0, 0, 0]),
                               "0.78": kf([4, 0, 0]), "0.84": kf([0, 0, 0])}},
        "boiler": {"scale": {"0.0": kf([1, 1, 1]), "0.5": kf([1.12, 1.1, 1.12]), "0.6": kf([0.94, 0.94, 0.94]), "0.8": kf([1, 1, 1])}},
    }}
    # assemble: parts drop into place and the head boots up
    a["assemble"] = {"animation_length": 1.4, "bones": {
        "root": {"scale": {"0.0": kf([0.2, 0.2, 0.2]), "0.4": kf([0.2, 0.2, 0.2]), "0.7": kf([1.05, 1.05, 1.05], "step", [3]), "0.8": kf([1, 1, 1])}},
        "torso": {"position": {"0.0": kf([0, 8, 0]), "0.5": kf([0, 8, 0]), "0.75": kf([0, 0, 0], "easeOutBounce")}},
        "head": {"position": {"0.0": kf([0, -3, 0]), "0.85": kf([0, -3, 0]), "1.0": kf([0, 0.6, 0], "step", [2]), "1.1": kf([0, 0, 0])},
                 "rotation": {"0.0": kf([0, 0, 0]), "1.1": kf([0, 0, 0]), "1.15": kf([0, 30, 0]), "1.25": kf([0, -30, 0]), "1.35": kf([0, 0, 0])}},
        "arm_r": {"rotation": {"0.0": kf([0, 0, -70]), "0.8": kf([0, 0, -70]), "1.0": kf([0, 0, 0], "step", [3])}},
        "arm_l": {"rotation": {"0.0": kf([0, 0, 70]), "0.8": kf([0, 0, 70]), "1.0": kf([0, 0, 0], "step", [3])}},
    }}
    # Mk.II only animations still need an entry so GeckoLib never misses a name
    a["grab"] = a["attack"]
    a["static"] = a["volley"]
    a["overload"] = {"loop": True, "animation_length": 0.5, "bones": {
        "torso": {"rotation": {"0.0": kf([15, 0, 3]), "0.25": kf([15, 0, -3]), "0.5": kf([15, 0, 3])}},
        "head": {"rotation": {"0.0": kf([30, 10, 0]), "0.25": kf([30, -10, 0]), "0.5": kf([30, 10, 0])}},
        "arm_r": {"rotation": {"0.0": kf([0, 0, -5])}}, "arm_l": {"rotation": {"0.0": kf([0, 0, 5])}}}}
    return geo, img, glow, anims(a)


# =========================================================================================== Automaton Mk.II (steam golem)

def automaton_mk2():
    bones = [
        ("root", None, [0, 0, 0], None),
        ("leg_r", "root", [-3.5, 9, 0], None),
        ("shin_r", "leg_r", [-3.5, 4.5, 0.5], None),
        ("leg_l", "root", [3.5, 9, 0], None),
        ("shin_l", "leg_l", [3.5, 4.5, 0.5], None),
        ("body", "root", [0, 10, 0], None),
        ("hull", "body", [0, 18, 0], None),
        ("emblem", "hull", [0, 20, -9.5], None),
        ("turbine", "hull", [0, 29.8, 0], None),
        ("head", "hull", [0, 28, -6.5], None),
        ("arm_r", "hull", [-9.5, 20.5, 0], None),
        ("forearm_r", "arm_r", [-10.75, 14.5, 0], None),
        ("fist_r", "forearm_r", [-10.5, 7.5, 0], None),
        ("arm_l", "hull", [9.5, 20.5, 0], None),
        ("forearm_l", "arm_l", [10.75, 14.5, 0], None),
        ("fist_l", "forearm_l", [10.5, 7.5, 0], None),
    ]
    cubes = []
    # spindly legs with spiked feet
    sym(cubes, "leg_r", "leg_l", [-5, 7.5, -1.5], [3, 2.5, 3], dark_iron, "hip")
    sym(cubes, "leg_r", "leg_l", [-4.5, 4.25, -0.5], [2, 3.5, 2], iron_plate, "thigh")
    sym(cubes, "leg_r", "leg_l", [-4.75, 4.5, 1.6], [0.8, 3.5, 0.8], copper, "thigh_piston")
    sym(cubes, "shin_r", "shin_l", [-4.75, 3.5, -0.75], [2.5, 1.5, 2.5], brass_dark, "knee")
    sym(cubes, "shin_r", "shin_l", [-4.5, 1.2, -0.5], [2, 2.4, 2], iron_plate, "shin")
    sym(cubes, "shin_r", "shin_l", [-6, 0, -4], [5, 1.2, 7], brass_dark, "foot")
    for i, (x, z) in enumerate(((-6.4, -4.4), (-2.4, -4.4), (-4.6, 2.6))):
        sym(cubes, "shin_r", "shin_l", [x, 0.1, z], [0.9, 0.9, 0.9], dark_iron, "spike%d" % i, rotation=[0, 45, 0])
    # spherical hull built from three intersecting boxes
    cubes.append(C("body", [-5, 9.5, -5], [10, 2, 10], dark_iron, name="skirt"))
    # round hull: horizontal octagonal slices (each octagon = union of four rectangles at 0/45/90/135 degrees)
    for i, (y0, y1, r) in enumerate(((11, 13.5, 6.0), (13.5, 16.5, 7.9), (16.5, 22.5, 8.5), (22.5, 25.5, 7.9), (25.5, 28.5, 6.0))):
        octagon(cubes, "hull", 0, 0, y0, y1, r, hull_plate, "slice%d" % i)
    octagon(cubes, "hull", 0, 0, 15.2, 16.8, 8.9, iron_plate, "belt")
    cubes.append(C("hull", [-6.5, 10.25, -6.5], [13, 1, 13], dark_iron, name="hull_bottom_ring"))
    sym(cubes, "hull", "hull", [-9.5, 18.5, -2.5], [2, 4, 5], dark_iron, "shoulder_socket")
    # top turbine with a collar ring
    cubes.append(C("hull", [-5, 28.5, -5], [10, 1, 10], iron_plate, name="collar"))
    for i, (o, s) in enumerate((([-5, 29.5, -5], [10, 1, 1]), ([-5, 29.5, 4], [10, 1, 1]), ([-5, 29.5, -4], [1, 1, 8]), ([4, 29.5, -4], [1, 1, 8]))):
        cubes.append(C("hull", o, s, iron_plate, name="collar_ring%d" % i))
    cubes.append(C("turbine", [-3.5, 29.5, -3.5], [7, 0.3, 7], glow_core, glow=True, name="turbine_glow"))
    for k in range(4):
        cubes.append(C("turbine", [-3.5, 29.85, -0.5], [7, 0.4, 1], dark_iron, name="blade%d" % k if k == 0 else None,
                       share=None if k == 0 else "blade0", rotation=[0, k * 45, 0], pivot=[0, 30, 0]))
    cubes.append(C("turbine", [-0.75, 29.9, -0.75], [1.5, 0.6, 1.5], brass, name="turbine_hub"))
    # little head sitting on the front of the hull
    cubes.append(C("head", [-2.5, 27.5, -8.5], [5, 4, 4], brass, name="head_shell"))
    cubes.append(C("head", [-2, 28, -8.9], [4, 2.5, 0.5], dark_iron, name="head_face"))
    sym(cubes, "head", "head", [-1.6, 28.9, -9.15], [1.1, 1.1, 0.35], white_eye, "eye", glow=True)
    cubes.append(C("head", [-0.5, 31.5, -8], [1, 1.2, 3], brass_dark, name="head_fin"))
    # chest emblem with lightning bolt
    cubes.append(C("emblem", [-3.5, 16.6, -9.1], [7, 7, 0.7], iron_plate, name="emblem_ring"))
    cubes.append(C("emblem", [-2.75, 17.35, -9.35], [5.5, 5.5, 0.4], brass_dark, name="emblem_disc"))
    cubes.append(C("emblem", [-0.1, 20.2, -9.65], [0.9, 2.6, 0.35], emblem_bolt, glow=True, name="bolt_top", rotation=[0, 0, -25], pivot=[0.35, 21.5, -9.5]))
    cubes.append(C("emblem", [-0.9, 19.6, -9.65], [1.9, 0.7, 0.35], emblem_bolt, glow=True, name="bolt_mid"))
    cubes.append(C("emblem", [-0.9, 17.7, -9.65], [0.9, 2.4, 0.35], emblem_bolt, glow=True, name="bolt_bottom", rotation=[0, 0, -25], pivot=[-0.45, 18.9, -9.5]))
    # huge arms
    sym(cubes, "arm_r", "arm_l", [-12.25, 18.5, -2], [3, 4, 4], brass_dark, "shoulder")
    sym(cubes, "arm_r", "arm_l", [-11.75, 14, -1], [2, 5, 2], iron_plate, "upper_arm")
    sym(cubes, "arm_r", "arm_l", [-10.4, 16, 1.6], [3, 1, 1], hose, "hose_a")
    sym(cubes, "arm_r", "arm_l", [-11, 13.5, 1.6], [1, 3, 1], hose, "hose_b")
    sym(cubes, "forearm_r", "forearm_l", [-12.25, 13, -1.5], [3, 3, 3], dark_iron, "elbow")
    sym(cubes, "forearm_r", "forearm_l", [-13.75, 7, -3], [6, 6.5, 6], brass, "forearm")
    sym(cubes, "forearm_r", "forearm_l", [-14.1, 8.5, -1.5], [0.4, 3, 3], grill, "forearm_vent")
    sym(cubes, "forearm_r", "forearm_l", [-14, 11.5, -3.25], [6.5, 1, 6.5], iron_plate, "forearm_band")
    sym(cubes, "fist_r", "fist_l", [-14, 1.5, -3.5], [7, 5.5, 7], brass_dark, "palm")
    for i, x in enumerate((-13.75, -11.5, -9.25)):
        sym(cubes, "fist_r", "fist_l", [x, 0.5, -4.6], [2, 3.5, 1.6], brass, "finger%d" % i)
    sym(cubes, "fist_r", "fist_l", [-7.4, 2, -3], [1.2, 3, 2.5], iron_plate, "thumb")
    geo, img, glow = build("clockwork_automaton_mk2", 256, bones, cubes, (3.5, 3.5, 1.4))

    a = {}
    a["gears"] = {"loop": True, "animation_length": 1.0, "bones": {
        "turbine": spin("y", 1.0),
        "emblem": {"scale": {"0.0": kf([1, 1, 1]), "0.5": kf([1.04, 1.04, 1]), "1.0": kf([1, 1, 1])}},
    }}
    a["idle"] = {"loop": True, "animation_length": 3.0, "bones": {
        "hull": {"position": {"0.0": kf([0, 0, 0]), "1.0": kf([0, 0, 0]), "1.1": kf([0, -0.5, 0], "step", [2]), "1.8": kf([0, -0.5, 0]), "1.9": kf([0, 0, 0], "step", [2])}},
        "arm_r": {"rotation": {"0.0": kf([0, 0, 0]), "1.5": kf([-4, 0, 3], "step", [3]), "3.0": kf([0, 0, 0], "step", [3])}},
        "arm_l": {"rotation": {"0.0": kf([0, 0, 0]), "1.5": kf([-4, 0, -3], "step", [3]), "3.0": kf([0, 0, 0], "step", [3])}},
        "head": {"rotation": {"0.0": kf([0, 0, 0]), "0.8": kf([0, 0, 0]), "0.9": kf([0, 20, 0], "step", [2]), "2.0": kf([0, 20, 0]), "2.1": kf([0, 0, 0], "step", [2])}},
    }}
    a["walk"] = {"loop": True, "animation_length": 1.4, "bones": {
        "leg_r": {"rotation": {"0.0": kf([24, 0, 0]), "0.7": kf([-24, 0, 0]), "1.4": kf([24, 0, 0])}},
        "leg_l": {"rotation": {"0.0": kf([-24, 0, 0]), "0.7": kf([24, 0, 0]), "1.4": kf([-24, 0, 0])}},
        "shin_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.7": kf([0, 0, 0]), "0.9": kf([32, 0, 0]), "1.1": kf([0, 0, 0]), "1.4": kf([0, 0, 0])}},
        "shin_l": {"rotation": {"0.0": kf([0, 0, 0]), "0.2": kf([32, 0, 0]), "0.4": kf([0, 0, 0]), "1.4": kf([0, 0, 0])}},
        "body": {"position": {"0.0": kf([0, -1.2, 0]), "0.06": kf([0, 0.2, 0]), "0.35": kf([0, 0.6, 0]), "0.7": kf([0, -1.2, 0]), "0.76": kf([0, 0.2, 0]), "1.05": kf([0, 0.6, 0]), "1.4": kf([0, -1.2, 0])},
                 "rotation": {"0.0": kf([0, 0, 5]), "0.6": kf([0, 0, -5], "step", [2]), "1.3": kf([0, 0, 5], "step", [2]), "1.4": kf([0, 0, 5])}},
        "arm_r": {"rotation": {"0.0": kf([-15, 0, 0]), "0.6": kf([15, 0, 0], "step", [3]), "1.3": kf([-15, 0, 0], "step", [3]), "1.4": kf([-15, 0, 0])}},
        "arm_l": {"rotation": {"0.0": kf([15, 0, 0]), "0.6": kf([-15, 0, 0], "step", [3]), "1.3": kf([15, 0, 0], "step", [3]), "1.4": kf([15, 0, 0])}},
    }}
    # power fist: wind back, hold, uppercut
    a["attack"] = {"animation_length": 0.9, "bones": {
        "arm_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.3": kf([45, 0, 10], "step", [3]), "0.38": kf([45, 0, 10]), "0.46": kf([-120, 0, -10], "easeOutBack"),
                               "0.62": kf([-120, 0, -10]), "0.9": kf([0, 0, 0], "step", [3])}},
        "forearm_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.3": kf([-50, 0, 0], "step", [3]), "0.38": kf([-50, 0, 0]), "0.46": kf([-20, 0, 0]), "0.9": kf([0, 0, 0], "step", [3])}},
        "hull": {"rotation": {"0.0": kf([0, 0, 0]), "0.3": kf([-8, -20, 0], "step", [3]), "0.38": kf([-8, -20, 0]), "0.46": kf([10, 25, 0], "easeOutBack"),
                              "0.62": kf([10, 25, 0]), "0.9": kf([0, 0, 0], "step", [3])}},
        "turbine": {"scale": {"0.0": kf([1, 1, 1]), "0.44": kf([1, 1, 1]), "0.48": kf([1.2, 1.6, 1.2]), "0.7": kf([1, 1, 1])}},
    }}
    # rocket grab: the right fist launches forward on its piston and reels back in
    a["grab"] = {"animation_length": 1.3, "bones": {
        "arm_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.25": kf([-90, 0, 0], "step", [3]), "1.05": kf([-90, 0, 0]), "1.3": kf([0, 0, 0], "step", [3])}},
        "fist_r": {"position": {"0.0": kf([0, 0, 0]), "0.3": kf([0, 0, 0]), "0.45": kf([0, -24, 0], "easeOutQuad"), "0.65": kf([0, -24, 0]), "0.95": kf([0, 0, 0], "easeInQuad")},
                   "rotation": {"0.0": kf([0, 0, 0]), "0.3": kf([0, 0, 0]), "0.45": kf([0, 360, 0]), "0.95": kf([0, 720, 0])}},
        "hull": {"rotation": {"0.0": kf([0, 0, 0]), "0.25": kf([0, -15, 0], "step", [2]), "0.45": kf([0, 10, 0]), "0.95": kf([0, 10, 0]), "1.0": kf([0, -6, 0]), "1.3": kf([0, 0, 0])}},
        "turbine": {"scale": {"0.0": kf([1, 1, 1]), "0.3": kf([1, 1, 1]), "0.35": kf([1.2, 2, 1.2]), "0.6": kf([1, 1, 1])}},
    }}
    a["volley"] = {"animation_length": 1.0, "bones": {
        "arm_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.25": kf([-60, 0, 30], "step", [2]), "0.8": kf([-60, 0, 30]), "1.0": kf([0, 0, 0], "step", [2])}},
        "arm_l": {"rotation": {"0.0": kf([0, 0, 0]), "0.25": kf([-60, 0, -30], "step", [2]), "0.8": kf([-60, 0, -30]), "1.0": kf([0, 0, 0], "step", [2])}},
        "turbine": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([0, 1440, 0], "easeInOutQuad")}, "position": {"0.0": kf([0, 0, 0]), "0.4": kf([0, 1, 0]), "0.8": kf([0, 1, 0]), "1.0": kf([0, 0, 0])}},
        "hull": {"position": {"0.0": kf([0, 0, 0]), "0.6": kf([0, 0, 0]), "0.62": kf([0, 0, 1]), "0.7": kf([0, 0, 0]), "0.72": kf([0, 0, 1]), "0.8": kf([0, 0, 0])}},
    }}
    # static field: arms spread, emblem flares
    a["static"] = {"animation_length": 1.0, "bones": {
        "arm_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.2": kf([0, 0, -70], "step", [2]), "0.8": kf([0, 0, -70]), "1.0": kf([0, 0, 0], "step", [2])}},
        "arm_l": {"rotation": {"0.0": kf([0, 0, 0]), "0.2": kf([0, 0, 70], "step", [2]), "0.8": kf([0, 0, 70]), "1.0": kf([0, 0, 0], "step", [2])}},
        "emblem": {"scale": {"0.0": kf([1, 1, 1]), "0.3": kf([1.3, 1.3, 1.6]), "0.5": kf([1.1, 1.1, 1.2]), "0.7": kf([1.3, 1.3, 1.6]), "1.0": kf([1, 1, 1])}},
        "head": {"rotation": {"0.0": kf([0, 0, 0]), "0.2": kf([-20, 0, 0]), "0.8": kf([-20, 0, 0]), "1.0": kf([0, 0, 0])}},
    }}
    a["overload"] = {"loop": True, "animation_length": 0.5, "bones": {
        "hull": {"rotation": {"0.0": kf([16, 0, 3]), "0.125": kf([18, 0, -3]), "0.25": kf([16, 0, 3]), "0.375": kf([18, 0, -3]), "0.5": kf([16, 0, 3])},
                 "position": {"0.0": kf([0, -1.5, 0])}},
        "arm_r": {"rotation": {"0.0": kf([20, 0, 8])}}, "arm_l": {"rotation": {"0.0": kf([20, 0, -8])}},
        "forearm_r": {"rotation": {"0.0": kf([-10, 0, 0])}}, "forearm_l": {"rotation": {"0.0": kf([-10, 0, 0])}},
        "head": {"rotation": {"0.0": kf([35, 0, 0])}},
        "emblem": {"scale": {"0.0": kf([1, 1, 1]), "0.1": kf([1.5, 1.5, 2]), "0.25": kf([1, 1, 1]), "0.35": kf([1.5, 1.5, 2]), "0.5": kf([1, 1, 1])}},
        "turbine": {"rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([0, 1080, 0])}}}}
    a["assemble"] = {"animation_length": 1.4, "bones": {
        "root": {"scale": {"0.0": kf([0.2, 0.2, 0.2]), "0.4": kf([0.2, 0.2, 0.2]), "0.7": kf([1.08, 1.08, 1.08], "step", [3]), "0.8": kf([1, 1, 1])}},
        "hull": {"position": {"0.0": kf([0, 10, 0]), "0.5": kf([0, 10, 0]), "0.75": kf([0, 0, 0], "easeOutBounce")}},
        "arm_r": {"rotation": {"0.0": kf([0, 0, -80]), "0.8": kf([0, 0, -80]), "1.0": kf([0, 0, 0], "step", [3])}},
        "arm_l": {"rotation": {"0.0": kf([0, 0, 80]), "0.8": kf([0, 0, 80]), "1.0": kf([0, 0, 0], "step", [3])}},
        "head": {"position": {"0.0": kf([0, -3, 0]), "0.9": kf([0, -3, 0]), "1.05": kf([0, 0.5, 0], "step", [2]), "1.15": kf([0, 0, 0])}},
    }}
    return geo, img, glow, anims(a)


# =========================================================================================== Tech Dragon

K = 2.0  # dragon geometry is authored at half size and scaled up so the texture keeps a reasonable texel density


def _s(v):
    return [round(c * K, 3) for c in v]


def tech_dragon():
    raw_bones = [
        ("root", None, [0, 0, 0], None),
        ("body", "root", [0, 20, 0], None),
        ("chest_core", "body", [0, 18, -11], None),
        ("neck1", "body", [0, 22, -10], [-15, 0, 0]),
        ("neck2", "neck1", [0, 23.5, -18], [-10, 0, 0]),
        ("head", "neck2", [0, 24.5, -25.5], [20, 0, 0]),
        ("jaw", "head", [0, 21, -31], None),
        ("crest", "head", [0, 29, -29], None),
        ("wing_r", "body", [-7, 25, -5], None),
        ("wing_r2", "wing_r", [-25, 25.5, -5], None),
        ("wing_l", "body", [7, 25, -5], None),
        ("wing_l2", "wing_l", [25, 25.5, -5], None),
        ("leg_fr", "body", [-5.5, 16, -7], None),
        ("foot_fr", "leg_fr", [-6, 9, -7.5], None),
        ("leg_fl", "body", [5.5, 16, -7], None),
        ("foot_fl", "leg_fl", [6, 9, -7.5], None),
        ("leg_br", "body", [-5.5, 16, 7], None),
        ("foot_br", "leg_br", [-6, 8, 8], None),
        ("leg_bl", "body", [5.5, 16, 7], None),
        ("foot_bl", "leg_bl", [6, 8, 8], None),
        ("tail1", "body", [0, 20, 11], None),
        ("tail2", "tail1", [0, 20.5, 20], None),
        ("tail3", "tail2", [0, 21, 29], None),
        ("tail4", "tail3", [0, 21.25, 37.5], None),
        ("tail5", "tail4", [0, 21.5, 45.5], None),
    ]
    bones = [(n, p, _s(pv), r) for n, p, pv, r in raw_bones]
    raw = []

    def add(bone, origin, size, mat, name, **kw):
        c = C(bone, origin, size, mat, name=name, **kw)
        raw.append(c)
        return c

    def addsym(bone_r, bone_l, origin, size, mat, name, **kw):
        c = add(bone_r, origin, size, mat, name, **kw)
        raw.append(mirror(c, bone_l))
        return c

    # torso
    add("body", [-7, 14, -11], [14, 12, 22], scales, "torso")
    add("body", [-5.5, 13, -10], [11, 1, 19], belly, "belly")
    add("body", [-6, 26, -9], [12, 2.5, 17], armor_plate, "back_plate")
    add("body", [-7.5, 19, -12], [15, 6, 4], armor_plate, "chest_plate")
    addsym("body", "body", [-8, 21, -5], [2, 5, 8], armor_plate, "shoulder_guard")
    for i, z in enumerate((-6, -1, 4)):
        add("body", [-0.75, 28.5, z], [1.5, 3 - i * 0.5, 2], crystal, "spine_crystal%d" % i, glow=True, rotation=[-25, 0, 0], pivot=[0, 28.5, z + 1])
    add("chest_core", [-1.5, 16.5, -12.6], [3, 3, 1], gem, "core_gem", glow=True)
    add("chest_core", [-2.5, 15.5, -12.2], [5, 5, 0.6], armor_plate, "core_frame")
    # neck and head
    add("neck1", [-4, 18, -18.5], [8, 8, 9], scales, "neck1")
    add("neck1", [-4.5, 25, -17.5], [9, 1.5, 7], armor_plate, "neck1_plate")
    add("neck2", [-3.5, 19.5, -26], [7, 7, 8.5], scales, "neck2")
    add("neck2", [-4, 20, -24.5], [8, 6, 1.5], armor_plate, "collar")
    add("head", [-5.5, 21, -39], [11, 7.5, 14], scales, "skull")
    add("head", [-6, 27.5, -38.5], [12, 3, 13], armor_plate, "helm")
    add("head", [-1, 30.5, -37], [2, 1.5, 10], armor_plate, "helm_ridge")
    add("head", [-4.25, 20.5, -46], [8.5, 5.5, 7.5], scales, "snout")
    add("head", [-4.5, 25, -46.5], [9, 2, 8], armor_plate, "snout_plate")
    add("head", [-1.25, 26, -48], [2.5, 3, 2.5], armor_plate, "nose_spike", rotation=[45, 0, 0])
    addsym("head", "head", [-5.8, 24.5, -37], [0.5, 1.5, 3], gem, "eye", glow=True)
    addsym("head", "head", [-4, 19.75, -46], [0.9, 1, 6.5], bone_white, "teeth_up")
    addsym("head", "head", [-7.5, 24.5, -31], [2, 2, 6], armor_plate, "cheek_spike", rotation=[0, -25, 0])
    addsym("head", "head", [-6.5, 21, -33], [1.5, 1.5, 4], claw, "jaw_spike", rotation=[-15, -20, 0])
    add("jaw", [-4, 18, -44], [8, 3, 15], scales, "jaw")
    add("jaw", [-3.5, 20.75, -43.5], [7, 0.9, 0.9], bone_white, "teeth_low")
    add("jaw", [-4.5, 17.5, -38], [9, 1, 8], armor_plate, "jaw_plate")
    add("crest", [-1.1, 28, -32], [2.2, 13, 2.2], crystal, "crest_main", glow=True, rotation=[-38, 0, 0], pivot=[0, 28.5, -31])
    addsym("crest", "crest", [-4.2, 28, -31], [1.8, 10, 1.8], crystal, "crest_side", glow=True, rotation=[-42, 0, 18], pivot=[-3.3, 28.5, -30.1])
    addsym("crest", "crest", [-6, 27.5, -28], [1.4, 7, 1.4], crystal, "crest_back", glow=True, rotation=[-58, 0, 28], pivot=[-5.3, 27.5, -27.3])
    # wings: arm bone with membrane, outer finger with membrane, brass plate with glowing eye gem
    addsym("wing_r", "wing_l", [-25, 24, -6.5], [18, 3, 3], armor_plate, "wing_arm")
    for i, (x, d) in enumerate(((-13, 14), (-19, 17), (-25, 19))):
        addsym("wing_r", "wing_l", [x, 24.75, -3.5], [6, 0.6, d], membrane, "membrane_in%d" % i)
    addsym("wing_r", "wing_l", [-20, 24.9, -4], [1, 0.8, 15], claw, "wing_rib_in", rotation=[0, 12, 0], pivot=[-19.5, 25, -4])
    addsym("wing_r", "wing_l", [-21, 23.75, -7.5], [8, 3.5, 5], armor_plate, "wing_plate")
    addsym("wing_r", "wing_l", [-18.5, 25, -6.25], [3, 0.8, 2.5], gem, "wing_gem", glow=True, inflate=0.05)
    addsym("wing_r2", "wing_l2", [-46, 24.75, -6], [21, 2.5, 2.5], armor_plate, "wing_finger")
    for i, (x, w, d) in enumerate(((-32, 7, 19), (-39, 7, 15), (-46, 7, 10), (-50, 4, 5))):
        addsym("wing_r2", "wing_l2", [x, 25.25, -3.5], [w, 0.5, d], membrane, "membrane_out%d" % i)
    addsym("wing_r2", "wing_l2", [-33, 25.4, -4], [1, 0.7, 18], claw, "wing_rib_a", rotation=[0, 18, 0], pivot=[-32.5, 25.5, -4])
    addsym("wing_r2", "wing_l2", [-41, 25.4, -4], [1, 0.7, 13], claw, "wing_rib_b", rotation=[0, 30, 0], pivot=[-40.5, 25.5, -4])
    addsym("wing_r2", "wing_l2", [-50, 24.5, -6.5], [5, 3, 3], armor_plate, "wing_tip")
    addsym("wing_r2", "wing_l2", [-49.5, 25.8, -5.75], [1.2, 0.6, 1.2], gem, "wing_tip_gem", glow=True)
    addsym("wing_r2", "wing_l2", [-40, 24.4, -5.5], [3, 3, 1], claw, "wing_thumb", rotation=[0, 0, 30])
    # legs
    addsym("leg_fr", "leg_fl", [-8, 9, -9.5], [4.5, 8, 5], scales, "front_thigh")
    addsym("leg_fr", "leg_fl", [-8.4, 12, -10], [5.2, 4, 5.8], armor_plate, "front_knee_plate")
    addsym("foot_fr", "foot_fl", [-8.25, 6, -12], [4.5, 3, 7], scales, "front_foot")
    for i, x in enumerate((-8.25, -6.75, -5.25)):
        addsym("foot_fr", "foot_fl", [x, 6, -13.5], [1.2, 1.4, 1.8], claw, "front_talon%d" % i)
    addsym("leg_br", "leg_bl", [-9, 8, 4], [6, 10, 7], scales, "back_thigh")
    addsym("leg_br", "leg_bl", [-9.5, 13, 3.5], [7, 4, 8], armor_plate, "hip_plate")
    addsym("foot_br", "foot_bl", [-8.5, 5, 5], [5, 3.5, 8], scales, "back_foot")
    for i, x in enumerate((-8.5, -6.75, -5)):
        addsym("foot_br", "foot_bl", [x, 5, 3.5], [1.4, 1.5, 2], claw, "back_talon%d" % i)
    # tail
    add("tail1", [-4, 16.5, 10], [8, 7, 10.5], scales, "tail1")
    add("tail1", [-4.5, 22.5, 12], [9, 1.5, 6], armor_plate, "tail1_plate")
    add("tail2", [-3.25, 17.5, 19.5], [6.5, 6, 10], scales, "tail2")
    add("tail2", [-3.75, 23, 21], [7.5, 1.25, 7], armor_plate, "tail2_plate")
    add("tail2", [-0.5, 24, 23], [1, 2, 2], crystal, "tail_crystal", glow=True, rotation=[-30, 0, 0])
    add("tail3", [-2.5, 18.5, 28.5], [5, 5, 9.5], scales, "tail3")
    add("tail3", [-3, 22.75, 30], [6, 1, 6], armor_plate, "tail3_plate")
    add("tail4", [-2, 19.25, 37], [4, 4, 9], scales, "tail4")
    add("tail4", [-2.25, 21.75, 39.5], [4.5, 2, 4.5], armor_plate, "tail_ring")
    add("tail5", [-1.5, 20, 45], [3, 3, 7], scales, "tail5")
    add("tail5", [-0.5, 18, 50], [1, 7, 7], armor_plate, "tail_blade")
    add("tail5", [-1.25, 20.5, 51.5], [2.5, 2, 2], gem, "tail_gem", glow=True)
    add("tail5", [-0.75, 20, 55], [1.5, 3, 3], armor_plate, "tail_spike", rotation=[45, 0, 0])

    cubes = []
    for c in raw:
        c.origin = _s(c.origin)
        c.size = _s(c.size)
        if c.pivot:
            c.pivot = _s(c.pivot)
        cubes.append(c)
    geo, img, glow = build("tech_dragon", 512, bones, cubes, (18, 10, 2))
    return geo, img, glow, anims(dragon_animations())


def wave(length, amp, phase=0.0, axis=0, steps=8, base=None, easing="easeInOutSine"):
    """Sinusoidal rotation keyframes for looping motion (axis 0=x, 1=y, 2=z)."""
    frames = {}
    for i in range(steps + 1):
        t = length * i / steps
        v = [0, 0, 0] if base is None else list(base)
        v[axis] += amp * math.sin(2 * math.pi * (i / steps) + phase)
        frames["%g" % round(t, 4)] = kf([round(x, 2) for x in v], easing if i else None)
    return frames


def merge_rot(*parts):
    """Combines several single-axis waves that share the same keyframe times."""
    out = {}
    for p in parts:
        for t, k in p.items():
            if t not in out:
                out[t] = {"vector": list(k["vector"])}
                if "easing" in k:
                    out[t]["easing"] = k["easing"]
            else:
                out[t]["vector"] = [round(a + b, 2) for a, b in zip(out[t]["vector"], k["vector"])]
    return out


def dragon_animations():
    a = {}
    tail = ["tail1", "tail2", "tail3", "tail4", "tail5"]

    def tail_wave(length, amp_y, amp_x=0.0, base_x=0.0):
        d = {}
        for i, b in enumerate(tail):
            d[b] = {"rotation": merge_rot(wave(length, amp_y, -i * 0.7, 1), wave(length, amp_x, -i * 0.7 + 1, 0, base=[base_x, 0, 0]))}
        return d

    def wings(length, amp, base=0.0, fold=0.0, lag=0.9, outer=0.8):
        return {
            "wing_r": {"rotation": wave(length, amp, 0, 2, base=[0, fold, -base])},
            "wing_l": {"rotation": wave(length, -amp, 0, 2, base=[0, -fold, base])},
            "wing_r2": {"rotation": wave(length, amp * outer, -lag, 2, base=[0, fold * 0.5, -base * 0.5])},
            "wing_l2": {"rotation": wave(length, -amp * outer, -lag, 2, base=[0, -fold * 0.5, base * 0.5])},
        }

    def legs_tucked(x=35):
        return {"leg_fr": {"rotation": {"0.0": kf([x, 0, 0])}}, "leg_fl": {"rotation": {"0.0": kf([x, 0, 0])}},
                "leg_br": {"rotation": {"0.0": kf([x + 15, 0, 0])}}, "leg_bl": {"rotation": {"0.0": kf([x + 15, 0, 0])}},
                "foot_fr": {"rotation": {"0.0": kf([40, 0, 0])}}, "foot_fl": {"rotation": {"0.0": kf([40, 0, 0])}},
                "foot_br": {"rotation": {"0.0": kf([30, 0, 0])}}, "foot_bl": {"rotation": {"0.0": kf([30, 0, 0])}}}

    # flight loop
    fly = {"body": {"position": wave(1.6, 3, math.pi, 1, base=[0, 0, 0]) and {k: kf([0, v["vector"][1], 0], v.get("easing")) for k, v in wave(1.6, 3, math.pi, 1).items()},
                    "rotation": {"0.0": kf([0, 0, 0])}},
           "neck1": {"rotation": wave(1.6, 4, 0.5, 0)}, "head": {"rotation": wave(1.6, -5, 0.8, 0)}}
    fly.update(wings(1.6, 38, base=5))
    fly.update(tail_wave(1.6, 8, 4))
    fly.update(legs_tucked())
    a["fly"] = {"loop": True, "animation_length": 1.6, "bones": fly}

    hover = {"body": {"rotation": {"0.0": kf([-12, 0, 0])}, "position": {k: kf([0, v["vector"][1], 0], v.get("easing")) for k, v in wave(2.4, 2, math.pi, 1).items()}},
             "neck1": {"rotation": merge_rot(wave(2.4, 3, 0.3, 0, base=[10, 0, 0]))}, "head": {"rotation": wave(2.4, -4, 0.6, 0)}}
    hover.update(wings(2.4, 30, base=0, fold=-10))
    hover.update(tail_wave(2.4, 10, 5, base_x=8))
    hover.update(legs_tucked(20))
    a["hover"] = {"loop": True, "animation_length": 2.4, "bones": hover}

    glide = {"body": {"rotation": {"0.0": kf([5, 0, 0])}}}
    glide.update(wings(3.0, 6, base=8))
    glide.update(tail_wave(3.0, 6, 2))
    glide.update(legs_tucked(45))
    a["glide"] = {"loop": True, "animation_length": 3.0, "bones": glide}

    # dive: wings folded back, neck straight
    dive = {"body": {"rotation": {"0.0": kf([25, 0, 0])}},
            "wing_r": {"rotation": wave(0.6, 4, 0, 2, base=[0, -55, -15])}, "wing_l": {"rotation": wave(0.6, -4, 0, 2, base=[0, 55, 15])},
            "wing_r2": {"rotation": {"0.0": kf([0, -70, 10])}}, "wing_l2": {"rotation": {"0.0": kf([0, 70, -10])}},
            "neck1": {"rotation": {"0.0": kf([20, 0, 0])}}, "head": {"rotation": {"0.0": kf([-10, 0, 0])}}}
    dive.update(tail_wave(0.6, 3, 1))
    dive.update(legs_tucked(60))
    a["dive"] = {"loop": True, "animation_length": 0.6, "bones": dive}

    # ground idle / walk
    gidle = {"body": {"position": {k: kf([0, v["vector"][1], 0], v.get("easing")) for k, v in wave(3.0, 0.8, 0, 1).items()}},
             "neck1": {"rotation": wave(3.0, 3, 0.5, 0, base=[10, 0, 0])}, "head": {"rotation": wave(3.0, -3, 1, 0)},
             "wing_r": {"rotation": {"0.0": kf([0, -40, -35])}}, "wing_l": {"rotation": {"0.0": kf([0, 40, 35])}},
             "wing_r2": {"rotation": {"0.0": kf([0, -110, 40])}}, "wing_l2": {"rotation": {"0.0": kf([0, 110, -40])}},
             "jaw": {"rotation": {"0.0": kf([0, 0, 0]), "2.0": kf([0, 0, 0]), "2.3": kf([12, 0, 0]), "2.7": kf([0, 0, 0])}}}
    gidle.update(tail_wave(3.0, 12, 3))
    a["ground_idle"] = {"loop": True, "animation_length": 3.0, "bones": gidle}

    walk = dict(gidle)
    walk = {k: v for k, v in gidle.items() if k not in ("jaw",)}
    for leg, ph in (("leg_fr", 0), ("leg_bl", 0), ("leg_fl", math.pi), ("leg_br", math.pi)):
        walk[leg] = {"rotation": wave(1.6, 28, ph, 0)}
    walk["body"] = {"rotation": wave(1.6, 3, 0, 2), "position": {k: kf([0, abs(v["vector"][1]), 0], v.get("easing")) for k, v in wave(1.6, 1.5, 0, 1).items()}}
    walk.update(tail_wave(1.6, 14, 3))
    a["walk"] = {"loop": True, "animation_length": 1.6, "bones": walk}

    # roar
    roar = {"body": {"rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([-25, 0, 0], "easeOutBack"), "2.0": kf([-25, 0, 0]), "2.5": kf([0, 0, 0], "easeInOutSine")}},
            "neck1": {"rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([-20, 0, 0]), "2.0": kf([-20, 0, 0]), "2.5": kf([0, 0, 0])}},
            "head": {"rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([-25, 0, 0]), "0.7": kf([-22, 4, 0]), "0.9": kf([-25, -4, 0]), "1.1": kf([-22, 4, 0]), "1.3": kf([-25, -4, 0]),
                                  "1.5": kf([-22, 3, 0]), "2.0": kf([-25, 0, 0]), "2.5": kf([0, 0, 0])}},
            "jaw": {"rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([40, 0, 0], "easeOutBack"), "2.0": kf([40, 0, 0]), "2.4": kf([0, 0, 0])}},
            "crest": {"scale": {"0.0": kf([1, 1, 1]), "0.5": kf([1.3, 1.3, 1.3]), "1.0": kf([1.1, 1.1, 1.1]), "1.5": kf([1.3, 1.3, 1.3]), "2.5": kf([1, 1, 1])}},
            "wing_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([0, 10, 25]), "2.0": kf([0, 10, 25]), "2.5": kf([0, 0, 0])}},
            "wing_l": {"rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([0, -10, -25]), "2.0": kf([0, -10, -25]), "2.5": kf([0, 0, 0])}},
            "wing_r2": {"rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([0, 0, 15]), "2.0": kf([0, 0, 15]), "2.5": kf([0, 0, 0])}},
            "wing_l2": {"rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([0, 0, -15]), "2.0": kf([0, 0, -15]), "2.5": kf([0, 0, 0])}}}
    roar.update(tail_wave(2.5, 10, 6))
    a["roar"] = {"animation_length": 2.5, "bones": roar}

    # lightning breath: charge, then hold the jaw open while the head trembles
    a["breath_charge"] = {"animation_length": 1.0, "bones": {
        "neck1": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([-15, 0, 0], "easeInOutSine")}},
        "head": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([-20, 0, 0], "easeInOutSine")}},
        "jaw": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([15, 0, 0])}},
        "crest": {"scale": {"0.0": kf([1, 1, 1]), "0.5": kf([1.2, 1.2, 1.2]), "0.75": kf([1.05, 1.05, 1.05]), "1.0": kf([1.35, 1.35, 1.35])}},
        "chest_core": {"scale": {"0.0": kf([1, 1, 1]), "1.0": kf([1.5, 1.5, 1.5])}}}}
    a["breath"] = {"loop": True, "animation_length": 0.4, "bones": {
        "neck1": {"rotation": {"0.0": kf([10, 0, 0]), "0.2": kf([11, 1, 0]), "0.4": kf([10, 0, 0])}},
        "head": {"rotation": {"0.0": kf([5, 0, 0]), "0.1": kf([6, 2, 0]), "0.2": kf([5, -2, 0]), "0.3": kf([6, 1, 0]), "0.4": kf([5, 0, 0])}},
        "jaw": {"rotation": {"0.0": kf([38, 0, 0]), "0.2": kf([42, 0, 0]), "0.4": kf([38, 0, 0])}},
        "crest": {"scale": {"0.0": kf([1.3, 1.3, 1.3]), "0.2": kf([1.4, 1.4, 1.4]), "0.4": kf([1.3, 1.3, 1.3])}},
        "chest_core": {"scale": {"0.0": kf([1.4, 1.4, 1.4]), "0.2": kf([1.6, 1.6, 1.6]), "0.4": kf([1.4, 1.4, 1.4])}}}}

    # cog spit: three quick head jerks
    spit = {"jaw": {"rotation": {}}, "head": {"rotation": {}}, "neck1": {"rotation": {}}}
    for i in range(3):
        t = i * 0.3
        spit["head"]["rotation"]["%g" % t] = kf([-15, 0, 0])
        spit["head"]["rotation"]["%g" % (t + 0.1)] = kf([15, 0, 0], "easeOutBack")
        spit["jaw"]["rotation"]["%g" % t] = kf([5, 0, 0])
        spit["jaw"]["rotation"]["%g" % (t + 0.1)] = kf([35, 0, 0])
        spit["neck1"]["rotation"]["%g" % t] = kf([-8, 0, 0])
        spit["neck1"]["rotation"]["%g" % (t + 0.1)] = kf([8, 0, 0])
    for b in spit:
        spit[b]["rotation"]["1.0"] = kf([0, 0, 0], "easeInOutSine")
    a["cog_spit"] = {"animation_length": 1.0, "bones": spit}

    # thunder call: rear up, wings high, crest pulses
    thunder = {"body": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([-35, 0, 0], "easeOutBack"), "1.7": kf([-35, 0, 0]), "2.0": kf([0, 0, 0])}},
               "neck1": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([-15, 0, 0]), "1.7": kf([-15, 0, 0]), "2.0": kf([0, 0, 0])}},
               "head": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([-30, 0, 0]), "1.7": kf([-30, 0, 0]), "2.0": kf([0, 0, 0])}},
               "jaw": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([35, 0, 0]), "1.6": kf([35, 0, 0]), "2.0": kf([0, 0, 0])}},
               "crest": {"scale": {"0.0": kf([1, 1, 1]), "0.4": kf([1.5, 1.5, 1.5]), "0.6": kf([1.2, 1.2, 1.2]), "0.8": kf([1.5, 1.5, 1.5]), "1.0": kf([1.2, 1.2, 1.2]),
                                   "1.2": kf([1.5, 1.5, 1.5]), "2.0": kf([1, 1, 1])}},
               "wing_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([0, 15, 55]), "1.7": kf([0, 15, 55]), "2.0": kf([0, 0, 0])}},
               "wing_l": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([0, -15, -55]), "1.7": kf([0, -15, -55]), "2.0": kf([0, 0, 0])}},
               "wing_r2": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([0, 0, -20]), "1.7": kf([0, 0, -20]), "2.0": kf([0, 0, 0])}},
               "wing_l2": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([0, 0, 20]), "1.7": kf([0, 0, 20]), "2.0": kf([0, 0, 0])}}}
    thunder.update(tail_wave(2.0, 8, 8, base_x=15))
    thunder.update(legs_tucked(10))
    a["thunder"] = {"animation_length": 2.0, "bones": thunder}

    # slam (landing impact)
    slam = {"body": {"position": {"0.0": kf([0, 6, 0]), "0.25": kf([0, -3, 0], "easeInQuad"), "0.45": kf([0, 0.5, 0]), "1.2": kf([0, 0, 0])},
                     "rotation": {"0.0": kf([20, 0, 0]), "0.25": kf([-5, 0, 0]), "0.5": kf([0, 0, 0])}},
            "wing_r": {"rotation": {"0.0": kf([0, 0, 60]), "0.25": kf([0, 0, -40], "easeInQuad"), "0.8": kf([0, -40, -35]), "1.2": kf([0, -40, -35])}},
            "wing_l": {"rotation": {"0.0": kf([0, 0, -60]), "0.25": kf([0, 0, 40], "easeInQuad"), "0.8": kf([0, 40, 35]), "1.2": kf([0, 40, 35])}},
            "wing_r2": {"rotation": {"0.0": kf([0, 0, 0]), "0.3": kf([0, 0, -30]), "0.8": kf([0, -110, 40]), "1.2": kf([0, -110, 40])}},
            "wing_l2": {"rotation": {"0.0": kf([0, 0, 0]), "0.3": kf([0, 0, 30]), "0.8": kf([0, 110, -40]), "1.2": kf([0, 110, -40])}},
            "neck1": {"rotation": {"0.0": kf([-10, 0, 0]), "0.25": kf([25, 0, 0]), "0.6": kf([0, 0, 0])}},
            "head": {"rotation": {"0.0": kf([0, 0, 0]), "0.25": kf([10, 0, 0]), "0.6": kf([-10, 0, 0]), "1.2": kf([0, 0, 0])}},
            "jaw": {"rotation": {"0.0": kf([0, 0, 0]), "0.3": kf([30, 0, 0]), "1.0": kf([0, 0, 0])}}}
    a["slam"] = {"animation_length": 1.2, "bones": slam}

    # tail swipe: wind up then whip a full circle
    swipe = {"root": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([0, -30, 0], "easeOutSine"), "0.9": kf([0, 330, 0], "easeInOutQuad"), "1.0": kf([0, 360, 0])}},
             "body": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([0, 0, -8]), "0.9": kf([0, 0, 10]), "1.2": kf([0, 0, 0])}}}
    for i, b in enumerate(tail):
        swipe[b] = {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([0, 25, 0]), "0.65": kf([0, -15 - 5 * i, 0]), "1.0": kf([0, 10, 0]), "1.4": kf([0, 0, 0])}}
    a["tail_swipe"] = {"animation_length": 1.4, "bones": swipe}

    # claw strike with the right foreleg
    a["claw"] = {"animation_length": 1.0, "bones": {
        "body": {"rotation": {"0.0": kf([0, 0, 0]), "0.35": kf([-20, -10, 0]), "0.5": kf([8, 10, 0], "easeOutBack"), "1.0": kf([0, 0, 0])}},
        "leg_fr": {"rotation": {"0.0": kf([0, 0, 0]), "0.35": kf([-95, 0, -15]), "0.5": kf([35, 0, 5], "easeOutBack"), "0.7": kf([35, 0, 5]), "1.0": kf([0, 0, 0])}},
        "foot_fr": {"rotation": {"0.0": kf([0, 0, 0]), "0.35": kf([-40, 0, 0]), "0.5": kf([30, 0, 0]), "1.0": kf([0, 0, 0])}},
        "neck1": {"rotation": {"0.0": kf([0, 0, 0]), "0.35": kf([-10, 0, 0]), "0.5": kf([15, 0, 0]), "1.0": kf([0, 0, 0])}},
        "jaw": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([30, 0, 0]), "0.8": kf([0, 0, 0])}}}}

    # summon drones: chest core flares
    summon = {"body": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([-20, 0, 0]), "1.6": kf([-20, 0, 0]), "2.0": kf([0, 0, 0])}},
              "chest_core": {"scale": {"0.0": kf([1, 1, 1]), "0.5": kf([1.8, 1.8, 1.8]), "0.7": kf([1.4, 1.4, 1.4]), "0.9": kf([1.8, 1.8, 1.8]), "2.0": kf([1, 1, 1])}},
              "wing_r": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([0, 30, 10]), "1.6": kf([0, 30, 10]), "2.0": kf([0, 0, 0])}},
              "wing_l": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([0, -30, -10]), "1.6": kf([0, -30, -10]), "2.0": kf([0, 0, 0])}},
              "jaw": {"rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([25, 0, 0]), "1.5": kf([25, 0, 0]), "2.0": kf([0, 0, 0])}}}
    summon.update(tail_wave(2.0, 8, 4))
    a["summon"] = {"animation_length": 2.0, "bones": summon}

    # phase two overcharge: convulses, crystals swell
    p2 = {"body": {"rotation": {}}, "crest": {"scale": {}}, "neck1": {"rotation": {}}, "jaw": {"rotation": {"0.0": kf([0, 0, 0]), "0.6": kf([45, 0, 0]), "2.6": kf([45, 0, 0]), "3.0": kf([0, 0, 0])}}}
    for i in range(13):
        t = i * 0.25
        p2["body"]["rotation"]["%g" % t] = kf([-15 + (5 if i % 2 else -5), 0, (6 if i % 2 else -6)])
        p2["neck1"]["rotation"]["%g" % t] = kf([-25 + (6 if i % 2 else 0), (8 if i % 2 else -8), 0])
        p2["crest"]["scale"]["%g" % t] = kf([1 + 0.06 * i, 1 + 0.06 * i, 1 + 0.06 * i])
    p2["body"]["rotation"]["3.0"] = kf([0, 0, 0])
    p2["neck1"]["rotation"]["3.0"] = kf([0, 0, 0])
    p2["crest"]["scale"]["3.0"] = kf([1, 1, 1])
    p2.update(wings(0.5, 25, base=20))
    a["phase_two"] = {"animation_length": 3.0, "bones": p2}

    # spawn: wrapped in its wings, unfurls and roars
    spawn = {"body": {"position": {"0.0": kf([0, -6, 0]), "2.0": kf([0, -6, 0]), "3.0": kf([0, 0, 0], "easeOutBack"), "5.0": kf([0, 0, 0])},
                      "rotation": {"0.0": kf([30, 0, 0]), "2.0": kf([30, 0, 0]), "3.0": kf([-25, 0, 0], "easeOutBack"), "4.4": kf([-25, 0, 0]), "5.0": kf([0, 0, 0])}},
             "wing_r": {"rotation": {"0.0": kf([0, -20, -80]), "2.0": kf([0, -20, -80]), "3.0": kf([0, 10, 35], "easeOutBack"), "4.4": kf([0, 10, 35]), "5.0": kf([0, 0, 0])}},
             "wing_l": {"rotation": {"0.0": kf([0, 20, 80]), "2.0": kf([0, 20, 80]), "3.0": kf([0, -10, -35], "easeOutBack"), "4.4": kf([0, -10, -35]), "5.0": kf([0, 0, 0])}},
             "wing_r2": {"rotation": {"0.0": kf([0, 0, -100]), "2.2": kf([0, 0, -100]), "3.0": kf([0, 0, 15]), "5.0": kf([0, 0, 0])}},
             "wing_l2": {"rotation": {"0.0": kf([0, 0, 100]), "2.2": kf([0, 0, 100]), "3.0": kf([0, 0, -15]), "5.0": kf([0, 0, 0])}},
             "neck1": {"rotation": {"0.0": kf([50, 0, 0]), "2.0": kf([50, 0, 0]), "3.0": kf([-25, 0, 0]), "4.4": kf([-25, 0, 0]), "5.0": kf([0, 0, 0])}},
             "head": {"rotation": {"0.0": kf([30, 0, 0]), "2.0": kf([30, 0, 0]), "3.0": kf([-30, 0, 0]), "4.4": kf([-30, 0, 0]), "5.0": kf([0, 0, 0])}},
             "jaw": {"rotation": {"0.0": kf([0, 0, 0]), "3.0": kf([0, 0, 0]), "3.2": kf([45, 0, 0]), "4.3": kf([45, 0, 0]), "4.8": kf([0, 0, 0])}},
             "crest": {"scale": {"0.0": kf([0.3, 0.3, 0.3]), "2.0": kf([0.3, 0.3, 0.3]), "3.0": kf([1.4, 1.4, 1.4], "easeOutBack"), "5.0": kf([1, 1, 1])}},
             "chest_core": {"scale": {"0.0": kf([0.5, 0.5, 0.5]), "1.0": kf([1.6, 1.6, 1.6]), "1.5": kf([0.8, 0.8, 0.8]), "2.0": kf([1.8, 1.8, 1.8]), "3.0": kf([1, 1, 1])}}}
    for i, b in enumerate(tail):
        spawn[b] = {"rotation": {"0.0": kf([0, 35, 0]), "2.0": kf([0, 35, 0]), "3.0": kf([0, -10, 0]), "5.0": kf([0, 0, 0])}}
    a["spawn"] = {"animation_length": 5.0, "loop": "hold_on_last_frame", "bones": spawn}

    # death: spasm, wings droop, collapse
    death = {"body": {"rotation": {"0.0": kf([0, 0, 0]), "0.3": kf([-20, 0, 10]), "0.6": kf([-10, 0, -10]), "1.0": kf([-25, 0, 8]), "2.5": kf([15, 0, 35], "easeInQuad"), "4.0": kf([15, 0, 40])},
                      "position": {"0.0": kf([0, 0, 0]), "1.0": kf([0, 2, 0]), "2.5": kf([0, -8, 0], "easeInQuad"), "4.0": kf([0, -8, 0])}},
             "neck1": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([-35, 0, 0]), "2.5": kf([40, 15, 0], "easeInQuad"), "4.0": kf([40, 15, 0])}},
             "head": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([-25, 0, 0]), "2.5": kf([30, 0, 20]), "4.0": kf([30, 0, 20])}},
             "jaw": {"rotation": {"0.0": kf([0, 0, 0]), "0.4": kf([45, 0, 0]), "2.5": kf([25, 0, 0]), "4.0": kf([25, 0, 0])}},
             "wing_r": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([0, 0, 40]), "2.5": kf([0, -20, -60]), "4.0": kf([0, -20, -60])}},
             "wing_l": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([0, 0, -40]), "2.5": kf([0, 20, 50]), "4.0": kf([0, 20, 50])}},
             "wing_r2": {"rotation": {"0.0": kf([0, 0, 0]), "2.5": kf([0, 0, -40]), "4.0": kf([0, 0, -40])}},
             "wing_l2": {"rotation": {"0.0": kf([0, 0, 0]), "2.5": kf([0, 0, 40]), "4.0": kf([0, 0, 40])}},
             "crest": {"scale": {"0.0": kf([1, 1, 1]), "1.0": kf([1.5, 1.5, 1.5]), "3.0": kf([0.6, 0.6, 0.6])}},
             "chest_core": {"scale": {"0.0": kf([1, 1, 1]), "1.0": kf([2, 2, 2]), "3.0": kf([0.3, 0.3, 0.3])}}}
    for i, b in enumerate(tail):
        death[b] = {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([0, 20, 0]), "2.5": kf([10, -15 - 4 * i, 0]), "4.0": kf([10, -15 - 4 * i, 0])}}
    a["death"] = {"animation_length": 4.0, "loop": "hold_on_last_frame", "bones": death}
    return a


def recolor_overcharged(img):
    """Phase two: blue crystals and gems burn electric orange-white."""
    import colorsys
    out = img.copy()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, al = img.getpixel((x, y))
            if not al:
                continue
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if 0.53 < h < 0.65 and s > 0.6 and l > 0.25:
                nr, ng, nb = colorsys.hls_to_rgb(0.07, min(0.85, l * 1.05), 1.0)
                out.putpixel((x, y), (int(nr * 255), int(ng * 255), int(nb * 255), al))
    return out


# =========================================================================================== Clockwork Staff (item)

def tick_frames():
    """Clock hand: holds each position, then snaps 30 degrees in 0.04s, twelve times per 6s loop."""
    frames = {"0.0": kf([0, 0, 0])}
    for i in range(1, 13):
        t = 0.5 * i
        frames["%g" % round(t - 0.04, 2)] = kf([0, 0, -30 * (i - 1)])
        frames["%g" % t] = kf([0, 0, -30 * i])
    return frames


def clockwork_staff():
    bones = [
        ("staff", None, [0, 0, 0], None),
        ("shaft", "staff", [0, 0, 0], None),
        ("head", "staff", [0, 22, 0], None),
        ("ring", "head", [0, 22, 0], None),
        ("core", "head", [0, 22, 0], None),
        ("hand", "head", [0, 22, 0], None),
        ("orbit", "head", [0, 22, 0], None),
        ("small_gear", "staff", [-3.4, 13.6, 0], None),
    ]
    cubes = []
    # twisted shaft: 4 px segments alternating 0/45 degree twist, brass bands between
    y = -14
    for i in range(7):
        twist = 45 if i % 2 else 0
        cubes.append(C("shaft", [-0.9, y, -0.9], [1.8, 4.2, 1.8], wood, name="seg%d" % i if i < 2 else None, share=None if i < 2 else "seg%d" % (i % 2),
                       rotation=[0, twist, 0] if twist else None, pivot=[0, y + 2, 0]))
        y += 4
    for i, by in enumerate((-10.3, -2.3, 5.7, 12.6)):
        cubes.append(C("shaft", [-1.15, by, -1.15], [2.3, 0.8, 2.3], brass_dark, name="band%d" % i if i == 0 else None, share=None if i == 0 else "band0"))
    cubes.append(C("shaft", [-1.1, -1.5, -1.1], [2.2, 6, 2.2], leather_grip, name="grip"))
    cubes.append(C("shaft", [-0.75, -16.5, -0.75], [1.5, 2.6, 1.5], brass, name="ferrule"))
    cubes.append(C("shaft", [-0.6, -17.6, -0.6], [1.2, 1.2, 1.2], brass, name="ferrule_tip", rotation=[45, 0, 45], pivot=[0, -17, 0]))
    cubes.append(C("shaft", [-1.4, 14, -1.4], [2.8, 2.2, 2.8], brass_dark, name="collar"))
    cubes.append(C("shaft", [-0.8, 16, -0.8], [1.6, 2.4, 1.6], dark_iron, name="neck"))
    # cog ring (12 rim segments + 12 teeth) around the head
    r_rim, r_tooth = 5.6, 6.9
    for k in range(12):
        ang = k * 30
        rad = math.radians(ang)
        cx, cy = math.cos(rad) * r_rim, 22 + math.sin(rad) * r_rim
        cubes.append(C("ring", [cx - 1.6, cy - 0.6, -0.8], [3.2, 1.2, 1.6], brass, name="rim0" if k == 0 else None, share=None if k == 0 else "rim0",
                       rotation=[0, 0, ang + 90], pivot=[cx, cy, 0]))
        tx, ty = math.cos(rad) * r_tooth, 22 + math.sin(rad) * r_tooth
        cubes.append(C("ring", [tx - 0.6, ty - 0.6, -0.7], [1.2, 1.2, 1.4], brass_dark, name="tooth0" if k == 0 else None, share=None if k == 0 else "tooth0",
                       rotation=[0, 0, ang], pivot=[tx, ty, 0]))
    for k in range(3):
        cubes.append(C("ring", [-0.4, 22, -0.4], [0.8, 5.2, 0.8], dark_iron, name="spoke0" if k == 0 else None, share=None if k == 0 else "spoke0",
                       rotation=[0, 0, k * 120], pivot=[0, 22, 0]))
    # cyan core (two rotated cubes) inside a brass hub
    cubes.append(C("core", [-1.3, 20.7, -1.3], [2.6, 2.6, 2.6], glow_core, glow=True, name="core_a"))
    cubes.append(C("core", [-1.3, 20.7, -1.3], [2.6, 2.6, 2.6], glow_core, glow=True, share="core_a", rotation=[45, 45, 0], pivot=[0, 22, 0]))
    # lightning clock hand: zig-zag towards the upper right, arrow head on the tip
    cubes.append(C("hand", [-0.45, 22, -1.2], [0.9, 5, 0.6], orange_bolt, name="hand_a", rotation=[0, 0, -40], pivot=[0, 22, -0.9]))
    cubes.append(C("hand", [2.6, 25.2, -1.2], [0.9, 3.5, 0.6], orange_bolt, name="hand_b", rotation=[0, 0, -15], pivot=[3.05, 25.2, -0.9]))
    cubes.append(C("hand", [3.6, 28.2, -1.25], [2.2, 2.2, 0.7], orange_bolt, name="hand_tip", rotation=[0, 0, 45], pivot=[4.7, 29.3, -0.9]))
    cubes.append(C("hand", [-0.4, 18.4, -1.2], [0.8, 3.6, 0.6], orange_bolt, name="hand_tail", rotation=[0, 0, -40], pivot=[0, 22, -0.9]))
    # orbiting orbs
    cubes.append(C("orbit", [-9.2, 21, -1], [2, 2, 2], violet_orb, glow=True, name="orb"))
    cubes.append(C("orbit", [7.4, 25, -0.8], [1.6, 1.6, 1.6], violet_orb, glow=True, share="orb"))
    # small side cog under the head
    gear_disc(cubes, "small_gear", -3.4, 13.6, -0.4, 1.6, 0.8, "small_gear")
    geo, img, glow = build("clockwork_staff", 64, bones, cubes, (2, 3.5, 0.5))
    a = {"idle": {"loop": True, "animation_length": 6.0, "bones": {
        "ring": spin("z", 6.0),
        "small_gear": spin("z", 2.0, turns=1, reverse=True),
        "orbit": {"rotation": {"0.0": kf([0, 0, 0]), "6.0": kf([0, 360, 0])},
                  "position": {"0.0": kf([0, 0, 0]), "1.5": kf([0, 0.6, 0], "easeInOutSine"), "3.0": kf([0, 0, 0], "easeInOutSine"), "4.5": kf([0, -0.6, 0], "easeInOutSine"), "6.0": kf([0, 0, 0], "easeInOutSine")}},
        "core": {"scale": {"0.0": kf([1, 1, 1]), "0.75": kf([1.15, 1.15, 1.15], "easeInOutSine"), "1.5": kf([1, 1, 1], "easeInOutSine"), "2.25": kf([1.15, 1.15, 1.15], "easeInOutSine"),
                           "3.0": kf([1, 1, 1], "easeInOutSine"), "3.75": kf([1.15, 1.15, 1.15], "easeInOutSine"), "4.5": kf([1, 1, 1], "easeInOutSine"),
                           "5.25": kf([1.15, 1.15, 1.15], "easeInOutSine"), "6.0": kf([1, 1, 1], "easeInOutSine")}},
        # the clock hand ticks: one sharp step every half second
        "hand": {"rotation": tick_frames()},
    }}}
    return geo, img, glow, anims(a["idle"] and a)


# =========================================================================================== Rocket Hand (Rocket Grab)

def rocket_hand():
    """Big brass mechanical fist pointing towards +Z (the renderer aligns +Z with its flight), copper piston cuff."""
    bones = [
        ("hand", None, [0, 0, 0], None),
        ("cuff", "hand", [0, 0, -4], None),
        ("finger1", "hand", [-2.5, 1.5, 4], None),
        ("finger2", "hand", [0, 1.5, 4], None),
        ("finger3", "hand", [2.5, 1.5, 4], None),
        ("thumb", "hand", [-4.5, -1, 2], None),
    ]
    cubes = [
        C("hand", [-4, -3, -1], [8, 6, 5], brass_dark, name="palm"),
        C("hand", [-3.5, 2.6, -0.5], [7, 0.8, 4], brass, name="knuckle_plate"),
        C("hand", [-1, -1, -1.4], [2, 2, 0.6], glow_core, glow=True, name="palm_core"),
        C("cuff", [-3, -2.5, -9], [6, 5, 8], copper, name="cuff"),
        C("cuff", [-3.4, -2.9, -6], [6.8, 5.8, 1.2], brass, name="cuff_band"),
        C("cuff", [-1, -1, -12], [2, 2, 3], dark_iron, name="piston"),
    ]
    for i, x in enumerate((-4, -1.25, 1.5)):
        bone = "finger%d" % (i + 1)
        cubes.append(C(bone, [x, -1.5, 4], [2.5, 3, 4.5], brass, name="f%d" % i if i == 0 else None, share=None if i == 0 else "f0"))
        cubes.append(C(bone, [x + 0.25, -1.25, 8.2], [2, 2.5, 2], iron_plate, name="ft%d" % i if i == 0 else None, share=None if i == 0 else "ft0"))
    cubes.append(C("thumb", [-5.5, -2.5, 0], [2, 2.5, 4.5], brass, name="thumb"))
    geo, img, glow = build("rocket_hand", 64, bones, cubes, (1.5, 1.5, 0))
    a = {
        "open": {"loop": True, "animation_length": 1.0, "bones": {
            "finger1": {"rotation": {"0.0": kf([-35, 0, -8])}}, "finger2": {"rotation": {"0.0": kf([-35, 0, 0])}},
            "finger3": {"rotation": {"0.0": kf([-35, 0, 8])}}, "thumb": {"rotation": {"0.0": kf([0, -35, 0])}},
            "hand": {"rotation": {"0.0": kf([0, 0, 0]), "1.0": kf([0, 0, 360])}}}},
        "closed": {"loop": True, "animation_length": 1.0, "bones": {
            "finger1": {"rotation": {"0.0": kf([70, 0, 0])}}, "finger2": {"rotation": {"0.0": kf([70, 0, 0])}},
            "finger3": {"rotation": {"0.0": kf([70, 0, 0])}}, "thumb": {"rotation": {"0.0": kf([0, 50, 0])}}}},
    }
    return geo, img, glow, anims(a)
