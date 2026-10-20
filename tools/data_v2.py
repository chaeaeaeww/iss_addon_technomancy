"""
Data for the second content update (Clockwork Staff modules, Tech Dragon boss, Clockwork Altar and Shrine, Clockwork
Codex). Imported by generate_data.py, which calls run(w) and merges SOUNDS / EN / VI into its own outputs.
"""
import gzip
import io
import os
import struct

A = "assets/iss_technomancy/"
D = "data/iss_technomancy/"
NS = "iss_technomancy:"

MODULES = ["splitter", "caliber", "assembler", "capacitor", "tesla"]
ROMAN = {1: "I", 2: "II", 3: "III"}


def ev(name, pitch=1.0, volume=1.0):
    return {"name": name, "type": "event", "pitch": pitch, "volume": volume}


SOUNDS = {
    "entity.tech_dragon.ambient": [ev("minecraft:entity.ender_dragon.ambient", 1.2, 0.8)],
    "entity.tech_dragon.roar": [ev("minecraft:entity.ender_dragon.growl", 0.9), ev("minecraft:entity.lightning_bolt.thunder", 1.4, 0.5)],
    "entity.tech_dragon.hurt": [ev("minecraft:entity.ender_dragon.hurt", 1.1), ev("minecraft:block.anvil.land", 1.6, 0.3)],
    "entity.tech_dragon.death": [ev("minecraft:entity.ender_dragon.death", 1.2, 0.8)],
    "entity.tech_dragon.charge": [ev("minecraft:block.beacon.activate", 1.6), ev("minecraft:block.respawn_anchor.charge", 1.2)],
    "entity.tech_dragon.breath": [ev("minecraft:entity.lightning_bolt.thunder", 1.6, 0.6), ev("minecraft:entity.warden.sonic_boom", 1.4, 0.5)],
    "entity.tech_dragon.spit": [ev("minecraft:block.chain.break", 0.7), ev("minecraft:entity.ender_dragon.shoot", 1.2, 0.8)],
    "entity.tech_dragon.slam": [ev("minecraft:entity.generic.explode", 0.7), ev("minecraft:entity.warden.attack_impact", 0.6)],
}

STAFF_DISPLAY = {
    "thirdperson_righthand": {"translation": [0, 3, 1.25]},
    "thirdperson_lefthand": {"translation": [0, 3, 1.25]},
    "firstperson_righthand": {"translation": [1.5, -1, -2.75], "scale": [0.85, 0.85, 0.85]},
    "firstperson_lefthand": {"translation": [1.5, -1, -2.75], "scale": [0.85, 0.85, 0.85]},
    "ground": {"translation": [0, 4, 0], "scale": [0.45, 0.45, 0.45]},
    "fixed": {"rotation": [0, 0, -45], "translation": [0, -1, -0.75], "scale": [0.45, 0.45, 0.45]},
    "head": {"translation": [0, 12, 0]},
}


def gen(tex):
    return {"parent": "item/generated", "textures": {"layer0": NS + "item/" + tex}}


def shaped(pattern, key, result, count=1, category="misc"):
    k = {}
    for ch, v in key.items():
        k[ch] = {"tag": v[1:]} if v.startswith("#") else {"item": v}
    return {"type": "minecraft:crafting_shaped", "category": category, "pattern": pattern, "key": k, "result": {"item": result, "count": count}}


def item_entry(name, lo=1, hi=1, weight=None, looting=None):
    e = {"type": "minecraft:item", "name": name}
    fns = []
    if (lo, hi) != (1, 1):
        fns.append({"function": "minecraft:set_count", "count": {"min": lo, "max": hi}})
    if looting:
        fns.append({"function": "minecraft:looting_enchant", "count": {"min": 0, "max": looting}})
    if fns:
        e["functions"] = fns
    if weight:
        e["weight"] = weight
    return e


# ------------------------------------------------------------------------------------------- NBT (structure templates)

def _nbt_payload(tag, value, out):
    if tag == 1:
        out.write(struct.pack(">b", value))
    elif tag == 3:
        out.write(struct.pack(">i", value))
    elif tag == 5:
        out.write(struct.pack(">f", value))
    elif tag == 6:
        out.write(struct.pack(">d", value))
    elif tag == 8:
        b = value.encode("utf-8")
        out.write(struct.pack(">H", len(b)))
        out.write(b)
    elif tag == 9:
        elem_tag, items = value
        out.write(struct.pack(">b", elem_tag if items else 0 if elem_tag is None else elem_tag))
        out.write(struct.pack(">i", len(items)))
        for it in items:
            _nbt_payload(elem_tag, it, out)
    elif tag == 10:
        for name, (t, v) in value.items():
            out.write(struct.pack(">b", t))
            nb = name.encode("utf-8")
            out.write(struct.pack(">H", len(nb)))
            out.write(nb)
            _nbt_payload(t, v, out)
        out.write(b"\x00")
    else:
        raise ValueError(tag)


def nbt_file(root):
    buf = io.BytesIO()
    buf.write(struct.pack(">b", 10))
    buf.write(struct.pack(">H", 0))
    _nbt_payload(10, root, buf)
    return gzip.compress(buf.getvalue(), mtime=0)


