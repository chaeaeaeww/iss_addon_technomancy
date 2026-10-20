"""
Iron's Technomancy 1.9: spellbook model textures (laid out for irons_spellbooks:item/template_spell_book_model, 64x64,
1 texel per model px: outer cover 10x7 at (0,9), inner cover at (11,9), cover edges, spine at (10..14,21..32), pages
at (12..32,16..21) and (20..24,8..16)) and the Clockwork Altar (the dragon summoning device) block model + textures,
"Premium Fantasy" preset.
"""
import math

from PIL import Image

from premium import MAT

B, BD, WAL, CRM, NAV, AND, IRN, CU = (MAT[k] for k in ("brass", "brass_dark", "walnut", "cream", "navy", "andesite", "iron", "copper"))
AMB, CYA, VIO = MAT["amber_glow"], MAT["cyan_glow"], MAT["violet_glow"]


def r(mat, t):
    return mat.ramp[max(0, min(len(mat.ramp) - 1, int(round(t * (len(mat.ramp) - 1)))))]


def fill(img, x0, y0, x1, y1, fn):
    for y in range(y0, y1):
        for x in range(x0, x1):
            img.putpixel((x, y), fn(x - x0, y - y0, x1 - x0, y1 - y0))


def book(tier):
    """tier 1: cream cover in walnut with brass corners and an amber gem; tier 2: navy plate in brass, cyan crystal."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    cover, frame, gem = (CRM, WAL, AMB) if tier == 1 else (NAV, B, CYA)

    def outer(i, j, w, h):
        if i in (0, w - 1) or j in (0, h - 1):
            if (i in (0, w - 1)) and (j in (0, h - 1)):
                return r(B, 0.85)
            return r(frame, 0.55 if (i == 0 or j == 0) else 0.3)
        cx, cy = (w - 1) / 2, (h - 1) / 2
        d = math.hypot(i - cx, (j - cy) * 1.2)
        if d <= 1.0:
            return r(gem, 0.95 - 0.3 * (i - cx + j - cy))
        if d <= 2.2:
            return r(B, 0.7 - 0.15 * (i - cx + j - cy))
        if tier == 2 and abs(j - cy) < 0.6:
            return r(CYA, 0.7)
        return r(cover, 0.6 - 0.1 * j / h + (0.06 if (i + j) % 3 == 0 else 0))
    fill(img, 0, 9, 10, 16, outer)
    fill(img, 11, 9, 21, 16, lambda i, j, w, h: r(cover, 0.3 + 0.1 * (1 - j / h)))
    fill(img, 10, 9, 11, 16, lambda i, j, w, h: r(frame, 0.45))
    fill(img, 21, 9, 22, 16, lambda i, j, w, h: r(frame, 0.45))
    fill(img, 0, 16, 2, 26, lambda i, j, w, h: r(frame, 0.5 - 0.2 * i))
    # spine (top and bottom strips, brass bands every 3)
    fill(img, 10, 21, 14, 31, lambda i, j, w, h: r(B, 0.8) if j % 3 == 1 else r(frame, 0.5 - 0.15 * (i % 2)))
    fill(img, 0, 31, 24, 32, lambda i, j, w, h: r(B, 0.6))
    # pages
    fill(img, 12, 16, 32, 21, lambda i, j, w, h: r(CRM, 0.85 if j % 2 == 0 else 0.6))
    fill(img, 20, 8, 24, 16, lambda i, j, w, h: r(CRM, 0.8 if i % 2 == 0 else 0.62))
    return img


# ---------------------------------------------------------------------------------------------- altar

def altar_textures():
    """16x16 textures: andesite casing with brass trim (side), the summoning ring with a violet core (top), base, brass,
    violet crystal."""
    def tex(fn):
        im = Image.new("RGBA", (16, 16))
        for y in range(16):
            for x in range(16):
                im.putpixel((x, y), fn(x, y))
        return im

    def side(x, y):
        if y <= 1 or y >= 14:
            return r(B, 0.85 - 0.25 * (y >= 14) - 0.2 * (y in (1, 15)))
        if x in (0, 15):
            return r(AND, 0.2)
        if x in (3, 12) and 3 <= y <= 12:
            return r(CU, 0.6 if x == 3 else 0.4)
        if 6 <= x <= 9 and 5 <= y <= 10:
            if 7 <= x <= 8 and 6 <= y <= 9:
                return r(VIO, 0.9 - 0.08 * (y - 6))
            return r(IRN, 0.25)
        return r(AND, 0.55 + 0.12 * (0.5 - y / 15) + (0.05 if (x * 7 + y * 3) % 5 == 0 else 0))

    def top(x, y):
        d = math.hypot(x - 7.5, y - 7.5)
        a = (math.atan2(y - 7.5, x - 7.5) / (2 * math.pi) * 10) % 1.0
        if d <= 2.2:
            return r(VIO, 0.95 - 0.12 * d)
        if d <= 3.2:
            return r(IRN, 0.3)
        if d <= 5.4 or (d <= 6.8 and abs(a - 0.5) < 0.22):
            return r(B, 0.75 - 0.05 * (x + y - 15))
        if d <= 7.4:
            return r(AND, 0.25)
        return r(AND, 0.5 + (0.06 if (x + y) % 4 == 0 else 0))

    def base(x, y):
        return r(AND, 0.35 + (0.05 if (x * 3 + y) % 4 == 0 else 0))

    def brass(x, y):
        return r(B, 0.7 - 0.03 * (x + y) / 2 + (0.15 if x == 0 or y == 0 else 0))

    def crystal(x, y):
        return r(VIO, 0.95 - 0.04 * (x + y))
    return {"clockwork_altar_side": tex(side), "clockwork_altar_top": tex(top), "clockwork_altar_bottom": tex(base),
            "clockwork_altar_brass": tex(brass), "clockwork_altar_crystal": tex(crystal)}


def _el(f, t, tex, top=None, rot=None):
    faces = {}
    for face in ("north", "south", "east", "west", "up", "down"):
        if face in ("north", "south"):
            uv = [f[0], 16 - t[1], t[0], 16 - f[1]]
        elif face in ("east", "west"):
            uv = [f[2], 16 - t[1], t[2], 16 - f[1]]
        else:
            uv = [f[0], f[2], t[0], t[2]]
        faces[face] = {"uv": uv, "texture": top if (face == "up" and top) else tex}
    e = {"from": f, "to": t, "faces": faces}
    if rot:
        e["rotation"] = rot
    return e


def altar_model():
    """Dragon summoning device (ref: Dragon Summoning Device): a stepped andesite plinth with brass trim, four brass
    corner posts capped with violet crystals, a brass cog ring around a raised violet core socket on top."""
    els = [
        _el([0, 0, 0], [16, 3, 16], "#side", "#top_base"),
        _el([1, 3, 1], [15, 9, 15], "#side", "#top_base"),
        _el([0.5, 9, 0.5], [15.5, 11, 15.5], "#brass"),
        _el([2, 11, 2], [14, 12.5, 14], "#side", "#top"),
    ]
    for (x, z) in ((0, 0), (13, 0), (0, 13), (13, 13)):
        els.append(_el([x, 3, z], [x + 3, 13, z + 3], "#brass"))
        els.append(_el([x + 0.75, 13, z + 0.75], [x + 2.25, 15, z + 2.25], "#crystal",
                       rot={"angle": 45, "axis": "y", "origin": [x + 1.5, 14, z + 1.5]}))
    # the raised core socket and its cog teeth
    els.append(_el([6, 12.5, 6], [10, 14, 10], "#brass", "#crystal"))
    els.append(_el([6.5, 14, 6.5], [9.5, 15.5, 9.5], "#crystal", rot={"angle": 45, "axis": "y", "origin": [8, 14.75, 8]}))
    textures = {"side": "iss_technomancy:block/clockwork_altar_side", "top": "iss_technomancy:block/clockwork_altar_top",
                "top_base": "iss_technomancy:block/clockwork_altar_bottom", "brass": "iss_technomancy:block/clockwork_altar_brass",
                "crystal": "iss_technomancy:block/clockwork_altar_crystal", "particle": "iss_technomancy:block/clockwork_altar_side"}
    return {"parent": "block/block", "textures": textures, "elements": els}


def write_all(out, write_json):
    book(1).save(out("textures/item/spell_book_models/clockwork_spellbook.png"))
    book(2).save(out("textures/item/spell_book_models/clockwork_codex.png"))
    for name, im in altar_textures().items():
        im.save(out("textures/block/%s.png" % name))
    write_json("models/block/clockwork_altar.json", altar_model())
