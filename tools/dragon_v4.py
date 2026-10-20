"""
Tech Dragon v4 (1.6): a four-legged, two-winged dragon built in the style of Saint's Dragons (long low body, long
S-curved neck, a long tapering tail, huge bat wings with separate finger bones) and painted after the concept art
(idea/tech_dragon.png): indigo scales, lavender belly scutes, rose-bronze armor with gold rims and glowing hextech
engraving, blue crystal crown, bronze 'wing eye' discs at the wrists, a hextech core in the chest.

Nothing is copied from Saint's Dragons (its art is All Rights Reserved); only the general proportions and rig layout
were studied.

Rig notes
* Bones ending in "c" (neck1c, headc, tail3c...) are procedural controllers: the Java model sets them to ABSOLUTE
  rotations every frame (look-at and tail drag), animations never touch them, so nothing can accumulate.
* "flight" carries the procedural pitch/bank in the air, also never animated.
* Wing membranes are split into panels (between two fingers, finger 3 and the forearm, the upper arm and the flank),
  each cut into fan slices (memb_l1a, memb_l1b...). The baker (anim_v4.Rig.fit_membranes) turns and z-scales the
  slices every frame so each panel closes and opens like a fan between its owner bone and the next bone.
* "mouth", "saddle" and the *_tip locators have no cubes; the server uses baked positions of several bones for the
  multipart hitbox (dragon_v4_anim.export_parts).

Native size: 208 px (13 blocks) from snout to tail tip, 292 px wingspan. The boss renders at 2.0 (26 blocks), the
summoned dragon at 0.85 (~11 blocks).
Coordinates: Bedrock model space, front is -Z, the dragon's left is +X, 16 px = 1 block.
"""
import math

import numpy as np
from PIL import Image

import check_geo
import rig_v4
from pixelart import rgb, ramp

DENSITY = 2.0
TEX_W = 2048

# --------------------------------------------------------------------------------------------- palettes
HIDE = [rgb("080A22"), rgb("10133A"), rgb("181D52"), rgb("222A6C"), rgb("2E3888"), rgb("3E4AA6"), rgb("5664C4")]
BELLY = [rgb("1E1840"), rgb("2C2460"), rgb("3D337E"), rgb("51449A"), rgb("6858B4"), rgb("8270CA")]
BRONZE = [rgb("2A140E"), rgb("4A281C"), rgb("6E3E2C"), rgb("94583E"), rgb("B87658"), rgb("D69C7C"), rgb("F0CBB0")]
GOLD = [rgb("4A2C0C"), rgb("7A5018"), rgb("AA7A2A"), rgb("D6A64A"), rgb("F2D27E"), rgb("FFF0C0")]
MEMB = [rgb("120A30"), rgb("1E1248"), rgb("2C1C64"), rgb("3C2A80"), rgb("50389C"), rgb("6A50B8"), rgb("8A70D2")]
BLUE = [rgb("061C5A"), rgb("0C3CA0"), rgb("1E6EE8"), rgb("4CA4FF"), rgb("9AD4FF"), rgb("E4F6FF")]
CLAW = [rgb("0C0A18"), rgb("1A1630"), rgb("2C2648"), rgb("443C66"), rgb("6A6090")]
TEETH = [rgb("6E6656"), rgb("A49C86"), rgb("CEC6AE"), rgb("ECE6D4"), rgb("FFFCF2")]
MOUTH = [rgb("1E0614"), rgb("3A0C22"), rgb("5E1834"), rgb("86284A"), rgb("A8406A")]
CLEAR = (0, 0, 0, 0)


