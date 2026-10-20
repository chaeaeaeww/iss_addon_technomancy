"""
Iron's Technomancy 1.10 icons at Iron's Spells' own size, 16x16, "Premium Fantasy" preset scaled down:

- the 10 spell icons, full-bleed painted squares like ISS's (a glowing subject on a dark, coloured, vignetted
  ground), redrawn from the user's references (composition only, nothing traced): Rocket Grab = a golden mechanical
  hand on a chain flying out of a cyan streak; Summon Tech Drake = a gold-armoured dragon head with blue crystal horns;
  Gear Barrage = clear flying cogwheels; Assemble Automaton = the golden Blitz robot crackling with lightning;
  EMP Screech = a cut cable shorting out; Overdrive Protocol = a big "level up" triple chevron; Deploy Brass Sentry =
  a brass turret on its legs over a glowing summoning circle; Arc Welder, Magnetic Field, Steam Vent: their own motifs;
- the technomancy rune (an ISS rune: a grey stone tablet, the school's glyph - a cog - in its colour);
- the upgrade orb (8 frames: a brass-gold orb with a cogwheel turning round it);
- the Hextech upgrade template (a vanilla-style template tablet with the upgrade arrow, hextech navy/brass/cyan);
- the two spellbook icons (ISS-style closed books seen at an angle) and the technomancy scroll.
"""
import math

from PIL import Image

from premium import MAT, Canvas, Mat, capsule, circle, diamond, ellipse, ellipse_ring, gear, hue_ramp, minus, poly, rect, ring, union

N = 16
B, BD, CU, IRN, NAV, AND, CRM = (MAT[k] for k in ("brass", "brass_dark", "copper", "iron", "navy", "andesite", "cream"))
AMB, CYA, VIO, WIN, STL, LEA = MAT["amber_glow"], MAT["cyan_glow"], MAT["violet_glow"], MAT["wine"], MAT["steel_blade"], MAT["leather"]
GOLD = Mat(hue_ramp("#E0B040", 8, 0.08, 0.97, shadow_hue=0.05, light_hue=0.15), base=0.6, spread=0.65, gloss=0.4)
# small-icon gold: lighter and flatter (at 16 px nearly every pixel is near an edge, so the full bevel goes muddy)
GOLD_S = Mat(hue_ramp("#E8B848", 8, 0.2, 0.98, shadow_hue=0.05, light_hue=0.15), base=0.62, spread=0.35, gloss=0.3)
RED = Mat(hue_ramp("#D03028", 7, 0.1, 0.9, shadow_hue=0.85, light_hue=0.06), base=0.55, spread=0.55, gloss=0.4)
FIRE = Mat(hue_ramp("#FF7A18", 7, 0.25, 0.98, shadow_hue=0.98, light_hue=0.14, sat_curve=0.0), glow=True, base=0.72, spread=0.4, gloss=0.4)
STEAM = Mat(hue_ramp("#D0D6DE", 6, 0.5, 0.99, shift=0.03), base=0.7, spread=0.4, gloss=0.1)
STONE = Mat(hue_ramp("#8A8E94", 7, 0.12, 0.85, shift=0.03), base=0.52, spread=0.5, gloss=0.1)
RUBBER = Mat(hue_ramp("#3A3440", 6, 0.04, 0.5), base=0.45, spread=0.5, gloss=0.3)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ground(inner, outer, cx=8.0, cy=8.0, streak=None, seed=0):
    """Painted icon ground: a radial glow from `inner` at (cx, cy) to `outer`, darker toward the corners, a little
    dithered texture; `streak` (angle deg, colour) adds diagonal speed streaks."""
    a, b = rgb(inner), rgb(outer)
    img = Image.new("RGBA", (N, N))
    for y in range(N):
        for x in range(N):
            d = min(1.0, math.hypot(x + 0.5 - cx, y + 0.5 - cy) / 10.5)
            t = (1 - d) ** 1.4
            c = [b[i] + (a[i] - b[i]) * t for i in range(3)]
            corner = max(abs(x - 7.5), abs(y - 7.5)) / 7.5
            k = 1 - 0.28 * max(0.0, corner - 0.6) / 0.4 + (((x * 7 + y * 13 + seed) % 5) - 2) * 0.018
            img.putpixel((x, y), tuple(int(max(0, min(255, v * k))) for v in c) + (255,))
    if streak:
        ang, col = streak
        col = rgb(col)
        dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        for k, off in enumerate((-5, -2, 1, 4, 7)):
            for s in range(-12, 12):
                x = 8 + dx * s - dy * off
                y = 8 + dy * s + dx * off
                xi, yi = int(x), int(y)
                if 0 <= xi < N and 0 <= yi < N and (s + k * 3) % 7 < 4:
                    p = img.getpixel((xi, yi))
                    w = 0.45 if (s + k * 3) % 7 < 2 else 0.25
                    img.putpixel((xi, yi), tuple(int(p[i] + (col[i] - p[i]) * w) for i in range(3)) + (255,))
    return img


