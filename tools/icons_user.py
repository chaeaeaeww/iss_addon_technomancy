"""
The icons the user drew (sources in tools/art_src/user, copied from Techno/assets), turned into mod textures, all 32x32:
the ten spell icons, the rune, the scroll, the Hextech upgrade template, both spellbooks, the Technomancy upgrade orb
(animated, orb_anim.py), and the eight armour icons. Sources are large pixel-art renders: each is sampled down with
nearest-neighbour; item art has its background cut away (flood fill from the border), and stray specks removed.
The Tier 1 helmet, which loses its dark frame, gets its holes refilled and a dark outline round the silhouette.
Written last by generate_assets.premium_art, over every earlier icon.
"""
import os
from collections import Counter, deque

from PIL import Image

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art_src", "user")
SPELLS = {"arc_welder": "ars_spell_icons.png", "assemble_automaton": "assemble_automaton_spell_icons.png", "gear_barrage": "cogwheel_spell_icon.png",
          "emp_screech": "EMP_sreech_spell_icon.png", "magnetic_field": "magnetic_field_spell_icon.png",
          "overdrive_protocol": "Overdrive_protocol_spell_icons.png", "rocket_grab": "rocket_grab_spell_icon.jpg", "steam_vent": "steam_vent_spell_icon.png",
          "summon_tech_drake": "tech_dragon_summon_spell_icon.png", "deploy_brass_sentry": "turret_summon_spell_icon.png"}
ITEMS = {"technomancy_rune": ("technomancy_rune.png", 48), "scroll_technomancy": ("technomancy_scrolls_icon.png", 48),
         "hextech_upgrade_smithing_template": ("technomancy_upgrade_template.png", 90), "clockwork_spellbook": ("tier1_technomancy_spellbook.png", 160),
         "clockwork_codex": ("tier2_technomancy_spellbook.png", 160)}
SLOTS = ("helmet", "chestplate", "leggings", "boots")


def cut_background(im, tol=48):
    """Flood-fill from the border: pixels connected to the edge and close to one of the border's main colours (the
    background, and any thin frame line) become clear."""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    border = [px[x, y][:3] for x in range(w) for y in (0, 1, h - 2, h - 1)] + [px[x, y][:3] for y in range(h) for x in (0, 1, w - 2, w - 1)]
    common = [c for c, _ in Counter(tuple(v // 16 * 16 for v in c) for c in border).most_common(4)]
    seen = [[False] * w for _ in range(h)]
    q = deque([(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)])
    while q:
        x, y = q.popleft()
        if not (0 <= x < w and 0 <= y < h) or seen[y][x]:
            continue
        seen[y][x] = True
        r, g, b, a = px[x, y]
        if a == 0 or any(abs(r - c[0] - 8) + abs(g - c[1] - 8) + abs(b - c[2] - 8) <= tol for c in common):
            px[x, y] = (0, 0, 0, 0)
            q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return im


def square(im, pad=0.04):
    im = im.crop(im.getbbox())
    s = int(max(im.size) * (1 + pad))
    sq = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sq.paste(im, ((s - im.width) // 2, (s - im.height) // 2))
    return sq


def shrink(im, n=32):
    out = im.resize((n, n), Image.NEAREST)
    if out.mode == "RGBA" and out.getextrema()[3][0] == 0:
        px = out.load()
        seen = set()
        for y in range(n):
            for x in range(n):
                if px[x, y][3] == 0 or (x, y) in seen:
                    continue
                comp, q = [], [(x, y)]
                seen.add((x, y))
                while q:
                    cx, cy = q.pop()
                    comp.append((cx, cy))
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < n and 0 <= ny < n and (nx, ny) not in seen and px[nx, ny][3]:
                            seen.add((nx, ny))
                            q.append((nx, ny))
                if len(comp) < 4:
                    for cx, cy in comp:
                        px[cx, cy] = (0, 0, 0, 0)
    return out


def item(im, tol=48):
    return shrink(square(cut_background(im.resize((im.width // 2, im.height // 2), Image.NEAREST) if im.width > 600 else im, tol)))


def armour_t1(piece, slot):
    """Tier 1 armour: the dark frame goes. The helmet (option B) also gets its holes refilled and a dark outline."""
    half = piece.resize((piece.width // 2, piece.height // 2), Image.NEAREST).convert("RGBA")
    im = cut_background(half, 48)
    bb = im.getbbox()
    im, orig = im.crop(bb), half.crop(bb)
    inner = cut_background(im, 34)
    if slot != "helmet":
        return shrink(square(inner))
    w, h = inner.size
    px, op = inner.load(), orig.load()
    seen = [[False] * w for _ in range(h)]
    dq = deque([(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)])
    while dq:
        x, y = dq.popleft()
        if not (0 <= x < w and 0 <= y < h) or seen[y][x] or px[x, y][3]:
            continue
        seen[y][x] = True
        dq.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0 and not seen[y][x]:
                px[x, y] = op[x, y]
    out = shrink(square(inner))
    bp, n = out.load(), out.width
    edge = [(x, y) for y in range(n) for x in range(n) if bp[x, y][3] == 0 and any(
        0 <= x + dx < n and 0 <= y + dy < n and bp[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        bp[x, y] = (28, 16, 10, 255)
    return out


def icons():
    """{texture path under textures/: image}"""
    out = {}
    for name, f in SPELLS.items():
        out["gui/spell_icons/%s.png" % name] = Image.open(os.path.join(SRC, "spell_icons", f)).convert("RGBA").resize((32, 32), Image.NEAREST)
    for name, (f, tol) in ITEMS.items():
        out["item/%s.png" % name] = item(Image.open(os.path.join(SRC, "spell_stuffs", f)), tol)
    import orb_anim    # the upgrade orb: ISS's empty-orb stone with the Technomancy parts, animated (orb_anim.py)
    out["item/upgrade_orb_technomancy.png"] = orb_anim.strip_and_meta()[0]
    for tier, sheet, prefix in ((1, "tier1_technomancy_armors_icons.png", "clockwork_engineer_"), (2, "tier2_technomancy_armors_icons.png", "hextech_engineer_")):
        im = Image.open(os.path.join(SRC, "armors", sheet))
        for k, slot in enumerate(SLOTS):
            q = im.crop(((k % 2) * im.width // 2, (k // 2) * im.height // 2, (k % 2 + 1) * im.width // 2, (k // 2 + 1) * im.height // 2))
            out["item/%s%s.png" % (prefix, slot)] = item(q) if tier == 2 else armour_t1(q, slot)
    return out


def write_all(out, write_json):
    for path, im in icons().items():
        im.save(out("textures/" + path))
    import orb_anim
    write_json("textures/item/upgrade_orb_technomancy.png.mcmeta", orb_anim.strip_and_meta()[1])
    # the dragon core icon keeps its animation (icons_v8); nothing else here is animated
