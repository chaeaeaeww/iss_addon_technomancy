"""
Iron's Technomancy 1.9 data: the hextech blast damage type, the Hextech upgrade template and its recipes, the
Hextech armour / scepter star tiers / spellbooks recipes, item models, tags and lang.
"""

NS = "iss_technomancy:"
D = "data/iss_technomancy/"
A = "assets/iss_technomancy/"

STAFF_DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 4.5, 0.75], "scale": [1, 1, 1]},
    "thirdperson_lefthand": {"rotation": [0, 0, 0], "translation": [0, 4.5, 0.75], "scale": [1, 1, 1]},
    "firstperson_righthand": {"rotation": [0, -8, 18], "translation": [1.5, 2.5, 0], "scale": [0.8, 0.8, 0.8]},
    "firstperson_lefthand": {"rotation": [0, 8, -18], "translation": [1.5, 2.5, 0], "scale": [0.8, 0.8, 0.8]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 3, 0], "scale": [0.5, 0.5, 0.5]},
    "fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [0.6, 0.6, 0.6]},
}
SCEPTERS = [("hextech_scepter", "hextech_staff"), ("hextech_scepter_star1", "hextech_staff_1"), ("hextech_scepter_star2", "hextech_staff_2"),
            ("hextech_scepter_star3", "hextech_staff_3")]
SLOTS = ["helmet", "chestplate", "leggings", "boots"]
TEMPLATE = NS + "hextech_upgrade_smithing_template"
CORE = NS + "tech_dragon_core"


def smithing(base, result):
    return {"type": "minecraft:smithing_transform", "template": {"item": TEMPLATE}, "base": {"item": base}, "addition": {"item": CORE},
            "result": {"item": result}}


def book_model(name):
    tex = NS + "item/spell_book_models/" + name
    return {"parent": "minecraft:item/handheld", "loader": "forge:separate_transforms",
            "base": {"parent": "irons_spellbooks:item/template_spell_book_model", "textures": {"book": tex, "particle": tex}},
            "perspectives": {"gui": {"parent": "item/generated", "textures": {"layer0": NS + "item/" + name}},
                             "head": {"parent": "irons_spellbooks:item/template_spell_book_model_open", "textures": {"book": tex, "particle": tex}}}}


def damage(w):
    # the dying dragon's shell: kills within 20 blocks whatever the armour or protection enchantments (HextechShell)
    w(D + "damage_type/hextech_blast.json", {"exhaustion": 0.0, "message_id": "iss_technomancy.hextech_blast", "scaling": "never",
                                             "effects": "burning"})
    for tag in ("bypasses_armor", "bypasses_enchantments", "is_explosion", "no_knockback"):
        w("data/minecraft/tags/damage_type/%s.json" % tag, {"replace": False, "values": [NS + "hextech_blast"]})


