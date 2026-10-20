"""
Iron's Technomancy 1.10: the two spellbooks' 3D model textures (the layout of irons_spellbooks:item/
template_spell_book_model, 64x64: outer cover 10x7 at (0,9), inner cover at (11,9), cover edges, spine at
(10..14, 21..31), pages at (12..32, 16..21) and (20..24, 8..16)), more detailed than 1.9 and ANIMATED (6 frames): the
gem on the cover breathes and a glint runs along the brass/gold trim; the hextech codex's glyph line flickers.
"""
import math

from PIL import Image

from premium import MAT

B, BD, WAL, CRM, NAV, LEA = (MAT[k] for k in ("brass", "brass_dark", "walnut", "cream", "navy", "leather"))
AMB, CYA = MAT["amber_glow"], MAT["cyan_glow"]
FRAMES = 6


def r(mat, t):
    return mat.ramp[max(0, min(len(mat.ramp) - 1, int(round(t * (len(mat.ramp) - 1)))))]


def fill(img, x0, y0, x1, y1, fn):
    for y in range(y0, y1):
        for x in range(x0, x1):
            img.putpixel((x, y), fn(x - x0, y - y0, x1 - x0, y1 - y0))


def book(tier, f):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    cover, frame, gem = (LEA, B, AMB) if tier == 1 else (NAV, B, CYA)
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * f / FRAMES)
    glint = f * 3 - 2

    def outer(i, j, w, h):
        edge = i in (0, w - 1) or j in (0, h - 1)
        corner = (i in (0, 1, w - 2, w - 1)) and (j in (0, 1, h - 2, h - 1))
        if corner:
            return r(frame, 0.95 if (i + j) % 2 == 0 else 0.7)
        if edge:
            lit = abs((i + j) - glint) <= 0 and j == 0
            return r(frame, 1.0 if lit else (0.6 if (i == 0 or j == 0) else 0.35))
        cx, cy = (w - 1) / 2, (h - 1) / 2
        d = abs(i - cx) + abs(j - cy) * 1.2
        if d <= 1.0:
            return r(gem, 0.75 + 0.25 * pulse - 0.15 * (i - cx + j - cy))
        if d <= 2.0:
            return r(frame, 0.75 - 0.1 * (i - cx + j - cy))
        if tier == 2 and abs(j - cy) < 0.6:
            return r(CYA, 0.55 + 0.4 * (((i + f) % 3) == 0))
        if tier == 1 and abs(i - cx) < 0.6:
            return r(frame, 0.45)
        return r(cover, 0.55 - 0.12 * j / h + (0.06 if (i * 3 + j) % 5 == 0 else 0))
    fill(img, 0, 9, 10, 16, outer)
    # inner cover: endpaper with a printed cog / hextech diagram
    def inner(i, j, w, h):
        cx, cy = (w - 1) / 2, (h - 1) / 2
        d = math.hypot(i - cx, (j - cy) * 1.3)
        if 1.6 < d < 2.6:
            return r(frame, 0.55)
        return r(CRM, 0.55 - 0.08 * (j / h)) if tier == 1 else r(NAV, 0.35 + 0.05 * ((i + j) % 2))
    fill(img, 11, 9, 21, 16, inner)
    fill(img, 10, 9, 11, 16, lambda i, j, w, h: r(frame, 0.5))
    fill(img, 21, 9, 22, 16, lambda i, j, w, h: r(frame, 0.5))
    fill(img, 0, 16, 2, 26, lambda i, j, w, h: r(cover, 0.45 - 0.2 * i))
    # spine: raised bands every 3 rows, a glint travelling down it
    fill(img, 10, 21, 14, 31, lambda i, j, w, h: r(frame, 1.0 if j == (f * 2) % 10 and j % 3 == 1 else (0.8 if j % 3 == 1 else 0.3)) if j % 3 == 1
         else r(cover, 0.45 - 0.12 * (i % 2)))
    fill(img, 0, 31, 24, 32, lambda i, j, w, h: r(frame, 0.6))
    # pages: lines of text, a gilded edge
    fill(img, 12, 16, 32, 21, lambda i, j, w, h: r(frame, 0.8) if j in (0, h - 1) else r(CRM, 0.85 if j % 2 == 0 else 0.62))
    fill(img, 20, 8, 24, 16, lambda i, j, w, h: r(CRM, 0.8 if i % 2 == 0 else 0.62) if 0 < j < h - 1 else r(frame, 0.75))
    return img


def strip(tier):
    s = Image.new("RGBA", (64, 64 * FRAMES), (0, 0, 0, 0))
    for f in range(FRAMES):
        s.paste(book(tier, f), (0, 64 * f))
    return s


def write_all(out, write_json):
    for tier, name in ((1, "clockwork_spellbook"), (2, "clockwork_codex")):
        strip(tier).save(out("textures/item/spell_book_models/%s.png" % name))
        write_json("textures/item/spell_book_models/%s.png.mcmeta" % name, {"animation": {"frametime": 4, "interpolate": False}})
