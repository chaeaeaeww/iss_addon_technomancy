"""
Iron's Technomancy 1.10 data: the Hextech Thunderforge (blockstate by facing, a particle-only block model, the
animated 3D item), the 3D Overcharged Dynamo Core, one Hextech Scepter model for every Evolution, and lang (the
forge's name and messages, the rider's new keys, the Grand Cannon, the scepter's Evolution tooltip).
"""
NS = "iss_technomancy:"
A = "assets/iss_technomancy/"

STAFF_DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 4.5, 0.75], "scale": [1, 1, 1]},
    "thirdperson_lefthand": {"rotation": [0, 0, 0], "translation": [0, 4.5, 0.75], "scale": [1, 1, 1]},
    "firstperson_righthand": {"rotation": [0, -8, 18], "translation": [1.5, 2.5, 0], "scale": [0.8, 0.8, 0.8]},
    "firstperson_lefthand": {"rotation": [0, 8, -18], "translation": [1.5, 2.5, 0], "scale": [0.8, 0.8, 0.8]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 3, 0], "scale": [0.5, 0.5, 0.5]},
    "fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [0.6, 0.6, 0.6]},
}
FORGE_DISPLAY = {
    "gui": {"rotation": [30, 225, 0], "translation": [0, -1.5, 0], "scale": [0.5, 0.5, 0.5]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 3, 0], "scale": [0.25, 0.25, 0.25]},
    "fixed": {"rotation": [0, 0, 0], "translation": [0, -2, 0], "scale": [0.5, 0.5, 0.5]},
    "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.375, 0.375, 0.375]},
    "thirdperson_lefthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.375, 0.375, 0.375]},
    "firstperson_righthand": {"rotation": [0, 45, 0], "translation": [0, 0, 0], "scale": [0.4, 0.4, 0.4]},
    "firstperson_lefthand": {"rotation": [0, 225, 0], "translation": [0, 0, 0], "scale": [0.4, 0.4, 0.4]},
}
SCEPTERS = ["hextech_scepter", "hextech_scepter_star1", "hextech_scepter_star2", "hextech_scepter_star3"]


def run(w, R):
    # the Thunderforge: rendered by its block entity; the block model only gives the break particles
    w(A + "blockstates/clockwork_altar.json", {"variants": {"facing=%s" % f: {"model": NS + "block/clockwork_altar"} for f in ("north", "south", "east", "west")}})
    w(A + "models/block/clockwork_altar.json", {"textures": {"particle": NS + "block/hextech_thunderforge"}})
    w(A + "models/item/clockwork_altar.json", {"parent": "builtin/entity", "gui_light": "side", "textures": {"particle": NS + "block/hextech_thunderforge"},
                                               "display": FORGE_DISPLAY})
    # the Dynamo Core in 3D (the flat icon stays in the inventory)
    import dynamo_v7
    w(A + "models/item/overcharged_dynamo_core.json", dynamo_v7.model())
    # one Hextech Scepter: every Evolution uses the same model and icon
    for item in SCEPTERS:
        w(A + "models/item/%s.json" % item, {
            "loader": "forge:separate_transforms", "gui_light": "front",
            "base": {"parent": "builtin/entity", "textures": {"particle": NS + "item/hextech_scepter"}, "display": STAFF_DISPLAY},
            "perspectives": {"gui": {"parent": "item/generated", "textures": {"layer0": NS + "item/hextech_scepter"}}}})


EN = {
    "block.iss_technomancy.clockwork_altar": "Hextech Thunderforge",
    "message.iss_technomancy.altar_hint": "The Thunderforge hums... set an Overcharged Dynamo Core in its cradle.",
    "message.iss_technomancy.altar_charging": "The Thunderforge gathers the storm...",
    "message.iss_technomancy.dragon_awakens": "The ball of lightning bursts - the Tech Dragon is here!",
    "entity.iss_technomancy.siege_sentry": "Hextech Grand Cannon",
    "subtitles.iss_technomancy.entity.siege_sentry.shoot": "Grand Cannon fires",
    "key.iss_technomancy.drake_bite": "Tech Dragon: bite",
    "key.iss_technomancy.drake_claw": "Tech Dragon: claw rake",
    "key.iss_technomancy.drake_breath": "Tech Dragon: lightning breath (hold)",
    "key.iss_technomancy.drake_storm": "Tech Dragon: call the storm",
    "item.iss_technomancy.hextech_scepter_star1": "Hextech Scepter",
    "item.iss_technomancy.hextech_scepter_star2": "Hextech Scepter",
    "item.iss_technomancy.hextech_scepter_star3": "Hextech Scepter",
    "tooltip.iss_technomancy.evolution": "  [Evolution %s]",
    "tooltip.iss_technomancy.evolution_benefits": "✦ Evolution Benefits:",
    "tooltip.iss_technomancy.scepter_evo1": "[Evo 1] Static Charge: your spells charge what they hit; the 5th charge calls lightning down on it",
    "tooltip.iss_technomancy.scepter_evo2": "[Evo 2] +10% Cooldown Reduction, +15% Mana Regen; 4 charges are enough",
    "tooltip.iss_technomancy.scepter_evo3": "[Evo 3] Overload: every 20 s your next Technomancy or Lightning spell is cast 1 level higher",
    "tooltip.iss_technomancy.scepter_upgrade": "Evolve: smithing table, Hextech template + Tech Dragon Core",
}

VI = {
    "block.iss_technomancy.clockwork_altar": "Lò Rèn Sấm Hextech",
    "message.iss_technomancy.altar_hint": "Lò Rèn Sấm rung lên... hãy đặt một Lõi Dynamo Quá Tải vào giá đỡ.",
    "message.iss_technomancy.altar_charging": "Lò Rèn Sấm đang gom bão sét...",
    "message.iss_technomancy.dragon_awakens": "Quả cầu sét nổ tung - Rồng Công Nghệ đã xuất hiện!",
    "entity.iss_technomancy.siege_sentry": "Đại Pháo Hextech",
    "subtitles.iss_technomancy.entity.siege_sentry.shoot": "Đại pháo khai hoả",
    "key.iss_technomancy.drake_bite": "Rồng Công Nghệ: cắn",
    "key.iss_technomancy.drake_claw": "Rồng Công Nghệ: cào",
    "key.iss_technomancy.drake_breath": "Rồng Công Nghệ: khạc điện (giữ)",
    "key.iss_technomancy.drake_storm": "Rồng Công Nghệ: gọi trời sét",
    "item.iss_technomancy.hextech_scepter_star1": "Trượng Hextech",
    "item.iss_technomancy.hextech_scepter_star2": "Trượng Hextech",
    "item.iss_technomancy.hextech_scepter_star3": "Trượng Hextech",
    "tooltip.iss_technomancy.evolution": "  [Tiến hóa %s]",
    "tooltip.iss_technomancy.evolution_benefits": "✦ Lợi ích tiến hóa:",
    "tooltip.iss_technomancy.scepter_evo1": "[Evo 1] Tĩnh điện: phép trúng đích nạp điện cho nó; lần nạp thứ 5 gọi sét từ trời đánh xuống",
    "tooltip.iss_technomancy.scepter_evo2": "[Evo 2] +10% giảm hồi chiêu, +15% hồi mana; chỉ cần 4 lần nạp",
    "tooltip.iss_technomancy.scepter_evo3": "[Evo 3] Quá tải: mỗi 20 giây, phép Technomancy hoặc Lightning kế tiếp được +1 cấp",
    "tooltip.iss_technomancy.scepter_upgrade": "Tiến hóa: bàn rèn, khuôn Hextech + Lõi Rồng Công Nghệ",
}