def S(v):
    return (8, v)


def I(v):
    return (3, v)


def C(d):
    return (10, d)


def L(tag, items):
    return (9, (tag, items))


def shrine_structure():
    """13 x 8 x 13 ruined Clockwork Shrine: copper-and-blackstone dais, four lightning-rod pylons, altar, loot chest."""
    W, H = 13, 8
    blocks = {}
    palette = []
    index = {}

    def state(name, props=None):
        key = (name, tuple(sorted((props or {}).items())))
        if key not in index:
            index[key] = len(palette)
            entry = {"Name": S(name)}
            if props:
                entry["Properties"] = C({k: S(v) for k, v in props.items()})
            palette.append(entry)
        return index[key]

    def put(x, y, z, name, props=None, nbt=None):
        blocks[(x, y, z)] = (state(name, props), nbt)

    c = W // 2
    for x in range(W):
        for z in range(W):
            d = max(abs(x - c), abs(z - c))
            # floor: blackstone bricks with an oxidized copper ring and a copper heart
            if d == 6:
                name = "minecraft:waxed_oxidized_cut_copper" if (x + z) % 2 == 0 else "minecraft:polished_blackstone_bricks"
            elif d <= 1:
                name = "minecraft:waxed_copper_block"
            elif d == 4:
                name = "minecraft:waxed_weathered_cut_copper"
            else:
                name = "minecraft:cracked_polished_blackstone_bricks" if (x * 7 + z * 3) % 5 == 0 else "minecraft:polished_blackstone_bricks"
            put(x, 0, z, name)
            for y in range(1, H):
                put(x, y, z, "minecraft:air")
    # raised dais
    for x in range(c - 2, c + 3):
        for z in range(c - 2, c + 3):
            edge = max(abs(x - c), abs(z - c)) == 2
            put(x, 1, z, "minecraft:polished_blackstone_brick_slab" if edge else "minecraft:waxed_cut_copper",
                {"type": "bottom", "waterlogged": "false"} if edge else None)
    put(c, 2, c, NS + "clockwork_altar")
    # pylons
    for px, pz in ((1, 1), (11, 1), (1, 11), (11, 11)):
        put(px, 1, pz, "minecraft:waxed_copper_block")
        for y in (2, 3, 4):
            put(px, y, pz, "minecraft:chiseled_polished_blackstone" if y == 3 else "minecraft:polished_blackstone_bricks")
        put(px, 5, pz, "minecraft:waxed_cut_copper")
        put(px, 6, pz, "minecraft:lightning_rod", {"facing": "up", "powered": "false", "waterlogged": "false"})
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = px + dx, pz + dz
            if 0 <= nx < W and 0 <= nz < W:
                put(nx, 1, nz, "minecraft:polished_blackstone_brick_stairs",
                    {"facing": {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(dx, dz)], "half": "bottom", "shape": "straight", "waterlogged": "false"})
    for x, z in ((c - 3, c - 3), (c + 3, c - 3), (c - 3, c + 3), (c + 3, c + 3)):
        put(x, 1, z, "minecraft:soul_campfire", {"facing": "north", "lit": "true", "signal_fire": "false", "waterlogged": "false"})
    # broken arch fragments and chains
    for x in range(2, 5):
        put(x, 5, 1, "minecraft:polished_blackstone_brick_slab", {"type": "bottom", "waterlogged": "false"})
    for z in range(8, 11):
        put(11, 5, z, "minecraft:polished_blackstone_brick_slab", {"type": "top", "waterlogged": "false"})
    put(3, 4, 1, "minecraft:chain", {"axis": "y", "waterlogged": "false"})
    put(11, 4, 9, "minecraft:chain", {"axis": "y", "waterlogged": "false"})
    # gear-like iron bar rings beside the dais
    for x, z in ((c - 4, c), (c + 4, c), (c, c - 4)):
        put(x, 1, z, "minecraft:iron_bars", {"east": "false", "north": "false", "south": "false", "west": "false", "waterlogged": "false"})
    put(c, 1, c + 4, "minecraft:chest", {"facing": "north", "type": "single", "waterlogged": "false"},
        nbt=C({"id": S("minecraft:chest"), "LootTable": S(NS + "chests/clockwork_shrine")}))
    put(c - 1, 1, c + 4, "minecraft:barrel", {"facing": "up", "open": "false"},
        nbt=C({"id": S("minecraft:barrel"), "LootTable": S(NS + "chests/clockwork_shrine_supplies")}))

    entities = [{"blockPos": L(3, [c - 3, 1, c + 2]), "pos": L(6, [c - 2.5, 1.0, c + 2.5]),
                 "nbt": C({"id": S(NS + "technomancer"), "PersistenceRequired": (1, 1)})}]
    block_list = []
    for (x, y, z), (st, nbt) in sorted(blocks.items()):
        b = {"pos": L(3, [x, y, z]), "state": I(st)}
        if nbt:
            b["nbt"] = nbt
        block_list.append(b)
    root = {
        "DataVersion": I(3465),
        "size": L(3, [W, H, W]),
        "palette": L(10, palette),
        "blocks": L(10, block_list),
        "entities": L(10, [C(e)[1] for e in entities]),
    }
    return nbt_file(root)


