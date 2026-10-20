package net.isstechnomancy.block;

import net.isstechnomancy.entity.boss.TechDragon;
import net.isstechnomancy.registry.TechBlockEntities;
import net.isstechnomancy.registry.TechItems;
import net.isstechnomancy.registry.TechParticles;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.DirectionProperty;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * The Tech Dragon's summoning altar - 1.10: the Hextech Thunderforge (registry id kept: clockwork_altar), an animated
 * clockwork block ({@link HextechForgeBlockEntity}). Use an Overcharged Dynamo Core on it: the core is set in the
 * cradle on top and the summoning begins (6 s of gathering storm, then the dragon). Found in Clockwork Shrines or
 * crafted. Only one dragon may be awake within 96 blocks.
 */
public class ClockworkAltarBlock extends Block implements EntityBlock {
    public static final DirectionProperty FACING = HorizontalDirectionalBlock.FACING;
    private static final VoxelShape SHAPE = Shapes.or(
            // 1.10 forge: plinth, housing, the cradle on top, the four crystal pylons
            Block.box(0, 0, 0, 16, 3.5, 16),
            Block.box(2.5, 3.5, 2.5, 13.5, 13.5, 13.5),
            Block.box(5, 13.5, 5, 11, 15, 11),
            Block.box(1, 3.5, 1, 3, 15, 3), Block.box(13, 3.5, 1, 15, 15, 3),
            Block.box(1, 3.5, 13, 3, 15, 15), Block.box(13, 3.5, 13, 15, 15, 15));

    public ClockworkAltarBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        // the clock dial faces whoever places it
        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    public @NotNull VoxelShape getShape(@NotNull BlockState state, @NotNull BlockGetter level, @NotNull BlockPos pos, @NotNull CollisionContext context) {
        return SHAPE;
    }

    @Override
    public @NotNull RenderShape getRenderShape(@NotNull BlockState state) {
        return RenderShape.ENTITYBLOCK_ANIMATED;
    }

    @Nullable
    @Override
    public BlockEntity newBlockEntity(@NotNull BlockPos pos, @NotNull BlockState state) {
        return new HextechForgeBlockEntity(pos, state);
    }

    @Nullable
    @Override
    @SuppressWarnings("unchecked")
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(@NotNull Level level, @NotNull BlockState state, @NotNull BlockEntityType<T> type) {
        return type == TechBlockEntities.HEXTECH_FORGE.get()
                ? (BlockEntityTicker<T>) (BlockEntityTicker<HextechForgeBlockEntity>) HextechForgeBlockEntity::tick : null;
    }

    @Override
    public @NotNull InteractionResult use(@NotNull BlockState state, @NotNull Level level, @NotNull BlockPos pos, @NotNull Player player,
                                          @NotNull InteractionHand hand, @NotNull BlockHitResult hit) {
        ItemStack stack = player.getItemInHand(hand);
        if (!stack.is(TechItems.OVERCHARGED_DYNAMO_CORE.get())) {
            if (hand == InteractionHand.MAIN_HAND && !level.isClientSide) {
                player.displayClientMessage(Component.translatable("message.iss_technomancy.altar_hint").withStyle(ChatFormatting.GOLD), true);
            }
            return InteractionResult.PASS;
        }
        if (level.isClientSide) {
            return InteractionResult.SUCCESS;
        }
        ServerLevel server = (ServerLevel) level;
        if (!(level.getBlockEntity(pos) instanceof HextechForgeBlockEntity forge)) {
            return InteractionResult.FAIL;
        }
        if (forge.isSummoning()) {
            player.displayClientMessage(Component.translatable("message.iss_technomancy.altar_charging").withStyle(ChatFormatting.AQUA), true);
            return InteractionResult.FAIL;
        }
        if (!server.getEntitiesOfClass(TechDragon.class, new AABB(pos).inflate(96)).isEmpty()) {
            player.displayClientMessage(Component.translatable("message.iss_technomancy.altar_busy").withStyle(ChatFormatting.RED), true);
            return InteractionResult.FAIL;
        }
        if (!player.getAbilities().instabuild) {
            stack.shrink(1);
        }
        forge.startSummon(player);
        return InteractionResult.CONSUME;
    }

    @Override
    public void animateTick(@NotNull BlockState state, @NotNull Level level, @NotNull BlockPos pos, @NotNull RandomSource random) {
        if (random.nextInt(3) == 0) {
            double[] c = HextechForgeBlockEntity.CRYSTALS[random.nextInt(4)];
            level.addParticle(TechParticles.ARC_MOTE.get(), pos.getX() + 0.5 + c[0], pos.getY() + c[1], pos.getZ() + 0.5 + c[2], 0, 0.03, 0);
        }
        if (random.nextInt(14) == 0) {
            level.addParticle(TechParticles.STEAM_PUFF.get(), pos.getX() + 0.5, pos.getY() + 0.9, pos.getZ() + 0.5, 0, 0.04, 0);
        }
    }
}
