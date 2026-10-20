package net.isstechnomancy.entity.boss;

import net.isstechnomancy.registry.TechEntities;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;

/**
 * A chunk of ground thrown up when the Tech Dragon crashes down: purely visual (the way Cataclysm throws "falling
 * blocks" that never land - only the idea is borrowed). It copies the look of the block it was torn from, tumbles on
 * its own arc on both sides (the spawn packet carries the velocity) and crumbles into block dust when it lands. It
 * never places, breaks or drops a block, so the terrain is untouched.
 */
public class DragonDebris extends Entity {
    private static final EntityDataAccessor<BlockState> DATA_BLOCK = SynchedEntityData.defineId(DragonDebris.class, EntityDataSerializers.BLOCK_STATE);
    public static final int MAX_LIFE = 60;

    private int life;
    private int grounded;

    public DragonDebris(EntityType<? extends DragonDebris> type, Level level) {
        super(type, level);
    }

    public DragonDebris(Level level, Vec3 at, BlockState block, Vec3 velocity) {
        this(TechEntities.DRAGON_DEBRIS.get(), level);
        setPos(at.x, at.y, at.z);
        setBlock(block);
        setDeltaMovement(velocity);
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_BLOCK, Blocks.STONE.defaultBlockState());
    }

    public BlockState getBlock() {
        return this.entityData.get(DATA_BLOCK);
    }

    public void setBlock(BlockState state) {
        this.entityData.set(DATA_BLOCK, state);
    }

    /** Tumble angle for the renderer (degrees), different per piece. */
    public float spin(float partialTick) {
        return (life + partialTick) * (9f + (getId() % 7) * 2.5f) * ((getId() & 1) == 0 ? 1 : -1);
    }

    @Override
    public void tick() {
        super.tick();
        life++;
        Vec3 v = getDeltaMovement().add(0, -0.06, 0);
        move(MoverType.SELF, v);
        setDeltaMovement(getDeltaMovement().multiply(0.98, 0.98, 0.98));
        if (onGround() && life > 3) {
            grounded++;
            setDeltaMovement(getDeltaMovement().multiply(0.4, 0, 0.4));
            if (grounded == 1 && level().isClientSide) {
                for (int i = 0; i < 8; i++) {
                    level().addParticle(new BlockParticleOption(ParticleTypes.BLOCK, getBlock()), getX() + (random.nextDouble() - 0.5) * 0.8, getY() + 0.2,
                            getZ() + (random.nextDouble() - 0.5) * 0.8, (random.nextDouble() - 0.5) * 0.3, 0.2, (random.nextDouble() - 0.5) * 0.3);
                }
            }
        }
        if (!level().isClientSide && (grounded > 2 || life > MAX_LIFE)) {
            discard();
        }
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    public boolean isAttackable() {
        return false;
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }

    @Override
    protected void readAdditionalSaveData(@NotNull CompoundTag tag) {
    }

    @Override
    protected void addAdditionalSaveData(@NotNull CompoundTag tag) {
    }
}