# ------------------------------------------------------------------------------------------- run

def run(w, R):
    # item models
    for m in MODULES:
        for t in (1, 2, 3):
            w(A + "models/item/module_%s_%d.json" % (m, t), gen("module_%s_%d" % (m, t)))
    w(A + "models/item/tech_dragon_core.json", gen("tech_dragon_core"))
    w(A + "models/item/overcharged_dynamo_core.json", gen("overcharged_dynamo_core"))
    w(A + "models/item/tech_dragon_spawn_egg.json", {"parent": "minecraft:item/template_spawn_egg"})
    w(A + "models/item/clockwork_scepter.json", {
        "loader": "forge:separate_transforms",
        "gui_light": "front",
        "base": {"parent": "builtin/entity", "textures": {"particle": NS + "item/clockwork_scepter"}, "display": STAFF_DISPLAY},
        "perspectives": {"gui": {"parent": "item/generated", "textures": {"layer0": NS + "item/clockwork_scepter"}}}})
    w(A + "models/item/clockwork_codex.json", {
        "parent": "minecraft:item/handheld",
        "loader": "forge:separate_transforms",
        "base": {"parent": "irons_spellbooks:item/template_spell_book_model",
                 "textures": {"book": NS + "item/spell_book_models/clockwork_codex", "particle": NS + "item/spell_book_models/clockwork_codex"}},
        "perspectives": {
            "gui": {"parent": "item/generated", "textures": {"layer0": NS + "item/clockwork_codex"}},
            "head": {"parent": "irons_spellbooks:item/template_spell_book_model_open",
                     "textures": {"book": NS + "item/spell_book_models/clockwork_codex", "particle": NS + "item/spell_book_models/clockwork_codex"}}}})

    # altar block
    tex = {"top": NS + "block/clockwork_altar_top", "side": NS + "block/clockwork_altar_side",
           "bottom": NS + "block/clockwork_altar_bottom", "particle": NS + "block/clockwork_altar_side"}

    def el(f, t, top="#top"):
        return {"from": f, "to": t, "faces": {
            "north": {"uv": [f[0], 16 - t[1], t[0], 16 - f[1]], "texture": "#side"},
            "south": {"uv": [f[0], 16 - t[1], t[0], 16 - f[1]], "texture": "#side"},
            "east": {"uv": [f[2], 16 - t[1], t[2], 16 - f[1]], "texture": "#side"},
            "west": {"uv": [f[2], 16 - t[1], t[2], 16 - f[1]], "texture": "#side"},
            "up": {"uv": [f[0], f[2], t[0], t[2]], "texture": top},
            "down": {"uv": [f[0], f[2], t[0], t[2]], "texture": "#bottom"}}}

    w(A + "models/block/clockwork_altar.json", {"parent": "block/block", "textures": tex, "elements": [
        el([0, 0, 0], [16, 4, 16], "#bottom"), el([3, 4, 3], [13, 12, 13], "#bottom"), el([1, 12, 1], [15, 15, 15]),
        el([0, 4, 0], [2, 13, 2], "#bottom"), el([14, 4, 0], [16, 13, 2], "#bottom"), el([0, 4, 14], [2, 13, 16], "#bottom"), el([14, 4, 14], [16, 13, 16], "#bottom")]})
    w(A + "blockstates/clockwork_altar.json", {"variants": {"": {"model": NS + "block/clockwork_altar"}}})
    w(A + "models/item/clockwork_altar.json", {"parent": NS + "block/clockwork_altar"})
    w(D + "loot_tables/blocks/clockwork_altar.json", {"type": "minecraft:block", "pools": [
        {"rolls": 1, "conditions": [{"condition": "minecraft:survives_explosion"}], "entries": [item_entry(NS + "clockwork_altar")]}]})
    w("data/minecraft/tags/blocks/mineable/pickaxe.json", {"replace": False, "values": [NS + "clockwork_altar"]})
    w("data/minecraft/tags/blocks/needs_iron_tool.json", {"replace": False, "values": [NS + "clockwork_altar"]})

    # spellbook slot + staff tag already covers clockwork_scepter
    w("data/curios/tags/items/spellbook.json", {"replace": False, "values": [NS + "clockwork_codex"]})

    # recipes
    type_item = {"splitter": "minecraft:dispenser", "caliber": "minecraft:iron_block", "assembler": "minecraft:piston",
                 "capacitor": "minecraft:redstone_block", "tesla": "minecraft:lightning_rod"}
    for m in MODULES:
        w(D + "recipes/module_%s_1.json" % m, shaped(["IXI", "CPC", "IRI"], {
            "I": "minecraft:iron_ingot", "X": type_item[m], "C": "minecraft:copper_ingot", "P": NS + "arcane_cog", "R": "minecraft:redstone"},
            NS + "module_%s_1" % m))
        w(D + "recipes/module_%s_2.json" % m, shaped(["GRG", "DMD", "GRG"], {
            "G": "minecraft:gold_ingot", "R": NS + "technomancy_rune", "D": "minecraft:diamond", "M": NS + "module_%s_1" % m},
            NS + "module_%s_2" % m))
        w(D + "recipes/module_%s_3.json" % m, shaped(["ERE", "AMA", "ECE"], {
            "E": "irons_spellbooks:energized_core", "R": NS + "technomancy_rune", "A": "irons_spellbooks:arcane_ingot",
            "M": NS + "module_%s_2" % m, "C": NS + "tech_dragon_core"}, NS + "module_%s_3" % m))
    w(D + "recipes/overcharged_dynamo_core.json", shaped(["BNB", "RER", "BAB"], {
        "B": "irons_spellbooks:lightning_bottle", "N": "minecraft:netherite_ingot", "R": NS + "technomancy_rune",
        "E": "irons_spellbooks:energized_core", "A": "irons_spellbooks:arcane_ingot"}, NS + "overcharged_dynamo_core"))
    w(D + "recipes/clockwork_altar.json", shaped(["CRC", "ALA", "PPP"], {
        "C": NS + "arcane_cog", "R": NS + "technomancy_rune", "A": "irons_spellbooks:arcane_ingot", "L": "minecraft:lightning_rod",
        "P": "minecraft:polished_blackstone"}, NS + "clockwork_altar"))
    w(D + "recipes/clockwork_codex.json", shaped(["RDR", "CBC", "RER"], {
        "R": NS + "technomancy_rune", "D": NS + "tech_dragon_core", "C": NS + "arcane_cog", "B": "irons_spellbooks:netherite_spell_book",
        "E": "irons_spellbooks:energized_core"}, NS + "clockwork_codex", category="equipment"))

    # loot
    w(D + "loot_tables/entities/tech_dragon.json", {"type": "minecraft:entity", "pools": [
        {"rolls": 1, "entries": [item_entry(NS + "tech_dragon_core", 2, 4, looting=1)]},
        {"rolls": 1, "entries": [item_entry(NS + "technomancy_rune", 3, 6)]},
        {"rolls": 1, "entries": [item_entry(NS + "arcane_cog", 8, 16)]},
        {"rolls": 1, "entries": [item_entry("irons_spellbooks:energized_core", 1, 3)]},
        {"rolls": 1, "entries": [item_entry(NS + "module_%s_2" % m) for m in MODULES]},
        {"rolls": 1, "conditions": [{"condition": "minecraft:random_chance", "chance": 0.35}], "entries": [item_entry(NS + "module_%s_3" % m) for m in MODULES]},
        {"rolls": 2, "entries": [{"type": "minecraft:item", "name": "irons_spellbooks:scroll", "functions": [
            {"function": "irons_spellbooks:randomize_spell", "quality": {"min": 0.6, "max": 1.0}, "spell_filter": {"school": "iss_technomancy:technomancy"}}]}]},
        {"rolls": 1, "entries": [{"type": "minecraft:item", "name": "irons_spellbooks:scroll", "functions": [
            {"function": "irons_spellbooks:randomize_spell", "quality": {"min": 0.5, "max": 1.0}, "spell_filter": {"school": "irons_spellbooks:lightning"}}]}]},
        {"rolls": 1, "entries": [{"type": "minecraft:item", "name": "irons_spellbooks:scroll", "functions": [
            {"function": "irons_spellbooks:randomize_spell", "quality": {"min": 0.0, "max": 1.0},
             "spell_filter": {"spells": [NS + "summon_tech_drake"], "force": True}}]}]},
    ]})
    w(D + "loot_tables/chests/clockwork_shrine.json", {"type": "minecraft:chest", "pools": [
        {"rolls": 1, "conditions": [{"condition": "minecraft:random_chance", "chance": 0.35}], "entries": [item_entry(NS + "overcharged_dynamo_core")]},
        {"rolls": {"min": 1, "max": 2}, "entries": [item_entry(NS + "module_%s_1" % m) for m in MODULES]},
        {"rolls": 1, "conditions": [{"condition": "minecraft:random_chance", "chance": 0.25}], "entries": [item_entry(NS + "module_%s_2" % m) for m in MODULES]},
        {"rolls": {"min": 2, "max": 4}, "entries": [
            item_entry(NS + "arcane_cog", 2, 6, weight=6), item_entry(NS + "technomancy_rune", 1, 2, weight=3),
            item_entry("irons_spellbooks:lightning_bottle", 1, 2, weight=2), item_entry("irons_spellbooks:energized_core", weight=1),
            item_entry("irons_spellbooks:arcane_ingot", 1, 2, weight=2), item_entry("minecraft:copper_ingot", 4, 12, weight=6)]},
        {"rolls": 1, "entries": [{"type": "minecraft:item", "name": "irons_spellbooks:scroll", "functions": [
            {"function": "irons_spellbooks:randomize_spell", "quality": {"min": 0.2, "max": 0.9}, "spell_filter": {"school": "iss_technomancy:technomancy"}}]}]},
    ]})
    w(D + "loot_tables/chests/clockwork_shrine_supplies.json", {"type": "minecraft:chest", "pools": [
        {"rolls": {"min": 3, "max": 6}, "entries": [
            item_entry("minecraft:copper_ingot", 2, 8, weight=6), item_entry("minecraft:redstone", 2, 8, weight=5),
            item_entry("minecraft:gold_ingot", 1, 3, weight=3), item_entry("minecraft:iron_ingot", 1, 4, weight=4),
            item_entry("irons_spellbooks:arcane_essence", 1, 4, weight=4), item_entry(NS + "arcane_cog", 1, 3, weight=3)]}]})

    # worldgen: Clockwork Shrine
    nbt_path = os.path.join(R, D, "structures", "clockwork_shrine.nbt")
    os.makedirs(os.path.dirname(nbt_path), exist_ok=True)
    with open(nbt_path, "wb") as f:
        f.write(shrine_structure())
    w(D + "worldgen/template_pool/clockwork_shrine/start.json", {
        "name": NS + "clockwork_shrine/start", "fallback": "minecraft:empty",
        "elements": [{"weight": 1, "element": {"element_type": "minecraft:single_pool_element", "location": NS + "clockwork_shrine",
                                                "processors": "minecraft:empty", "projection": "rigid"}}]})
    w(D + "worldgen/structure/clockwork_shrine.json", {
        "type": "minecraft:jigsaw", "biomes": "#" + NS + "has_structure/clockwork_shrine", "step": "surface_structures",
        "spawn_overrides": {}, "terrain_adaptation": "beard_thin", "start_pool": NS + "clockwork_shrine/start", "size": 1,
        "start_height": {"absolute": 0}, "project_start_to_heightmap": "WORLD_SURFACE_WG", "max_distance_from_center": 80,
        "use_expansion_hack": False})
    w(D + "worldgen/structure_set/clockwork_shrine.json", {
        "structures": [{"structure": NS + "clockwork_shrine", "weight": 1}],
        "placement": {"type": "minecraft:random_spread", "spacing": 42, "separation": 16, "salt": 918273645}})
    # entity tags
    def opt(i):
        return {"id": i, "required": False}
    w(D + "tags/entity_types/mechanical.json", {"replace": False, "values": [
        NS + "clockwork_automaton", NS + "brass_sentry", NS + "siege_sentry", NS + "tech_dragon", NS + "tech_drake",
        "minecraft:iron_golem", "minecraft:snow_golem", "minecraft:shulker",
        opt("cataclysm:the_harbinger"), opt("cataclysm:the_watcher"), opt("cataclysm:the_prowler"), opt("cataclysm:netherite_monstrosity"),
        opt("cataclysm:ignis"), opt("alexscaves:magnetron"), opt("alexscaves:teletor"), opt("alexscaves:notor"), opt("alexscaves:ferrouslime"),
        opt("traveloptics:summoned_magnetron"), opt("traveloptics:summoned_the_watcher"), opt("traveloptics:summoned_the_prowler")]})
    w("data/forge/tags/entity_types/bosses.json", {"replace": False, "values": [NS + "tech_dragon"]})
    # Technomancers wander the plains, forests and mountains (rare)
    w(D + "forge/biome_modifier/technomancer_spawns.json", {
        "type": "forge:add_spawns", "biomes": "#" + NS + "has_spawn/technomancer",
        "spawners": {"type": NS + "technomancer", "weight": 3, "minCount": 1, "maxCount": 1}})
    w(D + "tags/worldgen/biome/has_spawn/technomancer.json", {"replace": False, "values": [
        "minecraft:plains", "minecraft:sunflower_plains", "minecraft:meadow", "minecraft:savanna", "minecraft:windswept_hills",
        "minecraft:forest", "minecraft:birch_forest", "minecraft:desert"]})
    w(A + "models/item/technomancer_spawn_egg.json", {"parent": "minecraft:item/template_spawn_egg"})
    w(D + "tags/worldgen/biome/has_structure/clockwork_shrine.json", {"replace": False, "values": [
        "minecraft:plains", "minecraft:sunflower_plains", "minecraft:meadow", "minecraft:desert", "minecraft:windswept_hills",
        "minecraft:windswept_gravelly_hills", "minecraft:stony_peaks", "#minecraft:is_savanna", "#minecraft:is_badlands"]})


