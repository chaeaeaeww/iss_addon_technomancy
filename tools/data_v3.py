"""
Update 1.3 data: the Clockwork Tower structure (Piltover style: cream stone, copper "gold" trim, teal oxidized-copper
roofs, cyan glass, clock faces on all four sides), its worldgen, loot tables and the Blitz guard loot table.

Floors (15 x 15 workshop base, 11 x 11 tower above it):
  y 1-7    workshop: anvils, blast furnaces, grindstone, chains, a Blitz (Automaton Mk.II) guarding on its pad
  y 9-14   library
  y 16-21  engine room / storage
  y 23-28  clock chamber (clock faces outside)
  y 30-35  the Technomancer's study (top floor) with a balcony
  y 36+    teal pyramid roof with a lightning-rod spire
A ladder in the back-left corner connects every floor. Vanilla blocks only (Create blocks can replace them later).
Run through generate_data.py.
"""
import os

from data_v2 import C, I, L, NS, S, item_entry, nbt_file

D = "data/iss_technomancy/"
MODULES = ["splitter", "caliber", "assembler", "capacitor", "tesla"]

W = 15
H = 46
C0 = 7  # centre


class Builder:
    def __init__(self):
        self.blocks = {}
        self.palette = []
        self.index = {}
        self.entities = []

    def state(self, name, props=None):
        key = (name, tuple(sorted((props or {}).items())))
        if key not in self.index:
            self.index[key] = len(self.palette)
            entry = {"Name": S(name)}
            if props:
                entry["Properties"] = C({k: S(v) for k, v in props.items()})
            self.palette.append(entry)
        return self.index[key]

    def put(self, x, y, z, name, props=None, nbt=None):
        if 0 <= x < W and 0 <= y < H and 0 <= z < W:
            self.blocks[(x, y, z)] = (self.state(name, props), nbt)

    def fill(self, x0, y0, z0, x1, y1, z1, name, props=None):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.put(x, y, z, name, props)

    def walls(self, x0, y0, z0, x1, y1, z1, name, props=None):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, z0, name, props)
                self.put(x, y, z1, name, props)
            for z in range(z0, z1 + 1):
                self.put(x0, y, z, name, props)
                self.put(x1, y, z, name, props)

    def entity(self, x, y, z, nbt):
        self.entities.append({"blockPos": L(3, [int(x), int(y), int(z)]), "pos": L(6, [x + 0.5, float(y), z + 0.5]), "nbt": C(nbt)})

    def build(self):
        block_list = []
        for (x, y, z), (st, nbt) in sorted(self.blocks.items()):
            b = {"pos": L(3, [x, y, z]), "state": I(st)}
            if nbt:
                b["nbt"] = nbt
            block_list.append(b)
        root = {"DataVersion": I(3465), "size": L(3, [W, H, W]), "palette": L(10, self.palette),
                "blocks": L(10, block_list), "entities": L(10, [C(e)[1] for e in self.entities])}
        return nbt_file(root)


WALL = "minecraft:smooth_quartz"
WALL2 = "minecraft:calcite"
TRIM = "minecraft:waxed_cut_copper"
TRIM_BLOCK = "minecraft:waxed_copper_block"
PILLAR = "minecraft:quartz_pillar"
FLOOR = "minecraft:polished_diorite"
PLANK = "minecraft:dark_oak_planks"
GLASS = "minecraft:cyan_stained_glass_pane"
ROOF = "minecraft:waxed_oxidized_cut_copper"
ROOF_STAIR = "minecraft:waxed_oxidized_cut_copper_stairs"
DARK = "minecraft:polished_blackstone_bricks"
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}


def chest(b, x, y, z, facing, table, kind="minecraft:chest"):
    props = {"facing": facing, "type": "single", "waterlogged": "false"} if kind == "minecraft:chest" else {"facing": "up", "open": "false"}
    b.put(x, y, z, kind, props, nbt=C({"id": S(kind), "LootTable": S(NS + table)}))


