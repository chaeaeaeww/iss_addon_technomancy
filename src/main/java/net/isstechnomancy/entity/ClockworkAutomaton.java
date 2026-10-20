package net.isstechnomancy.entity;

import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.damage.DamageSources;
import io.redspace.ironsspellbooks.entity.mobs.AntiMagicSusceptible;
import io.redspace.ironsspellbooks.entity.mobs.IMagicSummon;
import io.redspace.ironsspellbooks.api.registry.SchoolRegistry;
import io.redspace.ironsspellbooks.particle.ShockwaveParticleOptions;
import io.redspace.ironsspellbooks.particle.ZapParticleOption;
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.isstechnomancy.registry.TechEffects;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSounds;
import net.isstechnomancy.registry.TechSpells;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.goal.target.TargetGoal;
import net.minecraft.world.entity.ai.targeting.TargetingConditions;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
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

import net.isstechnomancy.entity.boss.TechDragon;

import java.util.EnumSet;
import java.util.List;
import java.util.UUID;

/**
 * Steam-powered servo robot with a window full of spinning cogs.
 * <ul>
 *     <li><b>Wild</b> (spawn egg, boss drones): hostile to players, persists like a normal monster and drops Arcane Cogs.</li>
 *     <li><b>Assembled</b> (Assemble Automaton spell): fights for its owner, follows them, expires after its lifetime and drops nothing.</li>
 *     <li><b>Mk.II "Blitz"</b> (Overdrive): a round brass steam golem (separate model). It jabs with alternating fists;
 *     1.10: about one jab in four calls a lightning bolt down from the sky onto the target, and one punch in eight is a
 *     launching uppercut that throws anything up to its own size into the air (the fall hurts; bigger things are only
 *     hit). It also has Rocket Grab (the hand flies from its right hand in a straight line and can miss), a Static
 *     Field, an overdrive sprint (2.5 s of arm-pumping speed, then 1 s of venting slowdown) and an electric burst
 *     (radius 4) when it blows up.</li>
 *     <li><b>Workshop guard</b> (Clockwork Tower): a wild Mk.II that is neutral; it only fights whoever attacks it or a
 *     nearby Technomancer and stays near its post.</li>
 * </ul>
 * Its animations are deliberately servo-jerky and it vents steam whenever it walks, punches or fires.
 */
public class ClockworkAutomaton extends PathfinderMob implements GeoEntity, OwnableEntity, AntiMagicSusceptible {
    /** Mk.II hitbox scale over the normal automaton (the Blitz model itself is authored at full size). */
    public static final float MK2_SCALE = 1.75f;
    public static final int VOLLEY_COOLDOWN = 100;
    public static final int MK2_VOLLEY_COOLDOWN = 70;
    public static final int VOLLEY_WINDUP = 12;
    public static final double VOLLEY_MIN_RANGE = 3;
    public static final double VOLLEY_MAX_RANGE = 14;
    public static final float WILD_GEAR_DAMAGE = 3f;
    public static final int GRAB_COOLDOWN = 160;
    public static final int GRAB_WINDUP = 9;
    public static final double GRAB_MIN_RANGE = 4;
    public static final double GRAB_MAX_RANGE = 15;
    public static final int STATIC_INTERVAL = 60;
    public static final double STATIC_RADIUS = 4.5;
    private static final int SPAWN_ANIMATION_TICKS = 28;