def over(base, c, outline=True):
    img = base.copy()
    img.alpha_composite(c.render(outline=outline))
    return img


def sprite(grid, pal):
    """A hand-placed 16x16 pixel sprite: one character per pixel, '.' clear."""
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), pal[ch] + (255,))
    return img


def bolt(c, pts, mat=CYA):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        c.add(capsule(x0, y0, x1, y1, 0.55), mat, flat=True, tone=0.2)


# ------------------------------------------------------------------------------------------- spells

def rocket_grab():
    g = ground("#3FD8F0", "#062A3A", 10, 6, streak=(-38, "#9AF6FF"))
    pal = {"K": (40, 22, 6), "o": (150, 96, 28), "g": (214, 160, 58), "G": (250, 214, 120), "W": (255, 246, 200),
           "s": (196, 204, 220), "S": (120, 128, 146), "d": (58, 62, 76)}
    hand = sprite([
        "..........KK....",
        "......KK.KGgK...",
        ".....KGgKKGgK.KK",
        ".....KGgKKGgKKGK",
        ".....KGgKKGgKKgK",
        "..KK.KGgKKGgKGgK",
        ".KGgKKGggGggGGoK",
        ".KgGGKGGWGGGGgoK",
        "..KgGGGGGGGGgooK",
        "...KgGGGGGGgooK.",
        "....KoggggggoK..",
        "...KdSSssSSdK...",
        "..KsdKdddddK....",
        ".KSdK.KK........",
        "KSKsdKSK........",
        "KK.KK.KK........",
    ], pal)
    g.alpha_composite(hand)
    return g


def summon_tech_drake():
    g = ground("#3A6CFF", "#060A26", 9, 8, seed=3)
    pal = {"K": (10, 12, 34), "N": (40, 60, 128), "n": (22, 32, 76), "G": (250, 222, 130), "g": (220, 166, 62), "o": (150, 98, 30),
           "C": (170, 240, 255), "c": (60, 170, 255), "b": (24, 84, 200), "W": (236, 240, 255), "E": (200, 255, 255), "e": (60, 200, 255)}
    head = sprite([
        "................",
        ".b..............",
        ".cb.....b.......",
        "..Cb....cb......",
        "..cCb..cCb......",
        "...KCbKCcKKK....",
        "..KgGGgGGGggKK..",
        ".KnoggGGGGGGGgKK",
        ".KNNoEeNNNNgGGgK",
        "KNNNNNNNNNNNNNNK",
        "KNNNNnKWKWKWKWK.",
        "KNNNNnK.........",
        "KNNNNnKKWKWKWK..",
        "KnNNNNNNNNNNNNK.",
        ".KnnNNNNNNNNKK..",
        "..KKnnnnKKKK....",
    ], pal)
    g.alpha_composite(head)
    return g