def pane(b, x, y, z, axis):
    """Glass pane connected along an axis ('x' or 'z')."""
    b.put(x, y, z, GLASS, {"east": "true" if axis == "x" else "false", "west": "true" if axis == "x" else "false",
                           "north": "true" if axis == "z" else "false", "south": "true" if axis == "z" else "false", "waterlogged": "false"})


def tower_structure():
    b = Builder()
    # clear everything first (structures only overwrite blocks they contain)
    b.fill(0, 0, 0, W - 1, H - 1, W - 1, "minecraft:air")

    # ------------------------------------------------------------------ foundation and workshop (y 0-8)
    for x in range(W):
        for z in range(W):
            d = max(abs(x - C0), abs(z - C0))
            b.put(x, 0, z, TRIM if d in (2, 5) else (DARK if d == 7 else FLOOR))
    b.walls(0, 1, 0, W - 1, 7, W - 1, WALL)
    # pilasters and copper bands
    for k in (0, 4, 10, 14):
        for y in range(1, 8):
            b.put(k, y, 0, PILLAR, {"axis": "y"})
            b.put(k, y, W - 1, PILLAR, {"axis": "y"})
            b.put(0, y, k, PILLAR, {"axis": "y"})
            b.put(W - 1, y, k, PILLAR, {"axis": "y"})
    b.walls(0, 7, 0, W - 1, 7, W - 1, TRIM)
    b.walls(0, 1, 0, W - 1, 1, W - 1, WALL2)
    # big arched door at the front (z = 0)
    b.fill(5, 1, 0, 9, 4, 0, "minecraft:air")
    b.fill(6, 5, 0, 8, 5, 0, "minecraft:air")
    for x, y in ((4, 5), (10, 5), (5, 6), (9, 6)):
        b.put(x, y, 0, TRIM_BLOCK)
    b.put(7, 6, 0, "minecraft:waxed_exposed_cut_copper")
    # windows on the workshop walls
    for k in (2, 12):
        for y in (3, 4):
            pane(b, k, y, W - 1, "x")
            pane(b, 0, y, k, "z")
            pane(b, W - 1, y, k, "z")
    for k in (7,):
        for y in (3, 4, 5):
            pane(b, 0, y, k, "z")
            pane(b, W - 1, y, k, "z")
            pane(b, k, y, W - 1, "x")
    # workshop ceiling / library floor (y 8) with a ladder hole
    b.fill(0, 8, 0, W - 1, 8, W - 1, PLANK)
    b.walls(0, 8, 0, W - 1, 8, W - 1, TRIM)
    # Blitz pad at the back of the workshop
    b.fill(5, 0, 8, 9, 0, 12, TRIM_BLOCK)
    b.fill(6, 0, 9, 8, 0, 11, "minecraft:waxed_exposed_copper")
    for x, z in ((5, 8), (9, 8), (5, 12), (9, 12)):
        b.put(x, 1, z, "minecraft:lightning_rod", {"facing": "up", "powered": "false", "waterlogged": "false"})
    b.entity(7, 1, 10, {"id": S(NS + "clockwork_automaton"), "Mk2": (1, 1), "Guard": (1, 1), "PersistenceRequired": (1, 1),
                        "Rotation": L(5, [180.0, 0.0])})
    # workbenches along the walls
    b.put(1, 1, 3, "minecraft:anvil", {"facing": "north"})
    b.put(1, 1, 5, "minecraft:smithing_table")
    b.put(1, 1, 6, "minecraft:grindstone", {"face": "floor", "facing": "east"})
    b.put(13, 1, 3, "minecraft:blast_furnace", {"facing": "west", "lit": "false"})
    b.put(13, 1, 4, "minecraft:blast_furnace", {"facing": "west", "lit": "false"})
    b.put(13, 2, 3, "minecraft:chain", {"axis": "y", "waterlogged": "false"})
    b.put(13, 1, 5, "minecraft:cauldron")
    b.put(13, 1, 6, "minecraft:crafting_table")
    b.put(13, 1, 11, "minecraft:piston", {"facing": "up", "extended": "false"})
    b.put(13, 1, 12, "minecraft:piston", {"facing": "up", "extended": "false"})
    b.put(13, 2, 12, "minecraft:observer", {"facing": "north", "powered": "false"})
    b.put(12, 1, 13, "minecraft:barrel", {"facing": "up", "open": "false"})
    chest(b, 11, 1, 13, "north", "chests/clockwork_tower_workshop")
    chest(b, 1, 1, 9, "east", "chests/clockwork_shrine_supplies", "minecraft:barrel")
    b.put(1, 1, 10, "minecraft:barrel", {"facing": "east", "open": "false"})
    b.put(1, 2, 10, "minecraft:barrel", {"facing": "up", "open": "false"})
    # hanging chains and lanterns
    for x, z in ((4, 4), (10, 4), (4, 10), (10, 10)):
        b.put(x, 7, z, "minecraft:chain", {"axis": "y", "waterlogged": "false"})
        b.put(x, 6, z, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})
    b.put(7, 7, 6, "minecraft:chain", {"axis": "y", "waterlogged": "false"})
    b.put(7, 6, 6, "minecraft:chain", {"axis": "y", "waterlogged": "false"})
    b.put(7, 5, 6, "minecraft:anvil", {"facing": "east"})
    # backing pillar for the ladder in the workshop (the shaft wall takes over above y 8)
    for y in range(1, 8):
        b.put(3, y, 12, PILLAR, {"axis": "y"})

    # ------------------------------------------------------------------ tower shaft (x/z 2..12) y 8-35
    t0, t1 = 2, 12
    b.walls(t0, 9, t0, t1, 35, t1, WALL)
    for y in range(9, 36):
        for x, z in ((t0, t0), (t1, t0), (t0, t1), (t1, t1)):
            b.put(x, y, z, PILLAR, {"axis": "y"})
    # buttresses at the corners above the workshop roof
    for x, z in ((1, 1), (13, 1), (1, 13), (13, 13)):
        b.fill(x, 9, z, x, 12, z, WALL2)
        b.put(x, 13, z, "minecraft:smooth_quartz_slab", {"type": "bottom", "waterlogged": "false"})
    # workshop roof terrace edge
    for x in range(W):
        for z in range(W):
            if max(abs(x - C0), abs(z - C0)) == 7:
                b.put(x, 9, z, "minecraft:smooth_quartz_slab", {"type": "bottom", "waterlogged": "false"})
    # copper bands and floors
    for fy in (15, 22, 29):
        b.walls(t0, fy, t0, t1, fy, t1, TRIM)
        b.fill(t0 + 1, fy, t0 + 1, t1 - 1, fy, t1 - 1, PLANK)
    # windows on every floor
    for fy in (11, 18, 32):
        for y in (fy, fy + 1):
            for k in (5, 9):
                pane(b, k, y, t0, "x")
                pane(b, k, y, t1, "x")
                pane(b, t0, y, k, "z")
                pane(b, t1, y, k, "z")
    # one ladder column at x=3, z=11 from the workshop floor to the study, through a hole in every floor
    for y in range(1, 30):
        b.put(3, y, 11, "minecraft:ladder", {"facing": "north", "waterlogged": "false"})

    # ---- library (y 16-21 is floor 3; library is y 9-14)
    for z in range(4, 11):
        for y in (9, 10, 11):
            b.put(t0 + 1, y, z, "minecraft:bookshelf")
            b.put(t1 - 1, y, z, "minecraft:bookshelf")
    b.put(7, 9, 8, "minecraft:lectern", {"facing": "south", "has_book": "false", "powered": "false"})
    b.put(7, 9, 10, "minecraft:dark_oak_stairs", {"facing": "north", "half": "bottom", "shape": "straight", "waterlogged": "false"})
    b.put(7, 14, 7, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})
    b.put(5, 9, 4, "minecraft:candle", {"candles": "3", "lit": "true", "waterlogged": "false"})

    # ---- engine room (y 16-21)
    for x, z in ((5, 5), (9, 5), (5, 9), (9, 9)):
        b.fill(x, 16, z, x, 21, z, "minecraft:chain", {"axis": "y", "waterlogged": "false"})
    b.fill(6, 16, 6, 8, 18, 8, TRIM_BLOCK)
    b.put(7, 19, 7, "minecraft:lightning_rod", {"facing": "up", "powered": "false", "waterlogged": "false"})
    b.put(7, 17, 5, "minecraft:sea_lantern")
    for z in (4, 5, 10):
        b.put(t1 - 1, 16, z, "minecraft:barrel", {"facing": "up", "open": "false"})
    b.put(t1 - 1, 17, 4, "minecraft:barrel", {"facing": "up", "open": "false"})

    # ---- clock chamber (y 23-28) and the clock faces outside
    b.fill(t0 + 1, 23, t0 + 1, t1 - 1, 28, t1 - 1, "minecraft:air")
    for y in range(23, 30):
        b.put(3, y, 11, "minecraft:ladder", {"facing": "north", "waterlogged": "false"})
    clock_faces(b, t0, t1, 26)
    b.put(7, 28, 7, "minecraft:chain", {"axis": "y", "waterlogged": "false"})
    b.put(7, 27, 7, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})

    # ---- top study (y 30-35): the Technomancer's floor with a balcony
    b.put(t1 - 1, 30, 4, "minecraft:enchanting_table")
    for z in range(5, 8):
        b.put(t1 - 1, 30, z, "minecraft:bookshelf")
        b.put(t1 - 1, 31, z, "minecraft:bookshelf")
    b.put(t0 + 1, 30, 4, "minecraft:brewing_stand", {"has_bottle_0": "false", "has_bottle_1": "false", "has_bottle_2": "false"})
    b.put(t0 + 1, 30, 5, "minecraft:crafting_table")
    chest(b, 9, 30, t1 - 1, "north", "chests/clockwork_tower_study")
    b.put(5, 30, t1 - 1, "minecraft:lectern", {"facing": "north", "has_book": "false", "powered": "false"})
    b.put(7, 35, 7, "minecraft:chain", {"axis": "y", "waterlogged": "false"})
    b.put(7, 34, 7, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})
    b.entity(7, 30, 7, {"id": S(NS + "technomancer"), "PersistenceRequired": (1, 1)})
    # balcony around the study: slab walkway and iron railing, door gaps on the front
    for x in range(W):
        for z in range(W):
            d = max(abs(x - C0), abs(z - C0))
            if d == 6:
                b.put(x, 29, z, "minecraft:smooth_quartz_slab", {"type": "top", "waterlogged": "false"})
            if d == 7:
                b.put(x, 29, z, "minecraft:smooth_quartz_slab", {"type": "top", "waterlogged": "false"})
                b.put(x, 30, z, "minecraft:iron_bars", {"east": "true", "west": "true", "north": "true", "south": "true", "waterlogged": "false"})
    b.fill(6, 30, t0, 8, 32, t0, "minecraft:air")
    b.put(6, 33, t0, TRIM_BLOCK)
    b.put(8, 33, t0, TRIM_BLOCK)

    # ------------------------------------------------------------------ roof: teal copper pyramid with a spire
    b.walls(t0, 36, t0, t1, 36, t1, TRIM)
    b.fill(t0 + 1, 36, t0 + 1, t1 - 1, 36, t1 - 1, PLANK)
    for k in range(0, 6):
        lo, hi = t0 - 1 + k, t1 + 1 - k
        y = 37 + k
        if lo > hi:
            break
        for x in range(lo, hi + 1):
            b.put(x, y, lo, ROOF_STAIR, {"facing": "south", "half": "bottom", "shape": "straight", "waterlogged": "false"})
            b.put(x, y, hi, ROOF_STAIR, {"facing": "north", "half": "bottom", "shape": "straight", "waterlogged": "false"})
        for z in range(lo + 1, hi):
            b.put(lo, y, z, ROOF_STAIR, {"facing": "east", "half": "bottom", "shape": "straight", "waterlogged": "false"})
            b.put(hi, y, z, ROOF_STAIR, {"facing": "west", "half": "bottom", "shape": "straight", "waterlogged": "false"})
        for x, z, shape, facing in ((lo, lo, "outer_left", "south"), (hi, lo, "outer_right", "south"), (lo, hi, "outer_right", "north"), (hi, hi, "outer_left", "north")):
            b.put(x, y, z, ROOF_STAIR, {"facing": facing, "half": "bottom", "shape": shape, "waterlogged": "false"})
        if hi - lo > 1:
            b.fill(lo + 1, y, lo + 1, hi - 1, y, hi - 1, ROOF)
    b.put(7, 42, 7, TRIM_BLOCK)
    b.put(7, 43, 7, "minecraft:waxed_exposed_copper")
    b.put(7, 44, 7, "minecraft:lightning_rod", {"facing": "up", "powered": "false", "waterlogged": "false"})
    # small dormer lanterns at the roof corners
    for x, z in ((t0 - 1, t0 - 1), (t1 + 1, t0 - 1), (t0 - 1, t1 + 1), (t1 + 1, t1 + 1)):
        b.put(x, 38, z, "minecraft:lantern", {"hanging": "false", "waterlogged": "false"})
    return b.build()