def h01(*v):
    """Deterministic hash in [0, 1)."""
    x = 2166136261
    for a in v:
        x = ((x ^ (int(math.floor(a * 7.0)) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
        x ^= x >> 13
    return (x % 10007) / 10007.0


def glow(c, g=None):
    return (c, g if g is not None else c)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


# --------------------------------------------------------------------------------------------- model description

class Cube:
    def __init__(self, bone, origin, size, paint, name, rotation=None, pivot=None, faces=None, inflate=0.0):
        self.bone, self.origin, self.size, self.paint, self.name = bone, [float(v) for v in origin], [float(v) for v in size], paint, name
        self.rotation = [float(v) for v in rotation] if rotation else None
        self.pivot = [float(v) for v in pivot] if pivot else None
        self.faces = faces or ("north", "south", "east", "west", "up", "down")
        self.inflate = inflate
        self.share = None
        self.uv = {}
        self.mirror_of = None


class Ctx:
    """What a paint function sees for one texel."""
    __slots__ = ("face", "p", "lp", "n", "i", "j", "w", "h", "fu", "fv", "size", "cube")


def face_size(c, face):
    w, h, d = c.size
    return {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}[face]


FACE_N = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}


def local_point(c, face, fu, fv):
    ox, oy, oz = c.origin
    sw, sh, sd = c.size
    if face == "north":
        return (ox + fu * sw, oy + sh - fv * sh, oz)
    if face == "south":
        return (ox + sw - fu * sw, oy + sh - fv * sh, oz + sd)
    if face == "east":
        return (ox + sw, oy + sh - fv * sh, oz + fu * sd)
    if face == "west":
        return (ox, oy + sh - fv * sh, oz + sd - fu * sd)
    if face == "up":
        return (ox + fu * sw, oy + sh, oz + sd - fv * sd)
    return (ox + fu * sw, oy, oz + sd - fv * sd)


class Dragon:
    def __init__(self):
        self.bones = []
        self.cubes = []
        self.panels = []

    def bone(self, name, parent, pivot, rest=None):
        self.bones.append((name, parent, [round(float(v), 4) for v in pivot], [round(float(v), 4) for v in rest] if rest else None))
        return name

    def cube(self, bone, origin, size, paint, name, **kw):
        c = Cube(bone, [round(v, 3) for v in origin], [round(v, 3) for v in size], paint, name, **kw)
        self.cubes.append(c)
        return c

    def mirror(self, c, bone=None):
        bone = bone or mirror_name(c.bone)
        x, y, z = c.origin
        w, h, d = c.size
        m = Cube(bone, [round(-(x + w), 3), y, z], [w, h, d], c.paint, c.name + "_m",
                 rotation=[c.rotation[0], -c.rotation[1], -c.rotation[2]] if c.rotation else None,
                 pivot=[-c.pivot[0], c.pivot[1], c.pivot[2]] if c.pivot else None, faces=c.faces, inflate=c.inflate)
        m.share = c.name
        m.mirror_of = c
        self.cubes.append(m)
        return m

    def sym(self, bone, origin, size, paint, name, **kw):
        c = self.cube(bone, origin, size, paint, name, **kw)
        self.mirror(c)
        return c

    def seg(self, bone, a, b, w, d, paint, name, extend=(0.0, 0.0), roll=0.0, mirror=False):
        """Box from point a to point b (long axis = its local +z), cross-section w (local x) by d (local y)."""
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)
        v = b - a
        L = float(np.linalg.norm(v))
        u = v / L
        rxd = math.degrees(math.asin(max(-1.0, min(1.0, u[1]))))
        ryd = math.degrees(math.atan2(u[0], u[2]))
        origin = [a[0] - w / 2, a[1] - d / 2, a[2] - extend[0]]
        c = self.cube(bone, origin, [w, d, L + extend[0] + extend[1]], paint, name,
                      rotation=[round(rxd, 3), round(ryd, 3), round(roll, 3)], pivot=[round(x, 3) for x in a])
        if mirror:
            self.mirror(c)
        return c


def mirror_name(n):
    for a, b in (("_l", "_r"),):
        if n.endswith(a):
            return n[: -len(a)] + b
        if a + "_" in n or n.endswith(a + "i"):
            return n.replace(a, b, 1)
        k = n.find(a)
        if k >= 0 and (k + 2 == len(n) or n[k + 2].isdigit() or n[k + 2] == "i"):
            return n[:k] + b + n[k + 2:]
    return n


# --------------------------------------------------------------------------------------------- body geometry

# key points (rest pose, wings fully spread)
S = (9.0, 39.0, -28.0)        # wing shoulder
E = (36.0, 40.0, -24.0)       # wing elbow
W = (66.0, 41.0, -36.0)       # wing wrist
TIPS = ((146.0, 41.0, -26.0), (136.0, 41.0, 14.0), (106.0, 41.0, 44.0))
TE = (46.0, 40.0, 31.0)       # trailing edge point behind the elbow
B = (11.0, 39.0, 7.0)         # membrane root on the flank
TAIL_N = 8
TAIL_LEN = (13, 13, 12, 12, 11, 11, 10, 10)
TAIL_W = (16, 13.6, 11.6, 9.8, 8.2, 6.8, 5.6, 4.4)
TAIL_H = (15, 12.8, 11, 9.4, 8, 6.6, 5.4, 4.4)
TAIL_Y = (30, 30, 29.8, 29.6, 29.4, 29.2, 29, 28.8)
TAIL_Z0 = 14.0
NECK = [  # pivot y, pivot z, width, height, cube y0
    (30.0, -36.0, 15.0, 14.0, 24.0),
    (31.0, -48.0, 13.2, 13.6, 24.4),
    (32.0, -60.0, 11.8, 12.2, 26.2),
    (33.0, -72.0, 10.6, 11.0, 27.8),
]


def tail_z(n):
    return TAIL_Z0 + sum(TAIL_LEN[:n])


def finger_rest(k):
    d = np.subtract(TIPS[k], W)
    return math.degrees(math.atan2(-d[2], d[0])), float(math.hypot(d[0], d[2]))


def yrot(deg):
    return rig_v4.ry(math.radians(deg))


def build_dragon():
    D = Dragon()
    P = Paints()
    bone = D.bone
    bone("root", None, [0, 0, 0])
    bone("flight", "root", [0, 27, -10])
    bone("body", "flight", [0, 27, -10])
    bone("chest", "body", [0, 28, -8])
    bone("hips", "body", [0, 28, -4])
    bone("ribs", "chest", [0, 28, -26])
    bone("core", "chest", [0, 20.4, -43.6])
    bone("saddle", "chest", [0, 41.5, -22])
    parent = "chest"
    for k, (py, pz, w, h, y0) in enumerate(NECK):
        bone("neck%d" % (k + 1), parent, [0, py, pz])
        bone("neck%dc" % (k + 1), "neck%d" % (k + 1), [0, py, pz])
        parent = "neck%dc" % (k + 1)
    bone("head", parent, [0, 34, -84])
    bone("headc", "head", [0, 34, -84])
    bone("jaw", "headc", [0, 31, -92])
    bone("crest", "headc", [0, 42, -93])
    bone("mouth", "headc", [0, 30, -114])
    bone("lid_l", "headc", [6.3, 37.4, -102.7])
    bone("lid_r", "headc", [-6.3, 37.4, -102.7])
    for s, sg in (("l", 1), ("r", -1)):
        bone("arm_" + s, "chest", [sg * 11, 27, -28])
        bone("forearm_" + s, "arm_" + s, [sg * 12.5, 15, -24])
        bone("hand_" + s, "forearm_" + s, [sg * 12.5, 4.5, -28])
        bone("claws_" + s, "hand_" + s, [sg * 12.5, 1.5, -35])
        bone("thigh_" + s, "hips", [sg * 10.5, 27, 8])
        bone("shin_" + s, "thigh_" + s, [sg * 12, 14, 2])
        bone("meta_" + s, "shin_" + s, [sg * 12, 6.5, 13])
        bone("foot_" + s, "meta_" + s, [sg * 12, 1.8, 9])
        bone("gear_" + s, "chest", [sg * 12.8, 40.5, -27])
        bone("wing_" + s, "chest", [sg * S[0], S[1], S[2]])
        bone("wing_%s2" % s, "wing_" + s, [sg * E[0], E[1], E[2]])
        bone("wing_%s3" % s, "wing_%s2" % s, [sg * W[0], W[1], W[2]])
        for k in range(3):
            ang, _ = finger_rest(k)
            bone("finger_%s%d" % (s, k + 1), "wing_%s3" % s, [sg * W[0], W[1], W[2]], [0, sg * ang, 0])
    parent = "hips"
    for n in range(TAIL_N):
        z = tail_z(n)
        bone("tail%d" % (n + 1), parent, [0, TAIL_Y[n], z])
        bone("tail%dc" % (n + 1), "tail%d" % (n + 1), [0, TAIL_Y[n], z])
        parent = "tail%dc" % (n + 1)
    bone("tail_tip", parent, [0, TAIL_Y[-1], tail_z(TAIL_N) + 6])

    torso(D, P)
    neck_and_head(D, P)
    legs(D, P)
    tail(D, P)
    wing(D, P)
    D.paints = P
    return D


# --------------------------------------------------------------------------------------------- parts

def torso(D, P):
    c = D.cube
    # chest / ribcage (front torso), rounded with overlapping slabs
    c("ribs", [-12, 16, -38], [24, 24, 25], P.hide, "ribcage")
    c("ribs", [-13.4, 19, -36.5], [26.8, 17.5, 22], P.hide, "rib_bulge")
    c("ribs", [-10.5, 18, -41.2], [21, 19.5, 4], P.hide, "chest_front")
    c("ribs", [-9, 14.6, -37], [18, 2.4, 21], P.belly, "sternum", faces=("down", "east", "west", "north", "south"))
    c("chest", [-10, 38.2, -37.5], [20, 3, 24], P.hide, "withers")
    c("chest", [-10.5, 18.5, -14], [21, 20, 15], P.hide, "waist")
    c("chest", [-8, 16.6, -14], [16, 2.2, 15], P.belly, "waist_belly", faces=("down", "east", "west", "north", "south"))
    # chest armor: pectoral plates and the hextech core frame
    D.sym("chest", [1.2, 18.5, -42.6], [8.8, 15, 2.6], P.plate("pec"), "pec_plate", rotation=[-8, -14, 0], pivot=[1.2, 26, -41])
    c("chest", [-4.6, 15.6, -43.6], [9.2, 9.6, 2.2], P.plate("core_frame", rim_only=True), "core_frame")
    c("core", [-3.0, 17.4, -44.4], [6.0, 6.0, 1.6], P.core, "core_gem", rotation=[0, 0, 45], pivot=[0, 20.4, -43.6])
    # back armor: overlapping plates with square gems along the spine, spine crystals between them
    for k, (z, w) in enumerate(((-37, 21), (-27.5, 22), (-18, 21), (-9, 19))):
        c("chest", [-w / 2, 39.4, z], [w, 3.2, 10.5], P.plate("back%d" % k, gem=True), "back_plate%d" % k, rotation=[7, 0, 0], pivot=[0, 39.4, z])
        D.seg("chest", [0, 41.5, z + 6.5], [0, 47.5 - k * 0.6, z + 12], 2.6, 2.6, P.crystal, "spine_c%d" % k)
    # shoulder pauldrons over the leg roots
    D.sym("chest", [9.5, 24, -36], [6, 12, 12], P.plate("pauldron"), "pauldron", rotation=[0, 0, -14], pivot=[12, 33, -30])
    D.sym("chest", [11.5, 33.5, -34.5], [3.5, 3.5, 9], P.crystal, "pauldron_crystal", rotation=[-18, 0, -38], pivot=[13, 35, -30])
    # wing root gears (spin in flight)
    gear(D, P, "gear_l", (12.8, 40.5, -27), 4.6, 1.4)
    # hips
    h = "hips"
    c(h, [-11, 19, -2], [22, 19, 18], P.hide, "pelvis")
    c(h, [-12.4, 21, 0], [24.8, 15, 14], P.hide, "pelvis_bulge")
    c(h, [-9.6, 21, 14.5], [19.2, 15.5, 4], P.hide, "rump")
    c(h, [-8, 17.4, -1], [16, 2, 16], P.belly, "hip_belly", faces=("down", "east", "west", "north", "south"))
    for k, (z, w) in enumerate(((0, 18), (8.5, 17))):
        c(h, [-w / 2, 37.4, z], [w, 3, 9.5], P.plate("hip%d" % k, gem=(k == 0)), "hip_plate%d" % k, rotation=[6, 0, 0], pivot=[0, 37.4, z])
        D.seg(h, [0, 39.5, z + 5.5], [0, 45 - k, z + 10.5], 2.4, 2.4, P.crystal, "hip_spine%d" % k)
    D.sym(h, [11.6, 22.5, 3], [2.4, 12, 14], P.plate("hip_side"), "hip_guard", rotation=[0, 0, -6], pivot=[12, 30, 10])


def gear(D, P, bone, center, r, t):
    """Bronze cog facing sideways (normal x): two square slabs at 45 degrees plus 8 teeth, painted round."""
    cx, cy, cz = center
    for side in (1, -1):
        b = bone if side == 1 else mirror_name(bone)
        x0 = cx - t / 2 if side == 1 else -cx - t / 2
        for k, ang in enumerate((0, 45)):
            g = D.cube(b, [x0, cy - r, cz - r], [t, 2 * r, 2 * r], P.gear(r), "gear%s%d" % ("" if side == 1 else "_m", k),
                       rotation=[ang, 0, 0], pivot=[x0 + t / 2, cy, cz], faces=("east", "west"))


def neck_and_head(D, P):
    c = D.cube
    for k, (py, pz, w, h, y0) in enumerate(NECK):
        b = "neck%dc" % (k + 1)
        z0 = pz - 13
        c(b, [-w / 2, y0, z0], [w, h, 14.5], P.hide, "neck%d" % k)
        c(b, [-w / 2 + 1.4, y0 - 1.2, z0 + 0.8], [w - 2.8, 1.6, 13], P.belly, "throat%d" % k, faces=("down", "east", "west", "north", "south"))
        c(b, [-w / 2 - 0.6, y0 + h - 1.2, z0 + 1.2], [w + 1.2, 2.8, 11.5], P.plate("neckp%d" % k, gem=(k % 2 == 1)), "neck_plate%d" % k,
          rotation=[5, 0, 0], pivot=[0, y0 + h, z0 + 12])
        D.seg(b, [0, y0 + h + 1.2, z0 + 4.5], [0, y0 + h + 6.2 - k * 0.6, z0 + 10.5], 2.2 - k * 0.15, 2.2 - k * 0.15, P.crystal, "neck_spine%d" % k)
        # side frills of plate on the upper neck segments
        if k >= 2:
            D.sym(b, [w / 2 - 0.4, y0 + 3, z0 + 3], [1.2, h - 5, 8], P.plate("frill%d" % k, seam=False), "neck_frill%d" % k,
                  rotation=[0, -12, 0], pivot=[w / 2, y0 + h / 2, z0 + 7])
    # ---------------- head (on headc): wedge-shaped, the snout tapers in three steps toward the nose
    hb = "headc"
    c(hb, [-7.2, 29.5, -99.5], [14.4, 11, 16], P.hide, "cranium")
    c(hb, [-8.2, 30, -97.5], [16.4, 7, 11.5], P.hide, "cheeks")
    c(hb, [-6.4, 39.5, -97], [12.8, 2.6, 13], P.hide, "skull_top")
    snout = ((-6.0, 8.8, -107.0, 8.0), (-5.2, 7.6, -113.5, 7.0), (-4.3, 6.3, -119.0, 6.0))
    for k, (x0, hh, z0, d) in enumerate(snout):
        c(hb, [x0, 30, z0], [-2 * x0, hh, d], P.hide, "snout%d" % k)
        # palate: roof of the mouth, seen when the jaw opens
        c(hb, [x0 + 0.6, 29.7, z0 + 0.2], [-2 * x0 - 1.2, 0.5, d - 0.2], P.mouth, "palate%d" % k, faces=("down",))
        # upper tooth rows along both edges, with gaps
        D.sym(hb, [-x0 - 1.0, 28.3, z0 + 0.3], [0.8, 1.8, d - 0.4], P.teeth, "teeth_up%d" % k)
    c(hb, [-3.4, 28.3, -119.2], [6.8, 1.8, 0.8], P.teeth, "teeth_front")
    D.sym(hb, [3.6, 26.4, -111.8], [1.2, 3.8, 1.2], P.fang, "fang", rotation=[-6, 0, 0], pivot=[4.2, 29.5, -111.2])
    # bronze armor: helm with gem, sloping snout plate (gives the wedge profile), nasal blade
    c(hb, [-6.6, 41.4, -100], [13.2, 2.2, 15], P.plate("helm", gem=True), "helm", rotation=[-6, 0, 0], pivot=[0, 42, -100])
    D.seg(hb, [0, 41.0, -99.0], [0, 36.0, -119.4], 8.6, 2.0, P.plate("snout_plate"), "snout_plate", extend=(0, 0.4))
    D.seg(hb, [0, 37.6, -116.0], [0, 41.6, -110.0], 1.6, 3.4, P.plate("nasal", seam=False), "nasal_blade")
    # brows: heavy angled ridges over the eyes, swept back into the horns
    D.seg(hb, [6.2, 38.6, -107.0], [6.8, 41.4, -94.0], 3.0, 3.0, P.plate("brow", seam=False), "brow", extend=(0.5, 0.5), mirror=True)
    D.sym(hb, [6.0, 34.3, -105.8], [0.95, 3.1, 5.8], P.eye, "eye", faces=("east", "north", "up", "down", "south"))
    D.sym(hb, [5.98, 33.4, -106.8], [0.12, 5.0, 7.8], P.socket, "eye_socket", faces=("east",))
    D.sym(hb, [6.0, 35.5, -100.1], [0.5, 0.9, 5.5], P.eye_trail, "eye_trail", faces=("east", "up", "south"))
    D.cube("lid_l", [5.95, 37.5, -106.1], [1.1, 3.3, 6.2], P.lid, "lid")
    D.mirror(D.cubes[-1], "lid_r")
    # cheek guards: bronze fins sweeping back from the jaw hinge
    D.seg(hb, [7.6, 32.0, -99.0], [9.6, 34.5, -86.0], 1.4, 6.0, P.plate("cheek"), "cheek_guard", mirror=True)
    D.sym(hb, [2.0, 35.3, -119.4], [1.4, 1.0, 1.0], P.nostril, "nostril", faces=("north", "up"))
    # horns: bronze, sweeping back in four tapering segments; smaller jaw horns below
    pts = [(5.0, 40.5, -92.0), (7.8, 43.8, -81.0), (9.4, 45.4, -70.0), (10.0, 48.6, -61.0), (9.8, 52.6, -55.0)]
    widths = (3.6, 3.0, 2.4, 1.7)
    for k in range(4):
        D.seg(hb, pts[k], pts[k + 1], widths[k], widths[k], P.horn(k), "horn%d" % k, extend=(0.8, 0.4), mirror=True)
    pts = [(7.4, 33.0, -90.0), (10.6, 31.8, -81.0), (12.4, 31.4, -74.0)]
    for k in range(2):
        D.seg(hb, pts[k], pts[k + 1], 2.4 - k * 0.7, 2.4 - k * 0.7, P.horn(k + 1), "jaw_horn%d" % k, extend=(0.6, 0.3), mirror=True)
    # crystal crown (on "crest" so it can flare)
    D.seg("crest", [0, 42.6, -95], [0, 55, -73], 2.8, 2.8, P.crystal, "crest_main", extend=(1, 0))
    D.seg("crest", [2.6, 42.4, -93], [5.2, 51.5, -76], 2.2, 2.2, P.crystal, "crest_side", extend=(1, 0), mirror=True)
    D.seg("crest", [4.4, 42, -90], [8.8, 47.6, -77], 1.8, 1.8, P.crystal, "crest_back", extend=(0.8, 0), mirror=True)
    # ---------------- jaw: tapers like the snout
    j = "jaw"
    c(j, [-6.6, 25.4, -97], [13.2, 5.6, 10.5], P.hide, "jaw_rear")
    jaw = ((-5.6, 4.2, -107.0, 11.0), (-4.8, 3.8, -113.5, 7.0), (-4.0, 3.4, -119.0, 6.0))
    for k, (x0, hh, z0, d) in enumerate(jaw):
        c(j, [x0, 30 - hh, z0], [-2 * x0, hh, d], P.hide, "jaw%d" % k)
        c(j, [x0 + 0.6, 29.6, z0 + 0.2], [-2 * x0 - 1.2, 0.6, d - 0.2], P.mouth, "mouth_floor%d" % k, faces=("up",))
        D.sym(j, [-x0 - 1.0, 30, z0 + 0.3], [0.8, 1.6, d - 0.4], P.teeth, "teeth_low%d" % k)
    c(j, [-3.0, 30, -118.8], [6.0, 1.6, 0.8], P.teeth, "teeth_low_front")
    c(j, [-2.6, 29.9, -114], [5.2, 0.9, 18], P.tongue, "tongue", faces=("up", "north", "east", "west"))
    D.seg(j, [0, 25.6, -97.0], [0, 26.4, -118.0], 7.6, 1.4, P.plate("chin", seam=False), "jaw_plate")
    D.seg(j, [0, 26.0, -113], [0, 23.0, -108], 2.2, 2.2, P.horn(2), "chin_spike")
    D.sym(j, [3.0, 30, -110.5], [1.1, 3.0, 1.1], P.fang, "fang_low")


def legs(D, P):
    # ---------------- front legs (arms)
    s = "_l"
    D.seg("arm" + s, (11.0, 28.0, -28.5), (12.5, 15.0, -24.5), 8.5, 9.5, P.hide, "upper_arm", extend=(2, 1.5), mirror=True)
    D.sym("arm" + s, [7.6, 21, -34], [8.6, 11, 11], P.hide, "deltoid")
    D.seg("arm" + s, (12.5, 18.0, -29.6), (12.8, 13.5, -27.6), 9.2, 3.0, P.plate("elbow"), "elbow_guard", mirror=True)
    D.seg("forearm" + s, (12.5, 15.0, -24.0), (12.5, 4.5, -28.0), 6.4, 7.0, P.hide, "forearm", extend=(1.5, 1), mirror=True)
    D.seg("forearm" + s, (12.5, 13.5, -27.6), (12.5, 6.0, -30.4), 6.9, 2.6, P.plate("greave_f", gem=True), "greave_front", mirror=True)
    D.sym("forearm" + s, [14.8, 7, -27.4], [1.6, 2.6, 2.6], P.gem, "wrist_gem")
    D.sym("hand" + s, [9, 0, -35], [7, 4.6, 9.5], P.hide, "palm")
    D.sym("hand" + s, [9.4, 3.6, -34.4], [6.2, 1.6, 6], P.plate("knuckle", seam=False), "knuckle_plate")
    D.sym("hand" + s, [8.2, 0.4, -29.5], [1.8, 2.4, 3.5], P.claw, "dewclaw", rotation=[0, 0, 0])
    for k, x in enumerate((9.2, 11.6, 14.0)):
        D.sym("claws" + s, [x, 0, -38], [2.0, 2.8, 3.6], P.hide, "finger%d" % k)
        D.seg("claws" + s, (x + 1.0, 1.6, -37.6), (x + 1.0, 0.2, -41.2), 1.6, 1.8, P.claw, "talon%d" % k, extend=(0, 0.3), mirror=True)
    # ---------------- hind legs
    D.sym("thigh" + s, [6.4, 16.5, -1.5], [10, 14, 16], P.hide, "haunch", rotation=[-10, 0, 0], pivot=[10.5, 27, 8])
    D.seg("thigh" + s, (10.5, 27.0, 8.0), (12.0, 14.0, 2.0), 8.6, 10.5, P.hide, "thigh", extend=(2, 1.5), mirror=True)
    D.seg("thigh" + s, (13.6, 25.0, 3.0), (14.6, 17.0, 1.6), 3.0, 9.0, P.plate("thigh_plate", gem=True), "thigh_plate", mirror=True)
    D.seg("shin" + s, (12.0, 14.0, 2.0), (12.0, 6.5, 13.0), 5.8, 6.4, P.hide, "shin", extend=(1.5, 1.2), mirror=True)
    D.seg("shin" + s, (12.0, 13.4, 0.6), (12.0, 8.6, 7.8), 6.4, 2.2, P.plate("knee", seam=False), "knee_guard", mirror=True)
    D.sym("shin" + s, [14.6, 9.6, 6.6], [1.6, 2.6, 2.6], P.gem, "knee_gem")
    D.seg("meta" + s, (12.0, 6.5, 13.0), (12.0, 1.8, 9.0), 4.8, 4.8, P.hide, "meta", extend=(1.2, 1.0), mirror=True)
    D.seg("meta" + s, (12.0, 7.4, 15.0), (12.0, 10.8, 19.4), 1.8, 1.8, P.claw, "heel_spur", mirror=True)
    D.sym("foot" + s, [9, 0, 2], [6.6, 3.4, 9.4], P.hide, "foot")
    D.sym("foot" + s, [9.3, 2.8, 3], [6, 1.4, 6.6], P.plate("toe_plate", seam=False), "toe_plate")
    for k, x in enumerate((9.1, 11.3, 13.5)):
        D.sym("foot" + s, [x, 0, -1], [1.9, 2.6, 3.4], P.hide, "toe%d" % k)
        D.seg("foot" + s, (x + 0.95, 1.5, -0.6), (x + 0.95, 0.2, -4.0), 1.5, 1.7, P.claw, "toe_talon%d" % k, extend=(0, 0.3), mirror=True)


def tail(D, P):
    for n in range(TAIL_N):
        b = "tail%dc" % (n + 1)
        z = tail_z(n)
        w, h, y = TAIL_W[n], TAIL_H[n], TAIL_Y[n]
        L = TAIL_LEN[n]
        D.cube(b, [-w / 2, y - h / 2, z - 1], [w, h, L + 2], P.hide, "tail%d" % n)
        D.cube(b, [-w / 2 + 1, y - h / 2 - 0.8, z], [w - 2, 1.2, L], P.belly, "tail_belly%d" % n, faces=("down", "east", "west", "north", "south"))
        D.cube(b, [-w / 2 - 0.5, y + h / 2 - 0.9, z + 0.6], [w + 1, 2.4, L - 1], P.plate("tailp%d" % n, gem=(n % 2 == 0)), "tail_plate%d" % n,
               rotation=[4, 0, 0], pivot=[0, y + h / 2, z + L])
        if n < TAIL_N - 1:
            D.seg(b, [0, y + h / 2 + 1, z + L * 0.45], [0, y + h / 2 + 5.4 - n * 0.45, z + L * 0.95], max(1.0, 2.2 - n * 0.15), max(1.0, 2.2 - n * 0.15),
                  P.crystal, "tail_spine%d" % n)
        if 2 <= n <= 6:
            D.seg(b, [w / 2 - 0.4, y - 0.6, z + 2], [w / 2 + 4.2 - n * 0.3, y - 0.2, z + L - 1], 1.4, 1.4, P.crystal, "tail_blade%d" % n, mirror=True)
    # tip: bronze disc and blade (concept art)
    zt = tail_z(TAIL_N)
    yt = TAIL_Y[-1]
    b = "tail8c"
    D.cube(b, [-2.6, yt - 2.6, zt - 1], [5.2, 5.2, 4.4], P.plate("tail_hub", seam=False), "tail_hub")
    D.cube(b, [-0.8, yt - 7, zt - 3.5], [1.6, 14, 14], P.disc(7.0, zt + 3.5, yt), "tail_disc", faces=("east", "west"))
    D.seg(b, [0, yt, zt + 9], [0, yt, zt + 21], 1.2, 3.6, P.crystal, "tail_blade_tip")
    D.seg(b, [0, yt + 2.5, zt + 6], [0, yt + 7, zt + 12], 1.2, 2.2, P.crystal, "tail_fin_up")
    D.seg(b, [0, yt - 2.5, zt + 6], [0, yt - 7, zt + 12], 1.2, 2.2, P.crystal, "tail_fin_down")


def wing(D, P):
    """Left wing (+x) in rest space; the right wing is mirrored (bones and cubes)."""
    start = len(D.cubes)
    D.seg("wing_l", S, E, 4.4, 4.6, P.wingbone, "humerus", extend=(3, 1.5))
    D.seg("wing_l", (S[0] + 2, S[1] + 2.2, S[2] - 0.4), (E[0] - 3, E[1] + 2.4, E[2] - 0.2), 5.0, 1.6, P.plate("hum_plate"), "humerus_plate")
    D.cube("wing_l2", [E[0] - 3, E[1] - 3, E[2] - 3.2], [6, 6, 6.4], P.plate("elbow_w", seam=False), "elbow_knob")
    D.seg("wing_l2", E, W, 3.6, 3.8, P.wingbone, "forearm", extend=(1, 1.5))
    D.seg("wing_l2", (E[0] + 6, E[1] + 1.9, E[2] - 2.0), (W[0] - 5, W[1] + 1.9, W[2] + 1.8), 4.2, 1.4, P.plate("fore_plate", gem=True), "forearm_plate")
    # wrist: round bronze 'wing eye' disc lying in the wing plane
    D.cube("wing_l3", [W[0] - 6, W[1] - 1.5, W[2] - 6], [12, 3, 12], P.disc_flat(6.0, W[0], W[2]), "wrist_disc", faces=("up", "down"))
    D.cube("wing_l3", [W[0] - 3.5, W[1] - 1.6, W[2] - 3.5], [7, 3.2, 7], P.plate("wrist_hub", seam=False), "wrist_hub", faces=("north", "south", "east", "west"))
    D.seg("wing_l3", (W[0] - 1, W[1] - 0.4, W[2] - 2), (W[0] + 1.5, W[1] - 1.5, W[2] - 9.5), 2.2, 2.2, P.claw, "thumb")
    for k in range(3):
        ang, L = finger_rest(k)
        b = "finger_l%d" % (k + 1)
        # cubes in the finger's pre-rotation frame: the finger points along +x from the wrist
        D.cube(b, [W[0] + 2, W[1] - 1.1, W[2] - 1.1], [L * 0.42, 2.2, 2.2], P.wingbone, "finger%d_a" % k)
        D.cube(b, [W[0] + L * 0.42, W[1] - 0.8, W[2] - 0.8], [L * 0.58 - 1.5, 1.6, 1.6], P.wingbone, "finger%d_b" % k)
        D.cube(b, [W[0] + L - 2.2, W[1] - 1.3, W[2] - 1.3], [3.4, 2.6, 2.6], P.claw, "finger%d_claw" % k)
        D.cube(b, [W[0] + L * 0.42 - 1, W[1] - 1.3, W[2] - 1.3], [2.2, 2.6, 2.6], P.gem, "finger%d_gem" % k)
    # membranes
    tips = [np.array(t) for t in TIPS]
    Wv, Ev, Sv, Tv, Bv = np.array(W), np.array(E), np.array(S), np.array(TE), np.array(B)
    panels = []
    for k in range(3):
        owner = "finger_l%d" % (k + 1)
        ang, _ = finger_rest(k)
        if k < 2:
            far = tips[k + 1]
            poly = [Wv, tips[k]] + scallop(tips[k], tips[k + 1], Wv, 0.26 - 0.03 * k) + [tips[k + 1]]
            far_bone = "finger_l%d" % (k + 2)
        else:
            far = Ev
            poly = [Wv, tips[2]] + scallop(tips[2], Tv, Wv * 0.3 + Ev * 0.7, 0.2) + [Tv, Ev]
            far_bone = "wing_l2"
        panels.append(dict(name="memb_l%d" % (k + 1), owner=owner, pivot=Wv, rest_y=ang, poly=poly, far=far, far_bone=far_bone,
                           veins=[(Wv, (tips[k] * 0.55 + (far * 0.45)))], dy=-0.05 * k))
    a0 = math.degrees(math.atan2(-(Ev[2] - Sv[2]), Ev[0] - Sv[0]))
    poly = [Sv, Ev, Tv] + scallop(Tv, Bv, (Sv + Ev) / 2, 0.22) + [Bv]
    panels.append(dict(name="memb_l0", owner="wing_l", pivot=Sv, rest_y=a0, poly=poly, far=Bv, far_bone="chest",
                       veins=[(Sv * 0.5 + Ev * 0.5, Tv * 0.6 + Bv * 0.4)], dy=-0.2))
    for pnl in panels:
        add_panel(D, P, pnl)
    D.panels = panels
    # bronze trim along the trailing edge root
    for c in list(D.cubes[start:]):
        D.mirror(c)


def scallop(a, b, toward, depth=0.25, steps=7):
    a, b, toward = np.asarray(a, float), np.asarray(b, float), np.asarray(toward, float)
    mid = (a + b) / 2
    ctrl = mid + (toward - mid) * depth
    out = []
    for s in range(1, steps):
        t = s / steps
        out.append((1 - t) ** 2 * a + 2 * (1 - t) * t * ctrl + t * t * b)
    return out


SLICES = {"memb_l1": 2, "memb_l2": 2, "memb_l3": 3, "memb_l0": 4}
SLICE_PAD = 0.012  # radians of overlap between neighbouring slices


def add_panel(D, P, pnl):
    """A membrane panel cut into fan slices around its pivot. Each slice is its own bone (child of the owner) whose
    lower edge lies along its local +x; the baker rotates and z-scales the slices so the fan closes/opens with the
    far bone like a real folding membrane. Polygon coordinates are in the panel frame (anchor along +x)."""
    piv = pnl["pivot"]
    inv = yrot(-pnl["rest_y"])
    pts2 = [(float(q[0]), float(q[2])) for q in (inv @ (np.asarray(p, float) - piv) for p in pnl["poly"])]
    veins2 = []
    for a, b in pnl["veins"]:
        la, lb = inv @ (np.asarray(a, float) - piv), inv @ (np.asarray(b, float) - piv)
        veins2.append(((la[0], la[2]), (lb[0], lb[2])))
    far = inv @ (np.asarray(pnl["far"], float) - piv)
    pnl["far_local"] = (float(far[0]), float(far[2]))
    pnl["far_angle"] = math.atan2(far[2], far[0])
    pnl["local_poly"] = pts2
    angs = [math.atan2(z, x) for x, z in pts2 if math.hypot(x, z) > 0.5]
    lo, hi = min(0.0, min(angs)), max(pnl["far_angle"], max(angs))
    n = SLICES[pnl["name"]]
    paint = P.membrane(pts2, veins2)
    # interior sample grid (panel frame) to size each slice's slab
    xs = [q[0] for q in pts2]
    zs = [q[1] for q in pts2]
    grid = [(float(x), float(z)) for x in np.arange(min(xs), max(xs) + 0.5, 0.5) for z in np.arange(min(zs), max(zs) + 0.5, 0.5)
            if in_poly(x, z, pts2)] + pts2
    pnl["slices"] = []
    owner_rest = pnl["rest_y"] if pnl["owner"] == "wing_l" else 0.0
    for j in range(n):
        a0 = lo + (hi - lo) * j / n
        a1 = lo + (hi - lo) * (j + 1) / n
        name = "%s%s" % (pnl["name"], "abcd"[j])
        sec = [(x, z) for x, z in grid if a0 - SLICE_PAD - 0.02 <= math.atan2(z, x) <= a1 + SLICE_PAD + 0.02 or math.hypot(x, z) < 1.0]
        loc = [(x * math.cos(a0) + z * math.sin(a0), -x * math.sin(a0) + z * math.cos(a0)) for x, z in sec]
        lx = [q[0] for q in loc]
        lz = [q[1] for q in loc]
        rest_deg = owner_rest - math.degrees(a0)
        for side, sg in (("l", 1), ("r", -1)):
            D.bone(name.replace("_l", "_" + side, 1), pnl["owner"].replace("_l", "_" + side, 1), [sg * piv[0], piv[1], piv[2]], [0, sg * rest_deg, 0])
        y = piv[1] + pnl["dy"] + 0.09 * j
        origin = [piv[0] + min(lx) - 0.6, y - 0.15, piv[2] + min(lz) - 0.6]
        size = [max(lx) - min(lx) + 1.2, 0.3, max(lz) - min(lz) + 1.2]
        D.cube(name, origin, size, slice_paint(paint, piv, a0, a0 - SLICE_PAD, a1 + SLICE_PAD), name, faces=("up", "down"))
        pnl["slices"].append(dict(name=name, a0=a0, w=a1 - a0))


def slice_paint(paint, piv, rot, amin, amax):
    """Paint a slice from the panel's painter: slice-local point -> panel frame, clipped to the slice's sector."""
    c, s_ = math.cos(rot), math.sin(rot)

    def fn(x):
        u = x.lp[0] - piv[0]
        v = x.lp[2] - piv[2]
        pu, pv = u * c - v * s_, u * s_ + v * c
        if math.hypot(pu, pv) > 1.0 and not (amin <= math.atan2(pv, pu) <= amax):
            return CLEAR
        return paint(x, pu, pv)
    return fn


# --------------------------------------------------------------------------------------------- painting

LIGHT = {"up": 1.0, "north": 0.9, "east": 0.84, "west": 0.84, "south": 0.78, "down": 0.55}


def body_axis(p):
    """Rough centre line (y) and half-height of the body at rest-space z, for counter-shading."""
    z = p[2]
    if z < -84:
        return 34.0, 6.5
    if z < -36:
        k = (z + 84) / 48.0
        return 33.0 - 3 * k, 5.5 + 2.2 * k
    if z < 16:
        return 28.0, 11.5
    k = min(1.0, (z - 16) / 92.0)
    return 30.0 - 1.2 * k, 7.5 - 5.3 * k


class Paints:
    def __init__(self):
        self.cache = {}

    # ---- hide: overlapping scales that point backward, counter-shaded
    def hide(self, x):
        p, n, face = x.p, x.n, x.face
        cy, rh = body_axis(p)
        lp = x.lp
        rotated = x.cube.rotation is not None and abs(x.cube.rotation[0]) + abs(x.cube.rotation[1]) > 20
        if rotated:  # limbs: scale rows along the limb
            a = lp[2]
            b = lp[0] if face in ("up", "down", "north", "south") else lp[1]
        elif face in ("east", "west"):
            a, b = p[2], p[1]
        elif face in ("up", "down"):
            a, b = p[2], p[0]
        else:
            a, b = p[0], p[1]
        s = 3.0
        row = math.floor(b / s)
        aa = a / s + (0.5 if row % 2 else 0.0)
        cell = math.floor(aa)
        fa = aa - cell
        fb = b / s - row
        # vertical position on the body: -1 belly .. +1 back
        hv = max(-1.4, min(1.4, (p[1] - cy) / max(3.0, rh)))
        base = 0.4 + 0.1 * hv
        if face == "down" or n[1] < -0.6:
            base -= 0.12
        if n[1] > 0.6:
            base += 0.04
        # scale: lit dome toward the front, dark crescent at the free (rear) edge, thin outline
        d = (fa - 0.32) ** 2 * 1.4 + (fb - 0.5) ** 2 * 2.6
        t = base + 0.2 * max(0.0, 1 - d * 3.2)
        rim = 0.8 + 0.16 * math.cos((fb - 0.5) * 3.2)
        if fa > rim:
            t -= 0.2
        elif fa > rim - 0.12:
            t -= 0.08
        elif fa < 0.12:
            t -= 0.04
        if fb < 0.06 or fb > 0.94:
            t -= 0.07
        t += (h01(cell, row, 3.1) - 0.5) * 0.08
        t = t * LIGHT[face] / 0.9
        return ramp(HIDE, t)

    def belly(self, x):
        p, face = x.p, x.face
        a = p[2] if x.cube.rotation is None else x.lp[2]
        band = (a / 2.6) % 1.0
        t = 0.52 - (0.22 if band < 0.16 else 0) + (0.07 if 0.3 < band < 0.6 else 0)
        if face == "down":
            t -= 0.06
        t += (h01(math.floor(a / 2.6), 7) - 0.5) * 0.05
        return ramp(BELLY, t * LIGHT[face] / 0.9)

    def plate(self, key, gem=False, seam=True, rim_only=False):
        seed = h01(sum(ord(ch) for ch in key), 11)

        def fn(x):
            i, j, w, h, face = x.i, x.j, x.w, x.h, x.face
            b = min(i, j, w - 1 - i, h - 1 - j)
            lit = LIGHT[face]
            down = face == "down"
            # sheen: vertical gradient plus a soft diagonal highlight band
            t = 0.46 + 0.14 * (1 - j / max(1, h - 1)) - (0.22 if down else 0)
            diag = ((i + j * 0.7) / max(4.0, (w + h) * 0.5)) % 1.0
            if 0.25 < diag < 0.36:
                t += 0.07
            if b == 0:
                return GOLD[4] if (j < h * 0.35 and not down) else (GOLD[2] if not down else GOLD[1])
            if b == 1 and min(w, h) >= 6:
                return GOLD[3] if j < h / 2 else GOLD[1]
            if b == 2 and min(w, h) >= 9:
                return ramp(BRONZE, (t - 0.28) * lit)
            if rim_only:
                return ramp(BRONZE, 0.22 * lit)
            cx, cy = (w - 1) / 2, (h - 1) / 2
            if gem and min(w, h) >= 9 and not down:
                dd = abs(i - cx) / max(2.0, w * 0.5) + abs(j - cy) / max(2.0, h * 0.5)
                if dd < 0.3:
                    k = 1 - dd / 0.3
                    hi = 0.22 if (i < cx and j < cy) else 0.0
                    return glow(ramp(BLUE, 0.4 + 0.5 * k + hi))
                if dd < 0.39:
                    return GOLD[4] if j < cy else GOLD[2]
                if dd < 0.45:
                    return ramp(BRONZE, 0.16 * lit)
            if seam and not down and min(w, h) >= 12:
                # hextech filigree: an engraved inset frame with glowing runs and corner nodes
                inset = 4 if min(w, h) < 20 else 5
                on_frame = b == inset
                corner = (min(i, w - 1 - i) <= inset + 1) and (min(j, h - 1 - j) <= inset + 1)
                if on_frame:
                    run = ((i if w >= h else j) // 3) % 4 != 0
                    if corner or not run:
                        return GOLD[2]
                    return glow(BLUE[3], BLUE[2])
                if b == inset - 1 or b == inset + 1:
                    return ramp(BRONZE, (t - 0.16) * lit)
                if corner and b == inset + 2:
                    return GOLD[3]
            # rivets along the rim
            if b == 3 and min(w, h) >= 12 and ((i if j <= 3 or j >= h - 4 else j) % 6 == 2):
                return BRONZE[6]
            t += (h01(x.p[0] * 2, x.p[1] * 2, x.p[2] * 2) - 0.5) * 0.05 + (seed - 0.5) * 0.06
            return ramp(BRONZE, t * lit / 0.9)
        return fn

    def crystal(self, x):
        i, j, w, h = x.i, x.j, x.w, x.h
        # facets: two tones split down the middle, darker base, bright tip and one lit edge
        k = (x.lp[2] - x.cube.origin[2]) / max(1.0, x.cube.size[2])
        half = 0.1 if i < w / 2 else -0.06
        t = 0.22 + 0.42 * k + half
        if i == 0 and x.face != "down":
            t += 0.22
        if x.face == "up" or x.face == "south":
            t += 0.12
        if (i * 5 + j * 3) % 17 == 0:
            t += 0.3
        if x.face == "down":
            t -= 0.12
        return glow(ramp(BLUE, t), ramp(BLUE, t * 0.85))

    def core(self, x):
        cx, cy = (x.w - 1) / 2, (x.h - 1) / 2
        d = max(abs(x.i - cx), abs(x.j - cy)) / max(1.0, x.w / 2)
        return glow(ramp(BLUE, 1.05 - d * 0.9), ramp(BLUE, 1.0 - d * 0.6))

    def gem(self, x):
        cx, cy = (x.w - 1) / 2, (x.h - 1) / 2
        d = abs(x.i - cx) / max(1, x.w) + abs(x.j - cy) / max(1, x.h)
        return glow(ramp(BLUE, 1.0 - d * 1.1))

    def eye(self, x):
        if x.face in ("east", "west"):
            # almond eye: dark rim, bright cyan iris, white glint, dark slit pupil
            cx, cy = (x.w - 1) * 0.5, (x.h - 1) * 0.5
            dx, dy = (x.i - cx) / max(1.0, x.w / 2), (x.j - cy) / max(1.0, x.h / 2)
            if abs(dy) > 1 - dx * dx * 0.55 or abs(dx) > 0.96:
                return rgb("0A0C24")
            if abs(dx + 0.05) < 0.11 and abs(dy) < 0.8:
                return glow(rgb("04103A"), rgb("061A50"))
            if -0.55 < dx < -0.25 and -0.75 < dy < -0.35:
                return glow(rgb("F4FDFF"))
            return glow(ramp(BLUE, 0.98 - 0.35 * math.hypot(dx, dy)), ramp(BLUE, 1.0 - 0.2 * math.hypot(dx, dy)))
        return glow(BLUE[3])

    def eye_trail(self, x):
        k = (x.lp[2] - x.cube.origin[2]) / max(1.0, x.cube.size[2])
        return glow(ramp(BLUE, 0.95 - 0.5 * k))

    def socket(self, x):
        cx, cy = (x.w - 1) / 2, (x.h - 1) / 2
        d = math.hypot((x.i - cx) / max(1.0, x.w / 2), (x.j - cy) / max(1.0, x.h / 2))
        if d > 1.0:
            return CLEAR
        return ramp(HIDE, 0.05 + 0.12 * d)

    def lid(self, x):
        return ramp(HIDE, 0.32 + 0.12 * (x.j / max(1, x.h)) + (0.08 if x.j == x.h - 1 else 0))

    def nostril(self, x):
        return rgb("05040C")

    def teeth(self, x):
        if x.face in ("east", "west", "north", "south") and x.j >= x.h - 2:
            per = 3
            if (x.i % per) == per - 1:
                return CLEAR
            if x.j == x.h - 1 and (x.i % per) == 1:
                return CLEAR
        return ramp(TEETH, 0.75 - 0.35 * x.j / max(1, x.h))

    def fang(self, x):
        return ramp(TEETH, 0.95 - 0.5 * x.j / max(1, x.h) + (0.1 if x.i == 0 else 0))

    def mouth(self, x):
        rid = (x.p[2] / 1.6) % 1.0
        return ramp(MOUTH, 0.35 + (0.25 if rid < 0.3 else 0) + (h01(x.p[0], x.p[2]) - 0.5) * 0.1)

    def tongue(self, x):
        return ramp(MOUTH, 0.75 - 0.2 * abs(x.p[0]) / 3 + (0.1 if abs(x.p[0]) < 0.4 else 0))

    def claw(self, x):
        k = (x.lp[2] - x.cube.origin[2]) / max(1.0, x.cube.size[2])
        t = 0.55 - 0.35 * k + (0.25 if x.i == 0 and x.face != "down" else 0)
        return ramp(CLAW, t * LIGHT[x.face])

    def horn(self, k):
        def fn(x):
            q = (x.lp[2] - x.cube.origin[2]) / max(1.0, x.cube.size[2])
            if x.cube.size[2] > 5 and abs(q - 0.1) < 0.05:
                return GOLD[3] if x.face != "down" else GOLD[1]
            t = 0.62 - 0.08 * k - 0.12 * q + (0.16 if x.i == 0 and x.face != "down" else 0) - (0.2 if x.face == "down" else 0)
            if (x.lp[2] - x.cube.origin[2]) % 2.4 < 0.45:
                t -= 0.12
            t += (h01(x.p[0], x.p[1], x.p[2]) - 0.5) * 0.06
            return ramp(BRONZE, t * LIGHT[x.face] / 0.9)
        return fn

    def wingbone(self, x):
        t = 0.55 + (0.12 if x.face == "up" else 0) - (0.2 if x.face == "down" else 0)
        if x.j == 0 and x.face != "down":
            return GOLD[3]
        ring = (x.lp[0] if x.cube.rotation is None else x.lp[2]) % 7.0
        if ring < 0.5:
            return GOLD[2]
        return ramp(BRONZE, t * LIGHT[x.face] / 0.9 + (h01(x.p[0], x.p[2]) - 0.5) * 0.05)

    def gear(self, r):
        def fn(x):
            if x.face not in ("east", "west"):
                return ramp(BRONZE, 0.4)
            # cube-local coords on the face plane
            cz = x.cube.origin[2] + x.cube.size[2] / 2
            cy = x.cube.origin[1] + x.cube.size[1] / 2
            dz, dy = x.lp[2] - cz, x.lp[1] - cy
            d = math.hypot(dz, dy)
            a = math.atan2(dy, dz)
            tooth = (a / (2 * math.pi) * 12) % 1.0 < 0.5
            if d > r or (d > r * 0.8 and not tooth):
                return CLEAR
            if d > r * 0.8:
                return GOLD[3] if dy > 0 else GOLD[1]
            if d < r * 0.28:
                return glow(ramp(BLUE, 1 - d / r * 2))
            if d < r * 0.38:
                return GOLD[4]
            spoke = abs(math.sin(a * 3)) < 0.25
            if r * 0.4 < d < r * 0.68 and not spoke:
                return ramp(BRONZE, 0.18)
            return ramp(BRONZE, 0.62 + 0.15 * dy / r)
        return fn

    def disc(self, radius, cz, cy):
        def fn(x):
            dz, dy = x.lp[2] - cz, x.lp[1] - cy
            return disc_color(math.hypot(dz, dy) / radius, math.atan2(dy, dz), dy / radius)
        return fn

    def disc_flat(self, radius, cx, cz):
        def fn(x):
            dx, dz = x.lp[0] - cx, x.lp[2] - cz
            return disc_color(math.hypot(dx, dz) / radius, math.atan2(dz, dx), -dz / radius)
        return fn

    def membrane(self, pts, veins):
        n = len(pts)
        edges = [(pts[k], pts[(k + 1) % n]) for k in range(n)]

        def is_bone(e):
            (ax, az), (bx, bz) = e
            if math.hypot(ax, az) < 0.5 or math.hypot(bx, bz) < 0.5:
                return True
            return abs(az) < 0.5 and abs(bz) < 0.5
        bone_edges = [e for e in edges if is_bone(e)]
        free = [e for e in edges if not is_bone(e)]

        def fn(x, u, v):
            if x.face not in ("up", "down"):
                return CLEAR
            if not in_poly(u, v, pts):
                return CLEAR
            df = min(seg_dist(u, v, a, b) for a, b in free) if free else 99
            db = min(seg_dist(u, v, a, b) for a, b in bone_edges) if bone_edges else 99
            if df < 0.45:
                return glow(BLUE[3], BLUE[2])
            if df < 1.2:
                return GOLD[3] if x.face == "up" else GOLD[2]
            if df < 1.7:
                return ramp(MEMB, 0.18)
            for a, b in veins:
                if seg_dist(u, v, a, b) < 0.4:
                    return glow(MEMB[5], BLUE[1])
            r = math.hypot(u, v)
            ang = math.atan2(v, u)
            wrinkle = abs(math.sin(ang * 26 + r * 0.06)) < 0.12 and r > 12
            t = 0.28 + 0.4 * min(1.0, db / 16.0) - 0.1 * min(1.0, df / 24.0)
            if wrinkle:
                t -= 0.07
            if x.face == "down":
                t -= 0.08
            t += (h01(math.floor(u / 1.5), math.floor(v / 1.5)) - 0.5) * 0.05
            return ramp(MEMB, t)
        return fn


def disc_color(d, a, shade):
    if d > 1.0:
        return CLEAR
    if d > 0.88:
        return GOLD[4] if shade > 0 else GOLD[2]
    if d > 0.55:
        if abs((a * 4 / math.pi) % 2 - 1) < 0.12 and 0.64 < d < 0.8:
            return GOLD[4]
        return ramp(BRONZE, 0.55 + 0.2 * shade)
    if d > 0.45:
        return GOLD[3]
    return glow(ramp(BLUE, 1.0 - d * 1.2))


def in_poly(px, pz, pts):
    c = False
    n = len(pts)
    for k in range(n):
        ax, az = pts[k]
        bx, bz = pts[(k + 1) % n]
        if (az > pz) != (bz > pz) and px < (bx - ax) * (pz - az) / (bz - az + 1e-12) + ax:
            c = not c
    return c


def seg_dist(px, pz, a, b):
    ax, az = a
    bx, bz = b
    dx, dz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / max(1e-9, dx * dx + dz * dz)))
    return math.hypot(px - ax - t * dx, pz - az - t * dz)


