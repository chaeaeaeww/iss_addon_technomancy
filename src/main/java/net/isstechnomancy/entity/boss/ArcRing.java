package net.isstechnomancy.entity.boss;

import net.isstechnomancy.registry.TechEntities;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;

/**
 * An electric "sound wave" (1.9): a ring of jagged lightning that races outward from a point and fades, with a softer
 * glow ring trailing it and sparks jumping up from its edge. Purely visual; drawn by ArcRingRenderer in the additive
 * lightning render type. The ring lies in the plane facing {@code (yaw, pitch)}: pitch 90 = flat on the ground.
 */
public class ArcRing extends Entity {
    private static final EntityDataAccessor<Float> DATA_RADIUS = SynchedEntityData.defineId(ArcRing.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Integer> DATA_LIFE = SynchedEntityData.defineId(ArcRing.class, EntityDataSerializers.INT);
    /** 0 cyan-white (lightning), 1 violet-white (hextech core), 2 ember (overload). */
    private static final EntityDataAccessor<Integer> DATA_STYLE = SynchedEntityData.defineId(ArcRing.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Float> DATA_YAW = SynchedEntityData.defineId(ArcRing.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Float> DATA_PITCH = SynchedEntityData.defineId(ArcRing.class, EntityDataSerializers.FLOAT);

    public ArcRing(EntityType<? extends ArcRing> type, Level level) {
        super(type, level);
        this.noPhysics = true;
        this.noCulling = true;
    }

    /** A ring flat on the ground. */
    public static ArcRing flat(Level level, Vec3 at, float radius, int life, int style) {
        return of(level, at, radius, life, style, 0f, 90f);
    }

    /** A ring standing up, facing (yaw, pitch) like an entity's look (rings around a charging core or mouth). */
    public static ArcRing of(Level level, Vec3 at, float radius, int life, int style, float yaw, float pitch) {
        ArcRing ring = new ArcRing(TechEntities.ARC_RING.get(), level);
        ring.setPos(at.x, at.y, at.z);
        ring.entityData.set(DATA_RADIUS, radius);
        ring.entityData.set(DATA_LIFE, Math.max(2, life));
        ring.entityData.set(DATA_STYLE, style);
        ring.entityData.set(DATA_YAW, yaw);
        ring.entityData.set(DATA_PITCH, pitch);
        return ring;
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(DATA_RADIUS, 4f);
        this.entityData.define(DATA_LIFE, 12);
        this.entityData.define(DATA_STYLE, 0);
        this.entityData.define(DATA_YAW, 0f);
        this.entityData.define(DATA_PITCH, 90f);
    }

    public float getRadius() {
        return this.entityData.get(DATA_RADIUS);
    }

    public int getLife() {
        return this.entityData.get(DATA_LIFE);
    }

    public int getStyle() {
        return this.entityData.get(DATA_STYLE);
    }

    public float getRingYaw() {
        return this.entityData.get(DATA_YAW);
    }

    public float getRingPitch() {
        return this.entityData.get(DATA_PITCH);
    }

    /** 0 at birth, 1 at the end. */
    public float progress(float partialTick) {
        return Math.min(1f, (tickCount + partialTick) / getLife());
    }

    @Override
    public void tick() {
        super.tick();
        if (!level().isClientSide && tickCount > getLife()) {
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
