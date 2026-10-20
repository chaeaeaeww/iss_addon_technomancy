package net.isstechnomancy.registry;

import io.redspace.ironsspellbooks.api.registry.SchoolRegistry;
import io.redspace.ironsspellbooks.api.spells.SchoolType;
import net.isstechnomancy.ISSTechnomancy;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.Style;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public class TechSchools {
    /**
     * Brass. Also used by Iron's Spells as the targeting/UI color of the school.
     */
    public static final int TECHNOMANCY_COLOR = 0xC8913A;

    private static final DeferredRegister<SchoolType> SCHOOLS = DeferredRegister.create(SchoolRegistry.SCHOOL_REGISTRY_KEY, ISSTechnomancy.MODID);

    public static final ResourceLocation TECHNOMANCY_RESOURCE = ISSTechnomancy.id("technomancy");

    public static final RegistryObject<SchoolType> TECHNOMANCY = SCHOOLS.register(TECHNOMANCY_RESOURCE.getPath(), () -> new SchoolType(
            TECHNOMANCY_RESOURCE,
            TechTags.TECHNOMANCY_FOCUS,
            Component.translatable("school.iss_technomancy.technomancy").withStyle(Style.EMPTY.withColor(TECHNOMANCY_COLOR)),
            TechAttributes.TECHNOMANCY_SPELL_POWER,
            TechAttributes.TECHNOMANCY_MAGIC_RESIST,
            TechSounds.TECHNOMANCY_CAST,
            TechTags.TECHNOMANCY_MAGIC
    ));

    public static void register(IEventBus modEventBus) {
        SCHOOLS.register(modEventBus);
    }
}