# ------------------------------------------------------------------------------------------- lang

def _modules_lang(names, short, desc, roman_fmt):
    out = {}
    for m in MODULES:
        out["module.iss_technomancy." + m] = names[m]
        out["module.iss_technomancy.%s.short" % m] = short[m]
        out["module.iss_technomancy.%s.desc" % m] = desc[m]
        for t in (1, 2, 3):
            out["item.iss_technomancy.module_%s_%d" % (m, t)] = roman_fmt % (names[m], ROMAN[t])
    return out


EN = {
    "item.iss_technomancy.clockwork_scepter": "Clockwork Dynamo Staff",
    "item.iss_technomancy.tech_dragon_core": "Tech Dragon Core",
    "item.iss_technomancy.overcharged_dynamo_core": "Overcharged Dynamo Core",
    "item.iss_technomancy.tech_dragon_spawn_egg": "Tech Dragon Spawn Egg",
    "item.iss_technomancy.clockwork_codex": "Clockwork Codex",
    "block.iss_technomancy.clockwork_altar": "Clockwork Altar",
    "entity.iss_technomancy.tech_dragon": "Tech Dragon, the Thunderforged",
    "container.iss_technomancy.staff_modules": "Staff Modules",
    "tooltip.iss_technomancy.module_tier": "Tier %s Module",
    "tooltip.iss_technomancy.module_hint": "Sneak + use a Clockwork Dynamo Staff to socket it",
    "tooltip.iss_technomancy.staff_modules": "Modules:",
    "tooltip.iss_technomancy.empty_socket": "Empty socket",
    "tooltip.iss_technomancy.staff_hint": "Sneak + use to open the module sockets",
    "message.iss_technomancy.altar_hint": "The altar hums... it craves an Overcharged Dynamo Core.",
    "message.iss_technomancy.altar_busy": "A Tech Dragon is already awake nearby.",
    "message.iss_technomancy.dragon_awakens": "The Tech Dragon awakens! Thunder and gears fill the sky...",
    "subtitles.iss_technomancy.entity.tech_dragon.ambient": "Tech Dragon rumbles",
    "subtitles.iss_technomancy.entity.tech_dragon.roar": "Tech Dragon roars",
    "subtitles.iss_technomancy.entity.tech_dragon.hurt": "Tech Dragon hurts",
    "subtitles.iss_technomancy.entity.tech_dragon.death": "Tech Dragon dies",
    "subtitles.iss_technomancy.entity.tech_dragon.charge": "Tech Dragon charges",
    "subtitles.iss_technomancy.entity.tech_dragon.breath": "Lightning breath crackles",
    "subtitles.iss_technomancy.entity.tech_dragon.spit": "Tech Dragon spits gears",
    "subtitles.iss_technomancy.entity.tech_dragon.slam": "Tech Dragon slams down",
}
EN.update(_modules_lang(
    {"splitter": "Splitter Module", "caliber": "Caliber Module", "assembler": "Assembler Module", "capacitor": "Capacitor Module", "tesla": "Tesla Coil Module"},
    {"splitter": "SPL", "caliber": "CAL", "assembler": "ASM", "capacitor": "CAP", "tesla": "TES"},
    {"splitter": "Level +%s: one more projectile, sentry bolt, volley gear or arc fork per level; wider steam cones",
     "caliber": "Level +%s: +10%% damage and +20%% projectile size per level",
     "assembler": "Level +%s: more Brass Sentries and Automatons per cast, +10%% construct health per level",
     "capacitor": "Level +%s: cooldown reduction, faster casting and Technomancy power on the staff",
     "tesla": "Level +%s: Technomancy hits chain lightning to one more enemy per level"},
    "%s %s"))

