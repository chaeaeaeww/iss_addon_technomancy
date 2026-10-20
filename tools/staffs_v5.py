"""
Iron's Technomancy 1.9 staff models (GeckoLib items):

- clockwork_staff (tier 1, ref: "Clockwork Apprentice Staff" + an armillary staff): a walnut shaft with brass bands
  and a leather grip, a gear-and-gem pommel, and a head where a standing brass cog ring holds a maroon/cream orb while
  a big LEVEL ring of brass cogs turns around it (with two little planet cogs riding on it);
- hextech_staff and its star levels 1-3: a navy shaft with brass fittings and an armillary of brass rings turning
  around a tall glowing cyan crystal. Each star adds more: orbiting crystal shards (1), a third ring and more shards
  (2), a crown of crystal spikes (3), and the crystal grows.
"""
import math

import models
from models import C, build, gear_face
from models_v2 import anims, gear_disc, leather_grip, spin
from pixelart import BRASS, COPPER, IRON, line, put, ramp, rgb

WALNUT = [rgb("24140C"), rgb("3A2214"), rgb("54331D"), rgb("6E4528"), rgb("8A5A34")]
NAVY = [rgb("070C20"), rgb("0F1834"), rgb("18264E"), rgb("22366C"), rgb("31498C"), rgb("4566B0")]
HCYAN = [rgb("0A3A70"), rgb("1670C8"), rgb("38B4FF"), rgb("8AE0FF"), rgb("D8F8FF"), rgb("FFFFFF")]
MAROON = [rgb("2E0A16"), rgb("521428"), rgb("7C223E"), rgb("A8405C"), rgb("D27A90")]
CREAM = [rgb("8C7350"), rgb("B89C70"), rgb("DCC59A"), rgb("F2E4C2"), rgb("FFF8E6")]


def shade(colors, img, x, y, w, h, base, spread, seed=0):
    for j in range(h):
        for i in range(w):
            t = base + spread * (0.5 - j / max(1, h)) * 0.8 + ((i * 7 + j * 13 + seed) % 5 - 2) * 0.02
            put(img, x + i, y + j, ramp(colors, t))