def clock_faces(b, t0, t1, cy):
    """7x7 round clock faces centred on each side of the clock chamber: copper rim, white dial, dark hands."""
    for side in ("north", "south", "west", "east"):
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                r2 = dx * dx + dy * dy
                if r2 > 11:
                    continue
                if side == "north":
                    x, y, z = C0 + dx, cy + dy, t0
                elif side == "south":
                    x, y, z = C0 - dx, cy + dy, t1
                elif side == "west":
                    x, y, z = t0, cy + dy, C0 - dx
                else:
                    x, y, z = t1, cy + dy, C0 + dx
                if r2 >= 8:
                    name = TRIM_BLOCK if (dx + dy) % 2 == 0 else TRIM
                elif (dx == 0 and dy in (0, 1, 2)) or (dy == 0 and dx in (1, 2)):
                    name = "minecraft:black_concrete"
                elif r2 == 4 and (dx == 0 or dy == 0):
                    name = "minecraft:waxed_exposed_cut_copper"
                else:
                    name = "minecraft:white_concrete"
                b.put(x, y, z, name)


def run(w, R):
    # loot
    w(D + "loot_tables/entities/blitz_guard.json", {"type": "minecraft:entity", "pools": [
        {"rolls": 1, "entries": [item_entry(NS + "arcane_cog", 3, 7, looting=2)]},
        {"rolls": 1, "entries": [item_entry(NS + "technomancy_rune", 1, 2)]},
        {"rolls": 1, "entries": [item_entry("minecraft:copper_ingot", 4, 10, looting=3)]},
        {"rolls": 1, "conditions": [{"condition": "minecraft:killed_by_player"}, {"condition": "minecraft:random_chance", "chance": 0.3}],
         "entries": [item_entry("irons_spellbooks:energized_core")]},
        {"rolls": 1, "conditions": [{"condition": "minecraft:killed_by_player"}, {"condition": "minecraft:random_chance", "chance": 0.25}],
         "entries": [item_entry(NS + "module_%s_2" % m) for m in MODULES]},
    ]})
    w(D + "loot_tables/chests/clockwork_tower_workshop.json", {"type": "minecraft:chest", "pools": [
        {"rolls": {"min": 1, "max": 2}, "entries": [item_entry(NS + "module_%s_1" % m) for m in MODULES]},
        {"rolls": {"min": 3, "max": 6}, "entries": [
            item_entry(NS + "arcane_cog", 2, 6, weight=6), item_entry("minecraft:copper_ingot", 4, 12, weight=6),
            item_entry("minecraft:iron_ingot", 2, 6, weight=4), item_entry("minecraft:redstone", 4, 12, weight=4),
            item_entry("minecraft:gold_ingot", 1, 4, weight=3), item_entry(NS + "technomancy_rune", 1, 2, weight=2),
            item_entry("irons_spellbooks:arcane_essence", 2, 6, weight=3)]},
    ]})
    w(D + "loot_tables/chests/clockwork_tower_study.json", {"type": "minecraft:chest", "pools": [
        {"rolls": 1, "conditions": [{"condition": "minecraft:random_chance", "chance": 0.5}], "entries": [item_entry(NS + "overcharged_dynamo_core")]},
        {"rolls": 1, "entries": [item_entry(NS + "module_%s_2" % m) for m in MODULES]},
        {"rolls": 1, "conditions": [{"condition": "minecraft:random_chance", "chance": 0.15}], "entries": [item_entry(NS + "module_%s_3" % m) for m in MODULES]},
        {"rolls": {"min": 2, "max": 4}, "entries": [
            item_entry(NS + "arcane_cog", 2, 6, weight=5), item_entry(NS + "technomancy_rune", 1, 3, weight=4),
            item_entry("irons_spellbooks:lightning_bottle", 1, 2, weight=2), item_entry("irons_spellbooks:energized_core", weight=2),
            item_entry("irons_spellbooks:arcane_ingot", 1, 2, weight=2)]},
        {"rolls": {"min": 1, "max": 2}, "entries": [{"type": "minecraft:item", "name": "irons_spellbooks:scroll", "functions": [
            {"function": "irons_spellbooks:randomize_spell", "quality": {"min": 0.3, "max": 1.0}, "spell_filter": {"school": "iss_technomancy:technomancy"}}]}]},
    ]})
    # worldgen
    nbt_path = os.path.join(R, D, "structures", "clockwork_tower.nbt")
    os.makedirs(os.path.dirname(nbt_path), exist_ok=True)
    with open(nbt_path, "wb") as f:
        f.write(tower_structure())
    w(D + "worldgen/template_pool/clockwork_tower/start.json", {
        "name": NS + "clockwork_tower/start", "fallback": "minecraft:empty",
        "elements": [{"weight": 1, "element": {"element_type": "minecraft:single_pool_element", "location": NS + "clockwork_tower",
                                                "processors": "minecraft:empty", "projection": "rigid"}}]})
    w(D + "worldgen/structure/clockwork_tower.json", {
        "type": "minecraft:jigsaw", "biomes": "#" + NS + "has_structure/clockwork_tower", "step": "surface_structures",
        "spawn_overrides": {}, "terrain_adaptation": "beard_box", "start_pool": NS + "clockwork_tower/start", "size": 1,
        "start_height": {"absolute": 0}, "project_start_to_heightmap": "WORLD_SURFACE_WG", "max_distance_from_center": 80,
        "use_expansion_hack": False})
    w(D + "worldgen/structure_set/clockwork_tower.json", {
        "structures": [{"structure": NS + "clockwork_tower", "weight": 1}],
        "placement": {"type": "minecraft:random_spread", "spacing": 48, "separation": 20, "salt": 527391846}})
    w(D + "tags/worldgen/biome/has_structure/clockwork_tower.json", {"replace": False, "values": [
        "minecraft:plains", "minecraft:sunflower_plains", "minecraft:meadow", "minecraft:savanna", "minecraft:forest",
        "minecraft:birch_forest", "minecraft:flower_forest", "minecraft:desert", "#minecraft:is_badlands"]})
