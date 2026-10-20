"""
Iron's Technomancy 1.10 worn armour (GeckoLib, Iron's Spells armour bone layout), redrawn after the user's two
concept sheets ("Steampunk Clockwork Mage Armor" Tier 1 and its hextech Tier 2), built the way Hazen'n'Stuff and
TravelOptics build theirs (studied, nothing copied): the vanilla body boxes inflated a little as the cloth layer, then
extra cubes for every piece that stands out - hat brims and crowns, collars, coat tails, pauldrons, cuffs, buckles -
some turned, a few animated bones; 2 texels per model pixel.

Tier 1, clockwork mage (dark cocoa cloth, cream panels and trim, brass and copper, amber lenses):
  a wide-brimmed wizard hat in three steps with the tip bent back, a brass band with goggles and a turning cog;
  a long coat - high collar, cream lapels and front panels, brass gear buttons, a leather belt with a gear buckle,
  coat tails split at the front with cream lining; cog pauldrons, wide cream cuffs; banded trousers; buckled boots;
  the extras the user picked: a ring of glowing cogs turning behind the back (magic ring) and a gear charm hanging
  from the belt.
Tier 2, hextech (navy, gold trim, cream, glowing blue crystals): the same cut, a big gold cog with a blue gem on the
  hat band and crystal lanterns hanging from the brim, gold epaulettes with crystals, a crystal brooch and buckle.
"""
import math

from PIL import Image

from armor_v6 import BONES as BONES6, cog_emblem, glyphs, lens, plate, rivets, stripe, with_details
from premium import MAT, Mat, hue_ramp

TEX = 256
DENS = 2
B, BD, CU, LEA, CRM, NAV, IRN = (MAT[k] for k in ("brass", "brass_dark", "copper", "leather", "cream", "navy", "iron"))
AMB, CYA = MAT["amber_glow"], MAT["cyan_glow"]
COCOA = Mat(hue_ramp("#4A2C1E", 7, 0.03, 0.5, shift=0.04), base=0.5, spread=0.5, gloss=0.1, dither=True)
NAVY2 = Mat(hue_ramp("#1A2550", 8, 0.02, 0.5, shift=0.05), base=0.52, spread=0.5, gloss=0.2, dither=True)
GOLD = Mat(hue_ramp("#E0B040", 8, 0.12, 0.97, shadow_hue=0.05, light_hue=0.15), base=0.6, spread=0.55, gloss=0.4)
BLUEG = Mat(hue_ramp("#2A6CFF", 8, 0.12, 0.98, shadow_hue=0.7, light_hue=0.55, sat_curve=0.0), glow=True, base=0.7, spread=0.45, gloss=0.5)
GLASS = Mat(hue_ramp("#9AD8E8", 6, 0.3, 0.98, shift=0.03), base=0.6, spread=0.5, gloss=0.6)

HEAD, BODY, RA, LA, RL, LL, RB, LB, TORSO = ("armorHead", "armorBody", "armorRightArm", "armorLeftArm", "armorRightLeg", "armorLeftLeg",
                                            "armorRightBoot", "armorLeftBoot", "armorLeggingTorsoLayer")
BONES = [b for b in BONES6 if b[0] not in ("hat_gear", "back_gear")] + [
    ("hat_tip", "armorHead", [0, 37.6, 0]), ("hat_gear", "armorHead", [4.9, 31.0, 0]),
    ("back_ring", "armorBody", [0, 18, 5.0]), ("charm", "armorBody", [2.6, 12.4, -2.8]), ("coat_tails", "armorBody", [0, 12, 0])]


class Cube:
    def __init__(self, bone, name, origin, size, paint, inflate=0.0, faces=("north", "east", "south", "west", "up", "down"), share=None, glow=False,
                 rotation=None, pivot=None):
        self.bone, self.name, self.origin, self.size, self.paint = bone, name, origin, size, paint
        self.inflate, self.faces, self.share, self.glow, self.rotation, self.pivot = inflate, faces, share, glow, rotation, pivot
        self.uv = {}


def face_size(c, face):
    w, h, d = c.size
    return {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}[face]


