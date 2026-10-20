"""
Iron's Technomancy 1.9 spell icons, effect icons, rune and the animated upgrade orb - 32x32, "Premium Fantasy".
Spell icons keep the 1.8 framing (dark plate in a brass frame with corner rivets) so they read as one school.
"""
import math

from PIL import Image

from premium import MAT, Canvas, Mat, capsule, circle, diamond, ellipse, ellipse_ring, gear, hue_ramp, minus, poly, rect, ring, union

B, BD, CU, IRN, NAV, AND = (MAT[k] for k in ("brass", "brass_dark", "copper", "iron", "navy", "andesite"))
AMB, CYA, VIO, WIN, STL = MAT["amber_glow"], MAT["cyan_glow"], MAT["violet_glow"], MAT["wine"], MAT["steel_blade"]
PANEL = Mat(hue_ramp("#24180F", 7, 0.03, 0.32, shift=0.04), base=0.5, spread=0.4, gloss=0.0, dither=True)
STEAM = Mat(hue_ramp("#C8CDD4", 6, 0.45, 0.98, shift=0.03), base=0.6, spread=0.45, gloss=0.1)
RED = Mat(hue_ramp("#C8302C", 7, 0.1, 0.9, shadow_hue=0.85, light_hue=0.08), base=0.55, spread=0.55, gloss=0.4)
FIRE = Mat(hue_ramp("#FF6A10", 7, 0.25, 0.98, shadow_hue=0.98, light_hue=0.14, sat_curve=0.0), glow=True, base=0.7, spread=0.4, gloss=0.4)


def framed(draw):
    def make():
        c = Canvas()
        c.add(rect(0, 0, 32, 32), PANEL, bevel=6, tone=0.05)
        c.add(minus(rect(0, 0, 32, 32), rect(2.2, 2.2, 29.8, 29.8)), B, bevel=1.0)
        for x, y in ((3.6, 3.6), (28.4, 3.6), (3.6, 28.4), (28.4, 28.4)):
            c.add(circle(x, y, 1.1), B, bevel=0.8, tone=0.25)
        draw(c)
        return c
    return make


def _arc(c, x0, y0, x1, y1, seed, mat=CYA, segs=6, jit=2.2):
    import random
    r = random.Random(seed)
    pts = [(x0, y0)]
    for i in range(1, segs):
        t = i / segs
        pts.append((x0 + (x1 - x0) * t + r.uniform(-jit, jit), y0 + (y1 - y0) * t + r.uniform(-jit, jit)))
    pts.append((x1, y1))
    for (a, b), (cc, d) in zip(pts, pts[1:]):
        c.add(capsule(a, b, cc, d, 0.9), mat, flat=True, tone=0.05)
    for (a, b), (cc, d) in zip(pts, pts[1:]):
        c.line(a, b, cc, d, mat.ramp[6], mat)


def arc_welder(c):
    c.add(capsule(6, 26, 13, 19, 2.6), IRN, bevel=1.4)
    c.add(capsule(11.5, 20.5, 15.5, 16.5, 2.0), B, bevel=1.2)
    c.add(capsule(14.5, 17.5, 17, 15, 1.1), CU, bevel=0.8)
    _arc(c, 17, 15, 26, 6, 3)
    for x, y in ((24, 9), (21, 6), (27, 11)):
        c.sparkle(x, y, CYA)
    c.sparkle(26, 5, AMB, big=True)


def assemble_automaton(c):
    c.add(rect(9, 7, 23, 19), B, bevel=2.2)
    c.add(rect(11, 10, 21, 14), PANEL, flat=True, tone=-0.1)
    for x in (13.5, 18.5):
        c.add(circle(x, 12, 1.6), AMB, dome=0.8)
    c.add(rect(12, 16, 20, 17.2), BD, flat=True)
    c.add(rect(7, 20, 25, 28), B, bevel=2, tone=-0.08)
    c.add(gear(16, 24, 3.4, 2.5, 8), CU, bevel=1.2)
    c.add(circle(16, 24, 1.1), AMB, dome=0.5)
    c.add(capsule(16, 7, 16, 4, 0.8), IRN, bevel=0.6)
    c.add(circle(16, 3.8, 1.3), AMB, dome=0.6)


def deploy_brass_sentry(c):
    for (a, b) in (((16, 19), (8, 28)), ((16, 19), (24, 28)), ((16, 19), (16, 28))):
        c.add(capsule(a[0], a[1], b[0], b[1], 1.0), IRN, bevel=0.8)
    c.add(ellipse(15, 15, 6.5, 5.5), B, bevel=2, dome=0.4)
    c.add(capsule(18, 13, 27, 9, 1.8), BD, bevel=1.1)
    c.add(circle(27.2, 9, 1.4), AMB, dome=0.6)
    c.add(circle(14, 14, 1.8), AMB, dome=0.8)
    c.sparkle(29, 6, AMB)


