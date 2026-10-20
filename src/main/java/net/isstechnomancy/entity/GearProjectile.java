package net.isstechnomancy.entity;

import io.redspace.ironsspellbooks.api.util.Utils;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.damage.DamageSources;
import io.redspace.ironsspellbooks.entity.spells.AbstractMagicProjectile;
import net.isstechnomancy.module.TeslaHelper;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSounds;
import net.isstechnomancy.registry.TechSpells;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.Optional;
import java.util.function.Supplier;

/**
 * Brass gear fired by Gear Barrage. Slight gravity, ricochets off block faces a limited number of times,
 * and is consumed on the first entity it damages. The bounce count is synced so client prediction matches the server.
 */
public class GearProjectile extends AbstractMagicProjectile implements GeoEntity {
    private static final EntityDataAccessor<Integer> DATA_BLOCK_BOUNCES = SynchedEntityData.defineId(GearProjectile.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Float> DATA_SCALE = SynchedEntityData.defineId(GearProjectile.class, EntityDataSerializers.FLOAT);
    private static final RawAnimation SPIN = RawAnimation.begin().thenLoop("spin");
    private static final int MAX_FLIGHT_TICKS = 60;
    private static final float BOUNCE_SPEED_RETAINED = 0.8f;

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private int teslaLevel;

    public GearProjectile(EntityType<? extends GearProjectile> entityType, Level level) {
        super(entityType, level);
        this.setNoGravity(false);
    }

    public GearProjectile(Level level, LivingEntity shooter) {
        this(TechEntities.GEAR_PROJECTILE.get(), level);
        setOwner(shooter);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_BLOCK_BOUNCES, 0);
        this.entityData.define(DATA_SCALE, 1f);
    }

    /**
     * Caliber module / boss gears: visual and hitbox scale.
     */
    public void setScale(float scale) {
        this.entityData.set(DATA_SCALE, scale);
        refreshDimensions();
    }

    public float getScale() {
        return this.entityData.get(DATA_SCALE);
    }

    public void setTeslaLevel(int teslaLevel) {
        this.teslaLevel = teslaLevel;
    }

    @Override
    public void onSyncedDataUpdated(@NotNull EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (DATA_SCALE.equals(key)) {
            refreshDimensions();
        }
    }

    @Override
    public @NotNull EntityDimensions getDimensions(@NotNull Pose pose) {
        return super.getDimensions(pose).scale(getScale());
    }

    public int getBlockBounces() {
        return this.entityData.get(DATA_BLOCK_BOUNCES);
    }

    public void setBlockBounces(int bounces) {
        this.entityData.set(DATA_BLOCK_BOUNCES, bounces);
    }

    @Override
    public void tick() {
        super.tick();
        if (!level().isClientSide && tickCount > MAX_FLIGHT_TICKS) {
            impactParticles(getX(), getY(), getZ());
            discard();
        }
    }

    @Override
    protected double getDefaultGravity() {
        return 0.02;
    }

    @Override
    public float getSpeed() {
        return 1.6f;
    }

    @Override
    public void trailParticles() {
        if (tickCount % 2 == 0) {
            Vec3 jitter = Utils.getRandomVec3(0.05);
            level().addParticle(TechParticles.BRASS_SPARK.get(), getX(), getY() + getBbHeight() * 0.5, getZ(), jitter.x, jitter.y, jitter.z);
        }
    }

    @Override
    public void impactParticles(double x, double y, double z) {
        MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), x, y, z, 8, 0.05, 0.05, 0.05, 0.18, false);
    }

    @Override
    public Optional<Supplier<SoundEvent>> getImpactSound() {
        return Optional.of(TechSounds.GEAR_IMPACT);
    }

    @Override
    protected void onHitBlock(@NotNull BlockHitResult result) {
        super.onHitBlock(result);
        int bounces = getBlockBounces();
        if (bounces <= 0) {
            discard();
            return;
        }
        Vec3 motion = getDeltaMovement();
        Vec3 reflected = switch (result.getDirection().getAxis()) {
            case X -> new Vec3(-motion.x, motion.y, motion.z);
            case Y -> new Vec3(motion.x, -motion.y, motion.z);
            case Z -> new Vec3(motion.x, motion.y, -motion.z);
        };
        setDeltaMovement(reflected.scale(BOUNCE_SPEED_RETAINED));
        Vec3 normal = Vec3.atLowerCornerOf(result.getDirection().getNormal());
        Vec3 resting = result.getLocation().add(normal.scale(0.05));
        setPos(resting.x, resting.y, resting.z);
        setBlockBounces(bounces - 1);
        if (!level().isClientSide) {
            level().playSound(null, getX(), getY(), getZ(), TechSounds.GEAR_RICOCHET.get(), SoundSource.NEUTRAL, 1.0f, 0.9f + random.nextFloat() * 0.3f);
        }
    }

    @Override
    protected void onHitEntity(@NotNull EntityHitResult hitResult) {
        super.onHitEntity(hitResult);
        if (!level().isClientSide) {
            Entity owner = getOwner();
            Entity attacker = owner == null ? this : owner;
            // iFrames 0 so every gear of the same volley can land on one target.
            DamageSources.applyDamage(hitResult.getEntity(), damage, TechSpells.GEAR_BARRAGE.get().getDamageSource(this, attacker).setIFrames(0));
            TeslaHelper.arc(this, owner, hitResult.getEntity(), damage, teslaLevel);
        }
        consumeEntityImpact(hitResult, true);
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("BlockBounces", getBlockBounces());
        tag.putFloat("Scale", getScale());
        tag.putInt("Tesla", teslaLevel);
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        setBlockBounces(tag.getInt("BlockBounces"));
        if (tag.contains("Scale")) {
            setScale(tag.getFloat("Scale"));
        }
        teslaLevel = tag.getInt("Tesla");
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "spin", 0, state -> state.setAndContinue(SPIN)));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