def pack(cubes):
    owners = {c.name: c for c in cubes}
    faces = [(c, f) for c in cubes if not c.share for f in c.faces]
    faces.sort(key=lambda cf: (-math.ceil(face_size(*cf)[1] * DENS), -math.ceil(face_size(*cf)[0] * DENS)))
    x, y, shelf = 0, 0, 0
    for c, f in faces:
        fw, fh = [max(1, math.ceil(v * DENS)) for v in face_size(c, f)]
        if x + fw > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        c.uv[f] = (x, y, fw, fh)
        x += fw + 1
        shelf = max(shelf, fh)
    assert y + shelf <= TEX, "armour texture overflow (%d)" % (y + shelf)
    for c in cubes:
        if c.share:
            c.uv = dict(owners[c.share].uv)


def ramp_at(mat, t):
    r = mat.ramp
    return r[max(0, min(len(r) - 1, int(round(t * (len(r) - 1)))))]


# ------------------------------------------------------------------------------------------- extra painters

def trim(mat, width=2, sides=("top", "bottom", "left", "right"), faces=("north", "south", "east", "west")):
    """A band of `mat` along the chosen edges of a face (piping, coat hems, lapels)."""
    def d(img, x, y, w, h, face):
        if face not in faces:
            return
        for j in range(h):
            for i in range(w):
                edge = ("top" in sides and j < width) or ("bottom" in sides and j >= h - width) or ("left" in sides and i < width) or (
                    "right" in sides and i >= w - width)
                if edge:
                    t = 0.72 - 0.18 * (j / max(1, h - 1)) + (0.12 if (j == 0 or i == 0) else 0) - (0.15 if (j == h - 1 or i == w - 1) else 0)
                    img.putpixel((x + i, y + j), ramp_at(mat, t))
    return d


def panel(mat, x0, x1, y0=0.0, y1=1.0, faces=("north",)):
    """A lighter panel (fractions of the face): the cream front panels of the coat."""
    def d(img, x, y, w, h, face):
        if face not in faces:
            return
        for j in range(int(h * y0), int(h * y1)):
            for i in range(int(w * x0), int(w * x1)):
                t = 0.62 - 0.2 * (j / max(1, h)) + (0.1 if i == int(w * x0) else 0) - (0.12 if i == int(w * x1) - 1 else 0)
                img.putpixel((x + i, y + j), ramp_at(mat, t))
    return d


def lapels(cloth, light, faces=("north",)):
    """The coat front: a V of cream lapels from the collar to the chest, a cream placket down the middle."""
    def d(img, x, y, w, h, face):
        if face not in faces:
            return
        cx = (w - 1) / 2
        for j in range(h):
            for i in range(w):
                v = j / max(1, h - 1)
                half = abs(i - cx)
                if v < 0.45 and abs(half - (1 - v / 0.45) * w * 0.32) < 2.4:
                    img.putpixel((x + i, y + j), ramp_at(light, 0.68 - 0.3 * v))
                elif v >= 0.45 and half < 1.9:
                    img.putpixel((x + i, y + j), ramp_at(light, 0.55))
    return d


def buttons(mat, n=3, faces=("north",), x_frac=0.66):
    def d(img, x, y, w, h, face):
        if face not in faces:
            return
        for k in range(n):
            j = int(h * (0.5 + 0.13 * k))
            i = int(w * x_frac)
            if j + 1 < h and i + 1 < w:
                img.putpixel((x + i, y + j), mat.ramp[-2])
                img.putpixel((x + i + 1, y + j), mat.ramp[3])
                img.putpixel((x + i, y + j + 1), mat.ramp[2])
                img.putpixel((x + i + 1, y + j + 1), mat.ramp[1])
    return d


def gem(mat):
    def paint(img, x, y, w, h, face):
        for j in range(h):
            for i in range(w):
                dx, dy = (i - (w - 1) / 2) / max(1, w / 2), (j - (h - 1) / 2) / max(1, h / 2)
                img.putpixel((x + i, y + j), ramp_at(mat, 0.98 - 0.5 * (abs(dx) + abs(dy))))
    return paint