def emp_screech(c):
    c.add(poly([(5, 12), (10, 12), (15, 7), (15, 25), (10, 20), (5, 20)]), IRN, bevel=1.6)
    c.add(rect(5, 12, 10, 20), B, bevel=1.2)
    for k, r in enumerate((6.5, 10.0, 13.5)):
        c.add(lambda x, y, r=r: r - 0.9 <= math.hypot(x - 13, y - 16) <= r + 0.9 and x > 16 and abs(y - 16) < (x - 13) * 1.1, CYA, flat=True, tone=0.1 - 0.08 * k)
    c.sparkle(27, 6, CYA)
    c.sparkle(27, 26, CYA)


def gear_barrage(c):
    for (x, y, r, t) in ((10, 21, 7.0, 0), (21.5, 11, 5.6, 0.2), (24.5, 24, 4.2, 0.1)):
        c.add(capsule(x - r * 1.25, y + r * 1.25, x - r * 0.7, y + r * 0.7, r * 0.22), AMB, flat=True, tone=-0.3)
        c.add(gear(x, y, r, r * 0.76, 8, hole=r * 0.28, phase=t, tooth=0.42), B, bevel=1.8)
        c.add(circle(x, y, r * 0.28), AMB, dome=0.5)
    c.sparkle(26, 6, AMB, big=True)


def magnetic_field(c):
    c.add(ellipse_ring(16, 22, 12, 4.4, 1.4), CYA, flat=True)
    c.add(ellipse_ring(16, 22, 8, 2.8, 1.2), CYA, flat=True, tone=-0.15)
    m = minus(ellipse(16, 12, 8, 8), ellipse(16, 12, 4, 4))
    c.add(lambda x, y: m(x, y) and y <= 13, RED, bevel=1.6)
    c.add(union(rect(8, 12, 12, 19), rect(20, 12, 24, 19)), RED, bevel=1.4)
    c.add(union(rect(8, 17, 12, 20), rect(20, 17, 24, 20)), STL, bevel=1)
    c.sparkle(5, 7, CYA)
    c.sparkle(27, 7, CYA)


def overdrive_protocol(c):
    c.add(gear(16, 18, 10, 7.8, 10, hole=4.2), B, bevel=2)
    c.add(poly([(16, 4), (23, 12), (19, 12), (19, 19), (13, 19), (13, 12), (9, 12)]), FIRE, bevel=1.6)
    c.add(circle(16, 18, 3.8), AMB, dome=0.8)
    c.sparkle(6, 6, FIRE)
    c.sparkle(27, 27, AMB)


def rocket_grab(c):
    c.add(capsule(4, 24, 10, 22, 2.2), FIRE, flat=True, tone=-0.1)
    for k in range(4):
        c.add(circle(8 + k * 2.3, 21.5 - k * 0.6, 0.9), IRN, bevel=0.6)
    c.add(poly([(13, 17), (22, 12), (27, 14), (27, 21), (22, 24), (13, 22)]), B, bevel=2)
    for y in (13.5, 16.5, 19.5):
        c.add(capsule(26, y, 29, y, 0.9), B, bevel=0.6, tone=0.1)
    c.add(circle(18, 19, 1.4), AMB, dome=0.5)
    c.sparkle(5, 28, FIRE)


def steam_vent(c):
    c.add(rect(5, 21, 18, 26), CU, bevel=1.4)
    c.add(rect(15, 18, 20, 28), B, bevel=1.2)
    c.add(gear(12, 19, 3, 2.1, 6), IRN, bevel=1)
    for (x, y, r) in ((21, 14, 4.2), (25, 9, 3.6), (18, 9, 3.0), (27, 16, 2.6)):
        c.add(circle(x, y, r), STEAM, dome=0.8)


def summon_tech_drake(c):
    head = poly([(4, 20), (12, 12), (22, 10), (28, 13), (27, 17), (20, 19), (18, 24), (8, 26)])
    c.add(head, NAV, bevel=2.2)
    c.add(poly([(17, 19), (27, 17), (26, 20), (18, 23)]), NAV, bevel=1, tone=-0.3)
    for (a, b) in (((14, 12), (8, 4)), ((19, 11), (16, 3))):
        c.spike(a[0], a[1], b[0], b[1], B, width=2.8)
    c.add(diamond(19, 14, 1.8, 1.0), CYA, flat=True, tone=0.2)
    for x in (20, 22.5, 25):
        c.spike(x, 18.5, x - 0.6, 21, STL, width=1.2)
    c.sparkle(27, 6, CYA, big=True)


SPELLS = {"arc_welder": arc_welder, "assemble_automaton": assemble_automaton, "deploy_brass_sentry": deploy_brass_sentry,
          "emp_screech": emp_screech, "gear_barrage": gear_barrage, "magnetic_field": magnetic_field,
          "overdrive_protocol": overdrive_protocol, "rocket_grab": rocket_grab, "steam_vent": steam_vent,
          "summon_tech_drake": summon_tech_drake}


# ---- effect icons (32x32, no frame)

