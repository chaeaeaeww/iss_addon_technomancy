package net.isstechnomancy;

import com.mojang.logging.LogUtils;
import net.isstechnomancy.registry.TechAttributes;
import net.isstechnomancy.registry.TechBlockEntities;
import net.isstechnomancy.registry.TechBlocks;
import net.isstechnomancy.registry.TechMenus;
import net.isstechnomancy.registry.TechCreativeTabs;
import net.isstechnomancy.registry.TechEffects;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechItems;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSchools;
import net.isstechnomancy.registry.TechSounds;
import net.isstechnomancy.registry.TechSpells;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;

@Mod(ISSTechnomancy.MODID)
public class ISSTechnomancy {
    public static final String MODID = "iss_technomancy";
    public static final Logger LOGGER = LogUtils.getLogger();

    public ISSTechnomancy() {
        IEventBus modEventBus = FMLJavaModLoadingContext.get().getModEventBus();

        TechAttributes.register(modEventBus);
        TechSounds.register(modEventBus);
        TechParticles.register(modEventBus);
        TechEffects.register(modEventBus);
        TechEntities.register(modEventBus);
        TechBlocks.register(modEventBus);
        TechBlockEntities.register(modEventBus);
        TechItems.register(modEventBus);
        TechMenus.register(modEventBus);
        TechCreativeTabs.register(modEventBus);
        TechSchools.register(modEventBus);
        TechSpells.register(modEventBus);
        net.isstechnomancy.network.TechNetwork.register();
    }

    public static ResourceLocation id(String path) {
        return new ResourceLocation(MODID, path);
    }
}
