"""
Generates the JSON data and resources of Iron's Technomancy that are not art: sounds.json, item models, tags,
recipes, loot tables, loot modifiers, upgrade orb type, Apotheosis gem, Patchouli entries and en_us / vi_vn lang.
Run from anywhere:

    python tools/generate_data.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data_v2  # noqa: E402
import data_v3  # noqa: E402
import data_v4  # noqa: E402
import data_v5  # noqa: E402

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources")


def w(rel, data):
    p = os.path.join(R, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


A = "assets/iss_technomancy/"
D = "data/iss_technomancy/"


def ev(name, pitch=1.0, volume=1.0):
    return {"name": name, "type": "event", "pitch": pitch, "volume": volume}


sounds = {
    "cast.technomancy": [ev("minecraft:block.chain.place", 1.3), ev("minecraft:block.beacon.activate", 1.8, 0.4)],
    "cast.gear_barrage": [ev("minecraft:block.chain.break", 1.5), ev("minecraft:entity.arrow.shoot", 1.3, 0.7)],
    "entity.gear.ricochet": [ev("minecraft:block.anvil.land", 1.9, 0.25)],
    "entity.gear.impact": [ev("minecraft:block.chain.hit", 1.3)],
    "cast.arc_welder.start": [ev("minecraft:block.respawn_anchor.charge", 1.6, 0.8)],
    "cast.arc_welder.loop": [ev("minecraft:block.redstone_torch.burnout", 1.8, 0.5)],
    "cast.arc_welder.end": [ev("minecraft:block.fire.extinguish", 1.3, 0.6)],
    "cast.brass_sentry.windup": [ev("minecraft:item.crossbow.loading_middle", 0.7), ev("minecraft:block.piston.contract", 0.8, 0.6)],
    "entity.brass_sentry.deploy": [ev("minecraft:block.anvil.place", 1.2, 0.6), ev("minecraft:block.piston.extend", 0.9)],
    "entity.brass_sentry.shoot": [ev("minecraft:entity.shulker.shoot", 1.5, 0.8)],
    "entity.brass_sentry.overclock": [ev("minecraft:block.beacon.power_select", 1.8, 0.8)],
    "entity.brass_sentry.destroyed": [ev("minecraft:entity.iron_golem.death", 1.5, 0.7)],
    "entity.sentry_bolt.impact": [ev("minecraft:entity.shulker_bullet.hit", 1.4, 0.8)],
    "cast.steam_vent": [ev("minecraft:block.fire.extinguish", 0.7, 1.0), ev("minecraft:entity.generic.extinguish_fire", 0.6, 0.8)],
    "cast.overdrive": [ev("minecraft:block.beacon.power_select", 1.3), ev("minecraft:block.piston.extend", 0.6, 0.7)],
    "overdrive.trigger": [ev("minecraft:block.respawn_anchor.deplete", 1.4, 0.9)],
    "entity.siege_sentry.shoot": [ev("minecraft:entity.generic.explode", 1.8, 0.45), ev("minecraft:block.piston.contract", 1.4, 0.6)],
    "entity.siege_shell.explode": [ev("minecraft:entity.generic.explode", 1.2, 0.7)],
    "cast.assemble_automaton": [ev("minecraft:block.anvil.use", 0.8, 0.7), ev("minecraft:block.piston.extend", 0.7)],
    "entity.clockwork_automaton.ambient": [ev("minecraft:block.chain.step", 0.7, 0.6), ev("minecraft:block.lava.pop", 0.6, 0.4)],
    "entity.clockwork_automaton.hurt": [ev("minecraft:entity.iron_golem.hurt", 1.4)],
    "entity.clockwork_automaton.death": [ev("minecraft:entity.iron_golem.death", 1.3)],
    "entity.clockwork_automaton.step": [ev("minecraft:entity.iron_golem.step", 1.3, 0.6)],
    "entity.clockwork_automaton.attack": [ev("minecraft:entity.iron_golem.attack", 1.2)],
    "entity.clockwork_automaton.volley": [ev("minecraft:block.chain.break", 1.2), ev("minecraft:entity.generic.extinguish_fire", 1.3, 0.6)],
}
sounds.update(data_v2.SOUNDS)
w(A + "sounds.json", {k: {"sounds": v, "subtitle": "subtitles.iss_technomancy." + k} for k, v in sounds.items()})


def gen(tex):
    return {"parent": "item/generated", "textures": {"layer0": "iss_technomancy:item/" + tex}}


for it in ["arcane_cog", "technomancy_rune", "clockwork_engineer_helmet", "clockwork_engineer_chestplate",
           "clockwork_engineer_leggings", "clockwork_engineer_boots", "scroll_technomancy", "affinity_ring_technomancy"]:
    w(A + "models/item/%s.json" % it, gen(it))
w(A + "models/item/technomancy_upgrade_orb.json", {"parent": "item/generated", "textures": {
    "layer0": "irons_spellbooks:item/upgrade_orb_base", "layer1": "irons_spellbooks:item/upgrade_orb_swirl",
    "layer2": "iss_technomancy:item/upgrade_orb_technomancy"}})
w(A + "models/item/clockwork_automaton_spawn_egg.json", {"parent": "minecraft:item/template_spawn_egg"})
w(D + "loot_tables/entities/clockwork_automaton.json", {"type": "minecraft:entity", "pools": [
    {"rolls": 1, "entries": [{"type": "minecraft:item", "name": "iss_technomancy:arcane_cog", "functions": [
        {"function": "minecraft:set_count", "count": {"min": 1, "max": 3}},
        {"function": "minecraft:looting_enchant", "count": {"min": 0, "max": 1}}]}]},
    {"rolls": 1, "entries": [{"type": "minecraft:item", "name": "minecraft:copper_ingot", "functions": [
        {"function": "minecraft:set_count", "count": {"min": 1, "max": 4}}]}]},
    {"rolls": 1, "conditions": [{"condition": "minecraft:killed_by_player"},
                                {"condition": "minecraft:random_chance_with_looting", "chance": 0.08, "looting_multiplier": 0.03}],
     "entries": [{"type": "minecraft:item", "name": "iss_technomancy:technomancy_rune"}]},
    {"rolls": 1, "conditions": [{"condition": "minecraft:killed_by_player"}, {"condition": "minecraft:random_chance", "chance": 0.05}],
     "entries": [{"type": "minecraft:item", "name": "irons_spellbooks:scroll", "functions": [
         {"function": "irons_spellbooks:randomize_spell", "quality": {"min": 0.0, "max": 0.6}, "spell_filter": {"school": "iss_technomancy:technomancy"}}]}]}]})
w("assets/apotheosis/models/item/gems/technomancy.json", {"parent": "item/generated", "textures": {"layer0": "apotheosis:items/gems/technomancy"}})

w(D + "damage_type/technomancy_magic.json", {"exhaustion": 0.0, "message_id": "technomancy_magic", "scaling": "when_caused_by_living_non_player"})
w(D + "tags/damage_type/technomancy_magic.json", {"values": ["iss_technomancy:technomancy_magic"]})
w(D + "tags/items/technomancy_focus.json", {"replace": False, "values": ["iss_technomancy:arcane_cog", "minecraft:clock"]})
w("data/irons_spellbooks/tags/items/school_focus.json", {"replace": False, "values": ["#iss_technomancy:technomancy_focus"]})
w("data/irons_spellbooks/tags/items/inscribed_rune.json", {"replace": False, "values": ["iss_technomancy:technomancy_rune"]})
w("data/irons_spellbooks/tags/items/staff.json", {"replace": False, "values": ["iss_technomancy:clockwork_scepter"]})
for slot, plural in [("helmet", "helmets"), ("chestplate", "chestplates"), ("leggings", "leggings"), ("boots", "boots")]:
    w("data/irons_spellbooks/tags/items/armors/%s.json" % plural, {"replace": False, "values": ["iss_technomancy:clockwork_engineer_" + slot]})
w(D + "irons_spellbooks/upgrade_orb_type/technomancy_power.json", {
    "amount": 0.05, "attribute": "iss_technomancy:technomancy_spell_power",
    "containerItem": {"Count": 1, "id": "iss_technomancy:technomancy_upgrade_orb"}, "operation": "MULTIPLY_BASE"})

w(D + "recipes/arcane_cog.json", {"type": "minecraft:crafting_shaped", "category": "misc",
                                  "pattern": ["CRC", "RGR", "CRC"],
                                  "key": {"C": {"item": "minecraft:copper_ingot"}, "R": {"item": "minecraft:redstone"}, "G": {"item": "minecraft:gold_ingot"}},
                                  "result": {"item": "iss_technomancy:arcane_cog", "count": 1}})
w(D + "recipes/technomancy_rune.json", {"type": "minecraft:crafting_shaped", "category": "misc",
                                        "pattern": ["FFF", "FRF", "FFF"],
                                        "key": {"F": {"tag": "iss_technomancy:technomancy_focus"}, "R": {"item": "irons_spellbooks:blank_rune"}},
                                        "result": {"item": "iss_technomancy:technomancy_rune", "count": 1}})
w(D + "recipes/technomancy_upgrade_orb.json", {"type": "minecraft:crafting_shaped", "category": "misc",
                                               "pattern": ["RRR", "ROR", "RRR"],
                                               "key": {"O": {"item": "irons_spellbooks:upgrade_orb"}, "R": {"item": "iss_technomancy:technomancy_rune"}},
                                               "result": {"item": "iss_technomancy:technomancy_upgrade_orb", "count": 1}})
w(D + "recipes/clockwork_scepter.json", {"type": "minecraft:crafting_shaped", "category": "equipment",
                                         "pattern": [" EC", " IE", "I  "],
                                         "key": {"E": {"item": "irons_spellbooks:arcane_essence"}, "C": {"item": "iss_technomancy:technomancy_rune"},
                                                 "I": {"item": "minecraft:copper_ingot"}},
                                         "result": {"item": "iss_technomancy:clockwork_scepter", "count": 1}})
for slot in ["helmet", "chestplate", "leggings", "boots"]:
    w(D + "recipes/clockwork_engineer_%s_crafting.json" % slot, {
        "type": "minecraft:crafting_shapeless", "category": "equipment",
        "ingredients": [{"tag": "irons_spellbooks:wizard_base_" + slot}, {"item": "iss_technomancy:technomancy_rune"},
                        {"item": "irons_spellbooks:arcane_essence"}],
        "result": {"item": "iss_technomancy:clockwork_engineer_" + slot, "count": 1}})
    w(D + "recipes/clockwork_engineer_%s_smithing.json" % slot, {
        "type": "minecraft:smithing_transform",
        "template": {"item": "iss_technomancy:technomancy_rune"}, "base": {"tag": "irons_spellbooks:wizard_base_" + slot},
        "addition": {"item": "irons_spellbooks:arcane_essence"}, "result": {"item": "iss_technomancy:clockwork_engineer_" + slot, "count": 1}})

w(D + "loot_tables/chests/technomancy_loot.json", {"type": "minecraft:chest", "pools": [
    {"rolls": 1, "conditions": [{"condition": "minecraft:random_chance", "chance": 0.35}], "entries": [
        {"type": "minecraft:item", "name": "irons_spellbooks:scroll", "weight": 6, "functions": [
            {"function": "irons_spellbooks:randomize_spell", "quality": {"min": 0.0, "max": 0.8},
             "spell_filter": {"school": "iss_technomancy:technomancy"}}]},
        {"type": "minecraft:item", "name": "irons_spellbooks:affinity_ring", "weight": 1, "functions": [
            {"function": "irons_spellbooks:randomize_ring_enhancement", "spell_filter": {"school": "iss_technomancy:technomancy"}}]},
        {"type": "minecraft:item", "name": "iss_technomancy:arcane_cog", "weight": 4, "functions": [
            {"function": "minecraft:set_count", "count": {"min": 1, "max": 3}}]},
        {"type": "minecraft:item", "name": "iss_technomancy:technomancy_rune", "weight": 1}]}]})
w(D + "loot_modifiers/technomancy_chest_loot.json", {
    "type": "irons_spellbooks:append_loot",
    "conditions": [{"condition": "minecraft:any_of", "terms": [{"condition": "forge:loot_table_id", "loot_table_id": t} for t in [
        "minecraft:chests/simple_dungeon", "minecraft:chests/abandoned_mineshaft", "minecraft:chests/village/village_toolsmith",
        "minecraft:chests/village/village_weaponsmith", "minecraft:chests/ancient_city", "minecraft:chests/stronghold_library",
        "minecraft:chests/trail_ruins_rare"]]}],
    "key": "iss_technomancy:chests/technomancy_loot"})
w("data/forge/loot_modifiers/global_loot_modifiers.json", {"replace": False, "entries": ["iss_technomancy:technomancy_chest_loot"]})

w(D + "gems/technomancy.json", {"variant": "technomancy", "weight": 5, "quality": 0, "dimensions": [], "bonuses": [
    {"type": "apotheosis:attribute", "gem_class": {"key": "anything", "types": ["helmet", "chestplate", "leggings", "boots"]},
     "attribute": "iss_technomancy:technomancy_spell_power", "operation": "MULTIPLY_TOTAL",
     "values": {k: {"min": v, "steps": 1, "step": 0} for k, v in
                [("common", 0.01), ("uncommon", 0.03), ("rare", 0.05), ("epic", 0.07), ("mythic", 0.1), ("ancient", 0.15)]}}]})

w("assets/irons_spellbooks/patchouli_books/iss_guide_book/en_us/entries/technomancy.json", {
    "name": "Technomancy", "icon": "iss_technomancy:arcane_cog", "category": "irons_spellbooks:root", "sortnum": 21, "read_by_default": True,
    "pages": [
        {"type": "patchouli:spotlight", "item": "iss_technomancy:arcane_cog", "title": "Technomancy",
         "text": "The Technomancy school, with an Arcane Cog as its Focus, is centered around $(l)deployed constructs$() and maintaining them. Craft Arcane Cogs from copper, gold and redstone; a Clock also works as a Focus."},
        {"type": "patchouli:text", "title": "Construct Synergy",
         "text": "A $(item)Brass Sentry$() is a stationary turret that fires at nearby hostiles. Hit your own Sentry with $(item)Arc Welder$() to repair it, extend its lifetime and $(l)Overclock$() it, making it fire faster for a few seconds."},
        {"type": "patchouli:spotlight", "item": "iss_technomancy:technomancy_rune", "title": "Technomancy Rune",
         "text": "Surround a Blank Rune with eight Technomancy Focus items. Runes upgrade wizard armor into the $(item)Clockwork Engineer$() set and become $(item)Technomancy Upgrade Orbs$()."},
        {"type": "patchouli:spotlight", "item": "iss_technomancy:clockwork_scepter", "title": "Clockwork Dynamo Staff",
         "text": "A spinning cog-ring staff that empowers Technomancy and shortens cooldowns. It holds three staff modules."},
        {"type": "patchouli:text", "title": "Overdrive Protocol",
         "text": "Overdrive upgrades the $(l)next$() Technomancy spell you cast: Gear Barrage fires 5 piercing gears, Arc Welder forks to 2 extra foes, Steam Vent becomes superheated, Deploy Brass Sentry builds a twin-cannon $(item)Siege Sentry$() and Assemble Automaton builds a $(item)Mk.II$() war construct."},
        {"type": "patchouli:spotlight", "item": "iss_technomancy:clockwork_automaton_spawn_egg", "title": "Clockwork Automaton",
         "text": "Rogue automatons punch hard and vent volleys of gears. Destroy them for Arcane Cogs and copper, or assemble your own with Assemble Automaton. Overdriven, it becomes a round $(item)Mk.II$() steam golem with Rocket Grab, Power Fist and a Static Field."},
        {"type": "patchouli:spotlight", "item": "iss_technomancy:module_splitter_1", "title": "Staff Modules",
         "text": "$(l)Sneak + use$() the Clockwork Dynamo Staff to open its three sockets. Modules only upgrade Technomancy spells cast with the staff: $(item)Splitter$() (more projectiles), $(item)Caliber$() (bigger, stronger), $(item)Assembler$() (more constructs), $(item)Capacitor$() (cooldown, cast speed) and $(item)Tesla Coil$() (chain lightning). Tiers stack up to level 5 per family."},
        {"type": "patchouli:spotlight", "item": "iss_technomancy:clockwork_altar", "title": "The Tech Dragon",
         "text": "Clockwork Shrines hide an altar; you can also craft one. Use an $(item)Overcharged Dynamo Core$() on it to wake the $(l)Tech Dragon$(): gear volleys, lightning breath, thunder storms, dive bombs and drone swarms, and a deadlier overcharged second phase."},
        {"type": "patchouli:spotlight", "item": "iss_technomancy:clockwork_codex", "title": "Clockwork Codex",
         "text": "A 12-slot spellbook bound with Tech Dragon Cores: +15% Technomancy power, +5% spell power and +200 mana."}]})
w("assets/irons_spellbooks/patchouli_books/iss_guide_book/vi_vn/entries/technomancy.json", {
    "name": "Cơ Khí Phép", "icon": "iss_technomancy:arcane_cog", "category": "irons_spellbooks:root", "sortnum": 21, "read_by_default": True,
    "pages": [
        {"type": "patchouli:spotlight", "item": "iss_technomancy:arcane_cog", "title": "Cơ Khí Phép",
         "text": "Hệ Cơ Khí Phép dùng $(item)Bánh Răng Bí Thuật$() làm Focus, xoay quanh việc $(l)triển khai công trình$() và bảo trì chúng. Chế Bánh Răng từ đồng, vàng và đá đỏ; Đồng Hồ cũng dùng được làm Focus."},
        {"type": "patchouli:text", "title": "Cộng Hưởng Công Trình",
         "text": "$(item)Tháp Pháo Đồng Thau$() đứng yên và tự bắn kẻ địch gần đó. Dùng $(item)Mỏ Hàn Hồ Quang$() bắn vào tháp của chính bạn để sửa chữa, kéo dài thời gian và $(l)Overclock$(), giúp tháp bắn nhanh hơn trong vài giây."},
        {"type": "patchouli:spotlight", "item": "iss_technomancy:technomancy_rune", "title": "Rune Cơ Khí",
         "text": "Bao quanh một Blank Rune bằng tám vật phẩm Focus của hệ. Rune dùng để nâng giáp pháp sư thành bộ $(item)Kỹ Sư Đồng Hồ$() và chế $(item)Orb Nâng Cấp Cơ Khí$()."},
        {"type": "patchouli:spotlight", "item": "iss_technomancy:clockwork_scepter", "title": "Trượng Động Cơ Đồng Hồ",
         "text": "Trượng vòng bánh răng xoay, tăng sức mạnh Cơ Khí Phép và giảm hồi chiêu. Có 3 ô mô-đun."},
        {"type": "patchouli:text", "title": "Giao Thức Quá Tải",
         "text": "Overdrive cường hoá phép Cơ Khí $(l)kế tiếp$(): Loạt Bánh Răng bắn 5 bánh răng xuyên giáp, Mỏ Hàn phóng tia nảy sang 2 kẻ địch, Phun Hơi thành hơi siêu nóng, Triển Khai Tháp Pháo dựng $(item)Tháp Công Thành$() nòng đôi và Lắp Ráp Automaton tạo bản $(item)Mk.II$()."},
        {"type": "patchouli:spotlight", "item": "iss_technomancy:clockwork_automaton_spawn_egg", "title": "Automaton Đồng Hồ",
         "text": "Automaton hoang đấm rất mạnh và phun loạt bánh răng. Hạ chúng để lấy Bánh Răng Bí Thuật và đồng, hoặc tự lắp ráp bằng phép Lắp Ráp Automaton. Khi Quá Tải nó thành $(item)Mk.II$() — golem hơi nước tròn với Rocket Grab, Power Fist và Trường Tĩnh Điện."},
        {"type": "patchouli:spotlight", "item": "iss_technomancy:module_splitter_1", "title": "Mô-đun Trượng",
         "text": "$(l)Shift + chuột phải$() với Trượng Động Cơ để mở 3 ô. Mô-đun chỉ nâng cấp phép Cơ Khí niệm bằng trượng: $(item)Đa Nòng$() (thêm đạn), $(item)Cỡ Nòng$() (to và mạnh hơn), $(item)Lắp Ráp$() (thêm công trình), $(item)Tụ Điện$() (hồi chiêu, niệm nhanh) và $(item)Cuộn Tesla$() (sét nảy). Cùng loại cộng dồn tối đa cấp 5."},
        {"type": "patchouli:spotlight", "item": "iss_technomancy:clockwork_altar", "title": "Rồng Công Nghệ",
         "text": "Đền Đồng Hồ có sẵn tế đàn; cũng có thể tự chế. Dùng $(item)Lõi Dynamo Quá Tải$() lên tế đàn để đánh thức $(l)Rồng Công Nghệ$(): bánh răng, hơi thở sét, bão sấm, bổ nhào, gọi drone và phase 2 quá tải nguy hiểm hơn."},
        {"type": "patchouli:spotlight", "item": "iss_technomancy:clockwork_codex", "title": "Mật Điển Đồng Hồ",
         "text": "Sách phép 12 ô đóng bằng Lõi Rồng Công Nghệ: +15% sức mạnh Cơ Khí, +5% sức mạnh phép và +200 mana."}]})


def lang(t):
    result = {
        "itemGroup.iss_technomancy.technomancy": t["tab"],
        "school.iss_technomancy.technomancy": t["school"],
        "attribute.iss_technomancy.technomancy_spell_power": t["power"],
        "attribute.iss_technomancy.technomancy_magic_resist": t["resist"],
        "item.iss_technomancy.arcane_cog": t["cog"],
        "item.iss_technomancy.technomancy_rune": t["rune"],
        "item.iss_technomancy.technomancy_upgrade_orb": t["orb"],
        "item.iss_technomancy.clockwork_scepter": t["scepter"],
        "item.iss_technomancy.clockwork_engineer_helmet": t["helmet"],
        "item.iss_technomancy.clockwork_engineer_chestplate": t["chest"],
        "item.iss_technomancy.clockwork_engineer_leggings": t["legs"],
        "item.iss_technomancy.clockwork_engineer_boots": t["boots"],
        "item.apotheosis.gem.iss_technomancy:technomancy": t["gem"],
        "entity.iss_technomancy.brass_sentry": t["sentry"],
        "entity.iss_technomancy.gear_projectile": t["gear"],
        "entity.iss_technomancy.arc_welder_beam": t["beam"],
        "entity.iss_technomancy.sentry_bolt": t["bolt"],
        "spell.iss_technomancy.gear_barrage": t["s1"],
        "spell.iss_technomancy.gear_barrage.guide": t["s1g"],
        "spell.iss_technomancy.arc_welder": t["s2"],
        "spell.iss_technomancy.arc_welder.guide": t["s2g"],
        "spell.iss_technomancy.deploy_brass_sentry": t["s3"],
        "spell.iss_technomancy.deploy_brass_sentry.guide": t["s3g"],
        "ui.iss_technomancy.damage_per_gear": t["dpg"],
        "ui.iss_technomancy.damage_per_pulse": t["dpp"],
        "ui.iss_technomancy.bolt_damage": t["bd"],
        "ui.iss_technomancy.sentry_lifetime": t["life"],
        "death.attack.technomancy_magic": t["d0"],
        "death.attack.iss_technomancy.gear_barrage": t["d1"],
        "death.attack.iss_technomancy.gear_barrage.item": t["d1i"],
        "death.attack.iss_technomancy.arc_welder": t["d2"],
        "death.attack.iss_technomancy.arc_welder.item": t["d2i"],
        "death.attack.iss_technomancy.deploy_brass_sentry": t["d3"],
        "death.attack.iss_technomancy.deploy_brass_sentry.item": t["d3i"],
    }
    for k, v in t["sub"].items():
        result["subtitles.iss_technomancy." + k] = v
    return result


en = dict(
    tab="Iron's Technomancy", school="Technomancy", power="Technomancy Spell Power", resist="Technomancy Magic Resistance",
    cog="Arcane Cog", rune="Technomancy Rune", orb="Technomancy Upgrade Orb", scepter="Clockwork Scepter",
    helmet="Clockwork Engineer Goggles", chest="Clockwork Engineer Coat", legs="Clockwork Engineer Trousers", boots="Clockwork Engineer Boots",
    gem="Clockwork Gem", sentry="Brass Sentry", gear="Brass Gear", beam="Welding Arc", bolt="Sentry Bolt",
    s1="Gear Barrage", s1g="Flick a fan of spinning brass gears. Each gear ricochets off one surface before shattering, perfect for close quarters.",
    s2="Arc Welder", s2g="Channel a short welding arc that burns and slows whatever it touches. Weld your own Brass Sentry to repair, extend and overclock it.",
    s3="Deploy Brass Sentry", s3g="Assemble a stationary brass turret that shoots arcane bolts at nearby hostiles. Only one sentry can be active at a time.",
    dpg="%s Damage per Gear", dpp="%s Damage per Pulse", bd="%s Bolt Damage", life="%ss Lifetime",
    d0="%1$s was disassembled by %2$s's technomancy",
    d1="%1$s was shredded by %2$s's gears", d1i="%1$s was shredded by %2$s's gears using %3$s",
    d2="%1$s was welded shut by %2$s", d2i="%1$s was welded shut by %2$s using %3$s",
    d3="%1$s was gunned down by %2$s's Brass Sentry", d3i="%1$s was gunned down by %2$s's Brass Sentry using %3$s",
    sub={"cast.technomancy": "Clockwork whirs", "cast.gear_barrage": "Gears fly", "entity.gear.ricochet": "Gear ricochets",
         "entity.gear.impact": "Gear strikes", "cast.arc_welder.start": "Welding arc ignites", "cast.arc_welder.loop": "Welding arc crackles",
         "cast.arc_welder.end": "Welding arc fizzles", "cast.brass_sentry.windup": "Wrench ratchets", "entity.brass_sentry.deploy": "Sentry unfolds",
         "entity.brass_sentry.shoot": "Sentry fires", "entity.brass_sentry.overclock": "Sentry overclocks",
         "entity.brass_sentry.destroyed": "Sentry breaks apart", "entity.sentry_bolt.impact": "Bolt crackles"})
vi = dict(
    tab="Cơ Khí Phép của Iron", school="Cơ Khí Phép", power="Sức Mạnh Phép Cơ Khí", resist="Kháng Phép Cơ Khí",
    cog="Bánh Răng Bí Thuật", rune="Rune Cơ Khí", orb="Orb Nâng Cấp Cơ Khí", scepter="Quyền Trượng Đồng Hồ",
    helmet="Kính Bảo Hộ Kỹ Sư Đồng Hồ", chest="Áo Khoác Kỹ Sư Đồng Hồ", legs="Quần Kỹ Sư Đồng Hồ", boots="Giày Kỹ Sư Đồng Hồ",
    gem="Ngọc Đồng Hồ", sentry="Tháp Pháo Đồng Thau", gear="Bánh Răng Đồng Thau", beam="Hồ Quang Hàn", bolt="Đạn Tháp Pháo",
    s1="Loạt Bánh Răng", s1g="Búng ra một chùm bánh răng đồng thau xoay tít. Mỗi bánh răng nảy bật khỏi một bề mặt trước khi vỡ, rất mạnh ở tầm gần.",
    s2="Mỏ Hàn Hồ Quang", s2g="Phóng tia hồ quang hàn tầm ngắn, thiêu đốt và làm chậm mục tiêu. Hàn vào Tháp Pháo của chính bạn để sửa, kéo dài và overclock nó.",
    s3="Triển Khai Tháp Pháo", s3g="Lắp ráp một tháp pháo đồng thau đứng yên, tự bắn bolt bí thuật vào kẻ địch gần đó. Mỗi lúc chỉ có một tháp.",
    dpg="%s Sát thương mỗi bánh răng", dpp="%s Sát thương mỗi nhịp", bd="%s Sát thương bolt", life="%s giây tồn tại",
    d0="%1$s bị tháo rời bởi phép cơ khí của %2$s",
    d1="%1$s bị bánh răng của %2$s xé nát", d1i="%1$s bị bánh răng của %2$s xé nát bằng %3$s",
    d2="%1$s bị %2$s hàn chết", d2i="%1$s bị %2$s hàn chết bằng %3$s",
    d3="%1$s bị Tháp Pháo của %2$s bắn hạ", d3i="%1$s bị Tháp Pháo của %2$s bắn hạ bằng %3$s",
    sub={"cast.technomancy": "Máy đồng hồ kêu rè rè", "cast.gear_barrage": "Bánh răng bay", "entity.gear.ricochet": "Bánh răng nảy",
         "entity.gear.impact": "Bánh răng va chạm", "cast.arc_welder.start": "Hồ quang bật", "cast.arc_welder.loop": "Hồ quang lách tách",
         "cast.arc_welder.end": "Hồ quang tắt", "cast.brass_sentry.windup": "Cờ-lê lách cách", "entity.brass_sentry.deploy": "Tháp pháo mở ra",
         "entity.brass_sentry.shoot": "Tháp pháo bắn", "entity.brass_sentry.overclock": "Tháp pháo overclock",
         "entity.brass_sentry.destroyed": "Tháp pháo vỡ", "entity.sentry_bolt.impact": "Bolt nổ lách tách"})
EXTRA_EN = {
    "item.iss_technomancy.clockwork_automaton_spawn_egg": "Clockwork Automaton Spawn Egg",
    "entity.iss_technomancy.clockwork_automaton": "Clockwork Automaton",
    "entity.iss_technomancy.siege_sentry": "Siege Sentry",
    "entity.iss_technomancy.siege_shell": "Siege Shell",
    "effect.iss_technomancy.overdrive": "Overdrive",
    "effect.iss_technomancy.overdrive.description": "Your next Technomancy spell is cast in its upgraded form.",
    "spell.iss_technomancy.steam_vent": "Steam Vent",
    "spell.iss_technomancy.steam_vent.guide": "Blast scalding steam in a cone, knocking enemies back and blinding them. Overdrive makes it superheated.",
    "spell.iss_technomancy.overdrive_protocol": "Overdrive Protocol",
    "spell.iss_technomancy.overdrive_protocol.guide": "Overclock your next Technomancy spell: piercing gear storms, forking arcs, superheated steam, Siege Sentries and Mk.II Automatons.",
    "spell.iss_technomancy.assemble_automaton": "Assemble Automaton",
    "spell.iss_technomancy.assemble_automaton.guide": "Assemble a steam-powered Clockwork Automaton that fights at your side and vents volleys of gears.",
    "ui.iss_technomancy.knockback": "%s Knockback",
    "death.attack.iss_technomancy.steam_vent": "%1$s was scalded by %2$s",
    "death.attack.iss_technomancy.steam_vent.item": "%1$s was scalded by %2$s using %3$s",
    "death.attack.iss_technomancy.overdrive_protocol": "%1$s was overclocked by %2$s",
    "death.attack.iss_technomancy.overdrive_protocol.item": "%1$s was overclocked by %2$s using %3$s",
    "death.attack.iss_technomancy.assemble_automaton": "%1$s was crushed by %2$s's automaton",
    "death.attack.iss_technomancy.assemble_automaton.item": "%1$s was crushed by %2$s's automaton using %3$s",
    "subtitles.iss_technomancy.cast.steam_vent": "Steam blasts",
    "subtitles.iss_technomancy.cast.overdrive": "Machinery overclocks",
    "subtitles.iss_technomancy.overdrive.trigger": "Overdrive discharges",
    "subtitles.iss_technomancy.entity.siege_sentry.shoot": "Siege cannon fires",
    "subtitles.iss_technomancy.entity.siege_shell.explode": "Shell explodes",
    "subtitles.iss_technomancy.cast.assemble_automaton": "Automaton assembles",
    "subtitles.iss_technomancy.entity.clockwork_automaton.ambient": "Automaton whirs",
    "subtitles.iss_technomancy.entity.clockwork_automaton.hurt": "Automaton clanks",
    "subtitles.iss_technomancy.entity.clockwork_automaton.death": "Automaton breaks down",
    "subtitles.iss_technomancy.entity.clockwork_automaton.step": "Automaton stomps",
    "subtitles.iss_technomancy.entity.clockwork_automaton.attack": "Automaton punches",
    "subtitles.iss_technomancy.entity.clockwork_automaton.volley": "Automaton vents gears",
}
EXTRA_VI = {
    "item.iss_technomancy.clockwork_automaton_spawn_egg": "Trứng Sinh Automaton Đồng Hồ",
    "entity.iss_technomancy.clockwork_automaton": "Automaton Đồng Hồ",
    "entity.iss_technomancy.siege_sentry": "Tháp Công Thành",
    "entity.iss_technomancy.siege_shell": "Đạn Công Thành",
    "effect.iss_technomancy.overdrive": "Quá Tải",
    "effect.iss_technomancy.overdrive.description": "Phép Cơ Khí kế tiếp của bạn được cường hoá.",
    "spell.iss_technomancy.steam_vent": "Phun Hơi",
    "spell.iss_technomancy.steam_vent.guide": "Phun hơi nước bỏng rát hình nón, hất văng và làm mù kẻ địch. Khi Quá Tải sẽ thành hơi siêu nóng.",
    "spell.iss_technomancy.overdrive_protocol": "Giao Thức Quá Tải",
    "spell.iss_technomancy.overdrive_protocol.guide": "Cường hoá phép Cơ Khí kế tiếp: bão bánh răng xuyên giáp, hồ quang nảy chuỗi, hơi siêu nóng, Tháp Công Thành và Automaton Mk.II.",
    "spell.iss_technomancy.assemble_automaton": "Lắp Ráp Automaton",
    "spell.iss_technomancy.assemble_automaton.guide": "Lắp ráp một Automaton chạy hơi nước chiến đấu bên cạnh bạn và phun loạt bánh răng.",
    "ui.iss_technomancy.knockback": "%s Lực đẩy",
    "death.attack.iss_technomancy.steam_vent": "%1$s bị %2$s luộc chín",
    "death.attack.iss_technomancy.steam_vent.item": "%1$s bị %2$s luộc chín bằng %3$s",
    "death.attack.iss_technomancy.overdrive_protocol": "%1$s bị %2$s quá tải",
    "death.attack.iss_technomancy.overdrive_protocol.item": "%1$s bị %2$s quá tải bằng %3$s",
    "death.attack.iss_technomancy.assemble_automaton": "%1$s bị automaton của %2$s nghiền nát",
    "death.attack.iss_technomancy.assemble_automaton.item": "%1$s bị automaton của %2$s nghiền nát bằng %3$s",
    "subtitles.iss_technomancy.cast.steam_vent": "Hơi nước phun",
    "subtitles.iss_technomancy.cast.overdrive": "Máy móc quá tải",
    "subtitles.iss_technomancy.overdrive.trigger": "Quá Tải phóng ra",
    "subtitles.iss_technomancy.entity.siege_sentry.shoot": "Pháo công thành khai hoả",
    "subtitles.iss_technomancy.entity.siege_shell.explode": "Đạn pháo nổ",
    "subtitles.iss_technomancy.cast.assemble_automaton": "Automaton được lắp ráp",
    "subtitles.iss_technomancy.entity.clockwork_automaton.ambient": "Automaton kêu rè rè",
    "subtitles.iss_technomancy.entity.clockwork_automaton.hurt": "Automaton loảng xoảng",
    "subtitles.iss_technomancy.entity.clockwork_automaton.death": "Automaton đổ sập",
    "subtitles.iss_technomancy.entity.clockwork_automaton.step": "Automaton dậm chân",
    "subtitles.iss_technomancy.entity.clockwork_automaton.attack": "Automaton đấm",
    "subtitles.iss_technomancy.entity.clockwork_automaton.volley": "Automaton phun bánh răng",
}
en_lang = lang(en)
en_lang.update(EXTRA_EN)
vi_lang = lang(vi)
vi_lang.update(EXTRA_VI)
en_lang.update(data_v2.EN)
vi_lang.update(data_v2.VI)
data_v2.run(w, R)
data_v3.run(w, R)
en_lang.update(data_v4.EN)
vi_lang.update(data_v4.VI)
data_v4.run(w, R)
en_lang.update(data_v5.EN)
vi_lang.update(data_v5.VI)
data_v5.run(w, R)
w(A + "lang/en_us.json", en_lang)
w(A + "lang/vi_vn.json", vi_lang)
print("ok")
