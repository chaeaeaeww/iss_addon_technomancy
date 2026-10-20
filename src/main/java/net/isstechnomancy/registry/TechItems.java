package net.isstechnomancy.registry;

import io.redspace.ironsspellbooks.api.registry.AttributeRegistry;
import io.redspace.ironsspellbooks.item.UpgradeOrbItem;
import io.redspace.ironsspellbooks.item.armor.UpgradeOrbType;
import io.redspace.ironsspellbooks.item.weapons.AttributeContainer;
import io.redspace.ironsspellbooks.item.weapons.StaffItem;
import io.redspace.ironsspellbooks.item.weapons.StaffTier;
import io.redspace.ironsspellbooks.registries.UpgradeOrbTypeRegistry;
import net.isstechnomancy.ISSTechnomancy;
import io.redspace.ironsspellbooks.item.SpellBook;
import net.isstechnomancy.item.ClockworkEngineerArmorItem;
import net.isstechnomancy.item.ClockworkStaffItem;
import net.isstechnomancy.item.StaffModuleItem;
import net.isstechnomancy.module.ModuleType;
import net.minecraft.world.item.BlockItem;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraftforge.common.ForgeSpawnEggItem;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;

public class TechItems {
    private static final DeferredRegister<Item> ITEMS = DeferredRegister.create(Registries.ITEM, ISSTechnomancy.MODID);

    /**
     * Datapack-driven upgrade orb type, defined in data/iss_technomancy/irons_spellbooks/upgrade_orb_type/technomancy_power.json
     */
    public static final ResourceKey<UpgradeOrbType> TECHNOMANCY_POWER_ORB_TYPE = ResourceKey.create(UpgradeOrbTypeRegistry.UPGRADE_ORB_REGISTRY_KEY, ISSTechnomancy.id("technomancy_power"));

    /**
     * Clockwork Staff: 5 attack damage, -3 attack speed, +20% Technomancy power, +10% cooldown reduction, +5% spell power.
     * Capacitor modules add more on top (see ClockworkStaffItem).
     */
    public static final StaffTier CLOCKWORK_SCEPTER_TIER = new StaffTier(5, -3,
            new AttributeContainer(TechAttributes.TECHNOMANCY_SPELL_POWER, 0.20, AttributeModifier.Operation.MULTIPLY_BASE),
            new AttributeContainer(AttributeRegistry.COOLDOWN_REDUCTION, 0.10, AttributeModifier.Operation.MULTIPLY_BASE),
            new AttributeContainer(AttributeRegistry.SPELL_POWER, 0.05, AttributeModifier.Operation.MULTIPLY_BASE)
    );

    // School focus
    public static final RegistryObject<Item> ARCANE_COG = ITEMS.register("arcane_cog", () -> new Item(new Item.Properties()));

    // Upgrade materials
    public static final RegistryObject<Item> TECHNOMANCY_RUNE = ITEMS.register("technomancy_rune", () -> new Item(new Item.Properties()));
    public static final RegistryObject<Item> TECHNOMANCY_UPGRADE_ORB = ITEMS.register("technomancy_upgrade_orb",
            () -> new UpgradeOrbItem(new Item.Properties().rarity(Rarity.UNCOMMON).fireResistant(), TECHNOMANCY_POWER_ORB_TYPE));

    // Weapon (registry name kept from the old Clockwork Scepter so existing items upgrade in place)
    public static final RegistryObject<Item> CLOCKWORK_SCEPTER = ITEMS.register("clockwork_scepter",
            () -> new ClockworkStaffItem(new Item.Properties().stacksTo(1).rarity(Rarity.RARE).fireResistant(), CLOCKWORK_SCEPTER_TIER));

    // Staff modules: module_<type>_<tier>
    public static final Map<ModuleType, List<RegistryObject<Item>>> MODULES = registerModules();

    // Boss
    public static final RegistryObject<Item> TECH_DRAGON_CORE = ITEMS.register("tech_dragon_core",
            () -> new Item(new Item.Properties().rarity(Rarity.EPIC).fireResistant()));
    public static final RegistryObject<Item> OVERCHARGED_DYNAMO_CORE = ITEMS.register("overcharged_dynamo_core",
            () -> new Item(new Item.Properties().stacksTo(16).rarity(Rarity.RARE).fireResistant()));
    public static final RegistryObject<Item> CLOCKWORK_ALTAR = ITEMS.register("clockwork_altar",
            () -> new net.isstechnomancy.item.HextechForgeItem(TechBlocks.CLOCKWORK_ALTAR.get(), new Item.Properties().rarity(Rarity.RARE)));
    public static final RegistryObject<Item> TECH_DRAGON_SPAWN_EGG = ITEMS.register("tech_dragon_spawn_egg",
            () -> new ForgeSpawnEggItem(TechEntities.TECH_DRAGON, 0x2B2258, 0x2A86EE, new Item.Properties()));