def mirror_pair(cubes, bone_r, bone_l, name, origin, size, paint, **kw):
    a = Cube(bone_r, name + "_r", origin, size, paint, **kw)
    x, y, z = origin
    w = size[0]
    kw2 = {k: v for k, v in kw.items() if k not in ("share", "rotation", "pivot")}
    rot, piv = kw.get("rotation"), kw.get("pivot")
    b = Cube(bone_l, name + "_l", [-(x + w), y, z], size, paint, share=name + "_r",
             rotation=[rot[0], -rot[1], -rot[2]] if rot else None, pivot=[-piv[0], piv[1], piv[2]] if piv else None, **kw2)
    cubes += [a, b]


# ------------------------------------------------------------------------------------------- the two sets

def mage_cubes(tier):
    t1 = tier == 1
    cloth, light, metal, glow = (COCOA, CRM, B, AMB) if t1 else (NAVY2, CRM, GOLD, BLUEG)
    hat = with_details(plate(cloth), trim(cloth, 1, ("bottom",)))
    cubes = [
        # ---- the hat: brim, three steps of crown, the tip bent back, a band with goggles (T1) or a gem (T2)
        Cube(HEAD, "brim", [-7.5, 29.0, -7.5], [15, 1, 15], with_details(plate(cloth, tone=-0.05), trim(metal if not t1 else light, 1, ("top", "bottom", "left", "right"), ("up",))), 0.0),
        Cube(HEAD, "brim_under", [-6.5, 28.6, -6.5], [13, 0.4, 13], plate(cloth, tone=-0.25), 0.0, ("down", "north", "south", "east", "west")),
        Cube(HEAD, "crown_a", [-4.6, 30.0, -4.6], [9.2, 3.2, 9.2], hat, 0.0),
        Cube(HEAD, "crown_b", [-3.7, 33.2, -3.4], [7.4, 2.6, 7.4], hat, 0.0, rotation=[-6, 0, 0], pivot=[0, 33.2, 0]),
        Cube(HEAD, "crown_c", [-2.7, 35.4, -2.0], [5.4, 2.4, 5.4], hat, 0.0, rotation=[-14, 0, 0], pivot=[0, 35.4, 0.6]),
        Cube("hat_tip", "tip_a", [-1.7, 37.4, -0.2], [3.4, 2.2, 3.4], hat, 0.0, rotation=[-38, 0, 0], pivot=[0, 37.6, 1.5]),
        Cube("hat_tip", "tip_b", [-1.0, 38.6, 2.6], [2.0, 1.8, 2.4], hat, 0.0, rotation=[-75, 0, 0], pivot=[0, 39.2, 3.6]),
        Cube(HEAD, "band", [-4.7, 30.2, -4.7], [9.4, 1.3, 9.4], with_details(plate(metal), rivets(BD)), 0.0, ("north", "south", "east", "west")),
        Cube("hat_gear", "hat_gear", [4.7, 29.4, -1.9], [0.6, 3.8, 3.8], with_details(plate(metal), cog_emblem(metal, glow, ("east", "west"), 0.48)), 0.0),
    ]
    if t1:
        cubes += [
            Cube(HEAD, "goggle_r", [-3.9, 30.4, -5.4], [3.0, 2.8, 0.8], lens(AMB), 0.0, glow=True),
            Cube(HEAD, "goggle_l", [0.9, 30.4, -5.4], [3.0, 2.8, 0.8], lens(AMB), 0.0, share="goggle_r", glow=True),
            Cube(HEAD, "goggle_rim_r", [-4.2, 30.1, -5.1], [3.6, 3.4, 0.5], plate(B), 0.0),
            Cube(HEAD, "goggle_rim_l", [0.6, 30.1, -5.1], [3.6, 3.4, 0.5], plate(B), 0.0, share="goggle_rim_r"),
            Cube(HEAD, "goggle_bridge", [-0.6, 31.4, -5.1], [1.2, 0.6, 0.5], plate(B), 0.0),
            Cube(HEAD, "side_cog", [-5.3, 29.8, -1.4], [0.6, 2.8, 2.8], with_details(plate(CU), cog_emblem(CU, AMB, ("east", "west"), 0.48)), 0.0),
        ]
    else:
        cubes += [
            Cube(HEAD, "brooch", [-1.9, 30.0, -5.2], [3.8, 3.8, 0.6], with_details(plate(GOLD), cog_emblem(GOLD, BLUEG, ("north",), 0.5)), 0.0),
            Cube(HEAD, "lantern_r", [-7.0, 26.4, -6.8], [1.2, 1.8, 1.2], gem(BLUEG), 0.0, glow=True),
            Cube(HEAD, "lantern_l", [5.8, 26.4, -6.8], [1.2, 1.8, 1.2], gem(BLUEG), 0.0, share="lantern_r", glow=True),
            Cube(HEAD, "lantern_cord_r", [-6.6, 28.2, -6.4], [0.4, 0.8, 0.4], plate(GOLD), 0.0),
            Cube(HEAD, "lantern_cord_l", [6.2, 28.2, -6.4], [0.4, 0.8, 0.4], plate(GOLD), 0.0, share="lantern_cord_r"),
        ]
    # ---- the coat
    coat = with_details(plate(cloth), lapels(cloth, light), buttons(metal), trim(light if t1 else metal, 1, ("left", "right"), ("east", "west")),
                        glyphs(CYA, ("south",)) if not t1 else (lambda *a: None))
    cubes += [
        Cube(BODY, "coat", [-4, 12, -2], [8, 12, 4], coat, 0.55),
        Cube(BODY, "collar", [-4.4, 22.6, -2.6], [8.8, 2.4, 5.2], with_details(plate(cloth, tone=0.05), trim(light if t1 else metal, 1, ("top",))), 0.35,
             ("north", "south", "east", "west", "up")),
        Cube(BODY, "belt", [-4.2, 12.4, -2.2], [8.4, 1.6, 4.4], with_details(plate(LEA if t1 else cloth, tone=-0.25), rivets(metal)), 0.75),
        Cube(BODY, "buckle", [-1.3, 12.2, -3.15], [2.6, 2.6, 0.5], with_details(plate(metal), cog_emblem(metal, glow, ("north",), 0.5)), 0.0),
        Cube(BODY, "brooch", [-1.0, 21.2, -3.1], [2.0, 2.0, 0.5], gem(glow), 0.0, glow=True),
        # coat tails: split in front with the lining showing, a full back panel and the sides
        Cube("coat_tails", "tail_fr", [-4.6, 3.0, -2.95], [4.3, 9.2, 0.6], with_details(plate(cloth), trim(light if t1 else metal, 2, ("left", "bottom"), ("north",))), 0.0),
        Cube("coat_tails", "tail_fl", [0.3, 3.0, -2.95], [4.3, 9.2, 0.6], with_details(plate(cloth), trim(light if t1 else metal, 2, ("right", "bottom"), ("north",))), 0.0),
        Cube("coat_tails", "tail_back", [-4.6, 2.4, 2.35], [9.2, 9.8, 0.6], with_details(plate(cloth), trim(light if t1 else metal, 1, ("bottom",), ("south",)),
                                                                                     panel(light, 0.45, 0.55, 0.0, 0.9, ("south",))), 0.0),
        Cube("coat_tails", "tail_r", [-5.1, 3.4, -2.6], [0.6, 8.8, 5.0], with_details(plate(cloth, tone=-0.05), trim(light, 1, ("bottom",), ("east", "west"))), 0.0),
        Cube("coat_tails", "tail_l", [4.5, 3.4, -2.6], [0.6, 8.8, 5.0], with_details(plate(cloth, tone=-0.05), trim(light, 1, ("bottom",), ("east", "west"))), 0.0),
        Cube("coat_tails", "lining", [-0.3, 3.4, -2.8], [0.6, 8.6, 0.4], plate(light, tone=0.05), 0.0, ("north",)),
    ]
    if t1:
        # the magic ring of glowing cogs behind the back, and the gear charm hanging from the belt
        for k in range(10):
            a = k * 36.0
            r = math.radians(a)
            cx, cy = math.cos(r) * 6.2, 18 + math.sin(r) * 6.2
            cubes.append(Cube("back_ring", "ring_cog" if k == 0 else "ring_cog%d" % k, [cx - 1.0, cy - 1.0, 5.0], [2.0, 2.0, 0.4],
                              with_details(plate(B), cog_emblem(B, AMB, ("north", "south"), 0.5)), 0.0, share=None if k == 0 else "ring_cog",
                              rotation=[0, 0, a], pivot=[cx, cy, 5.2]))
        cubes += [
            Cube("back_ring", "ring_core", [-1.2, 16.8, 5.1], [2.4, 2.4, 0.3], gem(AMB), 0.0, glow=True),
            Cube("charm", "charm_chain", [2.4, 9.8, -2.95], [0.4, 2.6, 0.4], plate(B), 0.0),
            Cube("charm", "charm_cog", [1.4, 7.6, -3.05], [2.4, 2.4, 0.5], with_details(plate(B), cog_emblem(B, AMB, ("north", "south"), 0.5)), 0.0),
        ]
    # ---- arms: pauldrons (a cog one on the left, T1; gold epaulettes with a crystal, T2), sleeves, wide cuffs
    mirror_pair(cubes, RA, LA, "sleeve", [-8, 12, -2], [4, 12, 4], with_details(plate(cloth), trim(light if t1 else metal, 1, ("left", "right"), ("north", "south"))), inflate=0.55)
    mirror_pair(cubes, RA, LA, "pauldron", [-9.0, 21.2, -2.8], [5.4, 2.6, 5.6], with_details(plate(metal if not t1 else cloth, tone=0.05),
                                                                                          trim(light if t1 else GOLD, 1, ("bottom",))), inflate=0.45)
    mirror_pair(cubes, RA, LA, "cuff", [-8.5, 12, -2.5], [5, 3.2, 5], with_details(plate(light if t1 else cloth, tone=0.05), trim(metal, 1, ("top",))), inflate=0.35)
    if t1:
        cubes.append(Cube(LA, "shoulder_cog", [8.7, 19.4, -2.4], [0.6, 4.8, 4.8], with_details(plate(B), cog_emblem(B, AMB, ("east", "west"), 0.5)), 0.0))
    else:
        mirror_pair(cubes, RA, LA, "epaulette_gem", [-9.6, 22.2, -0.6], [0.8, 1.2, 1.2], gem(BLUEG), inflate=0.0, glow=True)
    # ---- leggings: trousers with a stripe and knee straps, a pouch on the hip
    trousers = with_details(plate(cloth, tone=-0.08), stripe(light, True, 0.5, 1, ("east", "west")))
    cubes += [
        Cube(TORSO, "waist", [-4, 12, -2], [8, 12, 4], plate(cloth, tone=-0.12), 0.4),
        Cube(TORSO, "pouch", [-5.2, 9.6, -1.6], [1.4, 2.6, 3.2], with_details(plate(LEA if t1 else cloth), rivets(metal, faces=("east", "west"))), 0.0),
        Cube(RL, "trouser_r", [-4, 0, -2], [4, 12, 4], trousers, 0.3),
        Cube(LL, "trouser_l", [0, 0, -2], [4, 12, 4], trousers, 0.3, share="trouser_r"),
        Cube(RL, "knee_r", [-4, 5.5, -2], [4, 1.6, 4], with_details(plate(metal), rivets(BD)), 0.55, ("north", "east", "west", "south")),
        Cube(LL, "knee_l", [0, 5.5, -2], [4, 1.6, 4], with_details(plate(metal), rivets(BD)), 0.55, ("north", "east", "west", "south"), share="knee_r"),
        # ---- boots: cuffs, buckle straps, toe caps, soles
        Cube(RB, "boot_r", [-4, 0, -2], [4, 6, 4], with_details(plate(LEA if t1 else cloth), rivets(metal)), 0.75),
        Cube(LB, "boot_l", [0, 0, -2], [4, 6, 4], with_details(plate(LEA if t1 else cloth), rivets(metal)), 0.75, share="boot_r"),
        Cube(RB, "boot_cuff_r", [-4.3, 5.2, -2.3], [4.6, 1.8, 4.6], with_details(plate(light if t1 else metal), trim(metal, 1, ("bottom",))), 0.8),
        Cube(LB, "boot_cuff_l", [-0.3, 5.2, -2.3], [4.6, 1.8, 4.6], with_details(plate(light if t1 else metal), trim(metal, 1, ("bottom",))), 0.8, share="boot_cuff_r"),
        Cube(RB, "strap_r", [-4, 2.4, -2], [4, 1.2, 4], with_details(plate(metal, tone=-0.1), rivets(BD)), 0.9, ("north", "east", "west", "south")),
        Cube(LB, "strap_l", [0, 2.4, -2], [4, 1.2, 4], with_details(plate(metal, tone=-0.1), rivets(BD)), 0.9, ("north", "east", "west", "south"), share="strap_r"),
        Cube(RB, "toe_r", [-4, 0, -2.7], [4, 1.8, 1.8], plate(metal), 0.9, ("north", "east", "west", "up")),
        Cube(LB, "toe_l", [0, 0, -2.7], [4, 1.8, 1.8], plate(metal), 0.9, ("north", "east", "west", "up"), share="toe_r"),
    ]
    if not t1:
        cubes += [Cube(RB, "boot_gem_r", [-2.6, 2.1, -3.15], [1.2, 1.6, 0.4], gem(BLUEG), 0.0, glow=True),
                  Cube(LB, "boot_gem_l", [1.4, 2.1, -3.15], [1.2, 1.6, 0.4], gem(BLUEG), 0.0, share="boot_gem_r", glow=True)]
    return cubes