def eff_overdrive():
    c = Canvas()
    c.add(gear(16, 16, 13, 10.4, 10, hole=5), B, bevel=2)
    c.add(poly([(18, 4), (10, 17), (15, 17), (13, 28), (22, 14), (17, 14)]), FIRE, bevel=1.5)
    c.sparkle(5, 5, FIRE)
    return c


def eff_short_circuit():
    c = Canvas()
    c.add(circle(16, 16, 12), NAV, bevel=3, dome=0.4)
    _arc(c, 8, 9, 24, 23, 7)
    _arc(c, 22, 8, 10, 24, 11, mat=VIO, segs=5)
    c.sparkle(27, 5, CYA)
    return c


def eff_focus():
    c = Canvas()
    c.add(gear(16, 16, 13.4, 10.8, 12, hole=6.4), B, bevel=2)
    c.add(poly([(10, 9), (22, 9), (17, 16), (22, 23), (10, 23), (15, 16)]), CYA, bevel=1.4)
    c.sparkle(27, 5, CYA, big=True)
    return c


def eff_power():
    c = Canvas()
    for k in range(6):
        a = k * math.pi / 3
        c.spike(16 + math.cos(a) * 6, 16 + math.sin(a) * 6, 16 + math.cos(a) * 14, 16 + math.sin(a) * 14, VIO, width=3)
    c.add(diamond(16, 16, 6.5, 9), VIO, bevel=2.5)
    c.add(diamond(14.5, 13, 1.6, 2.6), VIO, flat=True, tone=0.35)
    c.sparkle(27, 27, CYA)
    return c


def rune():
    """Technomancy rune: an andesite tablet in a brass rim, an engraved cog glyph glowing amber."""
    c = Canvas()
    tab = poly([(7, 3), (25, 3), (28, 7), (28, 26), (24, 30), (8, 30), (4, 26), (4, 7)])
    c.add(tab, AND, bevel=2.6)
    c.add(minus(tab, poly([(8.5, 5.5), (23.5, 5.5), (25.5, 8), (25.5, 25), (23, 27.5), (9, 27.5), (6.5, 25), (6.5, 8)])), B, bevel=1.2)
    g = gear(16, 16.5, 7, 5.4, 8, hole=2.6)
    c.add(g, AMB, flat=True, tone=-0.05)
    c.add(minus(gear(16, 16.5, 5.6, 4.0, 8, hole=3.4), circle(16, 16.5, 0)), AND, flat=True, tone=-0.25)
    c.add(circle(16, 16.5, 1.6), AMB, dome=0.6)
    c.sparkle(27, 3, AMB)
    return c


def orb_frames(n=8):
    """Upgrade orb (animated strip): an amber energy sphere turning inside a brass cog cage."""
    frames = []
    for f in range(n):
        c = Canvas()
        ph = f / n
        c.add(circle(16, 16, 11.5), AMB, dome=1.0, tone=-0.05)
        for k in range(3):
            a = 2 * math.pi * (ph + k / 3)
            c.add(ellipse_ring(16, 16, 9 * abs(math.cos(a)) + 0.6, 9, 1.1), CU, flat=True, tone=-0.1 + 0.1 * k)
        c.add(ring(16, 16, 11.6, 13.4), B, bevel=1.0)
        c.add(gear(16, 16, 15.2, 13.0, 12, hole=13.0, phase=ph), B, bevel=1.0)
        c.add(circle(12.5, 12, 2.0), AMB, flat=True, tone=0.4)
        frames.append(c.render())
    strip = Image.new("RGBA", (32, 32 * n), (0, 0, 0, 0))
    for k, im in enumerate(frames):
        strip.paste(im, (0, 32 * k))
    return strip


EFFECTS = {"overdrive": eff_overdrive, "short_circuit": eff_short_circuit, "evolved_focus": eff_focus, "evolved_power": eff_power}


def write_all(out):
    for name, draw in SPELLS.items():
        framed(draw)().render().save(out("textures/gui/spell_icons/%s.png" % name))
    for name, fn in EFFECTS.items():
        fn().render().save(out("textures/mob_effect/%s.png" % name))
    rune().render().save(out("textures/item/technomancy_rune.png"))
    orb_frames().save(out("textures/item/upgrade_orb_technomancy.png"))


def sheet(path, scale=4):
    imgs = [framed(d)().render() for d in SPELLS.values()] + [fn().render() for fn in EFFECTS.values()] + [rune().render(), orb_frames().crop((0, 0, 32, 32))]
    cols = 8
    rows = (len(imgs) + cols - 1) // cols
    W = Image.new("RGBA", (cols * 36 * scale, rows * 36 * scale), (139, 139, 139, 255))
    for k, im in enumerate(imgs):
        W.alpha_composite(im.resize((32 * scale, 32 * scale), Image.NEAREST), ((k % cols) * 36 * scale + 8, (k // cols) * 36 * scale + 8))
    W.save(path)


if __name__ == "__main__":
    import sys
    sheet(sys.argv[1])