def walnut(img, x, y, w, h, face):
    shade(WALNUT, img, x, y, w, h, 0.55, 0.4, x + y)
    for j in range(0, h, 3):
        put(img, x + (j // 3) % max(1, w), y + j, WALNUT[1])


def navy(img, x, y, w, h, face):
    shade(NAVY, img, x, y, w, h, 0.55, 0.45, x * 3 + y)
    if h >= 4 and w >= 2:
        line(img, x + w // 2, y + 1, x + w // 2, y + h - 2, NAVY[4])


def brass(img, x, y, w, h, face):
    shade(BRASS, img, x, y, w, h, 0.62, 0.5, x + y * 3)
    line(img, x, y, x + w - 1, y, BRASS[5])


def brass_dark(img, x, y, w, h, face):
    shade(BRASS, img, x, y, w, h, 0.38, 0.4, x + y)


def copper(img, x, y, w, h, face):
    shade(COPPER, img, x, y, w, h, 0.6, 0.5, x + y)


def maroon_gem(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            t = 0.85 - 0.6 * (i + j) / max(1, w + h - 2)
            put(img, x + i, y + j, ramp(MAROON, t))
    put(img, x, y, CREAM[4])


def cream_cap(img, x, y, w, h, face):
    shade(CREAM, img, x, y, w, h, 0.6, 0.5, x)


def crystal(img, x, y, w, h, face):
    for j in range(h):
        for i in range(w):
            t = 0.95 - 0.55 * (j / max(1, h - 1)) + (0.1 if i == 0 else 0)
            put(img, x + i, y + j, ramp(HCYAN, t))
    put(img, x, y, HCYAN[5])


def ring_of(cubes, bone, cy, radius, segs, thick, depth, mat, teeth=None, tooth_mat=brass_dark, plane="xz", tilt=None, name="r"):
    """A ring of `segs` boxes around (0, cy, 0) in the given plane ('xz' level, 'xy' standing); optional outward teeth."""
    seg = 2 * math.pi * radius / segs * 1.12
    first = None
    for k in range(segs):
        a = k * 360.0 / segs
        r = math.radians(a)
        if plane == "xz":
            cx, cz = math.cos(r) * radius, math.sin(r) * radius
            c = C(bone, [cx - seg / 2, cy - depth / 2, cz - thick / 2], [seg, depth, thick], mat, share=first, name=None if first else name,
                  rotation=[0, -a - 90, 0], pivot=[cx, cy, cz])
        else:
            cx, cyy = math.cos(r) * radius, cy + math.sin(r) * radius
            c = C(bone, [cx - seg / 2, cyy - thick / 2, -depth / 2], [seg, thick, depth], mat, share=first, name=None if first else name,
                  rotation=[0, 0, -(a + 90)], pivot=[cx, cyy, 0])   # bedrock x is mirrored: z turns the other way
        cubes.append(c)
        first = first or c.name
    if teeth:
        tfirst = None
        for k in range(teeth):
            a = (k + 0.5) * 360.0 / teeth
            r = math.radians(a)
            rr = radius + thick * 0.5 + 0.45
            if plane == "xz":
                cx, cz = math.cos(r) * rr, math.sin(r) * rr
                c = C(bone, [cx - 0.5, cy - depth * 0.4, cz - 0.5], [1.0, depth * 0.8, 1.0], tooth_mat, share=tfirst, name=None if tfirst else name + "_t",
                      rotation=[0, -a, 0], pivot=[cx, cy, cz])
            else:
                cx, cyy = math.cos(r) * rr, cy + math.sin(r) * rr
                c = C(bone, [cx - 0.5, cyy - 0.5, -depth * 0.4], [1.0, 1.0, depth * 0.8], tooth_mat, share=tfirst, name=None if tfirst else name + "_t",
                      rotation=[0, 0, -a], pivot=[cx, cyy, 0])
            cubes.append(c)
            tfirst = tfirst or c.name


def shaft(cubes, mat, band_mat, grip=True):
    y = -16
    for i in range(8):
        cubes.append(C("shaft", [-0.95, y, -0.95], [1.9, 4.1, 1.9], mat, name="seg" if i == 0 else None, share=None if i == 0 else "seg",
                       rotation=[0, 45, 0] if i % 2 else None, pivot=[0, y + 2, 0]))
        y += 4
    for i, by in enumerate((-12.2, -4.0, 4.4, 12.0)):
        cubes.append(C("shaft", [-1.25, by, -1.25], [2.5, 0.9, 2.5], band_mat, name="band" if i == 0 else None, share=None if i == 0 else "band"))
    if grip:
        cubes.append(C("shaft", [-1.15, -2.8, -1.15], [2.3, 6.2, 2.3], leather_grip, name="grip"))
    cubes.append(C("shaft", [-1.6, 15.4, -1.6], [3.2, 2.0, 3.2], band_mat, name="collar"))
    cubes.append(C("shaft", [-1.0, 17.2, -1.0], [2.0, 1.6, 2.0], brass_dark, name="neck"))


# ============================================================================================ tier 1

def clockwork_staff():
    bones = [("staff", None, [0, 0, 0], None), ("shaft", "staff", [0, 0, 0], None), ("pommel", "staff", [0, -17.5, 0], None),
             ("head", "staff", [0, 24, 0], None), ("ring_v", "head", [0, 24, 0], None), ("ring_h", "head", [0, 24, 0], None),
             ("planet_a", "ring_h", [7.4, 24, 0], None), ("planet_b", "ring_h", [-7.4, 24, 0], None), ("orb", "head", [0, 24, 0], None)]
    cubes = []
    shaft(cubes, walnut, brass)
    # pommel: a small cog with a maroon gem
    gear_disc(cubes, "pommel", 0, -17.5, -0.5, 1.9, 1.0, "pommel_gear", material=brass)
    cubes.append(C("pommel", [-0.7, -19.6, -0.7], [1.4, 1.4, 1.4], maroon_gem, name="pommel_gem", rotation=[45, 0, 45], pivot=[0, -18.9, 0]))
    # crown prongs holding the head
    for k in range(4):
        cubes.append(C("head", [-0.4, 18.6, -0.4], [0.8, 3.4, 0.8], brass, name="prong" if k == 0 else None, share=None if k == 0 else "prong",
                       rotation=[0, k * 90 + 45, 24], pivot=[0, 18.6, 0]))
    # standing cog ring around the orb
    ring_of(cubes, "ring_v", 24, 4.6, 12, 1.0, 1.4, brass, teeth=12, plane="xy", name="vring")
    # the orb: maroon gem in a cream setting
    cubes.append(C("orb", [-1.6, 22.4, -1.6], [3.2, 3.2, 3.2], maroon_gem, glow=True, name="orb_a"))
    cubes.append(C("orb", [-1.6, 22.4, -1.6], [3.2, 3.2, 3.2], maroon_gem, glow=True, share="orb_a", rotation=[45, 45, 0], pivot=[0, 24, 0]))
    cubes.append(C("orb", [-0.6, 27.6, -0.6], [1.2, 1.2, 1.2], cream_cap, name="orb_tip", rotation=[45, 0, 45], pivot=[0, 28.2, 0]))
    # the big level ring of cogs (turns around the staff)
    ring_of(cubes, "ring_h", 24, 7.4, 16, 0.9, 0.9, brass, teeth=20, plane="xz", name="hring")
    for k in range(4):
        cubes.append(C("ring_h", [-7.4, 23.7, -0.3], [14.8, 0.6, 0.6], brass_dark, name="spoke" if k == 0 else None, share=None if k == 0 else "spoke",
                       rotation=[0, k * 45, 0], pivot=[0, 24, 0]))
    gear_disc(cubes, "planet_a", 7.4, 24, -0.5, 1.5, 1.0, "planet_a_g", material=copper)
    gear_disc(cubes, "planet_b", -7.4, 24, -0.5, 1.5, 1.0, "planet_b_g", material=copper)
    geo, img, glow = build("clockwork_staff", 64, bones, cubes, (2.2, 3.6, 0.5), bedrock_sides=True)
    a = {"idle": {"loop": True, "animation_length": 8.0, "bones": {
        "ring_h": {"rotation": {"0.0": models.kf([0, 0, 0]), "8.0": models.kf([0, 360, 0])}},
        "ring_v": spin("z", 4.0, turns=2, reverse=True),
        "planet_a": spin("z", 1.0, turns=8),
        "planet_b": spin("z", 1.0, turns=8, reverse=True),
        "pommel": spin("z", 2.0, turns=4),
        "orb": {"scale": {"0.0": models.kf([1, 1, 1]), "1.0": models.kf([1.1, 1.1, 1.1], "easeInOutSine"), "2.0": models.kf([1, 1, 1], "easeInOutSine"),
                          "3.0": models.kf([1.1, 1.1, 1.1], "easeInOutSine"), "4.0": models.kf([1, 1, 1], "easeInOutSine"), "5.0": models.kf([1.1, 1.1, 1.1], "easeInOutSine"),
                          "6.0": models.kf([1, 1, 1], "easeInOutSine"), "7.0": models.kf([1.1, 1.1, 1.1], "easeInOutSine"), "8.0": models.kf([1, 1, 1], "easeInOutSine")}},
    }}}
    return geo, img, glow, anims(a)


# ============================================================================================ hextech

def hextech_staff(stars):
    bones = [("staff", None, [0, 0, 0], None), ("shaft", "staff", [0, 0, 0], None), ("head", "staff", [0, 25, 0], None),
             ("ring_h", "head", [0, 25, 0], None), ("ring_v", "head", [0, 25, 0], None), ("ring_t", "head", [0, 25, 0], [0, 0, 35]),
             ("ring_t2", "head", [0, 25, 0], [0, 0, -35]), ("crystal", "head", [0, 25, 0], None), ("shards", "head", [0, 25, 0], None),
             ("crown", "head", [0, 25, 0], None)]
    cubes = []
    shaft(cubes, navy, brass, grip=True)
    cubes.append(C("shaft", [-0.8, -19.2, -0.8], [1.6, 2.6, 1.6], brass, name="ferrule"))
    cubes.append(C("shaft", [-0.6, -20.4, -0.6], [1.2, 1.2, 1.2], crystal, glow=True, name="ferrule_gem", rotation=[45, 0, 45], pivot=[0, -19.8, 0]))
    for k in range(4):
        cubes.append(C("head", [-0.45, 18.8, -0.45], [0.9, 4.2, 0.9], brass, name="prong" if k == 0 else None, share=None if k == 0 else "prong",
                       rotation=[0, k * 90 + 45, 28], pivot=[0, 18.8, 0]))
    size = 1.0 + 0.12 * stars
    h = 7.0 * size
    w = 2.4 * size
    cubes.append(C("crystal", [-w / 2, 25 - h / 2, -w / 2], [w, h, w], crystal, glow=True, name="cry_a", rotation=[0, 45, 0], pivot=[0, 25, 0]))
    cubes.append(C("crystal", [-w * 0.35, 25 - h * 0.62, -w * 0.35], [w * 0.7, h * 1.24, w * 0.7], crystal, glow=True, name="cry_b"))
    ring_of(cubes, "ring_h", 25, 6.2 + 0.3 * stars, 14, 0.8, 0.9, brass, teeth=16 if stars >= 2 else None, plane="xz", name="hring")
    ring_of(cubes, "ring_v", 25, 5.2, 12, 0.8, 0.9, brass, plane="xy", name="vring")
    ring_of(cubes, "ring_t", 25, 4.4, 10, 0.7, 0.8, brass_dark, plane="xz", name="tring")
    if stars >= 2:
        ring_of(cubes, "ring_t2", 25, 4.0, 10, 0.6, 0.7, brass_dark, plane="xz", name="t2ring")
    for k in range([0, 2, 4, 6][stars]):
        a = math.radians(k * 360 / max(1, [0, 2, 4, 6][stars]))
        x, z = math.cos(a) * 8.6, math.sin(a) * 8.6
        cubes.append(C("shards", [x - 0.5, 24.0 + (k % 2) * 1.6, z - 0.5], [1.0, 2.2, 1.0], crystal, glow=True, name="shard" if k == 0 else None,
                       share=None if k == 0 else "shard", rotation=[0, 45, 0], pivot=[x, 25, z]))
    if stars >= 3:
        for k in range(6):
            a = k * 60
            cubes.append(C("crown", [-0.45, 29.0, -0.45], [0.9, 3.2, 0.9], crystal, glow=True, name="spike" if k == 0 else None,
                           share=None if k == 0 else "spike", rotation=[0, a, 30], pivot=[0, 29.0, 0]))
    name = "hextech_staff" + ("_%d" % stars if stars else "")
    geo, img, glow = build(name, 64, bones, cubes, (2.4, 3.8, 0.5), bedrock_sides=True)
    speed = 1.0 + 0.25 * stars
    a = {"idle": {"loop": True, "animation_length": 8.0, "bones": {
        "ring_h": {"rotation": {"0.0": models.kf([0, 0, 0]), "8.0": models.kf([0, 360 * round(speed), 0])}},
        "ring_v": spin("z", 8.0, turns=max(1, round(speed)), reverse=True),
        "ring_t": {"rotation": {"0.0": models.kf([0, 0, 0]), "8.0": models.kf([0, -360, 0])}},
        "ring_t2": {"rotation": {"0.0": models.kf([0, 0, 0]), "8.0": models.kf([0, 720, 0])}},
        "shards": {"rotation": {"0.0": models.kf([0, 0, 0]), "8.0": models.kf([0, -720, 0])}},
        "crown": {"rotation": {"0.0": models.kf([0, 0, 0]), "8.0": models.kf([0, 360, 0])}},
        "crystal": {"rotation": {"0.0": models.kf([0, 0, 0]), "8.0": models.kf([0, 360, 0])},
                    "position": {"0.0": models.kf([0, 0, 0]), "2.0": models.kf([0, 0.5, 0], "easeInOutSine"), "4.0": models.kf([0, 0, 0], "easeInOutSine"),
                                 "6.0": models.kf([0, -0.5, 0], "easeInOutSine"), "8.0": models.kf([0, 0, 0], "easeInOutSine")}},
    }}}
    return geo, img, glow, anims(a)