def items(w):
    # the template: a netherite upgrade template, a dragon core, four arcane cogs and three copper ingots make two
    w(D + "recipes/hextech_upgrade_smithing_template.json", {
        "type": "minecraft:crafting_shaped", "category": "misc", "pattern": ["GCG", "CTC", "GDG"],
        "key": {"G": {"item": NS + "arcane_cog"}, "C": {"item": "minecraft:copper_ingot"}, "T": {"item": "minecraft:netherite_upgrade_smithing_template"},
                "D": {"item": CORE}},
        "result": {"item": TEMPLATE, "count": 2}})
    for slot in SLOTS:
        w(D + "recipes/hextech_engineer_%s_smithing.json" % slot, smithing(NS + "clockwork_engineer_" + slot, NS + "hextech_engineer_" + slot))
    chain = ["clockwork_scepter"] + [s for s, _ in SCEPTERS]
    for a, b in zip(chain, chain[1:]):
        w(D + "recipes/%s_smithing.json" % b, smithing(NS + a, NS + b))
    # spellbooks: the clockwork one at the crafting table, the hextech codex in the smithing table (replaces the 1.8 recipe)
    w(D + "recipes/clockwork_spellbook.json", {
        "type": "minecraft:crafting_shaped", "category": "equipment", "pattern": ["CGC", "LBL", "CNC"],
        "key": {"C": {"item": "minecraft:copper_ingot"}, "G": {"item": NS + "arcane_cog"}, "L": {"item": "minecraft:leather"},
                "B": {"item": "minecraft:book"}, "N": {"item": "minecraft:gold_ingot"}},
        "result": {"item": NS + "clockwork_spellbook"}})
    w(D + "recipes/clockwork_codex.json", smithing(NS + "clockwork_spellbook", NS + "clockwork_codex"))

    # models
    w(A + "models/item/hextech_upgrade_smithing_template.json", {"parent": "item/generated", "textures": {"layer0": NS + "item/hextech_upgrade_smithing_template"}})
    for slot in SLOTS:
        w(A + "models/item/hextech_engineer_%s.json" % slot, {"parent": "item/generated", "textures": {"layer0": NS + "item/hextech_engineer_" + slot}})
    for item, model in SCEPTERS:
        w(A + "models/item/%s.json" % item, {
            "loader": "forge:separate_transforms", "gui_light": "front",
            "base": {"parent": "builtin/entity", "textures": {"particle": NS + "item/" + item}, "display": STAFF_DISPLAY},
            "perspectives": {"gui": {"parent": "item/generated", "textures": {"layer0": NS + "item/" + item}}}})
    w(A + "models/item/clockwork_spellbook.json", book_model("clockwork_spellbook"))
    w(A + "models/item/clockwork_codex.json", book_model("clockwork_codex"))

    # tags
    w("data/irons_spellbooks/tags/items/staff.json", {"replace": False, "values": [NS + "clockwork_scepter"] + [NS + s for s, _ in SCEPTERS]})
    for slot, plural in zip(SLOTS, ["helmets", "chestplates", "leggings", "boots"]):
        w("data/irons_spellbooks/tags/items/armors/%s.json" % plural, {"replace": False, "values": [NS + "clockwork_engineer_" + slot, NS + "hextech_engineer_" + slot]})
    w("data/curios/tags/items/spellbook.json", {"replace": False, "values": [NS + "clockwork_spellbook", NS + "clockwork_codex"]})


