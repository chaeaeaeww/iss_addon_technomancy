package net.isstechnomancy.entity;

import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.entity.mobs.AntiMagicSusceptible;
import io.redspace.ironsspellbooks.entity.mobs.IMagicSummon;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.NeutralMob;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.BodyRotationControl;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.Comparator;
import java.util.UUID;

/**
 * Stationary construct deployed by Deploy Brass Sentry.
 * <ul>
 *     <li>Never moves, is immune to knockback and pushing, and is not saved to disk (short-lived).</li>
 *     <li>Tracks its own owner and lifetime (instead of Iron's SummonManager) so Arc Welder can extend it.</li>
 *     <li>Targets monsters, mobs targeting its owner, and whatever its owner recently hit or was hit by.</li>
 * </ul>
 */
public class BrassSentry extends PathfinderMob implements GeoEntity, OwnableEntity, AntiMagicSusceptible {
    public static final double TARGET_RANGE = 16;
    public static final double MAX_OWNER_DISTANCE = 48;
    public static final int FIRE_INTERVAL = 20;
    public static final int OVERCLOCK_FIRE_INTERVAL = 13;
    public static final int OVERCLOCK_TICKS = 60;
    public static final int WELD_HEAL = 2;
    public static final int WELD_LIFETIME_BONUS = 20;
    /** 1.10: the assembly (spawn) and fold-away (despawn) animations are longer. */
    public static final int SPAWN_ANIMATION_TICKS = 28;
    public static final int DESPAWN_ANIMATION_TICKS = 20;
    private static final int OWNER_AGGRO_MEMORY_TICKS = 100;

