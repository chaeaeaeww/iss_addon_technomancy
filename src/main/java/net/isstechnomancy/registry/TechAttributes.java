package net.isstechnomancy.registry;

import io.redspace.ironsspellbooks.api.attribute.MagicPercentAttribute;
import net.isstechnomancy.ISSTechnomancy;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraftforge.event.entity.EntityAttributeModificationEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

/**
 * School power and resistance attributes. Mirrors how Iron's Spells registers its own school attributes,
 * including attaching them to every living entity type so mobs can resist and players can scale Technomancy.
 */
public class TechAttributes {
    private static final DeferredRegister<Attribute> ATTRIBUTES = DeferredRegister.create(Registries.ATTRIBUTE, ISSTechnomancy.MODID);

    public static final RegistryObject<Attribute> TECHNOMANCY_SPELL_POWER = ATTRIBUTES.register("technomancy_spell_power",
            () -> new MagicPercentAttribute("attribute.iss_technomancy.technomancy_spell_power", 1.0D, -100, 100).setSyncable(true));
    public static final RegistryObject<Attribute> TECHNOMANCY_MAGIC_RESIST = ATTRIBUTES.register("technomancy_magic_resist",
            () -> new MagicPercentAttribute("attribute.iss_technomancy.technomancy_magic_resist", 1.0D, -100, 100).setSyncable(true));

    public static void register(IEventBus modEventBus) {
        ATTRIBUTES.register(modEventBus);
        modEventBus.addListener(TechAttributes::modifyEntityAttributes);
    }

    private static void modifyEntityAttributes(EntityAttributeModificationEvent event) {
        event.getTypes().forEach(entityType -> ATTRIBUTES.getEntries().forEach(attribute -> {
            if (!event.has(entityType, attribute.get())) {
                event.add(entityType, attribute.get());
            }
        }));
    }
}