def gear_barrage():
    g = ground("#3A2A6A", "#06040E", 5, 10, streak=(200, "#FFB040"), seed=5)
    c = Canvas(N)
    # three bright brass cogwheels flying out (toothed discs with a dark axle hole)
    for (x, y, ro, rr, t, ph, tone) in ((6.2, 9.4, 5.8, 4.5, 8, 0.0, 0.18), (12.6, 4.0, 3.4, 2.5, 6, 0.3, 0.25), (13.0, 12.8, 2.8, 2.1, 6, 0.1, 0.1)):
        c.add(gear(x, y, ro, rr, t, hole=max(0.7, rr * 0.28), phase=ph), GOLD_S, bevel=0.7, tone=tone)
    c.sparkle(2, 2, AMB)
    return over(g, c)


def assemble_automaton():
    g = ground("#7A3CFF", "#12052C", 8, 8, seed=7)
    c = Canvas(N)
    bolt(c, [(1, 4), (3, 6), (2, 8), (4, 11)])
    bolt(c, [(15, 3), (13, 6), (14.5, 8), (12.5, 11)])
    # legs, the round golden body, little head with two blue eyes, long arms with big hands
    c.add(rect(5.5, 12.5, 7, 15.5), IRN, bevel=0.6)
    c.add(rect(9, 12.5, 10.5, 15.5), IRN, bevel=0.6)
    c.add(capsule(3.5, 7.5, 2.8, 12.5, 1.1), GOLD, bevel=0.8, tone=-0.1)
    c.add(capsule(12.5, 7.5, 13.2, 12.5, 1.1), GOLD, bevel=0.8, tone=-0.1)
    c.add(ellipse(8, 9.2, 4.6, 4.0), GOLD, bevel=1.8)
    c.add(rect(5.8, 3.0, 10.2, 6.4), GOLD, bevel=0.9, tone=0.05)
    c.add(rect(6.4, 4.0, 9.6, 5.4), IRN, flat=True, tone=-0.3)
    c.px(7, 4, CYA.ramp[-1], CYA)
    c.px(9, 4, CYA.ramp[-1], CYA)
    c.add(circle(8, 9.8, 1.8), CYA, dome=0.5)
    c.px(8, 2, CYA.ramp[-2], CYA)
    return over(g, c)


def emp_screech():
    g = ground("#3AB8F0", "#060E1A", 8, 8, seed=11)
    pal = {"K": (14, 12, 20), "r": (52, 48, 62), "R": (96, 90, 112), "c": (200, 110, 60), "C": (250, 176, 112), "y": (255, 230, 120),
           "w": (255, 255, 255), "b": (130, 226, 255)}
    cable = sprite([
        "................",
        "............KKK.",
        "..........KKRrrK",
        ".........KRRrrK.",
        "........KRrrrK..",
        ".......KcRrrK...",
        "......KCcKKK.y..",
        "....b..Cc..ywy..",
        ".....by...y.y...",
        "...KK.ywyb......",
        "..KccK.y........",
        ".KRrcCK.........",
        "KRRrrK..........",
        "KRrrK...........",
        "KrrK............",
        ".KK.............",
    ], pal)
    g.alpha_composite(cable)
    return g


def overdrive_protocol():
    g = ground("#FF7A18", "#200802", 8, 7, seed=13)
    # a big "level up": three thick stacked upward chevrons (pixel-placed), brightest at the top
    K = (70, 14, 4, 255)
    shades = [((255, 250, 220), (255, 214, 96)), ((255, 214, 96), (255, 140, 36)), ((255, 150, 40), (214, 64, 20))]
    for c_i, apex in enumerate((0, 5, 10)):
        hi, lo = shades[c_i]
        for k in range(6):
            y = apex + k
            if y >= N:
                break
            for side in (-1, 1):
                x0 = 7 if side < 0 else 8
                xs = [x0 + side * (k + j) for j in (-1, 0, 1, 2)]
                cols = [K, hi + (255,), lo + (255,), K]
                if k == 0:
                    cols = [K, hi + (255,), hi + (255,), K]
                for x, col in zip(xs, cols):
                    if 0 <= x < N and not (k == 0 and col == K and (x in (7, 8))):
                        g.putpixel((x, y), col)
            if k == 0:
                g.putpixel((7, max(0, y - 1)) if y > 0 else (7, y), K) if y > 0 else None
    return g