VI = {
    "item.iss_technomancy.clockwork_scepter": "Trượng Động Cơ Đồng Hồ",
    "item.iss_technomancy.tech_dragon_core": "Lõi Rồng Công Nghệ",
    "item.iss_technomancy.overcharged_dynamo_core": "Lõi Dynamo Quá Tải",
    "item.iss_technomancy.tech_dragon_spawn_egg": "Trứng Sinh Rồng Công Nghệ",
    "item.iss_technomancy.clockwork_codex": "Mật Điển Đồng Hồ",
    "block.iss_technomancy.clockwork_altar": "Tế Đàn Đồng Hồ",
    "entity.iss_technomancy.tech_dragon": "Rồng Công Nghệ Lôi Đình",
    "container.iss_technomancy.staff_modules": "Mô-đun Trượng",
    "tooltip.iss_technomancy.module_tier": "Mô-đun cấp %s",
    "tooltip.iss_technomancy.module_hint": "Ngồi (Shift) + chuột phải với Trượng Động Cơ để lắp",
    "tooltip.iss_technomancy.staff_modules": "Mô-đun:",
    "tooltip.iss_technomancy.empty_socket": "Ô trống",
    "tooltip.iss_technomancy.staff_hint": "Shift + chuột phải để mở ô mô-đun",
    "message.iss_technomancy.altar_hint": "Tế đàn rung lên... nó cần một Lõi Dynamo Quá Tải.",
    "message.iss_technomancy.altar_busy": "Đã có một Rồng Công Nghệ đang thức gần đây.",
    "message.iss_technomancy.dragon_awakens": "Rồng Công Nghệ thức tỉnh! Sấm sét và bánh răng phủ kín bầu trời...",
    "subtitles.iss_technomancy.entity.tech_dragon.ambient": "Rồng Công Nghệ gầm gừ",
    "subtitles.iss_technomancy.entity.tech_dragon.roar": "Rồng Công Nghệ gầm thét",
    "subtitles.iss_technomancy.entity.tech_dragon.hurt": "Rồng Công Nghệ bị thương",
    "subtitles.iss_technomancy.entity.tech_dragon.death": "Rồng Công Nghệ gục ngã",
    "subtitles.iss_technomancy.entity.tech_dragon.charge": "Rồng Công Nghệ tích điện",
    "subtitles.iss_technomancy.entity.tech_dragon.breath": "Hơi thở sét lách tách",
    "subtitles.iss_technomancy.entity.tech_dragon.spit": "Rồng Công Nghệ phun bánh răng",
    "subtitles.iss_technomancy.entity.tech_dragon.slam": "Rồng Công Nghệ đập xuống",
}
VI.update(_modules_lang(
    {"splitter": "Mô-đun Đa Nòng", "caliber": "Mô-đun Cỡ Nòng", "assembler": "Mô-đun Lắp Ráp", "capacitor": "Mô-đun Tụ Điện", "tesla": "Mô-đun Cuộn Tesla"},
    {"splitter": "ĐN", "caliber": "CN", "assembler": "LR", "capacitor": "TĐ", "tesla": "TES"},
    {"splitter": "Cấp +%s: thêm một viên đạn, bolt tháp pháo, bánh răng automaton hoặc tia nảy mỗi cấp; nón hơi rộng hơn",
     "caliber": "Cấp +%s: +10%% sát thương và đạn to hơn 20%% mỗi cấp",
     "assembler": "Cấp +%s: thêm Tháp Pháo và Automaton mỗi lần niệm, +10%% máu công trình mỗi cấp",
     "capacitor": "Cấp +%s: giảm hồi chiêu, niệm nhanh hơn và tăng sức mạnh Cơ Khí cho trượng",
     "tesla": "Cấp +%s: đòn Cơ Khí phóng sét nảy sang thêm một kẻ địch mỗi cấp"},
    "%s %s"))


