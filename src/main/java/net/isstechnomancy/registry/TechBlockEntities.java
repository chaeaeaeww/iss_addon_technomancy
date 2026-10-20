package net.isstechnomancy.registry;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.block.HextechForgeBlockEntity;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public class TechBlockEntities {
    private static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES = DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, ISSTechnomancy.MODID);

    /** 1.10: the Hextech Thunderforge's clockwork and summoning (on the clockwork_altar block). */
    @SuppressWarnings("DataFlowIssue")
    public static final RegistryObject<BlockEntityType<HextechForgeBlockEntity>> HEXTECH_FORGE = BLOCK_ENTITIES.register("hextech_thunderforge",
            () -> BlockEntityType.Builder.of(HextechForgeBlockEntity::new, TechBlocks.CLOCKWORK_ALTAR.get()).build(null));

    public static void register(IEventBus modEventBus) {
        BLOCK_ENTITIES.register(modEventBus);
    }
}