def deploy_brass_sentry():
    g = ground("#C07020", "#120802", 8, 12, seed=17)
    c = Canvas(N)
    c.add(ellipse_ring(8, 13.4, 7.4, 2.3, 0.9), AMB, flat=True, tone=0.15)
    # tripod, the drum, the riveted housing with a cyan visor, the barrel pointing right, the steam stack
    for (x0, x1) in ((5.4, 2.6), (8.0, 8.0), (10.6, 13.4)):
        c.add(capsule(x0, 10.2, x1, 14.2, 0.7), IRN, bevel=0.5, tone=0.1)
    c.add(rect(5.0, 8.6, 11.0, 11.0), CU, bevel=0.8)
    c.add(rect(3.8, 3.4, 10.8, 9.0), GOLD, bevel=1.4)
    c.add(rect(10.0, 5.0, 15.0, 7.0), IRN, bevel=0.6, tone=0.15)
    c.add(rect(14.0, 4.4, 16.0, 7.6), BD, bevel=0.5)
    c.add(rect(5.0, 4.8, 8.6, 5.9), CYA, flat=True, tone=0.25)
    c.add(rect(3.0, 0.6, 4.6, 3.8), CU, bevel=0.5)
    c.sparkle(13, 1, AMB)
    return over(g, c)


def arc_welder():
    g = ground("#4AA8FF", "#04101E", 11, 6, seed=19)
    c = Canvas(N)
    c.add(capsule(1.5, 14.0, 6.5, 9.0, 1.4), CU, bevel=1.0)
    c.add(poly([(5.5, 8.5), (8.6, 5.4), (9.6, 6.4), (6.5, 9.5)]), IRN, bevel=0.8)
    c.add(rect(2.2, 12.0, 4.0, 14.0), B, bevel=0.6)
    bolt(c, [(9.2, 5.8), (11.0, 4.6), (10.6, 3.2), (12.8, 2.4)])
    bolt(c, [(9.2, 5.8), (11.6, 6.8), (13.4, 5.6)])
    c.sparkle(13, 3, CYA, big=True)
    c.sparkle(14, 9, AMB)
    c.sparkle(10, 10, AMB)
    return over(g, c)


def magnetic_field():
    g = ground("#2A5CDF", "#050716", 8, 6, seed=23)
    # field lines arcing over from pole to pole
    for r, col in ((6.6, (90, 200, 255)), (4.4, (190, 245, 255))):
        for k in range(64):
            a = math.pi + math.pi * k / 63
            x, y = int(round(7.5 + r * math.cos(a))), int(round(6.2 + r * 0.95 * math.sin(a)))
            if 0 <= x < N and 0 <= y < N:
                g.putpixel((x, y), col + (255,))
    pal = {"K": (24, 8, 12), "R": (240, 84, 72), "r": (190, 40, 36), "m": (110, 20, 24), "S": (226, 232, 244), "s": (140, 150, 170)}
    magnet = sprite([
        "................",
        "................",
        "................",
        "................",
        "................",
        "..KKKK....KKKK..",
        "..KSSK....KSSK..",
        "..KssK....KssK..",
        "..KRrK....KRrK..",
        "..KRrK....KRrK..",
        "..KRrrKKKKrRrK..",
        "..KmRrrrrrrRmK..",
        "...KmRRrrRRmK...",
        "....KKmmmmKK....",
        "................",
        "................",
    ], pal)
    g.alpha_composite(magnet)
    return g


def steam_vent():
    g = ground("#C88A60", "#1A0C06", 6, 10, seed=29)
    c = Canvas(N)
    for (x, y, r) in ((9.0, 6.8, 2.9), (12.4, 4.0, 2.6), (8.6, 2.6, 2.2), (13.6, 8.4, 1.8)):
        c.add(circle(x, y, r), STEAM, dome=0.8)
    c.add(rect(1.0, 10.0, 8.4, 13.4), CU, bevel=1.0)
    c.add(rect(6.4, 8.6, 9.0, 14.6), B, bevel=0.9)
    c.add(gear(3.6, 11.6, 1.6, 1.1, 6), IRN, bevel=0.6)
    return over(g, c)