EN.update({
    "entity.iss_technomancy.tech_drake": "Tech Drake",
    "entity.iss_technomancy.rocket_hand": "Rocket Hand",
    "entity.iss_technomancy.magnetic_field": "Magnetic Field",
    "entity.iss_technomancy.technomancer": "Technomancer",
    "item.iss_technomancy.technomancer_spawn_egg": "Technomancer Spawn Egg",
    "item.iss_technomancy.clockwork_shrine_map": "Clockwork Shrine",
    "effect.iss_technomancy.short_circuit": "Short Circuit",
    "effect.iss_technomancy.short_circuit.description": "Locked in place and unable to strike.",
    "spell.iss_technomancy.rocket_grab": "Rocket Grab",
    "spell.iss_technomancy.rocket_grab.guide": "Fire a mechanical fist on a cable. It latches onto the first creature it touches and reels it back to you, short-circuiting it.",
    "spell.iss_technomancy.magnetic_field": "Magnetic Field",
    "spell.iss_technomancy.magnetic_field.guide": "Raise a dome-shaped magnetic field around you. Everything inside but you is slowed and pinned to the ground, flyers are dragged down and projectiles bend away. It deals no damage.",
    "spell.iss_technomancy.emp_screech": "EMP Screech",
    "spell.iss_technomancy.emp_screech.guide": "Unleash a screeching electromagnetic wave that stuns machines and electric creatures for 3 seconds. It deals no damage and does not affect anything else.",
    "spell.iss_technomancy.summon_tech_drake": "Call the Tech Drake",
    "spell.iss_technomancy.summon_tech_drake.guide": "Call a young Tech Dragon to fight at your side with gears, lightning breath and thunder. Only the Tech Dragon carries this secret.",
    "ui.iss_technomancy.stun_duration": "%ss Stun",
    "ui.iss_technomancy.damage_per_second": "%s Damage per Second",
    "ui.iss_technomancy.machine_damage": "%s Damage to Machines",
    "ui.iss_technomancy.drake_power": "%s%% Drake Power",
    "death.attack.iss_technomancy.rocket_grab": "%1$s was yanked in by %2$s",
    "death.attack.iss_technomancy.rocket_grab.item": "%1$s was yanked in by %2$s using %3$s",
    "death.attack.iss_technomancy.magnetic_field": "%1$s was crushed by %2$s's magnetic field",
    "death.attack.iss_technomancy.magnetic_field.item": "%1$s was crushed by %2$s's magnetic field using %3$s",
    "death.attack.iss_technomancy.emp_screech": "%1$s was fried by %2$s's EMP",
    "death.attack.iss_technomancy.emp_screech.item": "%1$s was fried by %2$s's EMP using %3$s",
    "death.attack.iss_technomancy.summon_tech_drake": "%1$s was slain by %2$s's Tech Drake",
    "death.attack.iss_technomancy.summon_tech_drake.item": "%1$s was slain by %2$s's Tech Drake using %3$s",
})
VI.update({
    "entity.iss_technomancy.tech_drake": "Rồng Con Công Nghệ",
    "entity.iss_technomancy.rocket_hand": "Bàn Tay Tên Lửa",
    "entity.iss_technomancy.magnetic_field": "Từ Trường",
    "entity.iss_technomancy.technomancer": "Pháp Sư Cơ Khí",
    "item.iss_technomancy.technomancer_spawn_egg": "Trứng Sinh Pháp Sư Cơ Khí",
    "item.iss_technomancy.clockwork_shrine_map": "Đền Đồng Hồ",
    "effect.iss_technomancy.short_circuit": "Đoản Mạch",
    "effect.iss_technomancy.short_circuit.description": "Bị khoá tại chỗ và không thể ra đòn.",
    "spell.iss_technomancy.rocket_grab": "Kéo Tay Tên Lửa",
    "spell.iss_technomancy.rocket_grab.guide": "Phóng một nắm đấm cơ khí có dây cáp, móc vào sinh vật đầu tiên chạm phải, kéo nó về chỗ bạn và làm nó đoản mạch (choáng).",
    "spell.iss_technomancy.magnetic_field": "Từ Trường",
    "spell.iss_technomancy.magnetic_field.guide": "Tạo một vòm từ trường hình bán cầu quanh bạn. Mọi thứ bên trong trừ bạn bị làm chậm và ghì xuống đất, kẻ bay bị kéo xuống, đạn bị bẻ cong. Không gây sát thương.",
    "spell.iss_technomancy.emp_screech": "Sóng Nhiễu Điện",
    "spell.iss_technomancy.emp_screech.guide": "Phát sóng âm điện từ chói tai làm choáng máy móc và sinh vật điện trong 3 giây. Không gây sát thương, không ảnh hưởng thứ khác.",
    "spell.iss_technomancy.summon_tech_drake": "Triệu Hồi Rồng Con Công Nghệ",
    "spell.iss_technomancy.summon_tech_drake.guide": "Gọi một Rồng Công Nghệ non chiến đấu cùng bạn bằng bánh răng, hơi thở sét và sấm. Chỉ Rồng Công Nghệ nắm giữ bí mật này.",
    "ui.iss_technomancy.stun_duration": "%s giây choáng",
    "ui.iss_technomancy.damage_per_second": "%s Sát thương mỗi giây",
    "ui.iss_technomancy.machine_damage": "%s Sát thương lên máy móc",
    "ui.iss_technomancy.drake_power": "%s%% Sức mạnh rồng con",
    "death.attack.iss_technomancy.rocket_grab": "%1$s bị %2$s kéo tới",
    "death.attack.iss_technomancy.rocket_grab.item": "%1$s bị %2$s kéo tới bằng %3$s",
    "death.attack.iss_technomancy.magnetic_field": "%1$s bị từ trường của %2$s nghiền nát",
    "death.attack.iss_technomancy.magnetic_field.item": "%1$s bị từ trường của %2$s nghiền nát bằng %3$s",
    "death.attack.iss_technomancy.emp_screech": "%1$s bị EMP của %2$s nướng chín",
    "death.attack.iss_technomancy.emp_screech.item": "%1$s bị EMP của %2$s nướng chín bằng %3$s",
    "death.attack.iss_technomancy.summon_tech_drake": "%1$s bị Rồng Con của %2$s hạ gục",
    "death.attack.iss_technomancy.summon_tech_drake.item": "%1$s bị Rồng Con của %2$s hạ gục bằng %3$s",
})

