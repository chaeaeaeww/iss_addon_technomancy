package net.isstechnomancy.registry;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.block.ClockworkAltarBlock;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public class TechBlocks {
    private static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(Registries.BLOCK, ISSTechnomancy.MODID);

    public static final RegistryObject<Block> CLOCKWORK_ALTAR = BLOCKS.register("clockwork_altar",
            () -> new ClockworkAltarBlock(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.METAL)
                    .strength(40f, 1200f)
                    .requiresCorrectToolForDrops()
                    .sound(SoundType.NETHERITE_BLOCK)
                    .lightLevel(state -> 7)
                    .noOcclusion()
                    .pushReaction(PushReaction.BLOCK)));

    public static void register(IEventBus modEventBus) {
        BLOCKS.register(modEventBus);
    }
}