SPELLS = {"rocket_grab": rocket_grab, "summon_tech_drake": summon_tech_drake, "gear_barrage": gear_barrage,
          "assemble_automaton": assemble_automaton, "emp_screech": emp_screech, "overdrive_protocol": overdrive_protocol,
          "deploy_brass_sentry": deploy_brass_sentry, "arc_welder": arc_welder, "magnetic_field": magnetic_field, "steam_vent": steam_vent}


# ------------------------------------------------------------------------------------------- items (ISS forms)

def rune():
    """ISS rune form: a grey stone tablet with a dark rim; the school's glyph (a cog) engraved and glowing in its
    brass-gold colour."""
    c = Canvas(N)
    tab = poly([(4.5, 1.5), (11.5, 1.5), (13, 3), (13, 13.5), (11.5, 15), (4.5, 15), (3, 13.5), (3, 3)])
    c.add(tab, STONE, bevel=1.6)
    c.add(gear(8, 8.6, 4.0, 3.0, 6, hole=0), STONE, flat=True, tone=-0.35)
    c.add(gear(8, 8.2, 3.6, 2.7, 6, hole=1.1), AMB, flat=True, tone=-0.05)
    return c.render()


def orb_frames(n=8):
    """ISS upgrade orb form, technomancy: a gold-amber energy orb with a brass cogwheel turning round it (8 frames)."""
    strip = Image.new("RGBA", (N, N * n), (0, 0, 0, 0))
    for f in range(n):
        c = Canvas(N)
        ph = f / n
        c.add(gear(8, 8, 7.8, 6.2, 8, hole=5.2, phase=ph), B, bevel=0.8, tone=0.05)
        c.add(circle(8, 8, 4.4), AMB, dome=1.0, tone=-0.05)
        a = 2 * math.pi * ph
        c.add(ellipse_ring(8, 8, 3.2 * abs(math.cos(a)) + 0.5, 3.2, 0.6), CU, flat=True, tone=0.1)
        c.px(6, 6, AMB.ramp[-1])
        strip.paste(c.render(), (0, N * f))
    return strip


def template():
    """Vanilla smithing template form (a tablet with the upgrade arrow), hextech colours: navy, brass rim, cyan arrow,
    brass cogs and blue crystal shards at the corners like the TravelOptics templates."""
    c = Canvas(N)
    tab = poly([(4, 1.5), (12.5, 1.5), (13.8, 3), (13.8, 14), (12.5, 15.2), (4, 15.2), (2.6, 14), (2.6, 3)])
    c.add(tab, NAV, bevel=1.4)
    c.add(minus(tab, poly([(4.6, 2.8), (11.9, 2.8), (12.6, 3.6), (12.6, 13.4), (11.9, 14.0), (4.6, 14.0), (3.8, 13.4), (3.8, 3.6)])), B, bevel=0.8)
    c.add(poly([(8.2, 3.6), (11.6, 7.6), (9.6, 7.6), (9.6, 12.2), (6.8, 12.2), (6.8, 7.6), (4.8, 7.6)]), CYA, bevel=1.0)
    c.add(gear(2.4, 2.4, 2.2, 1.5, 6, hole=0.6), B, bevel=0.7)
    c.spike(13.0, 3.0, 15.4, 0.4, CYA, width=1.6)
    c.spike(13.6, 4.6, 15.6, 3.6, CYA, width=1.2)
    return c.render()