# 1.6: Tech Dragon v4 (pylons, death shell, rideable drake controls)
EN.update({
    "entity.iss_technomancy.tech_drake": "Tech Dragon (summoned)",
    "entity.iss_technomancy.hextech_pylon": "Hextech Pylon",
    "entity.iss_technomancy.hextech_shell": "Hextech Shell",
    "bossbar.iss_technomancy.pylons": "Hextech Pylons %s/%s - %ss",
    "key.categories.iss_technomancy": "Iron's Technomancy",
    "key.iss_technomancy.drake_descend": "Tech Dragon: descend / land",
    "key.iss_technomancy.drake_roar": "Tech Dragon: Thunder Roar",
    "key.iss_technomancy.drake_grab": "Tech Dragon: jaw grab",
    "spell.iss_technomancy.summon_tech_drake": "Call the Tech Dragon",
    "spell.iss_technomancy.summon_tech_drake.guide": "Call a younger Tech Dragon you can ride: right-click it to mount. Space climbs, Left Ctrl lands, left click bites and rakes, hold right click for lightning breath, R roars, G seizes small prey in its jaws. Only the Tech Dragon carries this secret.",
})
VI.update({
    "entity.iss_technomancy.tech_drake": "Rồng Công Nghệ (triệu hồi)",
    "entity.iss_technomancy.hextech_pylon": "Tháp Hextech",
    "entity.iss_technomancy.hextech_shell": "Vỏ Cầu Hextech",
    "bossbar.iss_technomancy.pylons": "Tháp Hextech %s/%s - %s giây",
    "key.categories.iss_technomancy": "Iron's Technomancy",
    "key.iss_technomancy.drake_descend": "Rồng Công Nghệ: hạ xuống / đáp",
    "key.iss_technomancy.drake_roar": "Rồng Công Nghệ: Gầm Sấm",
    "key.iss_technomancy.drake_grab": "Rồng Công Nghệ: ngậm cắn",
    "spell.iss_technomancy.summon_tech_drake": "Triệu Hồi Rồng Công Nghệ",
    "spell.iss_technomancy.summon_tech_drake.guide": "Gọi một Rồng Công Nghệ trẻ có thể cưỡi: chuột phải để leo lên. Space bay lên, Ctrl trái hạ xuống, chuột trái cắn/cào, giữ chuột phải để thở sét, R gầm sấm, G ngậm cắn con mồi nhỏ. Chỉ Rồng Công Nghệ nắm giữ bí mật này.",
})