# --------------------------------------------------------------------------------------------- build

def pack(cubes, tex_w, density):
    owners = {c.name: c for c in cubes}
    # a mirrored copy finds its texture by the original's name: two originals with one name would hand it the wrong one
    shared = {c.share for c in cubes if c.share}
    dup = [n for n in shared if sum(1 for c in cubes if c.name == n and not c.share) > 1]
    assert not dup, "cube names shared by mirrors must be unique: %s" % dup
    faces = [(c, f) for c in cubes if not c.share for f in c.faces]
    faces.sort(key=lambda cf: (-math.ceil(face_size(cf[0], cf[1])[1] * density), -math.ceil(face_size(cf[0], cf[1])[0] * density)))
    x, y, shelf = 0, 0, 0
    for c, face in faces:
        fw, fh = [max(1, math.ceil(v * density)) for v in face_size(c, face)]
        if x + fw > tex_w:
            x, y, shelf = 0, y + shelf + 1, 0
        c.uv[face] = (x, y, fw, fh)
        x += fw + 1
        shelf = max(shelf, fh)
    for c in cubes:
        if c.share:
            c.uv = dict(owners[c.share].uv)
    return y + shelf


def build(D, identifier="tech_dragon", tex_w=None, density=None, bounds=(24, 12, 3)):
    tex_w = tex_w or TEX_W
    density = density or DENSITY
    tex_h = pack(D.cubes, tex_w, density)
    tex_h = int(math.ceil(tex_h / 16.0) * 16)
    img = Image.new("RGBA", (tex_w, tex_h), (0, 0, 0, 0))
    glw = Image.new("RGBA", (tex_w, tex_h), (0, 0, 0, 0))
    skel = rig_v4.Skeleton(D.bones)
    rest = skel.rest_world()
    ipx, gpx = img.load(), glw.load()
    for c in D.cubes:
        if c.share:
            continue
        cm = rest[c.bone] @ rig_v4.cube_matrix({"rotation": c.rotation, "pivot": c.pivot or [c.origin[i] + c.size[i] / 2 for i in range(3)]})
        r3 = cm[:3, :3]
        for face, (x0, y0, fw, fh) in c.uv.items():
            nrm = r3 @ np.array(FACE_N[face], dtype=float)
            nrm /= max(1e-9, np.linalg.norm(nrm))
            ctx = Ctx()
            ctx.face, ctx.w, ctx.h, ctx.size, ctx.cube, ctx.n = face, fw, fh, c.size, c, nrm
            for j in range(fh):
                for i in range(fw):
                    fu, fv = (i + 0.5) / fw, (j + 0.5) / fh
                    lp = local_point(c, face, fu, fv)
                    wp = cm @ np.array([lp[0], lp[1], lp[2], 1.0])
                    ctx.i, ctx.j, ctx.fu, ctx.fv, ctx.lp, ctx.p = i, j, fu, fv, lp, wp[:3]
                    r = c.paint(ctx)
                    if r is None:
                        continue
                    if isinstance(r, tuple) and len(r) == 2 and isinstance(r[0], tuple):
                        col, g = r
                    else:
                        col, g = r, None
                    if len(col) == 3:
                        col = col + (255,)
                    ipx[x0 + i, y0 + j] = col
                    if g is not None:
                        gpx[x0 + i, y0 + j] = (g[0], g[1], g[2], 255)
    out_bones = []
    for name, parent, pivot, rotation in D.bones:
        b = {"name": name, "pivot": pivot}
        if parent:
            b["parent"] = parent
        if rotation:
            b["rotation"] = rotation
        own = [c for c in D.cubes if c.bone == name]
        if own:
            b["cubes"] = []
            for c in own:
                e = {"origin": c.origin, "size": c.size, "uv": {}}
                for face, (x, y, w, h) in c.uv.items():
                    fw, fh = [v * density for v in face_size(c, face)]
                    if face == "down":
                        e["uv"][face] = {"uv": [x, y + h], "uv_size": [fw, -fh]}
                    else:
                        e["uv"][face] = {"uv": [x, y], "uv_size": [fw, fh]}
                if c.mirror_of is not None:
                    # mirrored copy: flip u on every face so painted details read the same from outside
                    for face, uvd in e["uv"].items():
                        if face in ("north", "south", "up", "down", "east", "west"):
                            uvd["uv"] = [uvd["uv"][0] + uvd["uv_size"][0], uvd["uv"][1]]
                            uvd["uv_size"] = [-uvd["uv_size"][0], uvd["uv_size"][1]]
                    # east/west swap sides when mirrored
                    if "east" in e["uv"] or "west" in e["uv"]:
                        ea, we = e["uv"].get("east"), e["uv"].get("west")
                        e["uv"]["east"], e["uv"]["west"] = we, ea
                        e["uv"] = {k: v for k, v in e["uv"].items() if v is not None}
                if c.inflate:
                    e["inflate"] = c.inflate
                if c.rotation:
                    e["rotation"] = c.rotation
                    e["pivot"] = c.pivot if c.pivot else [c.origin[i] + c.size[i] / 2 for i in range(3)]
                b["cubes"].append(e)
        out_bones.append(b)
    geo = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry." + identifier, "texture_width": tex_w, "texture_height": tex_h,
                        "visible_bounds_width": bounds[0], "visible_bounds_height": bounds[1], "visible_bounds_offset": [0, bounds[2], 0]},
        "bones": out_bones}]}
    return geo, img, glw


def tech_dragon():
    D = build_dragon()
    geo, img, glw = build(D)
    return D, geo, img, glw


if __name__ == "__main__":
    import json
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    D, geo, img, glw = tech_dragon()
    json.dump(geo, open(out + "/tech_dragon.geo.json", "w"))
    img.save(out + "/tech_dragon.png")
    glw.save(out + "/tech_dragon_glowmask.png")
    print("bones", len(D.bones), "cubes", len(D.cubes), "texture", img.size)