    private static final EntityDataAccessor<Boolean> DATA_MK2 = SynchedEntityData.defineId(ClockworkAutomaton.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Integer> DATA_OVERLOAD = SynchedEntityData.defineId(ClockworkAutomaton.class, EntityDataSerializers.INT);
    /** 0 = normal, 1 = overdrive sprint, 2 = venting slowdown after the sprint. */
    private static final EntityDataAccessor<Integer> DATA_SPRINT = SynchedEntityData.defineId(ClockworkAutomaton.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> DATA_HAND_OUT = SynchedEntityData.defineId(ClockworkAutomaton.class, EntityDataSerializers.BOOLEAN);
    public static final int OVERLOAD_TICKS = 40;
    public static final double OVERLOAD_RADIUS = 4;
    public static final int SPRINT_INTERVAL = 200;
    public static final int SPRINT_TICKS = 50;
    public static final int VENT_TICKS = 20;
    public static final int JAB_TICKS = 12;
    public static final int JAB_HIT_TICK = 4;
    public static final int UPPERCUT_TICKS = 24;
    public static final int UPPERCUT_HIT_TICK = 10;
    private static final UUID SPRINT_SPEED_ID = UUID.fromString("6f0d5f9e-3c2b-4a8e-9f57-2b9b1f3a7c41");

    private static final RawAnimation ANIM_ASSEMBLE = RawAnimation.begin().thenPlay("assemble");
    private static final RawAnimation ANIM_IDLE = RawAnimation.begin().thenLoop("idle");
    private static final RawAnimation ANIM_WALK = RawAnimation.begin().thenLoop("walk");
    private static final RawAnimation ANIM_GEARS = RawAnimation.begin().thenLoop("gears");
    private static final RawAnimation ANIM_ATTACK = RawAnimation.begin().thenPlay("attack");
    private static final RawAnimation ANIM_VOLLEY = RawAnimation.begin().thenPlay("volley");
    private static final RawAnimation ANIM_GRAB = RawAnimation.begin().thenPlay("grab");
    private static final RawAnimation ANIM_STATIC = RawAnimation.begin().thenPlay("static");
    private static final RawAnimation ANIM_OVERLOAD = RawAnimation.begin().thenLoop("overload");
    private static final RawAnimation ANIM_RUN = RawAnimation.begin().thenLoop("run");
    private static final RawAnimation ANIM_VENT = RawAnimation.begin().thenLoop("vent");
    private static final RawAnimation ANIM_JAB_LEFT = RawAnimation.begin().thenPlay("jab_left");
    private static final RawAnimation ANIM_JAB_RIGHT = RawAnimation.begin().thenPlay("jab_right");
    private static final RawAnimation ANIM_UPPERCUT = RawAnimation.begin().thenPlay("uppercut");

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    @Nullable
    private UUID ownerUUID;
    @Nullable
    private LivingEntity cachedOwner;
    private int lifeTicks = -1;
    private float gearDamage = WILD_GEAR_DAMAGE;
    private int volleyCooldown = 40;
    private int grabCooldown = 60;
    private int staticCooldown = STATIC_INTERVAL;
    private int extraGears;
    private int teslaLevel;
    private int sprintCooldown = 100;
    private int sprintTicks;
    private boolean guard;
    private boolean guardInitialized;
    @Nullable
    private RocketHand activeHand;

    public ClockworkAutomaton(EntityType<? extends ClockworkAutomaton> entityType, Level level) {
        super(entityType, level);
        this.xpReward = 8;
        this.setMaxUpStep(1.0f);
    }

    /**
     * Assembled (owned) automaton.
     */
    public ClockworkAutomaton(Level level, LivingEntity owner, float meleeDamage, float gearDamage, int maxHealth, int lifetimeTicks, boolean mk2) {
        this(TechEntities.CLOCKWORK_AUTOMATON.get(), level);
        this.ownerUUID = owner.getUUID();
        this.cachedOwner = owner;
        this.gearDamage = gearDamage;
        this.lifeTicks = lifetimeTicks;
        this.xpReward = 0;
        setBase(Attributes.MAX_HEALTH, maxHealth);
        setBase(Attributes.ATTACK_DAMAGE, meleeDamage);
        setHealth(maxHealth);
        setMk2(mk2);
        setPersistenceRequired();
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 40)
                .add(Attributes.ATTACK_DAMAGE, 6)
                .add(Attributes.ATTACK_KNOCKBACK, 0.6)
                .add(Attributes.ARMOR, 8)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.6)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.FOLLOW_RANGE, 24);
    }

    private void setBase(net.minecraft.world.entity.ai.attributes.Attribute attribute, double value) {
        AttributeInstance instance = getAttribute(attribute);
        if (instance != null) {
            instance.setBaseValue(value);
        }
    }

    /**
     * Staff modules at assembly: Splitter adds gears to every volley, Tesla makes gears chain lightning.
     */
    public void setModules(int extraGears, int teslaLevel) {
        this.extraGears = extraGears;
        this.teslaLevel = teslaLevel;
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_MK2, false);
        this.entityData.define(DATA_OVERLOAD, -1);
        this.entityData.define(DATA_SPRINT, 0);
        this.entityData.define(DATA_HAND_OUT, false);
    }

    /** 0 = normal, 1 = sprinting, 2 = venting. */
    public int getSprintState() {
        return this.entityData.get(DATA_SPRINT);
    }

    /** True while the Mk.II's right fist is out on a Rocket Grab (the renderer hides the fist on the arm). */
    public boolean isHandOut() {
        return this.entityData.get(DATA_HAND_OUT);
    }

    public boolean isGuard() {
        return guard;
    }

    /**
     * Turns a wild Mk.II into a neutral workshop guard (Clockwork Tower): tougher, stays near its post, only fights back.
     */
    public void makeGuard() {
        guard = true;
        setMk2(true);
        if (!guardInitialized) {
            guardInitialized = true;
            setBase(Attributes.MAX_HEALTH, 150);
            setBase(Attributes.ATTACK_DAMAGE, 9);
            setBase(Attributes.ARMOR, 14);
            setBase(Attributes.FOLLOW_RANGE, 20);
            gearDamage = 4.5f;
            setHealth(getMaxHealth());
        }
        restrictTo(blockPosition(), 10);
        setPersistenceRequired();
    }

    public boolean isOverloading() {
        return this.entityData.get(DATA_OVERLOAD) >= 0;
    }

    /**
     * Mk.II death sequence: the golem shuts down, sparks and flashes for two seconds, then discharges in a lightning burst.
     */
    private void startOverload() {
        if (isOverloading() || level().isClientSide) {
            return;
        }
        this.entityData.set(DATA_OVERLOAD, OVERLOAD_TICKS);
        setNoAi(true);
        getNavigation().stop();
        setHealth(1f);
        playSound(SoundEvents.BEACON_DEACTIVATE, 1.5f, 0.6f);
        playSound(TechSounds.AUTOMATON_DEATH.get(), 1.2f, 0.6f);
    }

    private void tickOverload() {
        int ticks = this.entityData.get(DATA_OVERLOAD);
        setDeltaMovement(0, getDeltaMovement().y, 0);
        Vec3 core = position().add(0, getBbHeight() * 0.55, 0);
        if (ticks % 4 == 0) {
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, core.x, core.y, core.z, 8 + (OVERLOAD_TICKS - ticks) / 2, 0.6, 0.6, 0.6, 0.25, false);
            playSound(SoundEvents.NOTE_BLOCK_BIT.get(), 1.2f, 0.5f + (OVERLOAD_TICKS - ticks) / (float) OVERLOAD_TICKS * 1.5f);
        }
        if (ticks % 8 == 0) {
            steamBurst(position().add(0, getBbHeight(), 0), 6, 0.3);
        }
        if (ticks <= 0) {
            overloadBurst();
            return;
        }
        this.entityData.set(DATA_OVERLOAD, ticks - 1);
    }

    private void overloadBurst() {
        LivingEntity owner = getOwner();
        Entity attacker = owner != null ? owner : this;
        Vec3 core = position().add(0, getBbHeight() * 0.55, 0);
        for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(OVERLOAD_RADIUS),
                e -> e != this && e.isAlive() && !isAlliedTo(e) && e.distanceToSqr(this) < OVERLOAD_RADIUS * OVERLOAD_RADIUS * 1.3)) {
            Vec3 to = victim.getBoundingBox().getCenter();
            ((ServerLevel) level()).sendParticles(new ZapParticleOption(to), core.x, core.y, core.z, 1, 0, 0, 0, 0);
            if (victim instanceof ClockworkAutomaton other && other.isGuard() && isGuard()) {
                continue;
            }
            DamageSources.applyDamage(victim, gearDamage * 3f, TechSpells.ASSEMBLE_AUTOMATON.get().getDamageSource(this, attacker));
            victim.addEffect(new MobEffectInstance(TechEffects.STUNNED.get(), 30, 0), this);
            Vec3 push = to.subtract(core).normalize().scale(1.1);
            victim.push(push.x, 0.4, push.z);
            victim.hurtMarked = true;
        }
        // 1.10: an instant electric wave racing out along the ground to the blast radius and a dome of arcs over it
        net.isstechnomancy.entity.boss.ElectricFx.burst((ServerLevel) level(), position().add(0, 0.2, 0), (float) OVERLOAD_RADIUS * 1.15f, 0);
        net.isstechnomancy.entity.boss.ElectricFx.burst((ServerLevel) level(), core, (float) OVERLOAD_RADIUS * 0.6f, 1);
        net.isstechnomancy.entity.boss.ElectricFx.dome((ServerLevel) level(), position().add(0, 0.3, 0), (float) OVERLOAD_RADIUS);
        MagicManager.spawnParticles(level(), net.minecraft.core.particles.ParticleTypes.EXPLOSION_EMITTER, core.x, core.y, core.z, 1, 0, 0, 0, 0, true);
        MagicManager.spawnParticles(level(), ParticleHelper.ELECTRICITY, core.x, core.y, core.z, 50, OVERLOAD_RADIUS * 0.5, 1.2, OVERLOAD_RADIUS * 0.5, 0.3, true);
        MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + 0.3, getZ(), 60, OVERLOAD_RADIUS * 0.5, 0.2, OVERLOAD_RADIUS * 0.5, 0.4, true);
        MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), core.x, core.y, core.z, 40, 1, 1, 1, 0.5, false);
        playSound(SoundEvents.LIGHTNING_BOLT_THUNDER, 2f, 1.4f);
        playSound(SoundEvents.GENERIC_EXPLODE, 1.5f, 1.1f);
        if (!isAssembled()) {
            // wild/guard Blitz: a real death so loot and experience drop
            this.entityData.set(DATA_OVERLOAD, -1);
            hurt(damageSources().genericKill(), Float.MAX_VALUE);
            if (isAlive()) {
                discard();
            }
            return;
        }
        discard();
    }

    public boolean isMk2() {
        return this.entityData.get(DATA_MK2);
    }

    public void setMk2(boolean mk2) {
        this.entityData.set(DATA_MK2, mk2);
        refreshDimensions();
    }

    @Override
    public void onSyncedDataUpdated(@NotNull EntityDataAccessor<?> key) {
        super.onSyncedDataUpdated(key);
        if (DATA_MK2.equals(key)) {
            refreshDimensions();
        }
    }

    @Override
    public @NotNull EntityDimensions getDimensions(@NotNull Pose pose) {
        EntityDimensions dimensions = super.getDimensions(pose);
        return isMk2() ? dimensions.scale(MK2_SCALE) : dimensions;
    }

    /* ---------------------------------------------------------------- Ownership */

    public boolean isAssembled() {
        return ownerUUID != null;
    }

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

    @Override
    public boolean isAlliedTo(@NotNull Entity entity) {
        if (super.isAlliedTo(entity)) {
            return true;
        }
        if (!isAssembled()) {
            if (guard) {
                return entity instanceof TechnomancerEntity || (entity instanceof ClockworkAutomaton other && other.isGuard());
            }
            return (entity instanceof ClockworkAutomaton other && !other.isAssembled()) || entity instanceof TechDragon;
        }
        LivingEntity owner = getOwner();
        if (owner == null) {
            return false;
        }
        if (entity == owner || owner.isAlliedTo(entity)) {
            return true;
        }
        if (entity instanceof OwnableEntity ownable && ownerUUID.equals(ownable.getOwnerUUID())) {
            return true;
        }
        return entity instanceof IMagicSummon summon && summon.getSummoner() == owner;
    }

    @Override
    public boolean canAttack(@NotNull LivingEntity target) {
        return !isAlliedTo(target) && super.canAttack(target);
    }

    /* ---------------------------------------------------------------- AI */

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(1, new RocketGrabGoal());
        this.goalSelector.addGoal(2, new GearVolleyGoal());
        this.goalSelector.addGoal(3, new MeleeAttackGoal(this, 1.15, true) {
            @Override
            public boolean canUse() {
                return !isMk2() && super.canUse();
            }

            @Override
            public boolean canContinueToUse() {
                return !isMk2() && super.canContinueToUse();
            }
        });
        this.goalSelector.addGoal(3, new BlitzPunchGoal());
        this.goalSelector.addGoal(4, new FollowOwnerGoal());
        this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8f));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));

        this.targetSelector.addGoal(1, new OwnerTargetGoal(true));
        this.targetSelector.addGoal(2, new OwnerTargetGoal(false));
        this.targetSelector.addGoal(3, new HurtByTargetGoal(this, ClockworkAutomaton.class));
        this.targetSelector.addGoal(4, new GuardTargetGoal());
        this.targetSelector.addGoal(5, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false, player -> !isAssembled() && !guard));
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide) {
            clientSteam();
            return;
        }
        if (volleyCooldown > 0) {
            volleyCooldown--;
        }
        if (grabCooldown > 0) {
            grabCooldown--;
        }
        if (isOverloading()) {
            tickOverload();
            return;
        }
        if (isMk2() && --staticCooldown <= 0) {
            staticCooldown = STATIC_INTERVAL;
            staticField();
        }
        if (isMk2()) {
            tickSprint();
        }
        if (isHandOut() && (activeHand == null || activeHand.isRemoved())) {
            activeHand = null;
            this.entityData.set(DATA_HAND_OUT, false);
        }
        if (isAssembled()) {
            LivingEntity owner = getOwner();
            if (owner == null || !owner.isAlive()) {
                disassemble();
            } else if (--lifeTicks <= 0) {
                if (isMk2()) {
                    startOverload();
                } else {
                    disassemble();
                }
            }
        }
    }

    /**
     * Smokestack puffs (more when walking), foot vents on every stride, and a heavy plume while in combat.
     */
    private void clientSteam() {
        float scale = isMk2() ? MK2_SCALE : 1f;
        boolean moving = getDeltaMovement().horizontalDistanceSqr() > 2.5e-4;
        Vec3 back = Vec3.directionFromRotation(0, yBodyRot).scale(-0.3 * scale);
        Vec3 right = Vec3.directionFromRotation(0, yBodyRot + 90).scale(0.14 * scale);
        int interval = moving ? 4 : (getTarget() != null ? 8 : 30);
        if (tickCount % interval == 0) {
            double top = isMk2() ? getBbHeight() * 0.98 : getBbHeight() * 0.86;
            Vec3 stack = position().add(back).add(0, top, 0);
            if (isMk2()) {
                level().addParticle(TechParticles.STEAM_PUFF.get(), getX(), getY() + top, getZ(), 0, 0.09, 0);
            } else {
                level().addParticle(TechParticles.STEAM_PUFF.get(), stack.x + right.x, stack.y, stack.z + right.z, 0, 0.07, 0);
                level().addParticle(TechParticles.STEAM_PUFF.get(), stack.x - right.x, stack.y - 0.06, stack.z - right.z, 0, 0.06, 0);
            }
        }
        if (moving && tickCount % 12 == 0) {
            Vec3 side = Vec3.directionFromRotation(0, yBodyRot + 90).scale((tickCount % 24 == 0 ? 0.2 : -0.2) * scale);
            for (int i = 0; i < 2; i++) {
                level().addParticle(TechParticles.STEAM_PUFF.get(), getX() + side.x + (random.nextDouble() - 0.5) * 0.2, getY() + 0.1,
                        getZ() + side.z + (random.nextDouble() - 0.5) * 0.2, (random.nextDouble() - 0.5) * 0.05, 0.02, (random.nextDouble() - 0.5) * 0.05);
            }
        }
    }

    /**
     * Mk.II overdrive sprint: when its target is far it charges for 2.5 s (both arms pumping), then has to vent for 1 s
     * at a crawl before it can do anything fast again.
     */
    private void tickSprint() {
        int state = getSprintState();
        LivingEntity target = getTarget();
        if (state == 1) {
            if (--sprintTicks <= 0) {
                setSprint(2, VENT_TICKS);
                steamBurst(position().add(0, getBbHeight(), 0), 16, 0.45);
                playSound(SoundEvents.FIRE_EXTINGUISH, 1.2f, 0.6f);
            } else if (sprintTicks % 3 == 0) {
                MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + 0.3, getZ(), 3, 0.4, 0.1, 0.4, 0.05, false);
                if (sprintTicks % 6 == 0) {
                    steamBurst(position().add(0, getBbHeight() * 0.95, 0), 2, 0.15);
                }
            }
            return;
        }
        if (state == 2) {
            if (sprintTicks % 4 == 0) {
                steamBurst(position().add(0, getBbHeight() * 0.95, 0), 4, 0.3);
            }
            if (--sprintTicks <= 0) {
                setSprint(0, 0);
            }
            return;
        }
        if (--sprintCooldown <= 0 && target != null && target.isAlive() && distanceTo(target) > 6 && !isOverloading()) {
            sprintCooldown = SPRINT_INTERVAL;
            setSprint(1, SPRINT_TICKS);
            playSound(SoundEvents.BEACON_POWER_SELECT, 1.2f, 1.6f);
            playSound(SoundEvents.PISTON_EXTEND, 1.0f, 0.6f);
            steamBurst(position().add(0, getBbHeight() * 0.98, 0), 10, 0.3);
        }
    }

    private void setSprint(int state, int ticks) {
        this.entityData.set(DATA_SPRINT, state);
        sprintTicks = ticks;
        AttributeInstance speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed == null) {
            return;
        }
        speed.removeModifier(SPRINT_SPEED_ID);
        if (state == 1) {
            speed.addTransientModifier(new AttributeModifier(SPRINT_SPEED_ID, "Blitz sprint", 1.3, AttributeModifier.Operation.MULTIPLY_TOTAL));
        } else if (state == 2) {
            speed.addTransientModifier(new AttributeModifier(SPRINT_SPEED_ID, "Blitz venting", -0.75, AttributeModifier.Operation.MULTIPLY_TOTAL));
        }
    }

    private void steamBurst(Vec3 at, int count, double spread) {
        MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), at.x, at.y, at.z, count, spread, spread * 0.6, spread, 0.03, false);
    }

    @Override
    public boolean doHurtTarget(@NotNull Entity target) {
        triggerAnim("action", "attack");
        playSound(TechSounds.AUTOMATON_ATTACK.get(), 1.0f, (isMk2() ? 0.7f : 0.9f) + random.nextFloat() * 0.2f);
        Vec3 elbow = position().add(getViewVector(1f).scale(0.5 * (isMk2() ? MK2_SCALE : 1f))).add(0, getBbHeight() * 0.55, 0);
        steamBurst(elbow, isMk2() ? 10 : 6, 0.25);
        return super.doHurtTarget(target);
    }

    /**
     * Mk.II punch landing (called by {@link BlitzPunchGoal} on the impact frame of the jab / uppercut animation).
     */
    private void blitzStrike(LivingEntity target, boolean uppercut) {
        playSound(TechSounds.AUTOMATON_ATTACK.get(), 1.2f, uppercut ? 0.55f : 0.75f + random.nextFloat() * 0.2f);
        Vec3 fist = position().add(getViewVector(1f).multiply(1, 0, 1).normalize().scale(1.6)).add(0, uppercut ? getBbHeight() * 0.7 : getBbHeight() * 0.45, 0);
        steamBurst(fist, uppercut ? 14 : 6, 0.3);
        AttributeInstance damage = getAttribute(Attributes.ATTACK_DAMAGE);
        float base = damage == null ? 6f : (float) damage.getValue();
        boolean hit = target.hurt(damageSources().mobAttack(this), uppercut ? base * 1.5f : base);
        if (!hit) {
            return;
        }
        setLastHurtMob(target);
        if (!uppercut && random.nextInt(4) == 0) {
            // 1.10: the jab calls a lightning bolt down from the sky onto the target
            LivingEntity owner = getOwner();
            io.redspace.ironsspellbooks.entity.spells.LightningStrike bolt = new io.redspace.ironsspellbooks.entity.spells.LightningStrike(level());
            bolt.setOwner(owner != null ? owner : this);
            bolt.setDamage(Math.max(3f, gearDamage * 1.3f));
            bolt.setPos(target.getX(), target.getY(), target.getZ());
            level().addFreshEntity(bolt);
        }
        if (uppercut && !canLaunch(target)) {
            // too big to throw: a heavy blow and a jolt instead
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, target.getX(), target.getY() + target.getBbHeight() * 0.5, target.getZ(), 14, 0.4, 0.4, 0.4, 0.3, false);
            playSound(SoundEvents.ANVIL_LAND, 0.9f, 1.2f);
            return;
        }
        if (uppercut) {
            // launched straight up (a little away from the golem) and briefly stunned
            Vec3 away = target.position().subtract(position()).multiply(1, 0, 1);
            away = away.lengthSqr() < 1e-4 ? Vec3.ZERO : away.normalize().scale(0.25);
            double resist = 1 - Mth.clamp(target.getAttributeValue(Attributes.KNOCKBACK_RESISTANCE), 0, 1) * 0.6;
            // 1.10: thrown high enough that the landing hurts a little
            target.setDeltaMovement(target.getDeltaMovement().multiply(0.2, 0, 0.2).add(away.x, 1.35 * resist, away.z));
            target.hurtMarked = true;
            target.addEffect(new MobEffectInstance(TechEffects.STUNNED.get(), 16, 0), this);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, target.getX(), target.getY() + 0.3, target.getZ(), 18, 0.35, 0.1, 0.35, 0.3, false);
            MagicManager.spawnParticles(level(), net.minecraft.core.particles.ParticleTypes.EXPLOSION, target.getX(), target.getY() + 0.4, target.getZ(), 1, 0, 0, 0, 0, false);
            playSound(SoundEvents.ANVIL_LAND, 0.9f, 1.4f);
            playSound(SoundEvents.GENERIC_EXPLODE, 0.6f, 1.6f);
        } else {
            Vec3 push = target.position().subtract(position()).multiply(1, 0, 1);
            if (push.lengthSqr() > 1e-4) {
                target.knockback(0.45, -push.x, -push.z);
            }
            MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), target.getX(), target.getY() + target.getBbHeight() * 0.6, target.getZ(), 6, 0.2, 0.2, 0.2, 0.2, false);
        }
    }

    /** The uppercut throws things up to about its own size (1.10); never bosses. */
    private boolean canLaunch(LivingEntity target) {
        return target.getBbHeight() <= getBbHeight() * 1.05f && target.getBbWidth() <= getBbWidth() * 1.1f
                && !target.getType().is(net.isstechnomancy.registry.TechTags.BOSSES) && !(target instanceof net.isstechnomancy.entity.boss.TechDragon);
    }

    private void fireVolley(LivingEntity target) {
        int gears = (isMk2() ? 5 : 3) + extraGears;
        float scale = isMk2() ? MK2_SCALE : 1f;
        Vec3 origin = getEyePosition().add(getViewVector(1f).scale(0.6 * scale)).add(0, -0.4 * scale, 0);
        Vec3 aim = target.getBoundingBox().getCenter().subtract(origin).normalize();
        float spread = Math.min(7f, 42f / Math.max(1, gears - 1));
        for (int i = 0; i < gears; i++) {
            GearProjectile gear = new GearProjectile(level(), this);
            gear.setPos(origin.x, origin.y - gear.getBbHeight() * 0.5, origin.z);
            gear.shoot(aim.yRot((i - (gears - 1) / 2f) * spread * Mth.DEG_TO_RAD));
            gear.setDamage(gearDamage);
            gear.setBlockBounces(1);
            gear.setTeslaLevel(teslaLevel);
            level().addFreshEntity(gear);
        }
        playSound(TechSounds.AUTOMATON_VOLLEY.get(), 1.2f, 1.0f);
        steamBurst(origin, 8, 0.25);
        steamBurst(position().add(0, getBbHeight() * 0.9, 0), 6, 0.2);
    }

    /**
     * Mk.II: zaps up to three enemies standing close to it.
     */
    private void staticField() {
        LivingEntity owner = getOwner();
        List<LivingEntity> victims = level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(STATIC_RADIUS),
                e -> e != this && e.isAlive() && !isAlliedTo(e) && (getTarget() == e || (e instanceof Mob mob && mob.getTarget() != null
                        && (mob.getTarget() == this || mob.getTarget() == owner))) && distanceToSqr(e) < STATIC_RADIUS * STATIC_RADIUS * 1.5);
        if (victims.isEmpty()) {
            return;
        }
        triggerAnim("action", "static");
        Vec3 core = position().add(0, getBbHeight() * 0.55, 0);
        Entity attacker = owner != null ? owner : this;
        victims.stream().limit(3).forEach(victim -> {
            Vec3 to = victim.getBoundingBox().getCenter();
            ((ServerLevel) level()).sendParticles(new ZapParticleOption(to), core.x, core.y, core.z, 1, 0, 0, 0, 0);
            DamageSources.applyDamage(victim, gearDamage * 0.8f, TechSpells.ASSEMBLE_AUTOMATON.get().getDamageSource(this, attacker));
            victim.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 1), this);
        });
        MagicManager.spawnParticles(level(), ParticleHelper.ELECTRICITY, core.x, core.y, core.z, 16, 0.6, 0.6, 0.6, 0.1, false);
        playSound(SoundEvents.LIGHTNING_BOLT_IMPACT, 0.6f, 1.6f);
    }

    /**
     * Mk.II: Rocket Grab. Yanks the target back to the automaton and briefly stuns it.
     */
    private void rocketGrab(LivingEntity target) {
        // 1.10: from the right hand itself on the launch frame of the grab animation (model: 26 px right, 40 px up,
        // 26 px forward); the hand flies in a straight line at where the target was, so it can miss
        Vec3 forward = Vec3.directionFromRotation(0, yBodyRot);
        Vec3 right = Vec3.directionFromRotation(0, yBodyRot - 90);
        Vec3 from = position().add(forward.scale(26 / 16.0)).add(right.scale(26 / 16.0)).add(0, 40 / 16.0, 0);
        Vec3 aim = target.getBoundingBox().getCenter().subtract(from);
        RocketHand hand = new RocketHand(level(), this, from, aim, GRAB_MAX_RANGE + 2, gearDamage, 30, 1.35f);
        hand.setTeslaLevel(teslaLevel);
        level().addFreshEntity(hand);
        activeHand = hand;
        this.entityData.set(DATA_HAND_OUT, true);
        playSound(SoundEvents.FIREWORK_ROCKET_LAUNCH, 1.4f, 0.6f);
        playSound(SoundEvents.PISTON_EXTEND, 1.2f, 0.8f);
        steamBurst(position().add(0, getBbHeight() * 0.95, 0), 12, 0.3);
    }

    /**
     * Assembled automatons fall apart into steam and sparks instead of dying normally.
     */
    public void disassemble() {
        if (level().isClientSide || isRemoved()) {
            return;
        }
        MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), getX(), getY() + 1, getZ(), 16, 0.4, 0.6, 0.4, 0.03, false);
        MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), getX(), getY() + 1, getZ(), 20, 0.4, 0.6, 0.4, 0.25, false);
        playSound(TechSounds.AUTOMATON_DEATH.get(), 1.0f, 1.2f);
        discard();
    }

    @Override
    public void onAntiMagic(MagicData playerMagicData) {
        if (isAssembled()) {
            disassemble();
        }
    }

    @Override
    public boolean hurt(@NotNull DamageSource source, float amount) {
        Entity attacker = source.getEntity();
        if (attacker != null && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY) && isAlliedTo(attacker)) {
            return false;
        }
        if (isOverloading() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return false;
        }
        if (isMk2() && !level().isClientSide && amount >= getHealth() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            startOverload();
            return true;
        }
        boolean hurt = super.hurt(source, amount);
        if (hurt && !level().isClientSide && random.nextInt(3) == 0) {
            steamBurst(position().add(0, getBbHeight() * 0.6, 0), 4, 0.3);
        }
        return hurt;
    }

    @Override
    protected boolean shouldDropLoot() {
        return !isAssembled();
    }

    @Override
    protected void tickDeath() {
        if (isMk2() && !level().isClientSide) {
            // the overload burst already played; no tipping-over corpse
            remove(RemovalReason.KILLED);
            return;
        }
        super.tickDeath();
    }

    @Override
    protected net.minecraft.resources.ResourceLocation getDefaultLootTable() {
        return isMk2() ? net.isstechnomancy.ISSTechnomancy.id("entities/blitz_guard") : super.getDefaultLootTable();
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public boolean shouldBeSaved() {
        return !isAssembled() && super.shouldBeSaved();
    }

    @Override
    public boolean causeFallDamage(float distance, float multiplier, @NotNull DamageSource source) {
        return super.causeFallDamage(distance, multiplier * 0.5f, source);
    }

    /* ---------------------------------------------------------------- Sounds */

    @Override
    protected SoundEvent getAmbientSound() {
        return TechSounds.AUTOMATON_AMBIENT.get();
    }

    @Override
    protected SoundEvent getHurtSound(@NotNull DamageSource source) {
        return TechSounds.AUTOMATON_HURT.get();
    }

    @Override
    protected SoundEvent getDeathSound() {
        return TechSounds.AUTOMATON_DEATH.get();
    }

    @Override
    protected void playStepSound(@NotNull BlockPos pos, @NotNull BlockState state) {
        playSound(TechSounds.AUTOMATON_STEP.get(), isMk2() ? 0.8f : 0.5f, isMk2() ? 0.75f : 1.0f);
    }

    @Override
    protected float getSoundVolume() {
        return isMk2() ? 1.2f : 1.0f;
    }

    @Override
    public float getVoicePitch() {
        return isMk2() ? 0.75f : super.getVoicePitch();
    }

    /* ---------------------------------------------------------------- Persistence */

    @Override
    public void addAdditionalSaveData(@NotNull CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (ownerUUID != null) {
            tag.putUUID("Owner", ownerUUID);
        }
        tag.putInt("LifeTicks", lifeTicks);
        tag.putFloat("GearDamage", gearDamage);
        tag.putBoolean("Mk2", isMk2());
        tag.putInt("ExtraGears", extraGears);
        tag.putInt("Tesla", teslaLevel);
        tag.putBoolean("Guard", guard);
        tag.putBoolean("GuardInit", guardInitialized);
        if (guard && hasRestriction()) {
            tag.put("GuardHome", net.minecraft.nbt.NbtUtils.writeBlockPos(getRestrictCenter()));
        }
    }

    @Override
    public void readAdditionalSaveData(@NotNull CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.hasUUID("Owner")) {
            ownerUUID = tag.getUUID("Owner");
        }
        if (tag.contains("LifeTicks")) {
            lifeTicks = tag.getInt("LifeTicks");
        }
        if (tag.contains("GearDamage")) {
            gearDamage = tag.getFloat("GearDamage");
        }
        setMk2(tag.getBoolean("Mk2"));
        extraGears = tag.getInt("ExtraGears");
        teslaLevel = tag.getInt("Tesla");
        guardInitialized = tag.getBoolean("GuardInit");
        if (tag.getBoolean("Guard")) {
            makeGuard();
            if (tag.contains("GuardHome")) {
                restrictTo(net.minecraft.nbt.NbtUtils.readBlockPos(tag.getCompound("GuardHome")), 10);
            }
        }
    }

    /* ---------------------------------------------------------------- GeckoLib */

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 3, state -> {
            if (isOverloading()) {
                return state.setAndContinue(ANIM_OVERLOAD);
            }
            if (tickCount < SPAWN_ANIMATION_TICKS && isAssembled()) {
                return state.setAndContinue(ANIM_ASSEMBLE);
            }
            if (isMk2() && getSprintState() == 1) {
                return state.setAndContinue(ANIM_RUN);
            }
            if (isMk2() && getSprintState() == 2) {
                return state.setAndContinue(ANIM_VENT);
            }
            return state.setAndContinue(state.isMoving() ? ANIM_WALK : ANIM_IDLE);
        }));
        controllers.add(new AnimationController<>(this, "gears", 0, state -> state.setAndContinue(ANIM_GEARS)));
        controllers.add(new AnimationController<>(this, "action", 0, state -> PlayState.STOP)
                .triggerableAnim("attack", ANIM_ATTACK)
                .triggerableAnim("volley", ANIM_VOLLEY)
                .triggerableAnim("grab", ANIM_GRAB)
                .triggerableAnim("static", ANIM_STATIC)
                .triggerableAnim("jab_left", ANIM_JAB_LEFT)
                .triggerableAnim("jab_right", ANIM_JAB_RIGHT)
                .triggerableAnim("uppercut", ANIM_UPPERCUT));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    /* ---------------------------------------------------------------- Goals */

    /**
     * Stops, raises the shoulder launcher (volley animation) and vents a fan of gears at a mid-range target.
     */
    private class GearVolleyGoal extends Goal {
        private int windup;
        @Nullable
        private LivingEntity volleyTarget;

        GearVolleyGoal() {
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity target = getTarget();
            if (volleyCooldown > 0 || target == null || !target.isAlive()) {
                return false;
            }
            double distance = distanceTo(target);
            return distance >= VOLLEY_MIN_RANGE && distance <= VOLLEY_MAX_RANGE && hasLineOfSight(target);
        }

        @Override
        public boolean canContinueToUse() {
            return windup > 0 && volleyTarget != null && volleyTarget.isAlive();
        }

        @Override
        public void start() {
            volleyTarget = getTarget();
            windup = VOLLEY_WINDUP;
            getNavigation().stop();
            triggerAnim("action", "volley");
        }

        @Override
        public void tick() {
            if (volleyTarget == null) {
                return;
            }
            getLookControl().setLookAt(volleyTarget, 30f, 30f);
            if (--windup == 0) {
                fireVolley(volleyTarget);
                volleyCooldown = isMk2() ? MK2_VOLLEY_COOLDOWN : VOLLEY_COOLDOWN;
            }
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }
    }

    /**
     * Mk.II only: launches its fist on a piston and reels the target in.
     */
    private class RocketGrabGoal extends Goal {
        private int windup;
        @Nullable
        private LivingEntity grabTarget;

        RocketGrabGoal() {
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity target = getTarget();
            if (!isMk2() || grabCooldown > 0 || target == null || !target.isAlive()) {
                return false;
            }
            double distance = distanceTo(target);
            return distance >= GRAB_MIN_RANGE && distance <= GRAB_MAX_RANGE && hasLineOfSight(target);
        }

        @Override
        public boolean canContinueToUse() {
            return windup > 0 && grabTarget != null && grabTarget.isAlive();
        }

        @Override
        public void start() {
            grabTarget = getTarget();
            windup = GRAB_WINDUP;
            getNavigation().stop();
            triggerAnim("action", "grab");
            playSound(SoundEvents.PISTON_EXTEND, 1.2f, 0.7f);
        }

        @Override
        public void tick() {
            if (grabTarget == null) {
                return;
            }
            getLookControl().setLookAt(grabTarget, 40f, 40f);
            if (--windup == 0) {
                rocketGrab(grabTarget);
                grabCooldown = GRAB_COOLDOWN;
            }
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }
    }

    /**
     * Mk.II melee: walks up to the target and throws alternating jabs; one punch in three is a wound-up uppercut. The
     * damage lands on the impact frame of the animation, not when the swing starts.
     */
    private class BlitzPunchGoal extends Goal {
        private int attackTicks;
        private int hitTick;
        private boolean uppercut;
        private boolean leftNext;
        private int cooldown;
        private int repath;
        @Nullable
        private LivingEntity victim;

        BlitzPunchGoal() {
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity target = getTarget();
            return isMk2() && !isOverloading() && target != null && target.isAlive() && !isHandOut();
        }

        @Override
        public boolean canContinueToUse() {
            return attackTicks > 0 || canUse();
        }

        @Override
        public void stop() {
            attackTicks = 0;
            getNavigation().stop();
        }

        private double reach(LivingEntity target) {
            double r = getBbWidth() * 0.5 + target.getBbWidth() * 0.5 + 1.6;
            return r * r;
        }

        @Override
        public void tick() {
            if (cooldown > 0) {
                cooldown--;
            }
            if (attackTicks > 0) {
                attackTicks--;
                getNavigation().stop();
                if (victim != null) {
                    getLookControl().setLookAt(victim, 30f, 30f);
                    int elapsed = (uppercut ? UPPERCUT_TICKS : JAB_TICKS) - attackTicks;
                    if (elapsed == hitTick && victim.isAlive() && distanceToSqr(victim) <= reach(victim) * 1.3) {
                        blitzStrike(victim, uppercut);
                    }
                }
                return;
            }
            LivingEntity target = getTarget();
            if (target == null) {
                return;
            }
            getLookControl().setLookAt(target, 30f, 30f);
            double distance = distanceToSqr(target);
            if (distance <= reach(target) && cooldown <= 0 && hasLineOfSight(target)) {
                victim = target;
                uppercut = random.nextInt(8) == 0;
                attackTicks = uppercut ? UPPERCUT_TICKS : JAB_TICKS;
                hitTick = uppercut ? UPPERCUT_HIT_TICK : JAB_HIT_TICK;
                cooldown = uppercut ? 34 : 16;
                getNavigation().stop();
                if (uppercut) {
                    triggerAnim("action", "uppercut");
                    playSound(SoundEvents.PISTON_CONTRACT, 1.0f, 0.6f);
                } else {
                    triggerAnim("action", leftNext ? "jab_left" : "jab_right");
                    leftNext = !leftNext;
                }
                return;
            }
            if (--repath <= 0) {
                repath = 8;
                getNavigation().moveTo(target, 1.15);
            }
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }
    }

    /**
     * Workshop guard: answers anyone who attacks a Technomancer near its post.
     */
    private class GuardTargetGoal extends TargetGoal {
        @Nullable
        private LivingEntity candidate;

        GuardTargetGoal() {
            super(ClockworkAutomaton.this, false);
            setFlags(EnumSet.of(Flag.TARGET));
        }

        @Override
        public boolean canUse() {
            if (!guard || tickCount % 10 != 0) {
                return false;
            }
            for (TechnomancerEntity mage : level().getEntitiesOfClass(TechnomancerEntity.class, getBoundingBox().inflate(20))) {
                LivingEntity attacker = mage.getLastHurtByMob();
                if (attacker != null && attacker.isAlive() && mage.tickCount - mage.getLastHurtByMobTimestamp() < 200
                        && !isAlliedTo(attacker) && canAttack(attacker, TargetingConditions.DEFAULT)) {
                    candidate = attacker;
                    return true;
                }
            }
            return false;
        }

        @Override
        public void start() {
            mob.setTarget(candidate);
            super.start();
        }
    }

    /**
     * Assembled automatons stay close to their owner and catch up by teleporting when left far behind.
     */
    private class FollowOwnerGoal extends Goal {
        private static final double START_DISTANCE = 10;
        private static final double TELEPORT_DISTANCE = 24;

        FollowOwnerGoal() {
            setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            LivingEntity owner = getOwner();
            return owner != null && getTarget() == null && distanceToSqr(owner) > START_DISTANCE * START_DISTANCE;
        }

        @Override
        public boolean canContinueToUse() {
            LivingEntity owner = getOwner();
            return owner != null && getTarget() == null && distanceToSqr(owner) > 3 * 3;
        }

        @Override
        public void tick() {
            LivingEntity owner = getOwner();
            if (owner == null) {
                return;
            }
            getLookControl().setLookAt(owner, 10f, getMaxHeadXRot());
            if (distanceToSqr(owner) > TELEPORT_DISTANCE * TELEPORT_DISTANCE) {
                Vec3 behind = owner.position().add(owner.getLookAngle().multiply(1, 0, 1).normalize().scale(-2));
                teleportTo(behind.x, owner.getY(), behind.z);
                getNavigation().stop();
            } else if (tickCount % 10 == 0) {
                getNavigation().moveTo(owner, 1.2);
            }
        }

        @Override
        public void stop() {
            getNavigation().stop();
        }
    }

    /**
     * Defends the owner (attacks whatever hurt them) or assists the owner (attacks what they recently hit).
     */
    private class OwnerTargetGoal extends TargetGoal {
        private final boolean defend;
        @Nullable
        private LivingEntity candidate;

        OwnerTargetGoal(boolean defend) {
            super(ClockworkAutomaton.this, false);
            this.defend = defend;
            setFlags(EnumSet.of(Flag.TARGET));
        }

        @Override
        public boolean canUse() {
            LivingEntity owner = getOwner();
            if (owner == null) {
                return false;
            }
            candidate = defend ? owner.getLastHurtByMob() : owner.getLastHurtMob();
            return candidate != null && candidate != ClockworkAutomaton.this && !isAlliedTo(candidate)
                    && canAttack(candidate, TargetingConditions.DEFAULT);
        }

        @Override
        public void start() {
            mob.setTarget(candidate);
            super.start();
        }
    }
}