def book(tier):
    """ISS spellbook icon form: a book lying flat seen from above and in front - the decorated cover on top, the page
    block (cream, with the lower board under it) as the visible thickness. Tier 1 clockwork: brown leather, brass
    corners and clasp, an amber gem in a cog; tier 2 hextech codex: navy, gold trim, a cyan crystal."""
    c = Canvas(N)
    cover, trim, gem = (LEA, B, AMB) if tier == 1 else (NAV, GOLD, CYA)
    TL, TR, BR, BL = (1.0, 5.6), (10.6, 1.2), (15.2, 7.0), (5.6, 11.4)
    off = 3.0
    # the lower board and the page block below the cover (the book's thickness)
    c.add(poly([TL, BL, BR, (BR[0], BR[1] + off), (BL[0], BL[1] + off), (TL[0], TL[1] + off)]), cover, bevel=0.8, tone=-0.25)
    c.add(poly([(TL[0] + 0.6, TL[1] + 1.0), (BL[0], BL[1] + 0.9), (BR[0] - 0.4, BR[1] + 0.9), (BR[0] - 0.4, BR[1] + 2.0),
                (BL[0], BL[1] + 2.0), (TL[0] + 0.6, TL[1] + 2.1)]), CRM, flat=True, tone=0.15)
    cov = poly([TL, TR, BR, BL])
    c.add(cov, cover, bevel=1.6, tone=0.05)
    inner = poly([(3.0, 5.7), (10.5, 2.5), (13.6, 6.8), (6.0, 10.0)])
    c.add(minus(cov, inner), trim, bevel=0.7)
    if tier == 1:
        c.add(gear(8.2, 6.2, 2.4, 1.7, 6, hole=0), B, bevel=0.6)
    c.add(diamond(8.2, 6.2, 1.6, 1.2), gem, dome=0.7)
    if tier == 2:
        c.sparkle(14, 1, CYA)
    return c.render()


def scroll():
    """ISS scroll form at 16x16: a cream parchment roll tied with a cord, the school's seal (technomancy brass cog)."""
    c = Canvas(N)
    c.add(poly([(2.0, 10.5), (10.5, 2.0), (14.0, 5.5), (5.5, 14.0)]), CRM, bevel=1.4)
    c.add(capsule(2.0, 10.6, 5.4, 14.0, 1.4), CRM, bevel=1.0, tone=-0.1)
    c.add(capsule(10.6, 2.0, 14.0, 5.4, 1.4), CRM, bevel=1.0, tone=-0.1)
    c.add(capsule(5.2, 7.8, 8.2, 10.8, 0.5), WIN, flat=True, tone=0.1)
    c.add(gear(9.2, 7.0, 2.2, 1.6, 6, hole=0.6), GOLD, bevel=0.8)
    return c.render()


# spell icons drawn by the user (source art in tools/art_src): taken as they are, sampled down to 32x32 (Iron's Spells
# draws a spell icon at 16 GUI px whatever the texture size, so 32x32 keeps the detail)
USER_ICONS = {"summon_tech_drake": "summon_tech_drake.webp"}


def user_icon(file, size=32):
    import os
    src = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "art_src", file)).convert("RGBA")
    return src.resize((size, size), Image.NEAREST)


def write_all(out):
    for name, fn in SPELLS.items():
        img = user_icon(USER_ICONS[name]) if name in USER_ICONS else fn()
        img.save(out("textures/gui/spell_icons/%s.png" % name))
    rune().save(out("textures/item/technomancy_rune.png"))
    orb_frames().save(out("textures/item/upgrade_orb_technomancy.png"))
    template().save(out("textures/item/hextech_upgrade_smithing_template.png"))
    book(1).save(out("textures/item/clockwork_spellbook.png"))
    book(2).save(out("textures/item/clockwork_codex.png"))
    scroll().save(out("textures/item/scroll_technomancy.png"))


def sheet(path, scale=6):
    ims = [(k, f()) for k, f in SPELLS.items()] + [("rune", rune()), ("orb", orb_frames().crop((0, 0, 16, 16))), ("template", template()),
                                                    ("book1", book(1)), ("book2", book(2)), ("scroll", scroll())]
    W = Image.new("RGBA", (len(ims) * (N * scale + 6), N * scale + 6), (139, 139, 139, 255))
    for i, (_, im) in enumerate(ims):
        W.alpha_composite(im.resize((N * scale, N * scale), Image.NEAREST), (i * (N * scale + 6) + 3, 3))
    W.save(path)