    private static final EntityDataAccessor<Integer> DATA_OVERCLOCK_TICKS = SynchedEntityData.defineId(BrassSentry.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_DESPAWN_TICKS = SynchedEntityData.defineId(BrassSentry.class, EntityDataSerializers.INT);

    protected static final RawAnimation ANIM_SPAWN = RawAnimation.begin().thenPlay("spawn");
    protected static final RawAnimation ANIM_IDLE = RawAnimation.begin().thenLoop("idle");
    protected static final RawAnimation ANIM_OVERCLOCK = RawAnimation.begin().thenLoop("overclock");
    protected static final RawAnimation ANIM_DESPAWN = RawAnimation.begin().thenPlayAndHold("despawn");
    private static final RawAnimation ANIM_SHOOT = RawAnimation.begin().thenPlay("shoot");

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    @Nullable
    private UUID ownerUUID;
    @Nullable
    private LivingEntity cachedOwner;
    @Nullable
    private LivingEntity currentTarget;
    private float boltDamage;
    private int lifeTicks;
    private int maxLifeTicks;
    private int fireCooldown = SPAWN_ANIMATION_TICKS;
    private int extraBolts;
    private int teslaLevel;

    public BrassSentry(EntityType<? extends BrassSentry> entityType, Level level) {
        super(entityType, level);
        this.xpReward = 0;
        this.lifeTicks = 20 * 15;
        this.maxLifeTicks = this.lifeTicks;
    }

    public BrassSentry(Level level, LivingEntity owner, float boltDamage, int maxHealth, int lifetimeTicks) {
        this(TechEntities.BRASS_SENTRY.get(), level, owner, boltDamage, maxHealth, lifetimeTicks);
    }

    protected BrassSentry(EntityType<? extends BrassSentry> entityType, Level level, LivingEntity owner, float boltDamage, int maxHealth, int lifetimeTicks) {
        this(entityType, level);
        this.ownerUUID = owner.getUUID();
        this.cachedOwner = owner;
        this.boltDamage = boltDamage;
        this.lifeTicks = lifetimeTicks;
        this.maxLifeTicks = lifetimeTicks;
        var healthAttribute = getAttribute(Attributes.MAX_HEALTH);
        if (healthAttribute != null) {
            healthAttribute.setBaseValue(maxHealth);
        }
        setHealth(maxHealth);
    }

    /**
     * Staff modules at deploy time: Splitter adds bolts per volley, Tesla makes bolts chain lightning.
     */
    public void setModules(int extraBolts, int teslaLevel) {
        this.extraBolts = extraBolts;
        this.teslaLevel = teslaLevel;
    }

    protected int getExtraBolts() {
        return extraBolts;
    }

    protected int getTeslaLevel() {
        return teslaLevel;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 20)
                .add(Attributes.ARMOR, 6)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1)
                .add(Attributes.MOVEMENT_SPEED, 0)
                .add(Attributes.FOLLOW_RANGE, TARGET_RANGE);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_OVERCLOCK_TICKS, 0);
        this.entityData.define(DATA_DESPAWN_TICKS, -1);
    }

    /* ---------------------------------------------------------------- Ownership */

    @Nullable
    @Override
    public UUID getOwnerUUID() {
        return ownerUUID;
    }

    @Nullable
    @Override
    public LivingEntity getOwner() {
        if (cachedOwner != null && !cachedOwner.isRemoved()) {
            return cachedOwner;
        }
        if (ownerUUID != null && level() instanceof ServerLevel serverLevel && serverLevel.getEntity(ownerUUID) instanceof LivingEntity living) {
            cachedOwner = living;
            return living;
        }
        return null;
    }

    public boolean isOwnedBy(LivingEntity entity) {
        return ownerUUID != null && ownerUUID.equals(entity.getUUID());
    }

    @Override
    public boolean isAlliedTo(@NotNull Entity entity) {
        if (super.isAlliedTo(entity)) {
            return true;
        }
        LivingEntity owner = getOwner();
        if (owner == null) {
            return false;
        }
        if (entity == owner || owner.isAlliedTo(entity)) {
            return true;
        }
        if (entity instanceof OwnableEntity ownable && ownerUUID != null && ownerUUID.equals(ownable.getOwnerUUID())) {
            return true;
        }
        return entity instanceof IMagicSummon summon && summon.getSummoner() == owner;
    }

    /* ---------------------------------------------------------------- State */

    public boolean isOverclocked() {
        return this.entityData.get(DATA_OVERCLOCK_TICKS) > 0;
    }

    public boolean isDespawning() {
        return this.entityData.get(DATA_DESPAWN_TICKS) >= 0;
    }

    /**
     * Arc Welder synergy: repair, extend lifetime (never past the original duration) and overclock.
     */
    public void applyWeld() {
        if (isDespawning()) {
            return;
        }
        heal(WELD_HEAL);
        lifeTicks = Math.min(lifeTicks + WELD_LIFETIME_BONUS, maxLifeTicks);
        if (!isOverclocked()) {
            playSound(TechSounds.SENTRY_OVERCLOCK.get(), 1.0f, 1.0f);
        }
        this.entityData.set(DATA_OVERCLOCK_TICKS, OVERCLOCK_TICKS);
    }

    /**
     * Starts the fold-up animation; the entity removes itself when it finishes.
     */
    public void beginDespawn() {
        if (isDespawning() || level().isClientSide) {
            return;
        }
        this.entityData.set(DATA_DESPAWN_TICKS, DESPAWN_ANIMATION_TICKS);
        this.entityData.set(DATA_OVERCLOCK_TICKS, 0);
        playSound(TechSounds.SENTRY_DESTROYED.get(), 0.8f, 1.2f);
        MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), getX(), getY() + getBbHeight() * 0.7, getZ(), 10, getBbWidth() * 0.4, 0.2,
                getBbWidth() * 0.4, 0.04, false);
    }

    /** 1.10: the summoning, in step with the spawn animation - a cog sigil on the ground and steam as it climbs out,
     * sparks and a clank when the housing locks on, a puff from the stack when it is ready. */
    protected void assemblyEffects() {
        double h = getBbHeight();
        if (tickCount == 1) {
            MagicManager.spawnParticles(level(), TechParticles.COG_SIGIL.get(), getX(), getY() + 0.05, getZ(), 1, 0, 0, 0, 0, true);
            MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), getX(), getY() + 0.2, getZ(), 14, getBbWidth() * 0.5, 0.1, getBbWidth() * 0.5, 0.04, false);
            playSound(net.minecraft.sounds.SoundEvents.PISTON_EXTEND, 0.8f, 0.7f);
        }
        if (tickCount == assembleLockTick()) {
            MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), getX(), getY() + h * 0.6, getZ(), 16, getBbWidth() * 0.4, 0.2, getBbWidth() * 0.4, 0.25, false);
            playSound(net.minecraft.sounds.SoundEvents.ANVIL_PLACE, 0.5f, 1.6f);
        }
        if (tickCount == SPAWN_ANIMATION_TICKS - 4) {
            MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), getX(), getY() + h, getZ(), 8, 0.15, 0.1, 0.15, 0.05, false);
            playSound(net.minecraft.sounds.SoundEvents.FIRE_EXTINGUISH, 0.5f, 1.4f);
        }
    }

    /** Tick at which the housing drops onto the base in the spawn animation. */
    protected int assembleLockTick() {
        return 18;
    }

    private void burstAndRemove(RemovalReason reason) {
        MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), getX(), getY() + 0.6, getZ(), 10, 0.3, 0.3, 0.3, 0.03, false);
        MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), getX(), getY() + 0.6, getZ(), 16, 0.3, 0.3, 0.3, 0.25, false);
        remove(reason);
    }

    /* ---------------------------------------------------------------- Tick */

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide) {
            clientEffects();
            return;
        }
        int despawnTicks = this.entityData.get(DATA_DESPAWN_TICKS);
        if (despawnTicks >= 0) {
            if (despawnTicks == 0) {
                burstAndRemove(RemovalReason.DISCARDED);
            } else {
                this.entityData.set(DATA_DESPAWN_TICKS, despawnTicks - 1);
            }
            return;
        }

        assemblyEffects();
        LivingEntity owner = getOwner();
        if (owner == null || !owner.isAlive() || distanceToSqr(owner) > MAX_OWNER_DISTANCE * MAX_OWNER_DISTANCE || --lifeTicks <= 0) {
            beginDespawn();
            return;
        }

        int overclock = this.entityData.get(DATA_OVERCLOCK_TICKS);
        if (overclock > 0) {
            this.entityData.set(DATA_OVERCLOCK_TICKS, overclock - 1);
        }

        if (currentTarget == null || !isValidTarget(currentTarget, owner) || tickCount % 10 == 0) {
            currentTarget = findTarget(owner);
        }
        if (fireCooldown > 0) {
            fireCooldown--;
        }
        if (currentTarget != null) {
            getLookControl().setLookAt(currentTarget, 30f, 60f);
            if (fireCooldown <= 0 && hasLineOfSight(currentTarget)) {
                fireAt(currentTarget, owner);
                fireCooldown = getFireInterval();
            }
        }
    }

    private void clientEffects() {
        if (isDespawning()) {
            if (random.nextInt(2) == 0) {
                level().addParticle(TechParticles.BRASS_SPARK.get(), getRandomX(0.5), getY() + random.nextDouble() * 0.8, getRandomZ(0.5), 0, 0.1, 0);
            }
            return;
        }
        if (tickCount % 30 == 0 && tickCount > SPAWN_ANIMATION_TICKS) {
            Vec3 vent = ventPosition();
            level().addParticle(TechParticles.STEAM_PUFF.get(), vent.x, vent.y, vent.z, 0, 0.05, 0);
        }
        if (isOverclocked() && random.nextInt(3) == 0) {
            level().addParticle(TechParticles.ARC_MOTE.get(), getRandomX(0.6), getY() + 0.5 + random.nextDouble() * 0.6, getRandomZ(0.6), 0, 0.02, 0);
        }
    }

    /** Top of the steam stack (1.10 model: behind and left of the housing, 20 px up). */
    protected Vec3 ventPosition() {
        double yaw = Math.toRadians(yHeadRot);
        double lx = 1.8 / 16.0, back = 2.6 / 16.0;
        return position().add(Math.cos(yaw) * lx + Math.sin(yaw) * back, 20.5 / 16.0, Math.sin(yaw) * lx - Math.cos(yaw) * back);
    }

    /* ---------------------------------------------------------------- Combat */

    @Nullable
    private LivingEntity findTarget(LivingEntity owner) {
        return level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(getTargetRange()), entity -> isValidTarget(entity, owner))
                .stream()
                .filter(this::hasLineOfSight)
                .min(Comparator.comparingDouble(this::distanceToSqr))
                .orElse(null);
    }

    private boolean isValidTarget(LivingEntity entity, LivingEntity owner) {
        double range = getTargetRange();
        if (entity == this || entity == owner || !entity.isAlive() || isAlliedTo(entity) || distanceToSqr(entity) > range * range) {
            return false;
        }
        if (entity instanceof Player player && (player.isCreative() || player.isSpectator())) {
            return false;
        }
        if (entity instanceof Mob mob && (mob.getTarget() == owner || mob.getTarget() == this)) {
            return true;
        }
        if (entity == owner.getLastHurtByMob()) {
            return true;
        }
        if (entity == owner.getLastHurtMob() && owner.tickCount - owner.getLastHurtMobTimestamp() < OWNER_AGGRO_MEMORY_TICKS) {
            return true;
        }
        boolean calmNeutral = entity instanceof NeutralMob neutral && !neutral.isAngry();
        return entity instanceof Enemy && !calmNeutral;
    }

    protected double getTargetRange() {
        return TARGET_RANGE;
    }

    protected int getFireInterval() {
        return isOverclocked() ? OVERCLOCK_FIRE_INTERVAL : FIRE_INTERVAL;
    }

    protected float getBoltDamage() {
        return boltDamage;
    }

    protected void fireAt(LivingEntity target, LivingEntity owner) {
        Vec3 muzzle = getEyePosition().add(getViewVector(1f).scale(0.6));
        Vec3 direction = target.getBoundingBox().getCenter().subtract(muzzle).normalize();
        int count = 1 + extraBolts;
        for (int i = 0; i < count; i++) {
            float yaw = (i - (count - 1) / 2f) * 5f * net.minecraft.util.Mth.DEG_TO_RAD;
            SentryBolt bolt = new SentryBolt(level(), owner);
            bolt.setPos(muzzle.x, muzzle.y - bolt.getBbHeight() * 0.5, muzzle.z);
            bolt.shoot(direction.yRot(yaw));
            bolt.setDamage(boltDamage);
            bolt.setTeslaLevel(teslaLevel);
            level().addFreshEntity(bolt);
        }
        triggerAnim("action", "shoot");
        level().playSound(null, getX(), getY(), getZ(), TechSounds.SENTRY_SHOOT.get(), SoundSource.NEUTRAL, 0.8f, isOverclocked() ? 1.25f : 1.0f);
        MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), muzzle.x, muzzle.y, muzzle.z, 3, 0.02, 0.02, 0.02, 0.1, false);
    }

    @Override
    public boolean hurt(@NotNull DamageSource source, float amount) {
        Entity attacker = source.getEntity();
        if (attacker != null && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY) && isAlliedTo(attacker)) {
            return false;
        }
        return super.hurt(source, amount);
    }

    @Override
    protected void tickDeath() {
        if (!level().isClientSide && !isRemoved()) {
            playSound(TechSounds.SENTRY_DESTROYED.get(), 1.0f, 1.0f);
            burstAndRemove(RemovalReason.KILLED);
        }
    }

    @Override
    public void onAntiMagic(MagicData playerMagicData) {
        beginDespawn();
    }

    /* ---------------------------------------------------------------- Construct physics */

    @Override
    protected void registerGoals() {
        // Targeting and firing are handled directly in tick(); the sentry has no goals.
    }

    @Override
    protected @NotNull BodyRotationControl createBodyControl() {
        // Keep the tripod base fixed; only the head bone turns (via look control).
        return new BodyRotationControl(this) {
            @Override
            public void clientTick() {
            }
        };
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    protected void doPush(@NotNull Entity entity) {
    }

    @Override
    public void push(double x, double y, double z) {
    }

    @Override
    public boolean isPushedByFluid() {
        return false;
    }

    @Override
    public boolean canBeLeashed(@NotNull Player player) {
        return false;
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public boolean causeFallDamage(float distance, float multiplier, @NotNull DamageSource source) {
        return false;
    }

    @Override
    public boolean canBeAffected(@NotNull MobEffectInstance effect) {
        return false;
    }

    @Override
    protected SoundEvent getHurtSound(@NotNull DamageSource source) {
        return SoundEvents.CHAIN_HIT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return TechSounds.SENTRY_DESTROYED.get();
    }

    /* ---------------------------------------------------------------- Persistence (entity type is noSave; kept for /data and debugging) */

    @Override
    public void addAdditionalSaveData(@NotNull CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (ownerUUID != null) {
            tag.putUUID("Owner", ownerUUID);
        }
        tag.putFloat("BoltDamage", boltDamage);
        tag.putInt("LifeTicks", lifeTicks);
        tag.putInt("MaxLifeTicks", maxLifeTicks);
    }

    @Override
    public void readAdditionalSaveData(@NotNull CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.hasUUID("Owner")) {
            ownerUUID = tag.getUUID("Owner");
        }
        boltDamage = tag.getFloat("BoltDamage");
        lifeTicks = tag.getInt("LifeTicks");
        maxLifeTicks = Math.max(lifeTicks, tag.getInt("MaxLifeTicks"));
    }

    /* ---------------------------------------------------------------- GeckoLib */

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 4, state -> {
            if (isDespawning()) {
                return state.setAndContinue(ANIM_DESPAWN);
            }
            if (tickCount < SPAWN_ANIMATION_TICKS) {
                return state.setAndContinue(ANIM_SPAWN);
            }
            return state.setAndContinue(isOverclocked() ? ANIM_OVERCLOCK : ANIM_IDLE);
        }));
        controllers.add(new AnimationController<>(this, "action", 0, state -> PlayState.STOP)
                .triggerableAnim("shoot", ANIM_SHOOT));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
