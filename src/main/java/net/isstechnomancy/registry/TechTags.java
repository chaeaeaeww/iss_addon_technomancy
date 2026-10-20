package net.isstechnomancy.registry;

import net.isstechnomancy.ISSTechnomancy;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.ItemTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.entity.EntityType;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;

public class TechTags {
    /**
     * School focus. Used by Iron's Spells for rune crafting and the Scroll Forge.
     */
    public static final TagKey<Item> TECHNOMANCY_FOCUS = ItemTags.create(ISSTechnomancy.id("technomancy_focus"));

    /** Machines and electric creatures: EMP Screech stuns them. */
    public static final TagKey<EntityType<?>> MECHANICAL = TagKey.create(Registries.ENTITY_TYPE, ISSTechnomancy.id("mechanical"));
    /** Common boss tag (Rocket Grab never reels these in). */
    public static final TagKey<EntityType<?>> BOSSES = TagKey.create(Registries.ENTITY_TYPE, new ResourceLocation("forge", "bosses"));

    public static final ResourceKey<DamageType> TECHNOMANCY_MAGIC = ResourceKey.create(Registries.DAMAGE_TYPE, ISSTechnomancy.id("technomancy_magic"));
}