EN = {
    "death.attack.iss_technomancy.hextech_blast": "%1$s was vaporised by the Tech Dragon's dying blast",
    "death.attack.iss_technomancy.hextech_blast.player": "%1$s was vaporised by the dying blast of %2$s",
    "item.iss_technomancy.hextech_upgrade_smithing_template": "Smithing Template",
    "item.iss_technomancy.smithing_template.hextech.title": "Hextech Upgrade",
    "item.iss_technomancy.smithing_template.hextech.applies_to": "Clockwork Engineer armor, Clockwork / Hextech Scepter, Clockwork Spellbook",
    "item.iss_technomancy.smithing_template.hextech.ingredients": "Tech Dragon Core",
    "item.iss_technomancy.smithing_template.hextech.base_slot": "Add a Clockwork armor piece, scepter or spellbook",
    "item.iss_technomancy.smithing_template.hextech.additions_slot": "Add a Tech Dragon Core",
    "item.iss_technomancy.hextech_engineer_helmet": "Hextech Engineer Visor",
    "item.iss_technomancy.hextech_engineer_chestplate": "Hextech Engineer Robe",
    "item.iss_technomancy.hextech_engineer_leggings": "Hextech Engineer Greaves",
    "item.iss_technomancy.hextech_engineer_boots": "Hextech Engineer Boots",
    "item.iss_technomancy.hextech_scepter": "Hextech Scepter",
    "item.iss_technomancy.hextech_scepter_star1": "Hextech Scepter ★",
    "item.iss_technomancy.hextech_scepter_star2": "Hextech Scepter ★★",
    "item.iss_technomancy.hextech_scepter_star3": "Hextech Scepter ★★★",
    "item.iss_technomancy.clockwork_spellbook": "Clockwork Spellbook",
    "item.iss_technomancy.clockwork_codex": "Hextech Codex",
    "tooltip.iss_technomancy.scepter_upgrade": "Smithing: Hextech template + Tech Dragon Core for the next star",
    "tooltip.iss_technomancy.evolution.title": "Full set: Glorious Evolution",
    "tooltip.iss_technomancy.evolution.desc": "Dropping below 50%% health evolves a random buff for 10 s. Cooldown %ss.",
    "tooltip.iss_technomancy.evolution.pool": "Speed, Overdrive, Focus (cooldowns -40%%), Power, Mana surge, Plating, Repair",
    "message.iss_technomancy.evolution": "Glorious Evolution: %s",
    "message.iss_technomancy.evolution.speed": "Overclocked legs (Speed II)",
    "message.iss_technomancy.evolution.overdrive": "Overdrive",
    "message.iss_technomancy.evolution.focus": "Focus (cooldowns cut)",
    "message.iss_technomancy.evolution.power": "Power (+15% spell power)",
    "message.iss_technomancy.evolution.mana": "Mana surge",
    "message.iss_technomancy.evolution.plating": "Hextech plating",
    "message.iss_technomancy.evolution.repair": "Self repair",
    "effect.iss_technomancy.evolved_focus": "Evolved Focus",
    "effect.iss_technomancy.evolved_power": "Evolved Power",
    "entity.iss_technomancy.arc_ring": "Shock Ring",
    "entity.iss_technomancy.dragon_debris": "Debris",
}
VI = {
    "death.attack.iss_technomancy.hextech_blast": "%1$s bị vụ nổ hextech của Rồng Công Nghệ thiêu rụi",
    "death.attack.iss_technomancy.hextech_blast.player": "%1$s bị vụ nổ hấp hối của %2$s thiêu rụi",
    "item.iss_technomancy.hextech_upgrade_smithing_template": "Khuôn Rèn",
    "item.iss_technomancy.smithing_template.hextech.title": "Nâng cấp Hextech",
    "item.iss_technomancy.smithing_template.hextech.applies_to": "Giáp Kỹ Sư Đồng Hồ, Trượng Đồng Hồ / Hextech, Sách Phép Đồng Hồ",
    "item.iss_technomancy.smithing_template.hextech.ingredients": "Lõi Rồng Công Nghệ",
    "item.iss_technomancy.smithing_template.hextech.base_slot": "Đặt món giáp Đồng Hồ, trượng hoặc sách phép",
    "item.iss_technomancy.smithing_template.hextech.additions_slot": "Đặt Lõi Rồng Công Nghệ",
    "item.iss_technomancy.hextech_engineer_helmet": "Mũ Kính Kỹ Sư Hextech",
    "item.iss_technomancy.hextech_engineer_chestplate": "Áo Choàng Kỹ Sư Hextech",
    "item.iss_technomancy.hextech_engineer_leggings": "Giáp Chân Kỹ Sư Hextech",
    "item.iss_technomancy.hextech_engineer_boots": "Giày Kỹ Sư Hextech",
    "item.iss_technomancy.hextech_scepter": "Trượng Hextech",
    "item.iss_technomancy.hextech_scepter_star1": "Trượng Hextech ★",
    "item.iss_technomancy.hextech_scepter_star2": "Trượng Hextech ★★",
    "item.iss_technomancy.hextech_scepter_star3": "Trượng Hextech ★★★",
    "item.iss_technomancy.clockwork_spellbook": "Sách Phép Đồng Hồ",
    "item.iss_technomancy.clockwork_codex": "Mật Điển Hextech",
    "tooltip.iss_technomancy.scepter_upgrade": "Bàn rèn: khuôn Hextech + Lõi Rồng Công Nghệ để lên sao",
    "tooltip.iss_technomancy.evolution.title": "Đủ bộ: Tiến Hóa Vinh Quang",
    "tooltip.iss_technomancy.evolution.desc": "Máu tụt dưới 50%% sẽ tiến hóa ngẫu nhiên 1 buff trong 10 giây. Hồi %s giây.",
    "tooltip.iss_technomancy.evolution.pool": "Tốc độ, Quá Tải, Tập Trung (hồi chiêu -40%%), Sức Mạnh, Dâng Mana, Mạ Giáp, Tự Sửa",
    "message.iss_technomancy.evolution": "Tiến Hóa Vinh Quang: %s",
    "message.iss_technomancy.evolution.speed": "Chân ép xung (Tốc độ II)",
    "message.iss_technomancy.evolution.overdrive": "Quá Tải",
    "message.iss_technomancy.evolution.focus": "Tập Trung (giảm hồi chiêu)",
    "message.iss_technomancy.evolution.power": "Sức Mạnh (+15% sức mạnh phép)",
    "message.iss_technomancy.evolution.mana": "Dâng Mana",
    "message.iss_technomancy.evolution.plating": "Mạ Giáp Hextech",
    "message.iss_technomancy.evolution.repair": "Tự Sửa Chữa",
    "effect.iss_technomancy.evolved_focus": "Tiến Hóa: Tập Trung",
    "effect.iss_technomancy.evolved_power": "Tiến Hóa: Sức Mạnh",
    "entity.iss_technomancy.arc_ring": "Vòng Sóng Điện",
    "entity.iss_technomancy.dragon_debris": "Mảnh Đất Đá",
}


def run(w, R):
    damage(w)
    items(w)
    import books_altar_v6
    w(A + "models/block/clockwork_altar.json", books_altar_v6.altar_model())