    public static final RegistryObject<Item> TECHNOMANCER_SPAWN_EGG = ITEMS.register("technomancer_spawn_egg",
            () -> new ForgeSpawnEggItem(TechEntities.TECHNOMANCER, 0x8E1F1F, 0x4FE3C0, new Item.Properties()));

    // 1.9 spellbooks: the 7-slot Clockwork Spellbook (crafting table) and the 12-slot Hextech Codex (smithing: Hextech
    // template + Clockwork Spellbook + Tech Dragon Core). The codex keeps the old 12-slot id so books in worlds keep their spells.
    public static final RegistryObject<Item> CLOCKWORK_SPELLBOOK = ITEMS.register("clockwork_spellbook",
            () -> new net.isstechnomancy.item.TechSpellBookItem(7, new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON))
                    .withSpellbookAttributes(
                            new AttributeContainer(TechAttributes.TECHNOMANCY_SPELL_POWER, 0.08, AttributeModifier.Operation.MULTIPLY_BASE),
                            new AttributeContainer(AttributeRegistry.MAX_MANA, 100, AttributeModifier.Operation.ADDITION)));
    public static final RegistryObject<Item> CLOCKWORK_CODEX = ITEMS.register("clockwork_codex",
            () -> new net.isstechnomancy.item.TechSpellBookItem(12, new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant())
                    .withSpellbookAttributes(
                            new AttributeContainer(TechAttributes.TECHNOMANCY_SPELL_POWER, 0.18, AttributeModifier.Operation.MULTIPLY_BASE),
                            new AttributeContainer(AttributeRegistry.LIGHTNING_SPELL_POWER, 0.10, AttributeModifier.Operation.MULTIPLY_BASE),
                            new AttributeContainer(AttributeRegistry.SPELL_POWER, 0.05, AttributeModifier.Operation.MULTIPLY_BASE),
                            new AttributeContainer(AttributeRegistry.MAX_MANA, 250, AttributeModifier.Operation.ADDITION)));

    // 1.9 Hextech upgrade template (crafted from a netherite upgrade template and a Tech Dragon Core)
    public static final RegistryObject<Item> HEXTECH_UPGRADE_TEMPLATE = ITEMS.register("hextech_upgrade_smithing_template",
            () -> new net.minecraft.world.item.SmithingTemplateItem(
                    net.minecraft.network.chat.Component.translatable("item.iss_technomancy.smithing_template.hextech.applies_to").withStyle(net.minecraft.ChatFormatting.BLUE),
                    net.minecraft.network.chat.Component.translatable("item.iss_technomancy.smithing_template.hextech.ingredients").withStyle(net.minecraft.ChatFormatting.BLUE),
                    net.minecraft.network.chat.Component.translatable("item.iss_technomancy.smithing_template.hextech.title").withStyle(net.minecraft.ChatFormatting.GRAY),
                    net.minecraft.network.chat.Component.translatable("item.iss_technomancy.smithing_template.hextech.base_slot"),
                    net.minecraft.network.chat.Component.translatable("item.iss_technomancy.smithing_template.hextech.additions_slot"),
                    java.util.List.of(new net.minecraft.resources.ResourceLocation("item/empty_armor_slot_helmet"), new net.minecraft.resources.ResourceLocation("item/empty_armor_slot_chestplate"),
                            new net.minecraft.resources.ResourceLocation("item/empty_armor_slot_leggings"), new net.minecraft.resources.ResourceLocation("item/empty_armor_slot_boots"),
                            ISSTechnomancy.id("item/empty_slot_scepter"), ISSTechnomancy.id("item/empty_slot_book")),
                    java.util.List.of(ISSTechnomancy.id("item/empty_slot_dragon_core"))));

    // 1.9 Hextech scepter and its three star levels (each: Hextech template + previous scepter + Tech Dragon Core)
    public static final RegistryObject<Item> HEXTECH_SCEPTER = hextechScepter("hextech_scepter", 0, 7, 0.30, 0.15, 0.12, 0.08);
    public static final RegistryObject<Item> HEXTECH_SCEPTER_1 = hextechScepter("hextech_scepter_star1", 1, 7, 0.35, 0.18, 0.14, 0.10);
    public static final RegistryObject<Item> HEXTECH_SCEPTER_2 = hextechScepter("hextech_scepter_star2", 2, 8, 0.40, 0.21, 0.16, 0.12);
    public static final RegistryObject<Item> HEXTECH_SCEPTER_3 = hextechScepter("hextech_scepter_star3", 3, 8, 0.50, 0.25, 0.18, 0.15);

    private static RegistryObject<Item> hextechScepter(String id, int stars, int damage, double techno, double lightning, double cdr, double power) {
        StaffTier tier = new StaffTier(damage, -3,
                new AttributeContainer(TechAttributes.TECHNOMANCY_SPELL_POWER, techno, AttributeModifier.Operation.MULTIPLY_BASE),
                new AttributeContainer(AttributeRegistry.LIGHTNING_SPELL_POWER, lightning, AttributeModifier.Operation.MULTIPLY_BASE),
                // 1.10 Evo 2: +10% cooldown reduction and +15% mana regeneration
                new AttributeContainer(AttributeRegistry.COOLDOWN_REDUCTION, cdr + (stars >= 2 ? 0.10 : 0), AttributeModifier.Operation.MULTIPLY_BASE),
                new AttributeContainer(AttributeRegistry.SPELL_POWER, power, AttributeModifier.Operation.MULTIPLY_BASE),
                new AttributeContainer(AttributeRegistry.MANA_REGEN, stars >= 2 ? 0.15 : 0, AttributeModifier.Operation.MULTIPLY_BASE),
                new AttributeContainer(AttributeRegistry.CAST_TIME_REDUCTION, stars >= 3 ? 0.10 : 0.03 * stars, AttributeModifier.Operation.MULTIPLY_BASE));
        return ITEMS.register(id, () -> new ClockworkStaffItem(new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant(), tier,
                "hextech_staff", stars));   // 1.10: one scepter (one model) evolving 0-3, like TravelOptics' weapons
    }

    private static Map<ModuleType, List<RegistryObject<Item>>> registerModules() {
        Map<ModuleType, List<RegistryObject<Item>>> map = new EnumMap<>(ModuleType.class);
        for (ModuleType type : ModuleType.values()) {
            map.put(type, List.of(
                    ITEMS.register("module_" + type.id() + "_1", () -> new StaffModuleItem(type, 1)),
                    ITEMS.register("module_" + type.id() + "_2", () -> new StaffModuleItem(type, 2)),
                    ITEMS.register("module_" + type.id() + "_3", () -> new StaffModuleItem(type, 3))));
        }
        return map;
    }

    // Armor
    public static final RegistryObject<Item> CLOCKWORK_ENGINEER_HELMET = ITEMS.register("clockwork_engineer_helmet",
            () -> new ClockworkEngineerArmorItem(ArmorItem.Type.HELMET, new Item.Properties().stacksTo(1)));
    public static final RegistryObject<Item> CLOCKWORK_ENGINEER_CHESTPLATE = ITEMS.register("clockwork_engineer_chestplate",
            () -> new ClockworkEngineerArmorItem(ArmorItem.Type.CHESTPLATE, new Item.Properties().stacksTo(1)));
    public static final RegistryObject<Item> CLOCKWORK_ENGINEER_LEGGINGS = ITEMS.register("clockwork_engineer_leggings",
            () -> new ClockworkEngineerArmorItem(ArmorItem.Type.LEGGINGS, new Item.Properties().stacksTo(1)));
    public static final RegistryObject<Item> CLOCKWORK_ENGINEER_BOOTS = ITEMS.register("clockwork_engineer_boots",
            () -> new ClockworkEngineerArmorItem(ArmorItem.Type.BOOTS, new Item.Properties().stacksTo(1)));

    // 1.9 Hextech Engineer armor (smithing: Hextech template + Clockwork Engineer piece + Tech Dragon Core)
    public static final RegistryObject<Item> HEXTECH_ENGINEER_HELMET = ITEMS.register("hextech_engineer_helmet",
            () -> new net.isstechnomancy.item.HextechArmorItem(ArmorItem.Type.HELMET, new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant()));
    public static final RegistryObject<Item> HEXTECH_ENGINEER_CHESTPLATE = ITEMS.register("hextech_engineer_chestplate",
            () -> new net.isstechnomancy.item.HextechArmorItem(ArmorItem.Type.CHESTPLATE, new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant()));
    public static final RegistryObject<Item> HEXTECH_ENGINEER_LEGGINGS = ITEMS.register("hextech_engineer_leggings",
            () -> new net.isstechnomancy.item.HextechArmorItem(ArmorItem.Type.LEGGINGS, new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant()));
    public static final RegistryObject<Item> HEXTECH_ENGINEER_BOOTS = ITEMS.register("hextech_engineer_boots",
            () -> new net.isstechnomancy.item.HextechArmorItem(ArmorItem.Type.BOOTS, new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant()));

    // Spawn egg: brass shell with cyan spots
    public static final RegistryObject<Item> CLOCKWORK_AUTOMATON_SPAWN_EGG = ITEMS.register("clockwork_automaton_spawn_egg",
            () -> new ForgeSpawnEggItem(TechEntities.CLOCKWORK_AUTOMATON, 0xC8913A, 0x4FE3F0, new Item.Properties()));

    public static void register(IEventBus modEventBus) {
        ITEMS.register(modEventBus);
    }
}
