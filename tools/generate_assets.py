"""
Generates every procedural asset of Iron's Technomancy: GeckoLib models/animations (entities and armor),
PlayerAnimator casting animations, item/spell/effect/particle textures. Run from the project root:

    python tools/generate_assets.py

Art style: Create-like steampunk (brass, copper, blackened iron, leather) with a cyan arcane core.
The art lives in tools/pixelart.py (palette + drawing helpers), tools/sprites.py (2D sprites),
tools/armor.py (Clockwork Engineer armor) and tools/models.py (entities).
Re-running overwrites the outputs, so remove an entry below before hand-editing its file in Blockbench.
Requires Pillow (pip install pillow).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import armor  # noqa: E402
import models  # noqa: E402
import models_v2  # noqa: E402
import sprites  # noqa: E402
import sprites_v2  # noqa: E402
import sprites_v3  # noqa: E402
import check_geo  # noqa: E402
import blitz_v3  # noqa: E402
import dragon_v5  # noqa: E402
import dragon_v5_anims  # noqa: E402
import dragon_v4_anims  # noqa: E402
import pylon_v4  # noqa: E402
import technomancer_v3  # noqa: E402
import v4_assets  # noqa: E402
import turrets_v7  # noqa: E402
import forge_v7  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources", "assets")
NS = os.path.join(ROOT, "iss_technomancy")


def out(path):
    full = os.path.join(NS, path) if not os.path.isabs(path) else path
    os.makedirs(os.path.dirname(full), exist_ok=True)
    return full


def write_json(path, data):
    with open(out(path), "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def kf(vector, easing=None):
    k = {"vector": vector}
    if easing:
        k["easing"] = easing
    return k


# ---------------------------------------------------------------------------------------------- entities

def entity(name, builder, mk2=False):
    geo, img, glow, anims = builder()
    moved = check_geo.fix_geo(geo, img)
    if moved:
        print("  %s: pulled %d coplanar faces apart (z-fighting)" % (name, moved))
    write_json("geo/entity/%s.geo.json" % name, geo)
    write_json("animations/entity/%s.animation.json" % name, anims)
    img.save(out("textures/entity/%s.png" % name))
    if glow.getbbox() is not None:
        glow.save(out("textures/entity/%s_glowmask.png" % name))
    if mk2:
        models.recolor_mk2(img).save(out("textures/entity/%s_mk2.png" % name))
        models.recolor_mk2(glow).save(out("textures/entity/%s_mk2_glowmask.png" % name))


def tech_dragon():
    """Tech Dragon v5: model + textures (normal and phase-two), every animation, and the per-tick attack points and
    hitbox regions the server reads (data/iss_technomancy/tech_dragon/parts.json) baked from the same animations."""
    D, geo, img, glw, img2, glw2 = dragon_v5.tech_dragon()
    img2.save(out("textures/entity/tech_dragon_overcharged.png"))
    img2_glow = glw2
    img2_glow.save(out("textures/entity/tech_dragon_overcharged_glowmask.png"))
    D.drained[0].save(out("textures/entity/tech_dragon_drained.png"))
    D.drained[1].save(out("textures/entity/tech_dragon_drained_glowmask.png"))
    anims, events = dragon_v4_anims.all_animations(D)
    parts = dragon_v4_anims.export_parts(D, anims)
    boxes = dragon_v5_anims.export_boxes(D, anims)
    parts["regions"] = boxes["regions"]
    for name, frames in boxes["animations"].items():
        parts["animations"][name]["boxes"] = frames
    data = os.path.join(ROOT, "..", "data", "iss_technomancy", "tech_dragon")
    os.makedirs(data, exist_ok=True)
    with open(os.path.join(data, "parts.json"), "w", encoding="utf-8", newline=chr(10)) as f:
        json.dump(parts, f, separators=(",", ":"))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tech_dragon_events.json"), "w", encoding="utf-8", newline=chr(10)) as f:
        json.dump(events, f, indent=1)
    return geo, img, glw, anims


def clockwork_armor():
    """1.10: the two mage sets after the user's concept sheets (armor_v7): Tier 1 steampunk clockwork mage, Tier 2
    hextech."""
    import armor_v7
    for name, fn in (("clockwork_engineer", armor_v7.clockwork), ("hextech_engineer", armor_v7.hextech)):
        geo, img, glow, anims = fn()
        write_json("geo/%s_armor.geo.json" % name, geo)
        write_json("animations/%s_armor.animation.json" % name, anims)
        img.save(out("textures/models/armor/%s.png" % name))
        glow.save(out("textures/models/armor/%s_glowmask.png" % name))


def clockwork_staff():
    """The tier-1 clockwork staff and (1.10) the one Hextech scepter model shared by its Evolution levels (the
    full design: rings, shards and crown)."""
    import staffs_v5
    staffs = [("clockwork_staff", staffs_v5.clockwork_staff()), ("hextech_staff", staffs_v5.hextech_staff(3))]
    for k in (1, 2, 3):
        for stale in ("geo/item/hextech_staff_%d.geo.json", "animations/item/hextech_staff_%d.animation.json", "textures/item/hextech_staff_%d.png",
                      "textures/item/hextech_staff_%d_glowmask.png"):
            if os.path.exists(out(stale % k)):
                os.remove(out(stale % k))
    for name, (geo, img, glow, anims) in staffs:
        write_json("geo/item/%s.geo.json" % name, geo)
        write_json("animations/item/%s.animation.json" % name, anims)
        img.save(out("textures/item/%s.png" % name))
        glow.save(out("textures/item/%s_glowmask.png" % name))


def premium_art():
    """1.9 "Premium Fantasy" 32x32 icons (ART_STYLE_PREMIUM_FANTASY.md): written last, over the older icons."""
    import icons_v5
    import icons_v6
    import icons_v6_spells
    icons_v6.write_all(out)
    icons_v6_spells.write_all(out)
    import books_altar_v6
    books_altar_v6.write_all(out, lambda path, data: None)
    for name in ("empty_slot_dragon_core", "empty_slot_scepter", "empty_slot_book"):
        icons_v5.ICONS[name]().save(out("textures/item/%s.png" % name))
    # 1.10: Iron's Spells-sized 16x16 icons (spells, rune, orb, template, books, scroll) and the reworked 32x32 items
    import icons_v7
    import icons_v8
    icons_v7.write_all(out)
    icons_v8.write_all(out, write_json)
    import dynamo_v7
    dynamo_v7.write_all(out, write_json)
    import books_v7
    books_v7.write_all(out, write_json)
    # the icons the user drew (tools/art_src/user) replace the generated ones
    import icons_user
    icons_user.write_all(out, write_json)
    for k in (1, 2, 3):
        stale = out("textures/item/hextech_scepter_star%d.png" % k)
        if os.path.exists(stale):
            os.remove(stale)


def v2_textures():
    sprites_v2.clockwork_staff_icon().save(out("textures/item/clockwork_scepter.png"))
    for kind in sprites_v2.MODULE_COLORS:
        for tier in (1, 2, 3):
            sprites_v2.module_icon(kind, tier).save(out("textures/item/module_%s_%d.png" % (kind, tier)))
    sprites_v2.dragon_core().save(out("textures/item/tech_dragon_core.png"))
    sprites_v2.dynamo_core().save(out("textures/item/overcharged_dynamo_core.png"))
    sprites_v2.codex_icon().save(out("textures/item/clockwork_codex.png"))
    sprites_v2.codex_model_texture().save(out("textures/item/spell_book_models/clockwork_codex.png"))
    sprites_v2.altar_top().save(out("textures/block/clockwork_altar_top.png"))
    sprites_v2.altar_side().save(out("textures/block/clockwork_altar_side.png"))
    sprites_v2.altar_bottom().save(out("textures/block/clockwork_altar_bottom.png"))
    sprites_v2.module_gui().save(out("textures/gui/staff_modules.png"))
    v4_assets.magnetic_dome().save(out("textures/entity/magnetic_field_dome.png"))
    sprites_v3.cable().save(out("textures/entity/rocket_hand_cable.png"))
    sprites_v3.magnetic_sigil(128).save(out("textures/entity/magnetic_field.png"))
    sprites_v3.magnetic_sigil(64, inner=True).save(out("textures/entity/magnetic_field_inner.png"))
    sprites_v3.icon_rocket_grab().save(out("textures/gui/spell_icons/rocket_grab.png"))
    sprites_v3.icon_magnetic_field().save(out("textures/gui/spell_icons/magnetic_field.png"))
    sprites_v3.icon_emp_screech().save(out("textures/gui/spell_icons/emp_screech.png"))
    sprites_v3.icon_summon_drake().save(out("textures/gui/spell_icons/summon_tech_drake.png"))
    sprites_v3.effect_short_circuit().save(out("textures/mob_effect/short_circuit.png"))


# ---------------------------------------------------------------------------------------------- Player casting animations

def player_animations():
    gear_flick = {
        "animation_length": 0.4,
        "bones": {
            "torso": {"rotation": {"0.0": kf([0, -15, 0]), "0.15": kf([0, -15, 0]), "0.25": kf([0, 10, 0], "easeOutBack"), "0.4": kf([0, 0, 0], "easeInOutSine")}},
            "body": {"position": {"0.0": kf([0, 0, 0]), "0.25": kf([0, -1, 0], "easeOutSine"), "0.4": kf([0, 0, 0])}},
            "right_arm": {
                "rotation": {"0.0": kf([-40, 30, 0]), "0.15": kf([-45, 35, 10], "easeInSine"), "0.25": kf([-90, -5, 0], "easeOutBack"), "0.4": kf([-80, 0, 0], "easeInOutSine")},
                "position": {"0.0": kf([0, 0, 1]), "0.25": kf([0, 0, -3], "easeOutBack"), "0.4": kf([0, 0, 0])},
            },
            "left_arm": {"rotation": {"0.0": kf([15, 0, -20]), "0.25": kf([25, 10, -30], "easeOutSine"), "0.4": kf([10, 5, -10])}},
        },
    }
    welder_channel = {
        "loop": True,
        "animation_length": 0.4,
        "bones": {
            "torso": {"rotation": {"0.0": kf([-5, 0, 0])}},
            "right_arm": {"rotation": {
                "0.0": kf([-85, -8, 0]), "0.1": kf([-87, -6, 2]), "0.2": kf([-84, -9, -1]), "0.3": kf([-86, -7, 1]), "0.4": kf([-85, -8, 0])}},
            "left_arm": {
                "rotation": {"0.0": kf([-82, 32, 0]), "0.1": kf([-84, 30, -1]), "0.2": kf([-81, 33, 1]), "0.3": kf([-83, 31, 0]), "0.4": kf([-82, 32, 0])},
                "position": {"0.0": kf([-1, 0, -1])},
            },
            "rightItem": {"rotation": {"0.0": kf([-81, 0, 90])}, "position": {"0.0": kf([0, 3, 0])}},
            "right_leg": {"position": {"0.0": kf([0, 0, 2])}},
            "left_leg": {"position": {"0.0": kf([0, 0, -1])}},
        },
    }
    wrench = {"0.0": kf([0, 0, 0])}
    for i, t in enumerate((0.55, 0.75, 0.95, 1.15, 1.25)):
        wrench["%.2f" % t] = kf([-30, 0, 25 if i % 2 == 0 else -25] if i < 4 else [-30, 0, 0], "easeInOutSine")
    deploy_sentry = {
        "loop": "hold_on_last_frame",
        "animation_length": 1.5,
        "bones": {
            "torso": {
                "rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([20, 0, 0], "easeInOutSine")},
                "position": {"0.0": kf([0, 0, 0]), "0.5": kf([0, -4, -2], "easeInOutSine")},
            },
            "head": {"position": {"0.0": kf([0, 0, 0]), "0.5": kf([0, -4, -2], "easeInOutSine")}},
            "right_leg": {
                "rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([30, 0, 0], "easeInOutSine")},
                "position": {"0.0": kf([0, 0, 0]), "0.5": kf([0, -2, 3], "easeInOutSine")},
            },
            "left_leg": {
                "rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([-60, 0, 0], "easeInOutSine")},
                "position": {"0.0": kf([0, 0, 0]), "0.5": kf([0, -3, -4], "easeInOutSine")},
            },
            "right_arm": {
                "rotation": dict({"0.0": kf([0, 0, 0]), "0.5": kf([-30, 0, 0], "easeInOutSine")}, **{k: v for k, v in wrench.items() if k != "0.0"}),
                "position": {"0.0": kf([0, 0, 0]), "0.5": kf([0, -5, -3], "easeInOutSine")},
            },
            "left_arm": {
                "rotation": {"0.0": kf([0, 0, 0]), "0.5": kf([10, 0, -25], "easeInOutSine")},
                "position": {"0.0": kf([0, 0, 0]), "0.5": kf([0, -4, -2], "easeInOutSine")},
            },
        },
    }
    deploy_sentry_finish = {
        "animation_length": 0.3,
        "bones": {
            "torso": {
                "rotation": {"0.0": kf([25, 0, 0]), "0.1": kf([30, 0, 0], "easeInQuad"), "0.3": kf([0, 0, 0], "easeOutSine")},
                "position": {"0.0": kf([0, -4, -2]), "0.3": kf([0, 0, 0], "easeOutSine")},
            },
            "head": {"position": {"0.0": kf([0, -4, -2]), "0.3": kf([0, 0, 0], "easeOutSine")}},
            "right_arm": {
                "rotation": {"0.0": kf([-35, 0, 0]), "0.1": kf([-5, 0, 0], "easeInQuad"), "0.3": kf([0, 0, 0])},
                "position": {"0.0": kf([0, -5, -3]), "0.1": kf([0, -7, -3], "easeInQuad"), "0.3": kf([0, 0, 0], "easeOutSine")},
            },
            "right_leg": {"rotation": {"0.0": kf([30, 0, 0]), "0.3": kf([0, 0, 0], "easeOutSine")}, "position": {"0.0": kf([0, -2, 3]), "0.3": kf([0, 0, 0])}},
            "left_leg": {"rotation": {"0.0": kf([-60, 0, 0]), "0.3": kf([0, 0, 0], "easeOutSine")}, "position": {"0.0": kf([0, -3, -4]), "0.3": kf([0, 0, 0])}},
        },
    }
    steam_push = {
        "animation_length": 0.45,
        "bones": {
            "torso": {"rotation": {"0.0": kf([-5, 0, 0]), "0.1": kf([12, 0, 0], "easeOutBack"), "0.45": kf([0, 0, 0], "easeInOutSine")}},
            "body": {"position": {"0.0": kf([0, 0, 1]), "0.1": kf([0, -0.5, -1.5], "easeOutBack"), "0.45": kf([0, 0, 0])}},
            "right_arm": {"rotation": {"0.0": kf([-60, -10, 0]), "0.1": kf([-95, 15, 0], "easeOutBack"), "0.3": kf([-90, 12, 0]), "0.45": kf([-40, 0, 0], "easeInOutSine")},
                          "position": {"0.0": kf([0, 0, 2]), "0.1": kf([0, 0, -3], "easeOutBack"), "0.45": kf([0, 0, 0])}},
            "left_arm": {"rotation": {"0.0": kf([-60, 10, 0]), "0.1": kf([-95, -15, 0], "easeOutBack"), "0.3": kf([-90, -12, 0]), "0.45": kf([-40, 0, 0], "easeInOutSine")},
                         "position": {"0.0": kf([0, 0, 2]), "0.1": kf([0, 0, -3], "easeOutBack"), "0.45": kf([0, 0, 0])}},
            "right_leg": {"position": {"0.0": kf([0, 0, 0]), "0.1": kf([0, 0, 2]), "0.45": kf([0, 0, 0])}},
        },
    }
    write_json("player_animation/technomancy_animations.json", {
        "format_version": "1.8.0",
        "animations": {
            "gear_flick": gear_flick,
            "welder_channel": welder_channel,
            "deploy_sentry": deploy_sentry,
            "deploy_sentry_finish": deploy_sentry_finish,
            "steam_push": steam_push,
        },
        "geckolib_format_version": 2,
    })



# ---------------------------------------------------------------------------------------------- 2D textures

def item_textures():
    sprites.arcane_cog().save(out("textures/item/arcane_cog.png"))
    sprites.technomancy_rune().save(out("textures/item/technomancy_rune.png"))
    sprites.upgrade_orb_layer_frames(8).save(out("textures/item/upgrade_orb_technomancy.png"))
    write_json("textures/item/upgrade_orb_technomancy.png.mcmeta", {"animation": {"frametime": 2, "interpolate": False}})
    sprites.scroll_technomancy().save(out("textures/item/scroll_technomancy.png"))
    sprites.affinity_ring().save(out("textures/item/affinity_ring_technomancy.png"))
    sprites.clockwork_scepter().save(out("textures/item/clockwork_scepter.png"))
    for slot in ("helmet", "chestplate", "leggings", "boots"):
        sprites.armor_icon(slot).save(out("textures/item/clockwork_engineer_%s.png" % slot))
    gem = os.path.join(ROOT, "apotheosis", "textures", "items", "gems", "technomancy.png")
    os.makedirs(os.path.dirname(gem), exist_ok=True)
    sprites.technomancy_gem().save(gem)
    sprites.effect_overdrive().save(out("textures/mob_effect/overdrive.png"))


def spell_icons():
    icons = {
        "gear_barrage": sprites.icon_gear_barrage,
        "arc_welder": sprites.icon_arc_welder,
        "deploy_brass_sentry": sprites.icon_deploy_sentry,
        "steam_vent": sprites.icon_steam_vent,
        "overdrive_protocol": sprites.icon_overdrive,
        "assemble_automaton": sprites.icon_assemble_automaton,
    }
    for name, painter in icons.items():
        painter().save(out("textures/gui/spell_icons/%s.png" % name))


def particle_textures():
    for n in range(3):
        sprites.particle_brass_spark(n).save(out("textures/particle/brass_spark_%d.png" % n))
    for n in range(4):
        sprites.particle_steam(n).save(out("textures/particle/steam_puff_%d.png" % n))
    for n in range(2):
        sprites.particle_arc_mote(n).save(out("textures/particle/arc_mote_%d.png" % n))
    sprites.particle_cog_sigil().save(out("textures/particle/cog_sigil.png"))
    write_json("particles/brass_spark.json", {"textures": ["iss_technomancy:brass_spark_%d" % n for n in range(3)]})
    write_json("particles/steam_puff.json", {"textures": ["iss_technomancy:steam_puff_%d" % n for n in range(4)]})
    write_json("particles/arc_mote.json", {"textures": ["iss_technomancy:arc_mote_%d" % n for n in range(2)]})
    write_json("particles/cog_sigil.json", {"textures": ["iss_technomancy:cog_sigil"]})


def thunderforge():
    """1.10: the Hextech Thunderforge (the dragon's summoning altar) as an animated GeckoLib block."""
    geo, img, glow, anims = forge_v7.hextech_forge()
    moved = check_geo.fix_geo(geo, img)
    if moved:
        print("  hextech_thunderforge: pulled %d coplanar faces apart (z-fighting)" % moved)
    write_json("geo/block/hextech_thunderforge.geo.json", geo)
    write_json("animations/block/hextech_thunderforge.animation.json", anims)
    img.save(out("textures/block/hextech_thunderforge.png"))
    glow.save(out("textures/block/hextech_thunderforge_glowmask.png"))


if __name__ == "__main__":
    entity("brass_sentry", turrets_v7.brass_sentry)
    entity("siege_sentry", turrets_v7.siege_sentry)
    entity("clockwork_automaton", models_v2.automaton_robot)
    entity("clockwork_automaton_mk2", blitz_v3.blitz)
    entity("tech_dragon", tech_dragon)
    entity("hextech_pylon", pylon_v4.pylon)
    entity("hextech_shell", pylon_v4.shell)
    pylon_v4.shield_texture().save(out("textures/entity/dragon_shield.png"))
    entity("rocket_hand", models_v2.rocket_hand)
    entity("technomancer", technomancer_v3.technomancer)
    entity("gear_projectile", models.gear_projectile)
    thunderforge()
    clockwork_staff()
    v2_textures()
    clockwork_armor()
    player_animations()
    item_textures()
    spell_icons()
    particle_textures()
    premium_art()
    print("Assets generated under", os.path.normpath(ROOT))