def build(name, cubes, tier):
    pack(cubes)
    img = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    glow = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    glow_px = set(AMB.ramp[3:]) | set(CYA.ramp[3:]) | set(BLUEG.ramp[3:])
    for c in cubes:
        if c.share:
            continue
        for face, (x, y, w, h) in c.uv.items():
            c.paint(img, x, y, w, h, face)
            for j in range(h):
                for i in range(w):
                    px = img.getpixel((x + i, y + j))
                    if px[3] and (c.glow or px in glow_px):
                        glow.putpixel((x + i, y + j), px)
    bones = []
    for bname, parent, pivot in BONES:
        b = {"name": bname, "pivot": pivot}
        if parent:
            b["parent"] = parent
        own = [c for c in cubes if c.bone == bname]
        if own:
            b["cubes"] = []
            for c in own:
                e = {"origin": c.origin, "size": c.size, "uv": {}}
                for face, (x, y, w, h) in c.uv.items():
                    fw, fh = [v * DENS for v in face_size(c, face)]
                    # GeckoLib/Bedrock "east" is the cube's min-x side: the face painted for +x is written as "west"
                    key = {"east": "west", "west": "east"}.get(face, face)
                    e["uv"][key] = {"uv": [x, y + h], "uv_size": [fw, -fh]} if face == "down" else {"uv": [x, y], "uv_size": [fw, fh]}
                if c.inflate:
                    e["inflate"] = c.inflate
                if c.rotation:
                    e["rotation"] = c.rotation
                    e["pivot"] = c.pivot if c.pivot else [c.origin[i] + c.size[i] / 2 for i in range(3)]
                b["cubes"].append(e)
        bones.append(b)
    geo = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry." + name, "texture_width": TEX, "texture_height": TEX,
                        "visible_bounds_width": 4, "visible_bounds_height": 6, "visible_bounds_offset": [0, 2.5, 0]},
        "bones": bones}]}
    k = {"vector": [0, 0, 0]}
    idle = {"hat_gear": {"rotation": {"0.0": k, "4.0": {"vector": [360, 0, 0]}}},
            "hat_tip": {"rotation": {"0.0": k, "2.0": {"vector": [-4, 0, 3]}, "4.0": k}},
            "coat_tails": {"rotation": {"0.0": k, "2.0": {"vector": [2.5, 0, 0]}, "4.0": k}}}
    if tier == 1:
        idle["back_ring"] = {"rotation": {"0.0": k, "8.0": {"vector": [0, 0, -360]}},
                             "position": {"0.0": k, "4.0": {"vector": [0, 0.5, 0]}, "8.0": k}}
        idle["charm"] = {"rotation": {"0.0": {"vector": [0, 0, -8]}, "2.0": {"vector": [0, 0, 8]}, "4.0": {"vector": [0, 0, -8]}, "6.0": {"vector": [0, 0, 8]},
                                      "8.0": {"vector": [0, 0, -8]}}}
        L = 8.0
    else:
        L = 4.0
    anims = {"format_version": "1.8.0", "geckolib_format_version": 2, "animations": {"idle": {"loop": True, "animation_length": L, "bones": idle}}}
    return geo, img, glow, anims


def clockwork():
    return build("clockwork_engineer_armor", mage_cubes(1), 1)


def hextech():
    return build("hextech_engineer_armor", mage_cubes(2), 2)
