package net.isstechnomancy.entity.boss;

import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.isstechnomancy.registry.TechEntities;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * Hextech Pylon: one of the four towers the Tech Dragon raises at 30% health (~18 blocks tall, 120 health). While it
 * stands it pours power into the dragon's chest core (a beam drawn by the renderer) and keeps its shield up. It rises
 * out of the ground (invulnerable while rising), turns its eye toward the dragon and collapses back into the ground
 * when destroyed or when the dragon's charge ends.
 */
public class HextechPylon extends Mob implements GeoEntity {
    public static final float SCALE = 2.0f;
    public static final int RISE_TICKS = 44;
    public static final int COLLAPSE_TICKS = 40;
    /** Eye height above the base (model px 122 at scale 2). */
    public static final double EYE_HEIGHT = 122 / 16.0 * SCALE;

    private static final EntityDataAccessor<Integer> DATA_DRAGON = SynchedEntityData.defineId(HextechPylon.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_COLLAPSE = SynchedEntityData.defineId(HextechPylon.class, EntityDataSerializers.INT);
    public static final java.util.List<String> ANIMATION_NAMES = DragonAnimationNames.PYLON;
    private static final RawAnimation RISE = RawAnimation.begin().thenPlayAndHold("rise");
    private static final RawAnimation CHARGE = RawAnimation.begin().thenLoop("charge");
    private static final RawAnimation COLLAPSE = RawAnimation.begin().thenPlayAndHold("collapse");

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private int age;

    public HextechPylon(EntityType<? extends HextechPylon> type, Level level) {
        super(type, level);
        this.noCulling = true;
        setNoGravity(true);
        setPersistenceRequired();
    }

    public HextechPylon(Level level, TechDragon dragon) {
        this(TechEntities.HEXTECH_PYLON.get(), level);
        this.entityData.set(DATA_DRAGON, dragon.getId());
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 120)
                .add(Attributes.ARMOR, 4)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1)
                .add(Attributes.MOVEMENT_SPEED, 0);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_DRAGON, -1);
        this.entityData.define(DATA_COLLAPSE, -1);
    }

    @Nullable
    public TechDragon getDragon() {
        Entity e = level().getEntity(this.entityData.get(DATA_DRAGON));
        return e instanceof TechDragon d && d.isAlive() ? d : null;
    }

    public boolean isCollapsing() {
        return this.entityData.get(DATA_COLLAPSE) >= 0;
    }

    public boolean isRising() {
        return age < RISE_TICKS;
    }

    /** Beams flow while risen, standing and the dragon is still drinking. */
    public boolean isCharging() {
        TechDragon d = getDragon();
        return !isRising() && !isCollapsing() && isAlive() && d != null && d.getState() == TechDragon.State.PYLON_CHARGE;
    }

    public Vec3 eyePosition() {
        double yaw = Math.toRadians(getYRot());
        return position().add(-Math.sin(yaw) * 2.0, EYE_HEIGHT, Math.cos(yaw) * 2.0);
    }

    public void collapse() {
        if (!isCollapsing()) {
            this.entityData.set(DATA_COLLAPSE, 0);
            playSound(SoundEvents.BEACON_DEACTIVATE, 4f, 0.5f);
            playSound(SoundEvents.GENERIC_EXPLODE, 2f, 0.8f);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + EYE_HEIGHT, getZ(), 60, 2, 2, 2, 0.5, true);
            MagicManager.spawnParticles(level(), ParticleTypes.EXPLOSION, getX(), getY() + EYE_HEIGHT, getZ(), 3, 1.5, 1.5, 1.5, 0, true);
        }
    }

    @Override
    public void tick() {
        super.tick();
        age++;
        setDeltaMovement(Vec3.ZERO);
        if (level().isClientSide) {
            if (isCharging() && random.nextInt(2) == 0) {
                Vec3 eye = eyePosition();
                level().addParticle(ParticleTypes.ELECTRIC_SPARK, eye.x + random.nextGaussian() * 0.6, eye.y + random.nextGaussian() * 0.6, eye.z + random.nextGaussian() * 0.6, 0, 0, 0);
            }
            if (isRising()) {
                level().addParticle(ParticleTypes.CAMPFIRE_COSY_SMOKE, getRandomX(1.5), getY() + 0.2, getRandomZ(1.5), 0, 0.05, 0);
            }
            return;
        }
        int collapse = this.entityData.get(DATA_COLLAPSE);
        if (collapse >= 0) {
            this.entityData.set(DATA_COLLAPSE, collapse + 1);
            if (collapse + 1 >= COLLAPSE_TICKS) {
                discard();
            }
            return;
        }
        TechDragon dragon = getDragon();
        if (dragon == null || dragon.getState() != TechDragon.State.PYLON_CHARGE && age > RISE_TICKS) {
            collapse();
            return;
        }
        // the eye turns to the dragon
        Vec3 to = dragon.position().subtract(position());
        float yaw = (float) (Mth.atan2(to.z, to.x) * Mth.RAD_TO_DEG) - 90f;
        setYRot(Mth.approachDegrees(getYRot(), yaw, 6f));
        yBodyRot = getYRot();
        yHeadRot = getYRot();
        if (age == 2) {
            playSound(SoundEvents.ANVIL_PLACE, 3f, 0.5f);
        }
        if (age == RISE_TICKS) {
            playSound(SoundEvents.BEACON_ACTIVATE, 4f, 0.9f);
        }
        if (isCharging() && age % 40 == 0) {
            playSound(SoundEvents.BEACON_AMBIENT, 3f, 1.4f);
        }
    }

    @Override
    public boolean hurt(@NotNull DamageSource source, float amount) {
        if (isRising() || isCollapsing() || source.getEntity() instanceof TechDragon || source.getEntity() instanceof HextechPylon) {
            return false;
        }
        // only attacks break it: never terrain (it may stand half inside a hill), crowding, drowning, fire...
        if (source.getEntity() == null && !source.is(net.minecraft.tags.DamageTypeTags.IS_EXPLOSION)
                && !source.is(net.minecraft.tags.DamageTypeTags.BYPASSES_INVULNERABILITY) && !source.is(net.minecraft.world.damagesource.DamageTypes.GENERIC)) {
            return false;
        }
        boolean hurt = super.hurt(source, amount);
        if (hurt && !level().isClientSide) {
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + EYE_HEIGHT * 0.6, getZ(), 12, 1, 3, 1, 0.3, false);
            playSound(SoundEvents.ANVIL_HIT, 2f, 0.6f + random.nextFloat() * 0.2f);
        }
        return hurt;
    }

    @Override
    public void die(@NotNull DamageSource source) {
        super.die(source);
        collapse();
    }

    @Override
    protected void tickDeath() {
        // removal is handled by the collapse timer
        if (!level().isClientSide && !isCollapsing()) {
            collapse();
        }
        int c = this.entityData.get(DATA_COLLAPSE);
        if (!level().isClientSide && c >= COLLAPSE_TICKS) {
            discard();
        } else if (!level().isClientSide && c >= 0) {
            this.entityData.set(DATA_COLLAPSE, c + 1);
        }
    }

    @Override
    public boolean isInWall() {
        return false;
    }

    @Override
    public boolean canBeAffected(@NotNull MobEffectInstance effect) {
        return false;
    }

    @Override
    public void push(double x, double y, double z) {
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    protected void doPush(@NotNull Entity entity) {
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }

    @Override
    protected boolean shouldDropLoot() {
        return false;
    }

    @Override
    public boolean isAlliedTo(@NotNull Entity entity) {
        return entity instanceof TechDragon dragon && dragon == getDragon() || super.isAlliedTo(entity);
    }

    @Override
    public void addAdditionalSaveData(@NotNull CompoundTag tag) {
        super.addAdditionalSaveData(tag);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 4, state ->
                state.setAndContinue(isCollapsing() || isDeadOrDying() ? COLLAPSE : isRising() ? RISE : CHARGE)));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
