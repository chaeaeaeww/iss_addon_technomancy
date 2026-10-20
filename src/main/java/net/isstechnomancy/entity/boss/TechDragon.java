package net.isstechnomancy.entity.boss;

import io.redspace.ironsspellbooks.api.registry.SchoolRegistry;
import io.redspace.ironsspellbooks.api.registry.SpellRegistry;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.damage.DamageSources;
import io.redspace.ironsspellbooks.entity.spells.ChainLightning;
import io.redspace.ironsspellbooks.entity.mobs.IMagicSummon;
import io.redspace.ironsspellbooks.entity.spells.LightningStrike;
import io.redspace.ironsspellbooks.particle.ZapParticleOption;
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.isstechnomancy.compat.TravelOpticsCompat;
import net.isstechnomancy.entity.ClockworkAutomaton;
import net.isstechnomancy.entity.GearProjectile;
import net.isstechnomancy.entity.MagneticField;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.NeutralMob;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.BodyRotationControl;
import net.minecraft.world.entity.animal.AbstractGolem;
import net.minecraft.world.entity.animal.horse.AbstractHorse;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.npc.AbstractVillager;
import net.minecraft.world.entity.npc.Npc;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.trading.Merchant;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import net.minecraftforge.common.Tags;
import net.minecraftforge.event.ForgeEventFactory;
import org.joml.Vector3f;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Tech Dragon v5, the Technomancy boss: a four-legged, two-winged storm dragon in hextech armor
 * (model, animations and the baked hitbox/attack tracks are code-generated: tools/dragon_v5*.py, dragon_v4_anims*.py).
 *
 * <p>Fight: an aggressive ground predator. It runs its target down and closes gaps with a pounce, a dashing claw rake
 * and a horns-first ram, dodges aside and counter-attacks, chains bites and claw rakes, grabs and shakes small prey,
 * whips its tail at anything behind it, sweeps or blasts away crowds (tail sweep, wing gust, stomp, magnetic field
 * roar) and breathes lightning. It only takes to the air in short bursts: the dive chain (climbs and crashes down on
 * the target again and again), the storm call (hangs high over the arena raining lightning) and, in phase two,
 * Skyfall; or to chase a target that flies. Every melee hit is tested at the jaws / forefoot / tail tip position of
 * the animation frame it lands on ({@link DragonTracks}).</p>
 * <ul>
 *     <li>50% health: overcharge (phase two): its scales light up with hextech veins and glowing crystal fins grow
 *     along its back; faster, harder hitting, chains more, EM pulse, storm strikes and Skyfall.</li>
 *     <li>30% health, once: it lands at the lair centre behind an invulnerable shield and raises four Hextech Pylons
 *     that pour power into it for 25 s. Destroying all four shatters the shield and stuns it; otherwise it heals 8% of
 *     its health per pylon still standing and discharges a lightning blast.</li>
 *     <li>Death: it curls up, a sphere of hextech plates closes around it and explodes (40 blocks; a raised shield
 *     saves its holder but is destroyed).</li>
 * </ul>
 * EMP Screech stuns it (it drops to the ground). It cannot be pulled by grab/pull effects and has no pull skill.
 * The summoned {@link TechDrake} reuses this class, scaled down and rideable.
 */
public class TechDragon extends Monster implements GeoEntity {
    public static final double ARENA_RADIUS = 64;
    /** The boss renders (and collides) at twice the model's native size: ~26 blocks long, ~36 block wingspan. */
    public static final float BOSS_SCALE = 2.0f;
    public static final int LAND_AFTER = 80;
    public static final int SLEEP_AFTER = 1200;
    public static final float MAX_DAMAGE_PER_HIT = 50f;
    /** 1.9: an EMP can stun it once every 30 s. */
    public static final int STUN_IMMUNITY_TICKS = 600;
    public static final int PYLON_RISE = 48;
    public static final int PYLON_TIME = 500;

    public enum State {
        SPAWN(100, false), HOVER(0, false), LANDING(0, false), TAKEOFF(28, false),
        PERCH(0, true), LIE_DOWN(40, true), REST_UP(32, true), SLEEP(0, true), WAKE(48, true), GROUND(0, true),
        BITE(20, true), BITE_SWEEP(23, true), CLAW(23, true), GRAB(20, true), GRAB_HOLD(48, true), GRAB_TOSS(20, true),
        TAIL_WHIP(22, true), TAIL_SWEEP(32, true), STOMP(36, true), WING_GUST(38, true), FIELD_ROAR(40, true), REND(46, true),
        GBREATH_CHARGE(20, true), GBREATH(90, true), GROUND_ROAR(56, true), SLAM(24, true),
        COG_SPIT(24, false), BREATH_CHARGE(20, false), BREATH(90, false), THUNDER(64, false), ROAR(44, false), SWOOP(32, false),
        DIVE_RISE(18, false), DIVE(40, false), SKY_RISE(50, false), SKY_DIVE(40, false), SUMMON(40, false), EMP(34, false),
        ARC_BARRAGE(40, false), AIR_BITE(16, false),
        POUNCE(32, true), DASH_CLAW(25, true), DODGE(17, true), RAM(60, true), STORM_RISE(0, false), STORM(160, false), DIVE_BOUNCE(20, false),
        PHASE_TWO(68, true), PYLON_GO(0, false), PYLON_CHARGE(PYLON_RISE + PYLON_TIME, true), PYLON_FAIL(44, true),
        STUNNED(60, true), RIDDEN(0, true), DEATH(0, true),
        /* 1.8: kiting (wing-beat backstep, forward wing push, side hops) into the lightning spit; the crash landing */
        BACKSTEP(25, true), WING_PUSH(32, true), KITE_HOP(17, true), SPIT(26, true), CRASH(32, true),
        /* 1.9: EMP seizure, pin and gnaw, carry prey into the sky, the hextech core beam and its overload */
        EMP_STUN(60, true), PIN(64, true), CARRY(70, false), CORE_CHARGE(30, true), CORE_BEAM(56, true), OVERLOAD(48, true),
        /* 1.10: the 360 spin discharge, spacing hops, the sky breath and the strafing run; the rider's landing */
        SPIN(34, true), HOP(17, true), SKY_BREATH(120, false), STRAFE(70, false), RIDER_LAND(40, false);

        public final int duration;
        private final boolean grounded;

        State(int duration, boolean grounded) {
            this.duration = duration;
            this.grounded = grounded;
        }

        public boolean grounded() {
            return grounded;
        }
    }

    private static final EntityDataAccessor<Integer> DATA_STATE = SynchedEntityData.defineId(TechDragon.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_SERIAL = SynchedEntityData.defineId(TechDragon.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> DATA_PHASE_TWO = SynchedEntityData.defineId(TechDragon.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Integer> DATA_SHAKE = SynchedEntityData.defineId(TechDragon.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Float> DATA_SCALE = SynchedEntityData.defineId(TechDragon.class, EntityDataSerializers.FLOAT);
    /** Perched idle pose: 0 standing, 1 sitting, 2 lying down. */
    private static final EntityDataAccessor<Integer> DATA_IDLE = SynchedEntityData.defineId(TechDragon.class, EntityDataSerializers.INT);
    /** Attack variant: claw/tail whip 0 left, 1 right. */
    private static final EntityDataAccessor<Integer> DATA_VARIANT = SynchedEntityData.defineId(TechDragon.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> DATA_SHIELD = SynchedEntityData.defineId(TechDragon.class, EntityDataSerializers.BOOLEAN);
    /** Rideable drake: flying or walking. */
    protected static final EntityDataAccessor<Boolean> DATA_FLYING = SynchedEntityData.defineId(TechDragon.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> DATA_AIR_PHASE = SynchedEntityData.defineId(TechDragon.class, EntityDataSerializers.BOOLEAN);
    /** Entity id of the prey held in the jaws (-1 none): the client needs it to place that passenger at the mouth. */
    private static final EntityDataAccessor<Integer> DATA_GRABBED = SynchedEntityData.defineId(TechDragon.class, EntityDataSerializers.INT);
    /** 1.9: overloaded / EMP'd: every glowing part goes dead grey (the drained texture). */
    private static final EntityDataAccessor<Boolean> DATA_DRAINED = SynchedEntityData.defineId(TechDragon.class, EntityDataSerializers.BOOLEAN);
    /** 1.9: where the core beam ends this tick (the client draws the beam from the core to it). */
    private static final EntityDataAccessor<Vector3f> DATA_BEAM = SynchedEntityData.defineId(TechDragon.class, EntityDataSerializers.VECTOR3);

    private static final Map<String, RawAnimation> ANIMS = new HashMap<>();
    /** Every animation {@link #animationName()} can return (devtest ValidateAnimations checks they exist in the file). */
    public static final List<String> ANIMATION_NAMES = DragonAnimationNames.DRAGON;

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    protected final ServerBossEvent bossEvent = (ServerBossEvent) new ServerBossEvent(Component.translatable("entity.iss_technomancy.tech_dragon"),
            BossEvent.BossBarColor.PURPLE, BossEvent.BossBarOverlay.NOTCHED_10).setDarkenScreen(true);
    private final ServerBossEvent pylonEvent = (ServerBossEvent) new ServerBossEvent(Component.translatable("entity.iss_technomancy.hextech_pylon"),
            BossEvent.BossBarColor.BLUE, BossEvent.BossBarOverlay.NOTCHED_6);

    protected int stateTicks;
    protected int attackCooldown = 40;
    protected int groundTicks;
    protected int airAttacksLeft;
    @Nullable
    protected BlockPos home;
    protected Vec3 breathAim = Vec3.ZERO;
    private Vec3 diveTarget = Vec3.ZERO;
    private double diveStartY;
    protected Vec3 rendDirection = Vec3.ZERO;
    private State lastAttack = State.HOVER;
    protected double orbitAngle;
    private int stunImmunity;
    private int stunLength = 60;
    @Nullable
    protected LivingEntity grabbed;
    protected int idleTicks;
    protected int perchTicks;
    private int idleVariantTicks;
    protected Vec3 landSpot = Vec3.ZERO;
    @Nullable
    private State afterRise;
    @Nullable
    private LivingEntity aggroTarget;
    private int aggroTicks;
    protected int fieldCooldown = 200;
    protected int gustCooldown = 100;
    protected int grabCooldown = 100;
    protected int breathCooldown = 80;
    private final Set<Integer> hitThisAttack = new HashSet<>();
    private boolean pylonsDone;
    private final List<UUID> pylons = new ArrayList<>();
    private boolean skyfallSlam;
    private boolean lootReleased;
    @Nullable
    private DamageSource deathSource;
    private boolean shellSpawned;
    protected float flightPitch, flightPitchO, bank, bankO, tailDrag, tailDragO;
    /* v5 moveset */
    protected int skyTimer = 360;
    private int diveChainLeft;
    @Nullable
    private State afterTakeoff;
    private int dodgeCooldown;
    private int pendingDodge;
    private int unreachableTicks;
    private Vec3 leapFrom = Vec3.ZERO, leapTo = Vec3.ZERO;
    private double leapHeight;
    private Vec3 dashDir = Vec3.ZERO;
    private double dashSpeed;
    private double stormY;
    /* 1.8 */
    protected int tailCooldown = 60;
    protected int kiteCooldown = 160;
    protected int spitCooldown = 60;
    private int kiteHopsLeft;
    private int targetScan;
    private boolean crashSkyfall;
    /** Shock rings still to come from the last crash: {ticks left, radius, x, y, z}. */
    private final List<double[]> rings = new ArrayList<>();
    private final Set<Integer> ringHit = new HashSet<>();
    /* 1.9 */
    protected int pinCooldown = 160;
    protected int beamCooldown = 400;
    private Vec3 beamAim = Vec3.ZERO;
    private double carryTop;
    private int griefBudget;
    /* 1.10 */
    protected int spinCooldown = 120;
    protected int hopCooldown = 60;
    protected int roarCooldown = 300;
    /** Grows while something stands on its back (it spins it off), decays otherwise. */
    private int onBackTicks;
    /** Spacing hop: where to move, in model px of its own frame (x = left, z = forward). */
    private Vec3 hopShift = Vec3.ZERO;
    private int strafeSpits;

    /* multipart hitboxes, one per body region of the baked boxes (DragonTracks.R_*): sized and placed every tick */
    private final TechDragonPart[] parts = {
            new TechDragonPart(this, "head", 1.3f, true), new TechDragonPart(this, "neck_a", 1.0f, true), new TechDragonPart(this, "neck_b", 1.0f, true),
            new TechDragonPart(this, "chest", 1.0f, true), new TechDragonPart(this, "hips", 1.0f, true),
            new TechDragonPart(this, "leg_fl", 0.9f, true), new TechDragonPart(this, "leg_fr", 0.9f, true),
            new TechDragonPart(this, "leg_hl", 0.9f, true), new TechDragonPart(this, "leg_hr", 0.9f, true),
            new TechDragonPart(this, "tail_a", 0.9f, true), new TechDragonPart(this, "tail_b", 0.9f, true),
            new TechDragonPart(this, "tail_c", 0.9f, true), new TechDragonPart(this, "tail_d", 0.9f, true),
            new TechDragonPart(this, "wing_l_in", 0.7f, false), new TechDragonPart(this, "wing_l_out", 0.7f, false),
            new TechDragonPart(this, "wing_r_in", 0.7f, false), new TechDragonPart(this, "wing_r_out", 0.7f, false)};
    private final float[] boxBuf = new float[6];
    /** Rider's seat on the summoned dragon (model px): on the back between the wing roots, in the gap of the fin row. */
    public static final Vec3 SEAT = new Vec3(0, 42.5, -25);

    // client-side animation bookkeeping
    private int clientSerial = -1;
    private int seenSerial = -1;

    public TechDragon(EntityType<? extends TechDragon> type, Level level) {
        super(type, level);
        this.xpReward = 600;
        this.noCulling = true;
        setNoGravity(true);
        this.noPhysics = true;
        setPersistenceRequired();
        refreshDimensions();
        this.setId(ENTITY_COUNTER.getAndAdd(parts.length + 1) + 1);
        pylonEvent.setVisible(false);
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 1000)
                .add(Attributes.ARMOR, 16)
                .add(Attributes.ARMOR_TOUGHNESS, 8)
                .add(Attributes.ATTACK_DAMAGE, 22)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 72);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_STATE, State.SPAWN.ordinal());
        this.entityData.define(DATA_SERIAL, 0);
        this.entityData.define(DATA_PHASE_TWO, false);
        this.entityData.define(DATA_SHAKE, 0);
        this.entityData.define(DATA_SCALE, defaultScale());
        this.entityData.define(DATA_DRAINED, false);
        this.entityData.define(DATA_BEAM, new Vector3f());
        this.entityData.define(DATA_IDLE, 0);
        this.entityData.define(DATA_VARIANT, 0);
        this.entityData.define(DATA_SHIELD, false);
        this.entityData.define(DATA_FLYING, false);
        this.entityData.define(DATA_AIR_PHASE, true);
        this.entityData.define(DATA_GRABBED, -1);
    }

    @Override
    public SpawnGroupData finalizeSpawn(@NotNull ServerLevelAccessor level, @NotNull DifficultyInstance difficulty, @NotNull MobSpawnType reason,
                                        @Nullable SpawnGroupData data, @Nullable CompoundTag tag) {
        home = blockPosition();
        setState(State.SPAWN);
        return super.finalizeSpawn(level, difficulty, reason, data, tag);
    }

    /* ---------------------------------------------------------------- hooks for the summoned drake */

    /** Damage multiplier for every attack (the drake scales this down with spell power). */
    protected float damageScale() {
        return 1f;
    }

    protected boolean isBoss() {
        return true;
    }

    protected float defaultScale() {
        return BOSS_SCALE;
    }

    public int getIdleVariant() {
        return this.entityData.get(DATA_IDLE);
    }

    protected void setIdleVariant(int v) {
        this.entityData.set(DATA_IDLE, v);
    }

    public int getAttackVariant() {
        return this.entityData.get(DATA_VARIANT);
    }

    protected void setAttackVariant(int v) {
        this.entityData.set(DATA_VARIANT, v);
    }

    public boolean isShielded() {
        return this.entityData.get(DATA_SHIELD);
    }

    protected void setShielded(boolean shield) {
        this.entityData.set(DATA_SHIELD, shield);
    }

    public boolean isFlyingMount() {
        return this.entityData.get(DATA_FLYING);
    }

    /* ---------------------------------------------------------------- multipart */

    @Override
    public void setId(int id) {
        super.setId(id);
        for (int i = 0; i < parts.length; i++) {
            parts[i].setId(id + i + 1);
        }
    }

    @Override
    public boolean isMultipartEntity() {
        return true;
    }

    @Override
    public net.minecraftforge.entity.PartEntity<?>[] getParts() {
        return parts;
    }

    /** A hit on one of the body parts: the head is a weak spot (x1.3), the wings are tough (x0.7). */
    public boolean hurtFromPart(TechDragonPart part, DamageSource source, float amount) {
        return hurt(source, amount * part.damageMultiplier);
    }

    /** Sizes and places every hitbox on the bounds of its body region in the animation frame being played (the baked
     * model-space box, turned by the body yaw and the flight pitch). */
    protected void tickParts() {
        String anim = animationName();
        double t = animationTime(anim);
        float pitch = getState().grounded() && !isFlyingMount() ? 0 : flightPitch;
        double yaw = Math.toRadians(yBodyRot), p = Math.toRadians(pitch);
        double cy = Math.abs(Math.cos(yaw)), sy = Math.abs(Math.sin(yaw)), cp = Math.abs(Math.cos(p)), sp = Math.abs(Math.sin(p));
        float scale = getModelScale();
        double s = scale / 16.0;
        for (int i = 0; i < parts.length; i++) {
            float[] b = DragonTracks.box(anim, t, i, boxBuf);
            Vec3 c = DragonTracks.toWorld(new Vec3(b[0], b[1], b[2]), position(), yBodyRot, pitch, scale);
            double hx = b[3], hy = cp * b[4] + sp * b[5], hz = sp * b[4] + cp * b[5];
            double wx = Math.max(0.15, (cy * hx + sy * hz) * s), wz = Math.max(0.15, (sy * hx + cy * hz) * s), wy = Math.max(0.15, hy * s);
            parts[i].place(new AABB(c.x - wx, c.y - wy, c.z - wz, c.x + wx, c.y + wy, c.z + wz));
        }
    }

    /** Its own body never blocks it (the other solid parts are like a boat's hull to everything else). */
    @Override
    public boolean canCollideWith(@NotNull Entity other) {
        return !(other instanceof TechDragonPart part && part.getParent() == this) && super.canCollideWith(other);
    }

    /**
     * Anything the moving body ends up overlapping (players, mobs, other bosses) is pushed back out of it sideways, at
     * most 0.6 blocks a tick, so nothing can get stuck inside the dragon. 1.10: nothing is ever lifted on top of it any
     * more - whatever stands on its back (climbed, jumped or teleported up there) is slid off the nearer side and jolted
     * now and then; if it stays, the dragon spins round and discharges to throw it off (see pickGroundMove).
     */
    private void pushOutOverlapping() {
        AABB all = null;
        for (TechDragonPart part : parts) {
            if (part.solid) {
                all = all == null ? part.getBoundingBox() : all.minmax(part.getBoundingBox());
            }
        }
        if (all == null) {
            return;
        }
        boolean anyOnBack = false;
        for (Entity e : level().getEntities(this, all.expandTowards(0, 0.6, 0), e -> e instanceof LivingEntity && e.isAlive() && !e.isSpectator() && !e.noPhysics
                && e.getVehicle() == null && !(e instanceof HextechPylon) && !hasPassenger(e))) {
            AABB eb = e.getBoundingBox();
            Vec3 best = null;
            boolean onBack = false;
            for (TechDragonPart part : parts) {
                if (!part.solid) {
                    continue;
                }
                AABB pb = part.getBoundingBox();
                boolean overXZ = eb.maxX > pb.minX && eb.minX < pb.maxX && eb.maxZ > pb.minZ && eb.minZ < pb.maxZ;
                boolean resting = overXZ && eb.minY >= pb.maxY - 0.05 && eb.minY <= pb.maxY + 0.4;
                boolean inside = pb.intersects(eb);
                if (!inside && !resting) {
                    continue;
                }
                if (resting || eb.minY > pb.getCenter().y) {
                    onBack = true;
                    continue;
                }
                double dx = pb.maxX - eb.minX < eb.maxX - pb.minX ? pb.maxX - eb.minX : -(eb.maxX - pb.minX);
                double dz = pb.maxZ - eb.minZ < eb.maxZ - pb.minZ ? pb.maxZ - eb.minZ : -(eb.maxZ - pb.minZ);
                Vec3 v = Math.abs(dx) < Math.abs(dz) ? new Vec3(dx, 0, 0) : new Vec3(0, 0, dz);
                if (best == null || v.lengthSqr() > best.lengthSqr()) {
                    best = v;
                }
            }
            if (onBack) {
                // slide it off the nearer flank (never up: that is how teleporting mobs ended up parked on its back)
                Vec3 off = e.position().subtract(position()).multiply(1, 0, 1);
                Vec3 side = leftDir().scale(off.dot(leftDir()) >= 0 ? 1 : -1);
                double kb = e instanceof LivingEntity l ? 1 - l.getAttributeValue(Attributes.KNOCKBACK_RESISTANCE) * 0.5 : 1;
                Vec3 v = e.getDeltaMovement();
                e.setDeltaMovement(side.x * 0.55 * kb + v.x * 0.3, Math.max(v.y, 0.18), side.z * 0.55 * kb + v.z * 0.3);
                e.hurtMarked = true;
                if (e instanceof LivingEntity victim && canHit(victim)) {
                    anyOnBack = true;
                    if ((tickCount + e.getId()) % 12 == 0) {
                        DamageSources.applyDamage(victim, dmg(3f), lightningSource());
                        if (level() instanceof ServerLevel server) {
                            Vec3 core = position().add(0, getBbHeight() * 0.5, 0);
                            server.sendParticles(new ZapParticleOption(victim.getBoundingBox().getCenter()), core.x, core.y, core.z, 1, 0, 0, 0, 0);
                        }
                    }
                }
                continue;
            }
            if (best == null) {
                continue;
            }
            double len = best.length();
            Vec3 step = len > 0.6 ? best.scale(0.6 / len) : best;
            if (e instanceof Player) {
                // the player's own client moves the player: push with velocity
                Vec3 v = e.getDeltaMovement();
                e.setDeltaMovement(step.x != 0 ? step.x * 0.6 : v.x, v.y, step.z != 0 ? step.z * 0.6 : v.z);
                e.hurtMarked = true;
            } else {
                e.move(net.minecraft.world.entity.MoverType.SHULKER_BOX, step);
            }
        }
        onBackTicks = anyOnBack ? onBackTicks + 2 : Math.max(0, onBackTicks - 1);
    }

    /** Ticks since the current state began (the client mirrors it): the client model times the phase-two growth with it. */
    public int getStateTicks() {
        return stateTicks;
    }

    public float getModelScale() {
        return this.entityData.get(DATA_SCALE);
    }

    protected void setModelScale(float scale) {
        this.entityData.set(DATA_SCALE, scale);
        refreshDimensions();
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
        return super.getDimensions(pose).scale(getModelScale());
    }

    /* ---------------------------------------------------------------- tracks: where the jaws, feet, tail are */

    /** World position of a baked track point for the current animation frame. */
    public Vec3 track(int point) {
        String anim = animationName();
        return trackWorld(anim, animationTime(anim), point);
    }

    protected Vec3 trackWorld(String anim, double seconds, int point) {
        float pitch = getState().grounded() && !(isFlyingMount()) ? 0 : flightPitch;
        return DragonTracks.toWorld(DragonTracks.point(anim, seconds, point), position(), yBodyRot, pitch, getModelScale());
    }

    /** Seconds into the given animation (state-driven animations start with the state, loops run on the clock). */
    protected double animationTime(String anim) {
        return switch (anim) {
            case "ground_idle", "walk", "run", "fly", "fly_fast", "glide", "hover", "rest", "sleep", "sit", "stunned", "pylon_charge", "storm", "breath_down", "strafe" -> tickCount / 20.0;
            default -> stateTicks / 20.0;
        };
    }

    public Vec3 mouthPosition() {
        return track(DragonTracks.MOUTH);
    }

    public Vec3 corePosition() {
        return track(DragonTracks.CORE);
    }

    /* ---------------------------------------------------------------- state */

    public State getState() {
        int i = this.entityData.get(DATA_STATE);
        return i >= 0 && i < State.values().length ? State.values()[i] : State.HOVER;
    }

    protected void setState(State state) {
        if (state != State.GRAB_HOLD && state != State.GRAB_TOSS && state != State.GRAB && state != State.PIN && state != State.CARRY) {
            releaseGrabbed(Vec3.ZERO);
        }
        this.entityData.set(DATA_STATE, state.ordinal());
        this.entityData.set(DATA_DRAINED, state == State.EMP_STUN || state == State.OVERLOAD);
        this.entityData.set(DATA_SERIAL, this.entityData.get(DATA_SERIAL) + 1);
        stateTicks = 0;
        hitThisAttack.clear();
        applyPhysics(state);
        if (state == State.PERCH) {
            perchTicks = 0;
            idleVariantTicks = 140 + random.nextInt(100);
        }
        if (!state.grounded() && state != State.DEATH) {
            this.entityData.set(DATA_AIR_PHASE, true);
        } else if (state.grounded()) {
            this.entityData.set(DATA_AIR_PHASE, false);
        }
    }

    protected void applyPhysics(State state) {
        boolean grounded = state.grounded();
        setNoGravity(!grounded);
        this.noPhysics = !grounded && state != State.DEATH;
        setMaxUpStep(grounded ? 1.0f + getModelScale() * 0.6f : 0.6f);
    }

    public boolean isDrained() {
        return this.entityData.get(DATA_DRAINED);
    }

    /** The core beam's end (world), valid while in CORE_BEAM. */
    public Vec3 getBeamEnd() {
        Vector3f v = this.entityData.get(DATA_BEAM);
        return new Vec3(v.x, v.y, v.z);
    }

    public boolean isPhaseTwo() {
        return this.entityData.get(DATA_PHASE_TWO);
    }

    protected void setPhaseTwo(boolean phaseTwo) {
        this.entityData.set(DATA_PHASE_TWO, phaseTwo);
    }

    public int getShake() {
        return this.entityData.get(DATA_SHAKE);
    }

    protected void shake(int ticks) {
        if (isBoss()) {
            this.entityData.set(DATA_SHAKE, Math.max(getShake(), ticks));
        }
    }

    protected boolean isInvulnerableState() {
        State s = getState();
        return s == State.SPAWN || s == State.PHASE_TWO || s == State.DEATH || isShielded();
    }

    /** EMP Screech: drops the dragon (out of the sky if needed) and keeps it down for a moment. */
    public boolean applyStun(int ticks) {
        if (level().isClientSide || stunImmunity > 0 || isInvulnerableState() || getState() == State.STUNNED || getState() == State.PYLON_GO
                || getState() == State.PYLON_CHARGE || isVehicle() && !isBoss()) {
            return false;
        }
        releaseGrabbed(Vec3.ZERO);
        stunLength = Math.max(ticks, 60);
        setState(State.EMP_STUN);
        stunImmunity = STUN_IMMUNITY_TICKS;
        playSound(SoundEvents.ANVIL_LAND, 3f, 0.5f);
        playSound(SoundEvents.LIGHTNING_BOLT_IMPACT, 3f, 1.6f);
        MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + getBbHeight() * 0.6, getZ(), 60, 2, 1, 2, 0.4, true);
        ring(position().add(0, 0.3, 0), 6 * getModelScale(), 14, 0);
        return true;
    }

    protected void stun(int ticks) {
        stunLength = ticks;
        setState(State.STUNNED);
    }

    /* ---------------------------------------------------------------- boss bars */

    @Override
    public void startSeenByPlayer(@NotNull ServerPlayer player) {
        super.startSeenByPlayer(player);
        if (isBoss()) {
            bossEvent.addPlayer(player);
            pylonEvent.addPlayer(player);
        }
    }

    @Override
    public void stopSeenByPlayer(@NotNull ServerPlayer player) {
        super.stopSeenByPlayer(player);
        bossEvent.removePlayer(player);
        pylonEvent.removePlayer(player);
    }

    @Override
    public void setCustomName(@Nullable Component name) {
        super.setCustomName(name);
        bossEvent.setName(getDisplayName());
    }

    /* ---------------------------------------------------------------- pose data (both sides) */

    public float getBank(float partialTick) {
        return Mth.lerp(partialTick, bankO, bank);
    }

    public float getFlightPitch(float partialTick) {
        return Mth.lerp(partialTick, flightPitchO, flightPitch);
    }

    public float getTailDrag(float partialTick) {
        return Mth.lerp(partialTick, tailDragO, tailDrag);
    }

    private void updatePose() {
        bankO = bank;
        flightPitchO = flightPitch;
        tailDragO = tailDrag;
        State s = getState();
        boolean flying = (!s.grounded() || isFlyingMount() && s == State.RIDDEN) && s != State.DEATH && s != State.SPAWN;
        float yawDelta = Mth.wrapDegrees(yBodyRot - yBodyRotO);
        float targetBank = flying ? Mth.clamp(yawDelta * 7f, -40f, 40f) : 0f;
        bank += (targetBank - bank) * 0.12f;
        double dx = getX() - xo, dy = getY() - yo, dz = getZ() - zo;
        double hs = Math.sqrt(dx * dx + dz * dz);
        boolean ridingDive = s == State.RIDDEN && isFlyingMount() && dy < -0.35 * Math.max(1, getModelScale());
        boolean diving = s == State.DIVE || s == State.SKY_DIVE || s == State.SWOOP || ridingDive;
        float targetPitch = flying && !diving ? (float) Mth.clamp(Mth.atan2(dy, Math.max(hs, 0.08)) * Mth.RAD_TO_DEG * 0.7, -26, 26) : 0f;
        if (diving) {
            targetPitch = ridingDive ? (float) Mth.clamp(Mth.atan2(dy, Math.max(hs, 0.08)) * Mth.RAD_TO_DEG, -85, 10)
                    : (float) Mth.clamp(Mth.atan2(dy, Math.max(hs, 0.08)) * Mth.RAD_TO_DEG * 0.8, -55, 10);
        }
        flightPitch += (targetPitch - flightPitch) * 0.1f;
        tailDrag += (Mth.clamp(yawDelta * 5f, -30f, 30f) - tailDrag) * 0.15f;
    }

    /* ---------------------------------------------------------------- tick */

    @Override
    protected @NotNull BodyRotationControl createBodyControl() {
        return new BodyRotationControl(this) {
            @Override
            public void clientTick() {
                TechDragon.this.yBodyRot = TechDragon.this.getYRot();
            }
        };
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (level().isClientSide) {
            // mirror the server's state timer so jaws/saddle positions match the animation being played
            int serial = this.entityData.get(DATA_SERIAL);
            if (serial != seenSerial) {
                seenSerial = serial;
                stateTicks = 0;
            } else {
                stateTicks++;
            }
        }
        updatePose();
        tickParts();
        if (level().isClientSide) {
            clientEffects();
            return;
        }
        if (isAlive()) {
            pushOutOverlapping();
        }
        dodgeCooldown = Math.max(0, dodgeCooldown - 1);
        pendingDodge = Math.max(0, pendingDodge - 1);
        if (getShake() > 0) {
            this.entityData.set(DATA_SHAKE, getShake() - 1);
        }
        stunImmunity = Math.max(0, stunImmunity - 1);
        fieldCooldown = Math.max(0, fieldCooldown - 1);
        gustCooldown = Math.max(0, gustCooldown - 1);
        grabCooldown = Math.max(0, grabCooldown - 1);
        breathCooldown = Math.max(0, breathCooldown - 1);
        aggroTicks = Math.max(0, aggroTicks - 1);
        tailCooldown = Math.max(0, tailCooldown - 1);
        kiteCooldown = Math.max(0, kiteCooldown - 1);
        spitCooldown = Math.max(0, spitCooldown - 1);
        pinCooldown = Math.max(0, pinCooldown - 1);
        beamCooldown = Math.max(0, beamCooldown - 1);
        spinCooldown = Math.max(0, spinCooldown - 1);
        hopCooldown = Math.max(0, hopCooldown - 1);
        roarCooldown = Math.max(0, roarCooldown - 1);
        tickRings();
        State state = getState();
        if (state == State.DEATH) {
            return;
        }
        if (home == null) {
            home = blockPosition();
        }
        stateTicks++;
        LivingEntity target = findTarget();
        setTarget(target);
        if (isBoss()) {
            bossTick(state, target);
            state = getState();
        }
        tickState(state, target);
        if (isBoss() && target != null && tickCount % 2 == 0) {
            breakThrough();
        }
        if (tickCount % 22 == 0 && !getState().grounded() && getState() != State.DIVE && getState() != State.SKY_DIVE) {
            level().playSound(null, getX(), getY(), getZ(), SoundEvents.ENDER_DRAGON_FLAP, SoundSource.HOSTILE, 2.5f * getModelScale(), 0.7f + random.nextFloat() * 0.2f);
        }
    }

    /** Boss bar, phase two at 50%, pylons at 30%, the storm, healing while idle. */
    private void bossTick(State state, @Nullable LivingEntity target) {
        float progress = getHealth() / getMaxHealth();
        bossEvent.setProgress(state == State.SPAWN ? Math.min(1f, stateTicks / (float) State.SPAWN.duration) * progress : progress);
        boolean busy = state == State.SPAWN || state == State.PHASE_TWO || state == State.PYLON_GO || state == State.PYLON_CHARGE
                || state == State.PYLON_FAIL || state == State.STUNNED || state == State.GRAB_HOLD || state == State.GRAB_TOSS || state == State.SKY_DIVE;
        if (!busy && !isPhaseTwo() && getHealth() <= getMaxHealth() * 0.5f) {
            setPhaseTwo(true);
            bossEvent.setColor(BossEvent.BossBarColor.BLUE);
            setState(State.PHASE_TWO);
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 6f, 0.7f);
            return;
        }
        if (!busy && isPhaseTwo() && !pylonsDone && getHealth() <= getMaxHealth() * 0.3f) {
            pylonsDone = true;
            setShielded(true);
            setState(State.PYLON_GO);
            playSound(SoundEvents.BEACON_POWER_SELECT, 5f, 0.6f);
            return;
        }
        if (isPhaseTwo() && target != null && tickCount % 60 == 0 && !busy) {
            stormStrike(target);
        }
        if (target == null && getHealth() < getMaxHealth() && tickCount % 20 == 0) {
            heal(4f);
        }
    }

    protected void tickState(State state, @Nullable LivingEntity target) {
        switch (state) {
            case SPAWN -> tickSpawn();
            case HOVER -> tickHover(target);
            case LANDING -> tickLanding(target);
            case TAKEOFF -> tickTakeoff();
            case PERCH -> tickPerch(target);
            case LIE_DOWN, REST_UP -> tickLieTransition(target);
            case SLEEP -> tickSleep(target);
            case WAKE -> tickWake();
            case GROUND -> tickGround(target);
            case BITE, BITE_SWEEP -> tickBite(target);
            case CLAW -> tickClaw(target);
            case GRAB -> tickGrab(target);
            case GRAB_HOLD -> tickGrabHold();
            case GRAB_TOSS -> tickGrabToss();
            case TAIL_WHIP -> tickTailWhip();
            case TAIL_SWEEP -> tickTailSweep();
            case STOMP -> tickStomp();
            case WING_GUST -> tickWingGust(target);
            case FIELD_ROAR -> tickFieldRoar(target);
            case REND -> tickRend(target);
            case GBREATH_CHARGE, BREATH_CHARGE -> tickBreathCharge(target);
            case GBREATH, BREATH -> tickBreath(target);
            case GROUND_ROAR -> tickGroundRoar(target);
            case SLAM -> tickSlam();
            case COG_SPIT -> tickCogSpit(target);
            case THUNDER -> tickThunder(target);
            case ROAR -> tickRoar(target);
            case SWOOP -> tickSwoop(target);
            case DIVE_RISE -> tickDiveRise(target);
            case DIVE -> tickDive();
            case SKY_RISE -> tickSkyRise(target);
            case SKY_DIVE -> tickSkyDive();
            case SUMMON -> tickSummon(target);
            case EMP -> tickEmp(target);
            case ARC_BARRAGE -> tickArcBarrage(target);
            case AIR_BITE -> tickAirBite();
            case POUNCE -> tickPounce(target);
            case DASH_CLAW -> tickDashClaw(target);
            case DODGE -> tickDodge(target);
            case RAM -> tickRam(target);
            case STORM_RISE -> tickStormRise(target);
            case STORM -> tickStorm(target);
            case DIVE_BOUNCE -> tickDiveBounce(target);
            case BACKSTEP -> tickBackstep(target);
            case WING_PUSH -> tickWingPush(target);
            case KITE_HOP -> tickKiteHop(target);
            case SPIT -> tickSpit(target);
            case CRASH -> tickCrash(target);
            case EMP_STUN -> tickEmpStun();
            case PIN -> tickPin(target);
            case CARRY -> tickCarry();
            case CORE_CHARGE -> tickCoreCharge(target);
            case CORE_BEAM -> tickCoreBeam(target);
            case OVERLOAD -> tickOverload();
            case SPIN -> tickSpin();
            case HOP -> tickHop(target);
            case SKY_BREATH -> tickSkyBreath(target);
            case STRAFE -> tickStrafe(target);
            case PHASE_TWO -> tickPhaseTwo();
            case PYLON_GO -> tickPylonGo();
            case PYLON_CHARGE -> tickPylonCharge(target);
            case PYLON_FAIL -> tickPylonFail(target);
            case STUNNED -> tickStunned();
            default -> {
            }
        }
    }

    /* ---------------------------------------------------------------- targeting */

    /**
     * The boss is aggressive (1.8): whoever hurt it first, then players, then the most dangerous thing near it
     * (bosses first, then the nearest hostile, neutral mob, golem or pet). It keeps a target until that target is
     * dead, out of reach or out of range - no random switching - except that a player outranks a mob. It never picks
     * passive animals (horses and donkeys included, even tamed), villagers, traders or other NPCs (its area attacks
     * still hit whatever stands in them). The summoned drake overrides this and follows its owner.
     */
    @Nullable
    protected LivingEntity findTarget() {
        State st = getState();
        LivingEntity attacker = getLastHurtByMob();
        if (st == State.SLEEP || st == State.PERCH && getIdleVariant() == 2) {
            if (attacker != null && attacker.isAlive() && canHit(attacker)) {
                return attacker;
            }
            // asleep it only notices what comes close (a sneaking player can slip past)
            return tickCount % 10 == 0 ? nearestPrey(14, true) : null;
        }
        if (isValidAggro(aggroTarget)) {
            if (distanceToSqr(aggroTarget) < 56 * 56 || hasLineOfSight(aggroTarget)) {
                aggroTicks = Math.max(aggroTicks, 200);
            }
            if (aggroTicks > 0) {
                return aggroTarget;
            }
        }
        aggroTarget = null;
        LivingEntity current = getTarget();
        boolean keep = current != null && current.isAlive() && !current.isRemoved() && distanceToSqr(current) < 72 * 72 && isPrey(current);
        if (keep && (current instanceof Player || tickCount % 20 != 0)) {
            return current;
        }
        if (attacker != null && attacker.isAlive() && distanceToSqr(attacker) < 56 * 56 && canHit(attacker)) {
            return attacker;
        }
        if (keep) {
            // a player that just walked in outranks the mob it is fighting
            Player player = nearestPlayerPrey(60);
            return player != null ? player : current;
        }
        if (++targetScan % 10 != 1) {
            return null;
        }
        return nearestPrey(60, false);
    }

    @Nullable
    private Player nearestPlayerPrey(double range) {
        return level().getEntitiesOfClass(Player.class, getBoundingBox().inflate(range), this::isPrey)
                .stream().min(Comparator.comparingDouble(this::distanceToSqr)).orElse(null);
    }

    /** Players first; otherwise the nearest prey, bosses counting as twice as close. */
    @Nullable
    protected LivingEntity nearestPrey(double range, boolean ignoreSneaking) {
        Player player = level().getEntitiesOfClass(Player.class, getBoundingBox().inflate(range), p -> isPrey(p) && !(ignoreSneaking && p.isShiftKeyDown()))
                .stream().min(Comparator.comparingDouble(this::distanceToSqr)).orElse(null);
        if (player != null) {
            return player;
        }
        return level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(range * 0.8), e -> !(e instanceof Player) && isPrey(e))
                .stream().min(Comparator.comparingDouble(e -> distanceToSqr(e) * (isBossLike(e) ? 0.25 : 1.0))).orElse(null);
    }

    /** Other bosses (the forge:bosses tag - Wither, Ender Dragon, modded bosses that use it - or anything with 150+
     * max health): picked before ordinary mobs. */
    public static boolean isBossLike(LivingEntity e) {
        return e.getType().is(Tags.EntityTypes.BOSSES) || e.getMaxHealth() >= 150f;
    }

    /**
     * What the boss goes after on its own: players, hostile mobs (vanilla and modded), other bosses, neutral mobs,
     * golems (snow golems too) and anyone's pets or summons. Not passive animals, horses/donkeys/llamas (even tamed),
     * villagers, wandering traders, merchants or other NPCs, armour stands. The drake only hunts hostiles and its
     * owner's target.
     */
    public boolean isPrey(LivingEntity e) {
        if (!canHit(e) || e == grabbed || e instanceof ArmorStand || !e.isAttackable()) {
            return false;
        }
        if (!isBoss()) {
            return e == getTarget();
        }
        if (e instanceof Player) {
            return true;
        }
        if (e instanceof Npc || e instanceof Merchant || e instanceof AbstractVillager || e instanceof AbstractHorse) {
            return false;
        }
        if (e instanceof Enemy || e instanceof NeutralMob || e instanceof AbstractGolem || e instanceof IMagicSummon || e instanceof TechDragon) {
            return true;
        }
        if (e instanceof OwnableEntity pet && pet.getOwnerUUID() != null) {
            return true;
        }
        // big creatures count as dangerous even when the code calls them animals (Ice and Fire dragons are tamable
        // animals), and so does anything that is attacking something right now
        return isBossLike(e) || e.getMaxHealth() >= 60f || e instanceof Mob mob && mob.getTarget() != null && mob.getTarget().isAlive();
    }

    private boolean isValidAggro(@Nullable LivingEntity e) {
        return e != null && e.isAlive() && !e.isRemoved() && e.level() == level() && distanceToSqr(e) < 160 * 160 && canHit(e);
    }

    protected boolean isChasingAttacker() {
        return aggroTarget != null && aggroTarget == getTarget() && aggroTicks > 0;
    }

    protected boolean canHit(LivingEntity e) {
        return e != this && e.isAlive() && !isAlliedTo(e) && !(e instanceof Player p && (p.isCreative() || p.isSpectator()))
                && !(e instanceof HextechPylon) && e != getVehicle() && !hasPassenger(e) || e == grabbed && e.isAlive();
    }

    /** Target position in the dragon's frame, in model pixels: x = left, y = up, z = forward. */
    protected Vec3 local(Vec3 world) {
        double yaw = Math.toRadians(yBodyRot);
        double dx = world.x - getX(), dy = world.y - getY(), dz = world.z - getZ();
        double s = 16.0 / getModelScale();
        double left = dx * Math.cos(yaw) + dz * Math.sin(yaw);
        double fwd = -dx * Math.sin(yaw) + dz * Math.cos(yaw);
        return new Vec3(left * s, dy * s, fwd * s);
    }

    /* ---------------------------------------------------------------- movement helpers */

    protected void flyTowards(Vec3 point, double speed) {
        Vec3 delta = point.subtract(position());
        double dist = delta.length();
        Vec3 desired = dist < 0.5 ? Vec3.ZERO : delta.scale(Math.min(speed, dist * 0.25) / dist);
        setDeltaMovement(getDeltaMovement().lerp(desired, 0.12));
    }

    /** Flight along the heading, turning at a limited rate (no spinning on the spot). */
    protected void steer(Vec3 point, double speed, float turnRate) {
        Vec3 to = point.subtract(position());
        double horizontal = to.horizontalDistance();
        float yaw = getYRot();
        if (horizontal > 0.5) {
            float wanted = (float) (Mth.atan2(to.z, to.x) * Mth.RAD_TO_DEG) - 90f;
            yaw = Mth.approachDegrees(yaw, wanted, turnRate);
            setYRot(yaw);
            yBodyRot = yaw;
        }
        float misalign = Math.abs(Mth.wrapDegrees((float) (Mth.atan2(to.z, to.x) * Mth.RAD_TO_DEG) - 90f - yaw));
        double align = Mth.clamp(1.0 - misalign / 140.0, 0.35, 1.0);
        double forward = speed * align * Mth.clamp(horizontal / (6.0 * Math.max(1, getModelScale())), 0.12, 1.0);
        Vec3 heading = Vec3.directionFromRotation(0, yaw).scale(forward);
        double vertical = Mth.clamp(to.y * 0.08, -0.45, 0.45) * Math.max(1, getModelScale() * 0.7);
        setDeltaMovement(getDeltaMovement().lerp(new Vec3(heading.x, vertical, heading.z), 0.15));
    }

    protected Vec3 orbitPoint(Vec3 centre, double radius, double height, double angularSpeed) {
        orbitAngle += angularSpeed;
        double ahead = orbitAngle + 0.55;
        return centre.add(Math.cos(ahead) * radius, height, Math.sin(ahead) * radius);
    }

    protected void turnBody(Vec3 point, float maxTurn) {
        double dx = point.x - getX();
        double dz = point.z - getZ();
        if (dx * dx + dz * dz < 0.01) {
            return;
        }
        float wanted = (float) (Mth.atan2(dz, dx) * Mth.RAD_TO_DEG) - 90f;
        float yaw = Mth.approachDegrees(getYRot(), wanted, maxTurn);
        setYRot(yaw);
        yBodyRot = yaw;
    }

    /** Points the head (procedural neck look on the client) at a point, at most 70 degrees off the body. */
    protected void lookTowards(Vec3 point) {
        double dx = point.x - getX();
        double dz = point.z - getZ();
        float wanted = (float) (Mth.atan2(dz, dx) * Mth.RAD_TO_DEG) - 90f;
        float rel = Mth.clamp(Mth.wrapDegrees(wanted - yBodyRot), -70f, 70f);
        yHeadRot = Mth.approachDegrees(yHeadRot, yBodyRot + rel, 10f);
        double dy = point.y - (getY() + getBbHeight() * 0.8);
        setXRot((float) Mth.clamp(-(Mth.atan2(dy, Math.sqrt(dx * dx + dz * dz)) * Mth.RAD_TO_DEG), -40, 40));
    }

    protected void faceTowards(Vec3 point, float maxTurn) {
        turnBody(point, getState().grounded() || isFlyingMount() ? maxTurn : Math.min(maxTurn, 3.5f));
        lookTowards(point);
    }

    /** Air attacks keep gliding along the sweep around the target (slower) instead of stopping dead in the air. */
    protected void airDrift(@Nullable LivingEntity target, double fraction) {
        if (target == null) {
            setDeltaMovement(getDeltaMovement().scale(0.92));
            return;
        }
        float scale = Math.max(1f, getModelScale());
        double radius = 16 * Math.max(1, scale * 0.8);
        double speed = 0.62 * Math.max(1, scale * 0.65) * fraction;
        steer(clampToArena(orbitPoint(target.position(), radius, 9 * Math.max(1, scale * 0.7), speed / radius * 0.9)), speed, 2.5f);
        lookTowards(target.getEyePosition());
    }

    protected Vec3 forward() {
        return Vec3.directionFromRotation(0, getYRot());
    }

    protected Vec3 leftDir() {
        double yaw = Math.toRadians(yBodyRot);
        return new Vec3(Math.cos(yaw), 0, Math.sin(yaw));
    }

    protected Vec3 clampToArena(Vec3 point) {
        if (home == null || !isBoss() || isChasingAttacker()) {
            return point;
        }
        Vec3 center = Vec3.atBottomCenterOf(home);
        Vec3 flat = new Vec3(point.x - center.x, 0, point.z - center.z);
        if (flat.length() > ARENA_RADIUS) {
            flat = flat.normalize().scale(ARENA_RADIUS);
        }
        double ground = floorBelow(center.x + flat.x, Math.max(point.y, getY()) + 2, center.z + flat.z);
        return new Vec3(center.x + flat.x, Math.max(point.y, ground + 3), center.z + flat.z);
    }

    protected double groundBelow() {
        Vec3 from = position().add(0, 1, 0);
        BlockHitResult hit = level().clip(new ClipContext(from, from.add(0, -40, 0), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        return hit.getType() == HitResult.Type.MISS ? getY() - 40 : hit.getLocation().y;
    }

    /** Ground near the dragon's own level at (x, z): a ray from 16 blocks above it down to 24 below (not the heightmap,
     * which would put things on tree tops or on a cave's ceiling). */
    protected double groundNear(double x, double z) {
        Vec3 from = new Vec3(x, getY() + 16, z);
        BlockHitResult hit = level().clip(new ClipContext(from, new Vec3(x, getY() - 24, z), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        return hit.getType() == HitResult.Type.MISS ? getY() : hit.getLocation().y;
    }

    /** First surface below a point (or below the dragon's height, whichever is higher): lightning lands on the floor
     * the fight is on, not on a roof above it. */
    protected double surfaceUnder(Vec3 at) {
        double top = Math.max(at.y, getY()) + 10;
        BlockHitResult hit = level().clip(new ClipContext(new Vec3(at.x, top, at.z), new Vec3(at.x, top - 60, at.z), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        return hit.getType() == HitResult.Type.MISS ? groundY(at.x, at.z) : hit.getLocation().y;
    }

    /** First solid floor below (x, fromY, z), 64 blocks down at most: roofs, tree tops above the fight and the ceiling
     * of a covered arena are never taken for the ground (the heightmap would). */
    protected double floorBelow(double x, double fromY, double z) {
        BlockHitResult hit = level().clip(new ClipContext(new Vec3(x, fromY, z), new Vec3(x, fromY - 64, z), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        return hit.getType() == HitResult.Type.MISS ? Math.min(groundY(x, z), fromY) : hit.getLocation().y;
    }

    protected double groundY(double x, double z) {
        return level().getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, Mth.floor(x), Mth.floor(z));
    }

    protected float reachScale() {
        return getModelScale();
    }

    /* ---------------------------------------------------------------- damage helpers */

    protected float dmg(float base) {
        return base * damageScale() * (isPhaseTwo() && isBoss() ? 1.25f : 1f);
    }

    /** Hits every valid target within radius of a point once per attack; returns how many were hit. */
    protected int hitSphere(Vec3 c, double radius, float damage, @Nullable DamageSource source, double push, double lift) {
        int n = 0;
        for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, new AABB(c, c).inflate(radius + 2), this::canHit)) {
            if (victim == grabbed) {
                continue;
            }
            double d = Math.sqrt(victim.getBoundingBox().distanceToSqr(c));
            if (d > radius || !hitThisAttack.add(victim.getId())) {
                continue;
            }
            victim.hurt(source != null ? source : damageSources().mobAttack(this), damage);
            if (push != 0 || lift != 0) {
                Vec3 dir = victim.position().subtract(c).multiply(1, 0, 1);
                dir = dir.lengthSqr() < 1e-4 ? forward() : dir.normalize();
                double kb = 1 - victim.getAttributeValue(Attributes.KNOCKBACK_RESISTANCE) * 0.6;
                victim.setDeltaMovement(victim.getDeltaMovement().add(dir.x * push * kb, lift * kb, dir.z * push * kb));
                victim.hurtMarked = true;
            }
            n++;
        }
        return n;
    }

    protected DamageSource lightningSource() {
        return SpellRegistry.LIGHTNING_BOLT_SPELL.get().getDamageSource(this, this);
    }

    /* ---------------------------------------------------------------- states: intro, flight, landing */

    private void tickSpawn() {
        setDeltaMovement(0, 0.03, 0);
        if (stateTicks % 20 == 10 && stateTicks < 90) {
            for (int i = 0; i < 2; i++) {
                double a = random.nextDouble() * Math.PI * 2;
                visualLightning(getX() + Math.cos(a) * 8, getZ() + Math.sin(a) * 8);
            }
            shake(10);
        }
        if (stateTicks == 12) {
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 6f, 0.85f);
            shake(40);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + 3, getZ(), 80, 3, 2, 3, 0.4, true);
        }
        if (stateTicks >= State.SPAWN.duration) {
            airAttacksLeft = 1;
            setState(State.HOVER);
            attackCooldown = 20;
        }
    }

    protected void tickHover(@Nullable LivingEntity target) {
        float scale = Math.max(1f, getModelScale());
        if (target == null) {
            Vec3 centre = home == null ? position() : Vec3.atCenterOf(home);
            steer(orbitPoint(centre, 16 * scale, 10 * scale, 0.008), 0.5 * scale, 3f);
            yHeadRot = Mth.approachDegrees(yHeadRot, yBodyRot, 6f);
            if (++idleTicks > LAND_AFTER) {
                Vec3 spot = findLandingSpot(centre, 20 * scale);
                if (spot != null) {
                    beginLanding(spot);
                } else {
                    idleTicks = LAND_AFTER / 2;
                }
            }
            return;
        }
        idleTicks = 0;
        // it is a ground fighter: a target on the ground means landing right in front of it
        if (targetOnGround(target) && (airAttacksLeft <= 0 || stateTicks > 100)) {
            Vec3 spot = landingSpotFacing(target);
            if (spot != null) {
                beginLanding(spot);
                return;
            }
        }
        // a flying target: chase it (no Ender-dragon circling), keeping a little above and behind it
        Vec3 away = position().subtract(target.position()).multiply(1, 0, 1);
        away = away.lengthSqr() < 1e-4 ? forward().scale(-1) : away.normalize();
        Vec3 point = target.position().add(away.scale(9 * Math.max(1, scale * 0.6))).add(0, 4 * Math.max(1, scale * 0.6), 0);
        double speed = (isPhaseTwo() ? 0.95 : 0.8) * Math.max(1, scale * 0.65);
        steer(clampToArena(point), speed, 5f);
        lookTowards(target.getEyePosition());
        if (--attackCooldown <= 0) {
            chooseAirAttack(target);
        }
    }

    /** A landing spot with the target in front at striking distance (between the forefeet and the jaws). */
    @Nullable
    protected Vec3 landingSpotFacing(LivingEntity target) {
        float scale = Math.max(0.5f, getModelScale());
        Vec3 toward = target.position().subtract(position()).multiply(1, 0, 1);
        Vec3 dir = toward.lengthSqr() < 1e-4 ? forward() : toward.normalize();
        return findLandingSpot(target.position().subtract(dir.scale(80 * scale / 16.0)), 4 * scale);
    }

    protected boolean targetOnGround(LivingEntity target) {
        return target.onGround() || target.getY() - floorBelow(target.getX(), target.getY() + 0.5, target.getZ()) < 3;
    }

    @Nullable
    protected Vec3 findLandingSpot(Vec3 centre, double range) {
        for (int i = 0; i < 20; i++) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = i == 0 ? 0 : random.nextDouble() * range;
            double x = centre.x + Math.cos(a) * r;
            double z = centre.z + Math.sin(a) * r;
            double y = floorBelow(x, centre.y + 8, z);
            BlockPos below = BlockPos.containing(x, y - 1, z);
            if (!level().getFluidState(below).isEmpty() || !level().getBlockState(below).isSolid()) {
                continue;
            }
            AABB box = getDimensions(Pose.STANDING).makeBoundingBox(x, y + 0.05, z);
            if (level().noCollision(this, box) && !level().containsAnyLiquid(box)) {
                return new Vec3(x, y, z);
            }
        }
        return null;
    }

    protected void beginLanding(Vec3 spot) {
        landSpot = spot;
        idleTicks = 0;
        diveStartY = getY();
        setState(State.LANDING);
        // variant 1 (synced, for the animation): a crash landing into the fight; 0: settling down
        setAttackVariant(isBoss() && getTarget() != null ? 1 : 0);
    }

    private void tickLanding(@Nullable LivingEntity target) {
        float scale = Math.max(1f, getModelScale());
        Vec3 flat = new Vec3(landSpot.x - getX(), 0, landSpot.z - getZ());
        double ground = groundBelow();
        if (target != null) {
            lookTowards(target.getEyePosition());
        }
        if (isBoss() && target != null && getAttackVariant() == 1) {
            // 1.8: into a fight it never just settles down - it dives the last stretch and crashes in
            if (flat.length() > 2.5 * scale && getY() - ground > 3 * scale) {
                steer(landSpot.add(0, 6 * scale, 0), 0.7 * scale, 6f);
                diveStartY = getY();
            } else {
                Vec3 delta = landSpot.subtract(position());
                double speed = Math.min(2.2, 0.7 + Math.max(0, diveStartY - getY()) * 0.05 + stateTicks * 0.01);
                setDeltaMovement(delta.normalize().scale(Math.min(speed, delta.length())));
                turnBody(target.position(), 6f);
                if (getY() - ground <= 0.6 || delta.length() < 0.8) {
                    setPos(getX(), ground, getZ());
                    setDeltaMovement(Vec3.ZERO);
                    double drop = diveStartY - getY();
                    crash(Mth.clamp(0.35 + drop / 30.0, 0.35, 1.0), false);
                    return;
                }
            }
            if (stateTicks > 400) {
                setState(State.HOVER);
            }
            return;
        }
        if (flat.length() > 2.5 * scale) {
            steer(landSpot.add(0, 6 * scale, 0), 0.6 * scale, 5f);
        } else {
            if (target != null) {
                turnBody(target.position(), 4f);
            }
            setDeltaMovement(getDeltaMovement().multiply(0.75, 0, 0.75).add(flat.scale(0.04)).add(0, getY() - ground > 4 ? -0.22 * scale : -0.1, 0));
            if (getY() - ground <= 0.2) {
                setPos(getX(), ground, getZ());
                setDeltaMovement(Vec3.ZERO);
                playSound(TechSounds.TECH_DRAGON_SLAM.get(), 1.5f * getModelScale(), 1.3f);
                MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), getX(), getY() + 0.3, getZ(), 14, 1.5 * scale, 0.2, 1.5 * scale, 0.03, false);
                groundDust(2 * scale);
                if (target != null) {
                    groundTicks = (isPhaseTwo() ? 220 : 300) + random.nextInt(120);
                    setState(State.GROUND);
                } else {
                    setState(State.PERCH);
                    setIdleVariant(0);
                }
            }
        }
        if (stateTicks > 400) {
            setState(State.HOVER);
        }
    }

    protected void tickTakeoff() {
        if (stateTicks < 9) {
            setDeltaMovement(getDeltaMovement().multiply(0.5, 0, 0.5));
            return;
        }
        if (stateTicks == 9) {
            playSound(SoundEvents.ENDER_DRAGON_FLAP, 4f, 0.55f);
            groundDust(3 * getModelScale());
        }
        setDeltaMovement(getDeltaMovement().multiply(0.8, 0, 0.8).add(0, 0.35 * Math.max(1, getModelScale() * 0.6), 0).add(forward().scale(0.05)));
        if (stateTicks >= State.TAKEOFF.duration) {
            if (afterTakeoff != null) {
                State next = afterTakeoff;
                afterTakeoff = null;
                setState(next);
                return;
            }
            airAttacksLeft = 2 + random.nextInt(isPhaseTwo() ? 3 : 2);
            endAttack(20);
        }
    }

    /* ---- perching, lying down, sleeping */

    protected void tickPerch(@Nullable LivingEntity target) {
        perchTicks++;
        setDeltaMovement(getDeltaMovement().multiply(0.5, 1, 0.5));
        if (target != null) {
            leavePerch(State.GROUND_ROAR);
            return;
        }
        cycleIdle();
        if (isBoss() && getHealth() < getMaxHealth() && tickCount % 20 == 0) {
            heal(6f);
        }
        if (isBoss() && perchTicks > SLEEP_AFTER && getIdleVariant() == 2) {
            setState(State.SLEEP);
        }
    }

    /** Changes the perched pose now and then: standing (looking around), sitting, or lying down (via lie_down). */
    protected void cycleIdle() {
        if (--idleVariantTicks > 0) {
            return;
        }
        int current = getIdleVariant();
        int next = random.nextInt(10) < 5 ? 2 : random.nextInt(10) < 6 ? 0 : 1;
        if (next == current) {
            idleVariantTicks = 160 + random.nextInt(140);
            return;
        }
        if (next == 2) {
            setState(State.LIE_DOWN);
            return;
        }
        if (current == 2) {
            afterRise = State.PERCH;
            setState(State.REST_UP);
            setIdleVariant(next);
            return;
        }
        setIdleVariant(next);
        idleVariantTicks = 160 + random.nextInt(140);
    }

    protected void leavePerch(State next) {
        if (getIdleVariant() == 2 && (getState() == State.PERCH || getState() == State.LIE_DOWN)) {
            afterRise = next;
            setState(State.REST_UP);
        } else {
            setState(next);
        }
    }

    private void tickLieTransition(@Nullable LivingEntity target) {
        setDeltaMovement(getDeltaMovement().multiply(0.3, 1, 0.3));
        State s = getState();
        if (s == State.LIE_DOWN && target != null && stateTicks > 4) {
            leavePerch(State.GROUND_ROAR);
            return;
        }
        if (stateTicks >= s.duration) {
            if (s == State.LIE_DOWN) {
                setState(State.PERCH);
                setIdleVariant(2);
            } else {
                State next = afterRise == null ? State.PERCH : afterRise;
                afterRise = null;
                if (getIdleVariant() == 2) {
                    setIdleVariant(0);
                }
                setState(next);
            }
        }
    }

    private void tickSleep(@Nullable LivingEntity target) {
        setDeltaMovement(getDeltaMovement().multiply(0.3, 1, 0.3));
        yHeadRot = yBodyRot;
        if (getHealth() < getMaxHealth() && tickCount % 20 == 0) {
            heal(10f);
        }
        if (tickCount % 40 == 0) {
            Vec3 nose = mouthPosition();
            MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), nose.x, nose.y, nose.z, 3, 0.2, 0.1, 0.2, 0.01, false);
        }
        if (target != null || getLastHurtByMob() != null && tickCount - getLastHurtByMobTimestamp() < 20) {
            setState(State.WAKE);
        }
    }

    private void tickWake() {
        setDeltaMovement(getDeltaMovement().multiply(0.3, 1, 0.3));
        if (stateTicks == 18) {
            playSound(TechSounds.TECH_DRAGON_AMBIENT.get(), 3f, 0.7f);
        }
        if (stateTicks >= State.WAKE.duration) {
            setIdleVariant(0);
            setState(State.GROUND_ROAR);
        }
    }

    private void tickGroundRoar(@Nullable LivingEntity target) {
        setDeltaMovement(getDeltaMovement().multiply(0.3, 1, 0.3));
        if (target != null && stateTicks < 20) {
            faceTowards(target.getEyePosition(), 6f);
        }
        if (stateTicks == 18) {
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 6f * getModelScale(), 0.85f);
            shake(30);
            roarPush(9 * getModelScale(), 2.4);
            Vector3f color = SchoolRegistry.LIGHTNING.get().getTargetingColor();
            double radius = 7 * getModelScale();
            ring(new Vec3(getX(), getY() + 0.5, getZ()), (float) radius, 0, 0);
            groundDust(4 * getModelScale());
            if (skyfallSlam) {
                for (LivingEntity v : level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(radius), this::canHit)) {
                    v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 2), this);
                    v.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 80, 1), this);
                }
                skyfallSlam = false;
            }
        }
        if (stateTicks >= State.GROUND_ROAR.duration) {
            if (target == null) {
                setState(State.PERCH);
                return;
            }
            groundTicks = Math.max(groundTicks, 200);
            setState(State.GROUND);
        }
    }

    /* ---------------------------------------------------------------- ground combat */

    /* Reach bands, in model px in front of the dragon's origin (they scale with the dragon): the jaws strike 85-140,
     * the forefeet 28-85, "under" is below the chest; dash claw / pounce close 140-240, the ram and the run beyond. */
    private static final double BITE_MIN = 85, BITE_MAX = 140, CLAW_MIN = 28, DASH_MAX = 200, POUNCE_MAX = 240;

    private float relativeAngle(Vec3 point) {
        return Math.abs(Mth.wrapDegrees((float) (Mth.atan2(point.z - getZ(), point.x - getX()) * Mth.RAD_TO_DEG) - 90f - yBodyRot));
    }

    private float comboChance() {
        return isPhaseTwo() ? 0.55f : 0.35f;
    }

    private void tickGround(@Nullable LivingEntity target) {
        if (target == null) {
            setState(State.PERCH);
            setIdleVariant(0);
            return;
        }
        float s = reachScale();
        Vec3 loc = local(target.position());
        double ahead = loc.z, side = Math.abs(loc.x);
        boolean airborne = !targetOnGround(target) && target.getY() > getY() + getBbHeight();
        unreachableTicks = airborne ? unreachableTicks + 1 : Math.max(0, unreachableTicks - 2);
        // a target that keeps flying, or one far away: after it through the air
        if (unreachableTicks > 60 || distanceTo(target) > 70 * s / 2) {
            unreachableTicks = 0;
            startTakeoff(null);
            return;
        }
        lookTowards(target.getEyePosition());
        skyTimer--;
        float rel = relativeAngle(target.position());
        boolean inBite = ahead > BITE_MIN && ahead < BITE_MAX && side < 40;
        boolean inClaw = ahead > CLAW_MIN && ahead <= BITE_MIN && side < 44;
        boolean under = ahead <= CLAW_MIN && ahead > -20 && side < 40;
        if (--attackCooldown <= 0) {
            State next = pickGroundMove(target, loc, rel, inBite, inClaw, under);
            if (next != null) {
                startGroundMove(next, target);
                return;
            }
            attackCooldown = 3;
        }
        // chase: run it down, turning hard
        turnBody(target.position(), rel > 100 ? 8f : 11f);
        double want = inBite || inClaw || under ? 0 : (ahead > POUNCE_MAX ? 0.46 : ahead > BITE_MAX + 20 ? 0.32 : 0.14) * Math.max(1, s * 0.5);
        if (isPhaseTwo()) {
            want *= 1.15;
        }
        if (rel > 70) {
            want *= 0.35;
        }
        Vec3 dir = forward().scale(want);
        setDeltaMovement(dir.x, getDeltaMovement().y, dir.z);
        if (horizontalCollision && onGround()) {
            setDeltaMovement(getDeltaMovement().add(0, 0.5, 0));
        }
    }

    @Nullable
    private State pickGroundMove(LivingEntity target, Vec3 loc, float rel, boolean inBite, boolean inClaw, boolean under) {
        float s = reachScale();
        double ahead = loc.z, side = Math.abs(loc.x);
        int roll = random.nextInt(100);
        if (pendingDodge > 0 && dodgeCooldown <= 0 && (inClaw || under || inBite)) {
            setAttackVariant(loc.x > 0 ? 1 : 0);
            return State.DODGE;
        }
        // 1.10: something standing on its back: spin round and discharge to throw it off
        if (onBackTicks > 30 && spinCooldown <= 0) {
            spinCooldown = isPhaseTwo() ? 120 : 160;
            return State.SPIN;
        }
        // 1.8: the tail only lashes out when something it would attack really is where the tail reaches (not just
        // "the target is somewhere behind"), and not every time: its own cooldown and a 65% chance
        LivingEntity atTail = tailCooldown <= 0 ? preyAtTail() : null;
        if (atTail != null && roll < 65) {
            setAttackVariant(local(atTail.position()).x > 0 ? 0 : 1);
            tailCooldown = (isPhaseTwo() ? 70 : 100) + random.nextInt(50);
            return State.TAIL_WHIP;
        }
        int near = level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(9 * s), this::isPrey).size();
        if (near >= 3) {
            if (gustCooldown <= 0 && random.nextBoolean()) {
                return State.WING_GUST;
            }
            if (atTail != null) {
                tailCooldown = (isPhaseTwo() ? 90 : 130) + random.nextInt(50);
                return State.TAIL_SWEEP;
            }
            // 1.10: surrounded but nothing at the tail - the whole-body spin discharge instead of a blind tail sweep
            if (spinCooldown <= 0 && (under || roll < 55)) {
                spinCooldown = (isPhaseTwo() ? 140 : 200) + random.nextInt(60);
                return State.SPIN;
            }
            if (roarCooldown <= 0) {
                roarCooldown = (isPhaseTwo() ? 360 : 500) + random.nextInt(120);
                return State.GROUND_ROAR;
            }
            if (under) {
                return State.STOMP;
            }
        }
        // now and then a short flight: the dive chain or the storm call (Skyfall in phase two)
        if (skyTimer <= 0 && (ahead > BITE_MIN || roll < 30)) {
            return State.TAKEOFF;
        }
        if (rel > 35) {
            if (under || inClaw) {
                // something tucked against its flank: hop aside to bring it in front
                if (dodgeCooldown <= 0 && roll < 40) {
                    setAttackVariant(loc.x > 0 ? 1 : 0);
                    return State.DODGE;
                }
            }
            // 1.10: off to the side but within a hop: jump sideways/back to line it up with the jaws
            if (hopCooldown <= 0 && rel < 110 && Math.sqrt(loc.x * loc.x + loc.z * loc.z) < DASH_MAX && roll >= 40 && roll < 75) {
                return hop(loc);
            }
            return null;
        }
        // kiting: up close it may leap back on a wing beat or blow the target away, then spit lightning at it
        if ((inClaw || inBite || under) && kiteCooldown <= 0 && roll < (isPhaseTwo() ? 22 : 15)) {
            kiteCooldown = (isPhaseTwo() ? 160 : 220) + random.nextInt(80);
            return random.nextBoolean() ? State.BACKSTEP : State.WING_PUSH;
        }
        if (under) {
            // 1.10: too close for the jaws - hop back to striking distance, or stomp; the tail only for what is at the tail
            if (hopCooldown <= 0 && roll < 35) {
                return hop(loc);
            }
            if (dodgeCooldown <= 0 && roll < 55) {
                setAttackVariant(random.nextBoolean() ? 0 : 1);
                return State.DODGE;
            }
            if (spinCooldown <= 0 && roll >= 85) {
                spinCooldown = (isPhaseTwo() ? 140 : 200) + random.nextInt(60);
                return State.SPIN;
            }
            return State.STOMP;
        }
        // 1.9: pin it under a forefoot and gnaw it
        if (inClaw && pinCooldown <= 0 && canBePinned(target) && roll < 18) {
            pinCooldown = (isPhaseTwo() ? 220 : 300) + random.nextInt(80);
            return State.PIN;
        }
        // 1.9: the hextech core beam (not while the pylon shield is up)
        if (beamCooldown <= 0 && !isShielded() && ahead > BITE_MIN && ahead < 420 && roll < (isPhaseTwo() ? 24 : 15)) {
            beamCooldown = (isPhaseTwo() ? 420 : 560) + random.nextInt(100);
            return State.CORE_CHARGE;
        }
        if (inClaw) {
            if (roll < 45) {
                setAttackVariant(loc.x > 0 ? 0 : 1);
                return State.CLAW;
            }
            if (roll < 68) {
                return State.BITE;
            }
            if (roll < 85) {
                return State.STOMP;
            }
            setAttackVariant(loc.x > 0 ? 1 : 0);
            return dodgeCooldown <= 0 ? State.DODGE : State.BITE;
        }
        if (inBite) {
            boolean small = canGnaw(target);
            if (small && grabCooldown <= 0 && roll < 35) {
                return State.GRAB;
            }
            if (roll < 62) {
                return State.BITE;
            }
            return State.BITE_SWEEP;
        }
        if (ahead <= DASH_MAX) {
            if (kiteCooldown <= 0 && roll >= 90) {
                // side to side hops (Zinogre style), then the spit
                kiteCooldown = (isPhaseTwo() ? 160 : 220) + random.nextInt(80);
                kiteHopsLeft = isPhaseTwo() ? 3 : 2;
                setAttackVariant(random.nextBoolean() ? 0 : 1);
                return State.KITE_HOP;
            }
            if (roll < 42) {
                setAttackVariant(loc.x > 0 ? 0 : 1);
                return State.DASH_CLAW;
            }
            if (roll < 72) {
                return State.POUNCE;
            }
            // 1.10: just out of reach - a hop forward to striking distance, then straight into an attack
            if (hopCooldown <= 0 && roll < 84) {
                return hop(loc);
            }
            if (breathCooldown <= 0) {
                return State.GBREATH_CHARGE;
            }
            return null;
        }
        if (ahead <= POUNCE_MAX) {
            if (spitCooldown <= 0 && roll < 22) {
                return State.SPIT;
            }
            if (roll < 50) {
                return State.POUNCE;
            }
            if (roll < 75) {
                return State.RAM;
            }
            if (fieldCooldown <= 0) {
                return State.FIELD_ROAR;
            }
            return null;
        }
        if (spitCooldown <= 0 && roll < 35) {
            return State.SPIT;
        }
        if (roll < 55) {
            return isPhaseTwo() && random.nextInt(3) == 0 ? State.REND : State.RAM;
        }
        if (breathCooldown <= 0 && roll < 65 && ahead < 300) {
            return State.GBREATH_CHARGE;
        }
        return null;
    }

    private void startGroundMove(State next, LivingEntity target) {
        if (next == State.TAKEOFF) {
            startSkySkill();
            return;
        }
        lastAttack = next;
        if (next == State.DODGE) {
            dodgeCooldown = isPhaseTwo() ? 80 : 120;
            pendingDodge = 0;
        }
        setState(next);
        if (next == State.GBREATH_CHARGE) {
            playSound(TechSounds.TECH_DRAGON_CHARGE.get(), 3f, 1f);
        }
    }

    /** Short flights: the dive chain, the storm call, or Skyfall (phase two). */
    private void startSkySkill() {
        int roll = random.nextInt(100);
        State skill = isPhaseTwo() && roll < 18 ? State.SKY_RISE : roll < 40 ? State.DIVE_RISE : roll < 62 ? State.SKY_BREATH
                : roll < 80 ? State.STRAFE : State.STORM_RISE;
        if (skill == State.DIVE_RISE) {
            diveChainLeft = isPhaseTwo() ? 4 : 3;
        }
        skyTimer = (isPhaseTwo() ? 300 : 420) + random.nextInt(160);
        startTakeoff(skill);
    }

    protected void startTakeoff(@Nullable State after) {
        afterTakeoff = after;
        setState(State.TAKEOFF);
        playSound(SoundEvents.ENDER_DRAGON_FLAP, 4f, 0.6f);
    }

    protected void afterGroundAttack(int cooldown) {
        attackCooldown = isPhaseTwo() ? cooldown * 2 / 3 : cooldown;
        setState(State.GROUND);
    }

    /** Chains straight into a follow-up when the target is still where one lands; true if it did. */
    private boolean combo(@Nullable LivingEntity target, boolean allowBite, boolean allowClaw, boolean allowDash) {
        if (target == null || !target.isAlive() || random.nextFloat() >= comboChance()) {
            return false;
        }
        Vec3 loc = local(target.position());
        double ahead = loc.z, side = Math.abs(loc.x);
        if (allowClaw && ahead > CLAW_MIN && ahead <= BITE_MIN && side < 44) {
            setAttackVariant(loc.x > 0 ? 0 : 1);
            setState(State.CLAW);
            return true;
        }
        if (allowBite && ahead > BITE_MIN - 10 && ahead < BITE_MAX && side < 40) {
            setState(State.BITE);
            return true;
        }
        if (allowDash && ahead >= BITE_MAX && ahead <= DASH_MAX && side < 60) {
            setAttackVariant(loc.x > 0 ? 0 : 1);
            setState(State.DASH_CLAW);
            return true;
        }
        return false;
    }

    private void holdStill() {
        setDeltaMovement(getDeltaMovement().multiply(0.3, 1, 0.3));
    }

    /** Bite (hit 0.45 s) and sweeping bite (hit 0.55 s, wide arc): tested at the jaws of the frame. */
    private void tickBite(@Nullable LivingEntity target) {
        boolean sweep = getState() == State.BITE_SWEEP;
        int hit = sweep ? 11 : 9;
        holdStill();
        if (target != null && stateTicks < hit - 3) {
            faceTowards(target.getEyePosition(), 10f);
        }
        if (stateTicks == hit - 1) {
            playSound(SoundEvents.EVOKER_FANGS_ATTACK, 3f, 0.5f);
        }
        if (stateTicks >= hit - 1 && stateTicks <= hit + (sweep ? 3 : 1)) {
            Vec3 jaws = mouthPosition();
            float r = 1.7f * getModelScale();
            int n = hitSphere(jaws, r, dmg(sweep ? 18f : 22f), null, sweep ? 1.4 : 0.6, 0.3);
            if (n > 0 || stateTicks == hit) {
                MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, jaws.x, jaws.y, jaws.z, 10, 0.6, 0.4, 0.6, 0.3, false);
            }
        }
        if (stateTicks >= getState().duration) {
            if (combo(target, false, true, true)) {
                return;
            }
            afterGroundAttack(sweep ? 26 : 18);
        }
    }

    /** Claw rake (left / right forefoot), hit 0.52 s, along the path of the paw. */
    private void tickClaw(@Nullable LivingEntity target) {
        holdStill();
        boolean left = getAttackVariant() == 0;
        if (target != null && stateTicks < 7) {
            faceTowards(target.position(), 10f);
        }
        if (stateTicks == 8) {
            playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 3f, 0.5f);
        }
        if (stateTicks >= 9 && stateTicks <= 12) {
            Vec3 paw = track(left ? DragonTracks.HAND_L : DragonTracks.HAND_R);
            hitSphere(paw, 1.6f * getModelScale(), dmg(18f), null, 1.2, 0.4);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, paw.x, paw.y + 0.5, paw.z, 6, 0.6, 0.3, 0.6, 0.25, false);
        }
        if (stateTicks >= State.CLAW.duration) {
            if (combo(target, true, false, true)) {
                return;
            }
            afterGroundAttack(20);
        }
    }

    /* ---- jaw grab */

    /** 1.10: what fits in its jaws - up to Warden size for the boss (about a player for the drake); never bosses,
     * multipart giants, other dragons or something already riding. */
    public boolean canGnaw(LivingEntity e) {
        float f = Math.max(0.85f, getModelScale() / BOSS_SCALE);
        return e.getBbHeight() <= 3.2f * f && e.getBbWidth() <= 1.45f * f && !e.isPassenger() && !e.isVehicle() && !(e instanceof TechDragon)
                && !e.isMultipartEntity() && !e.getType().is(Tags.EntityTypes.BOSSES) && !(e instanceof Player p && (p.isCreative() || p.isSpectator()));
    }

    private void tickGrab(@Nullable LivingEntity target) {
        holdStill();
        if (target != null && stateTicks < 6) {
            faceTowards(target.getEyePosition(), 12f);
        }
        if (stateTicks >= 9 && stateTicks <= 11 && grabbed == null) {
            Vec3 jaws = mouthPosition();
            double r = 1.8 * getModelScale();
            LivingEntity prey = level().getEntitiesOfClass(LivingEntity.class, new AABB(jaws, jaws).inflate(r), e -> canHit(e) && canGnaw(e))
                    .stream().min(Comparator.comparingDouble(e -> e.distanceToSqr(jaws))).orElse(null);
            if (prey != null && prey.startRiding(this, true)) {
                grabbed = prey;
                this.entityData.set(DATA_GRABBED, prey.getId());
                prey.hurt(damageSources().mobAttack(this), dmg(8f));
                playSound(SoundEvents.PLAYER_ATTACK_CRIT, 3f, 0.5f);
                setState(State.GRAB_HOLD);
                return;
            }
        }
        if (stateTicks >= State.GRAB.duration) {
            grabCooldown = 100;
            afterGroundAttack(20);
        }
    }

    private void tickGrabHold() {
        holdStill();
        if (grabbed == null || !grabbed.isAlive() || grabbed.getVehicle() != this) {
            grabbed = null;
            this.entityData.set(DATA_GRABBED, -1);
            afterGroundAttack(20);
            return;
        }
        int phase = stateTicks % 16;
        if (phase == 4 || phase == 12) {
            grabbed.invulnerableTime = 0;
            grabbed.hurt(damageSources().mobAttack(this), dmg(6f));
            Vec3 jaws = mouthPosition();
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, jaws.x, jaws.y, jaws.z, 8, 0.4, 0.4, 0.4, 0.25, false);
            playSound(SoundEvents.PLAYER_HURT_SWEET_BERRY_BUSH, 2f, 0.5f);
        }
        if (stateTicks >= State.GRAB_HOLD.duration) {
            // 1.9: like an Ice and Fire dragon, it may fly off with the prey and drop it from high up
            if (isBoss() && random.nextInt(100) < (isPhaseTwo() ? 60 : 45)) {
                carryTop = getY() + 18 * Math.max(1, getModelScale() * 0.75);
                setState(State.CARRY);
                playSound(SoundEvents.ENDER_DRAGON_FLAP, 5f, 0.6f);
                return;
            }
            setState(State.GRAB_TOSS);
        }
    }

    private void tickGrabToss() {
        holdStill();
        if (stateTicks == 8 && grabbed != null) {
            Vec3 fling = leftDir().scale(-1.6).add(0, 0.9, 0).add(forward().scale(0.4));
            LivingEntity victim = grabbed;
            releaseGrabbed(fling);
            victim.hurt(damageSources().mobAttack(this), dmg(4f));
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 3f, 1.3f);
        }
        if (stateTicks >= State.GRAB_TOSS.duration) {
            grabCooldown = 200;
            afterGroundAttack(24);
        }
    }

    protected void releaseGrabbed(Vec3 velocity) {
        if (grabbed != null) {
            LivingEntity victim = grabbed;
            grabbed = null;
            this.entityData.set(DATA_GRABBED, -1);
            if (victim.getVehicle() == this) {
                victim.stopRiding();
            }
            if (velocity.lengthSqr() > 0) {
                victim.setDeltaMovement(velocity);
                victim.hurtMarked = true;
            }
        }
    }

    /** True while the jaws hold this entity (mount events stop it from sneaking out). */
    public boolean isCarrying(Entity entity) {
        return entity != null && (entity == grabbed || entity.getId() == this.entityData.get(DATA_GRABBED));
    }

    @Override
    protected void positionRider(@NotNull Entity passenger, @NotNull MoveFunction callback) {
        if ((passenger == grabbed || passenger.getId() == this.entityData.get(DATA_GRABBED)) && getState() == State.PIN) {
            // 1.10: pinned by the forefoot, then held in the jaws while they gnaw - on the ground in front of the chest,
            // never pushed up into it (a Warden used to end up inside the body)
            Vec3 paw = track(DragonTracks.HAND_L);
            Vec3 jaws = mouthPosition();
            double w = Mth.clamp((stateTicks - 10) / 6.0, 0, 1) * (stateTicks >= 54 ? 0 : 1);
            Vec3 at = paw.lerp(jaws, w);
            double y = Math.max(getY(), Mth.lerp(w, paw.y - 0.4, jaws.y - passenger.getBbHeight() * 0.5));
            callback.accept(passenger, at.x, y, at.z);
            return;
        }
        if (passenger == grabbed || passenger.getId() == this.entityData.get(DATA_GRABBED)) {
            Vec3 jaws = mouthPosition();
            double y = jaws.y - passenger.getBbHeight() * 0.55;
            if (getState().grounded()) {
                y = Math.max(getY(), y);
            }
            callback.accept(passenger, jaws.x, y, jaws.z);
            return;
        }
        // a fixed seat on the back, turned with the body and the flight pitch only: it does not bob or jump with the
        // animation, so the rider (and the camera) ride smoothly
        float pitch = getState().grounded() && !isFlyingMount() ? 0 : flightPitch;
        Vec3 seat = DragonTracks.toWorld(SEAT, position(), yBodyRot, pitch, getModelScale());
        callback.accept(passenger, seat.x, seat.y + passenger.getMyRidingOffset(), seat.z);
    }

    /** Overridden by the drake: the owner riding on its back (as opposed to prey held in the jaws). */
    protected boolean isVehicleRider(Entity passenger) {
        return false;
    }

    @Override
    protected boolean canAddPassenger(@NotNull Entity passenger) {
        return passenger == grabbed || getState() == State.GRAB || getState() == State.AIR_BITE;
    }

    @Override
    public boolean shouldRiderSit() {
        return !isBoss();
    }

    /* ---- tail */

    private void tickTailWhip() {
        holdStill();
        if (stateTicks == 9) {
            playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 4f, 0.4f);
        }
        if (stateTicks >= 10 && stateTicks <= 15) {
            float r = 1.8f * getModelScale();
            Vec3 tip = track(DragonTracks.TAIL_TIP);
            Vec3 mid = track(DragonTracks.TAIL3);
            hitSphere(tip, r, dmg(16f), null, 2.2, 0.6);
            hitSphere(mid, r, dmg(16f), null, 2.2, 0.6);
            MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), tip.x, tip.y, tip.z, 8, 1, 0.4, 1, 0.3, false);
        }
        if (stateTicks >= State.TAIL_WHIP.duration) {
            afterGroundAttack(16);
        }
    }

    private void tickTailSweep() {
        holdStill();
        if (stateTicks == 8 || stateTicks == 18) {
            playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 4f, 0.45f);
            hitThisAttack.clear();
        }
        if (stateTicks >= 9 && stateTicks <= 22) {
            float r = 2.0f * getModelScale();
            for (int p : new int[]{DragonTracks.TAIL_TIP, DragonTracks.TAIL3, DragonTracks.TAIL2}) {
                hitSphere(track(p), r, dmg(14f), null, 1.8, 0.45);
            }
            Vec3 tip = track(DragonTracks.TAIL_TIP);
            MagicManager.spawnParticles(level(), TechParticles.BRASS_SPARK.get(), tip.x, tip.y, tip.z, 4, 1, 0.3, 1, 0.3, false);
        }
        if (stateTicks >= State.TAIL_SWEEP.duration) {
            afterGroundAttack(24);
        }
    }

    /* ---- stomp, gust, field, rend */

    private void tickStomp() {
        holdStill();
        if (stateTicks == 11) {
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 4f, 1.15f);
        }
        if (stateTicks == 20) {
            float scale = getModelScale();
            double radius = 4.5 * scale;
            Vec3 front = track(DragonTracks.HAND_L).add(track(DragonTracks.HAND_R)).scale(0.5);
            shake(20);
            playSound(TechSounds.TECH_DRAGON_SLAM.get(), 4f, 1.0f);
            Vector3f color = SchoolRegistry.LIGHTNING.get().getTargetingColor();
            ring(new Vec3(front.x, getY() + 0.2, front.z), (float) radius, 0, 0);
            ring(new Vec3(front.x, getY() + 0.3, front.z), (float) radius * 1.3f, 12, 0);
            groundDust(radius * 0.6);
            for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, new AABB(front, front).inflate(radius, 3, radius), this::canHit)) {
                double d = victim.position().distanceTo(new Vec3(front.x, victim.getY(), front.z));
                if (d > radius || !victim.onGround() && victim.getY() > getY() + 2) {
                    continue;
                }
                float fall = (float) Mth.clamp(1.25 - d / radius, 0.4, 1.0);
                DamageSources.applyDamage(victim, dmg(16f) * fall, SpellRegistry.SHOCKWAVE_SPELL.get().getDamageSource(this, this));
                victim.setDeltaMovement(victim.getDeltaMovement().add(0, 0.8, 0));
                victim.hurtMarked = true;
                victim.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 2), this);
            }
        }
        if (stateTicks >= State.STOMP.duration) {
            afterGroundAttack(24);
        }
    }

    private void tickWingGust(@Nullable LivingEntity target) {
        holdStill();
        if (target != null && stateTicks < 18) {
            faceTowards(target.getEyePosition(), 6f);
        }
        if (stateTicks == 7) {
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 5f * getModelScale(), 0.75f);
            shake(15);
        }
        if (stateTicks == 21) {
            double radius = 12 * Math.max(1, getModelScale() * 0.8);
            playSound(SoundEvents.ENDER_DRAGON_FLAP, 6f, 0.4f);
            playSound(SoundEvents.GENERIC_EXPLODE, 2f, 1.6f);
            shake(20);
            Vec3 c = position().add(0, getBbHeight() * 0.5, 0);
            for (Entity e : level().getEntities(this, getBoundingBox().inflate(radius), e -> e != this && !(e instanceof TechDragonPart))) {
                if (e.distanceToSqr(c) > radius * radius) {
                    continue;
                }
                Vec3 push = e.position().subtract(position()).normalize();
                double falloff = 1.3 - e.distanceTo(this) / radius;
                if (e instanceof Projectile projectile) {
                    projectile.setDeltaMovement(push.scale(1.5));
                    projectile.hurtMarked = true;
                } else if (e instanceof LivingEntity victim && canHit(victim)) {
                    victim.hurt(damageSources().mobAttack(this), dmg(6f));
                    victim.setDeltaMovement(victim.getDeltaMovement().add(push.x * 2.6 * falloff, 0.6 + 0.4 * falloff, push.z * 2.6 * falloff));
                    victim.hurtMarked = true;
                }
            }
            MagicManager.spawnParticles(level(), ParticleTypes.CLOUD, c.x, c.y, c.z, 70, radius * 0.4, 1.5, radius * 0.4, 0.4, true);
            MagicManager.spawnParticles(level(), ParticleTypes.SWEEP_ATTACK, c.x, c.y, c.z, 14, radius * 0.4, 1, radius * 0.4, 0, true);
            groundDust(radius * 0.5);
        }
        if (stateTicks >= State.WING_GUST.duration) {
            gustCooldown = 200;
            afterGroundAttack(30);
        }
    }

    private void tickFieldRoar(@Nullable LivingEntity target) {
        holdStill();
        if (target != null && stateTicks < 12) {
            faceTowards(target.getEyePosition(), 5f);
        }
        if (stateTicks == 6) {
            playSound(TechSounds.TECH_DRAGON_CHARGE.get(), 4f, 0.7f);
        }
        if (stateTicks == 14) {
            float scale = Math.max(1, getModelScale() * 0.8f);
            MagneticField field = new MagneticField(level(), this, 10 * scale, isPhaseTwo() ? 200 : 160, isPhaseTwo());
            field.moveTo(getX(), groundBelow(), getZ());
            level().addFreshEntity(field);
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 5f, 0.6f);
            playSound(SoundEvents.BEACON_ACTIVATE, 4f, 0.6f);
            shake(12);
            fieldCooldown = 600;
        }
        if (stateTicks >= State.FIELD_ROAR.duration) {
            afterGroundAttack(24);
        }
    }

    private void tickRend(@Nullable LivingEntity target) {
        if (stateTicks < 10) {
            holdStill();
            if (target != null) {
                rendDirection = target.position().subtract(position()).multiply(1, 0, 1).normalize();
                turnBody(target.position(), 10f);
            }
            if (stateTicks == 4) {
                playSound(TechSounds.TECH_DRAGON_ROAR.get(), 4f, 1.25f);
            }
            return;
        }
        if (stateTicks < 40) {
            double speed = (stateTicks < 34 ? 0.5 : 0.5 * (40 - stateTicks) / 6.0) * Math.max(1, getModelScale() * 0.7);
            setDeltaMovement(rendDirection.x * speed, getDeltaMovement().y, rendDirection.z * speed);
            turnBody(position().add(rendDirection.scale(5)), 3f);
            if (stateTicks % 4 == 0) {
                Vec3 behind = position().subtract(rendDirection.scale(3));
                visualLightning(behind.x, behind.z);
                groundDust(2.5);
            }
            Vec3 jaws = mouthPosition();
            Vec3 chest = track(DragonTracks.CHEST);
            hitSphere(jaws, 1.8 * getModelScale(), dmg(14f), lightningSource(), 1.2, 0.5);
            hitSphere(chest, 1.6 * getModelScale(), dmg(14f), lightningSource(), 1.4, 0.5);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + 0.3, getZ(), 6, 1.5, 0.2, 1.5, 0.2, false);
            return;
        }
        holdStill();
        if (stateTicks >= State.REND.duration) {
            afterGroundAttack(26);
        }
    }

    /* ---- lightning breath (ground and air) */

    private void tickBreathCharge(@Nullable LivingEntity target) {
        boolean ground = getState() == State.GBREATH_CHARGE;
        setDeltaMovement(ground ? getDeltaMovement().multiply(0.3, 1, 0.3) : getDeltaMovement().scale(0.8));
        if (target != null) {
            faceTowards(target.getEyePosition(), 8f);
            breathAim = target.getBoundingBox().getCenter().subtract(mouthPosition()).normalize();
        }
        Vec3 mouth = mouthPosition();
        MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, mouth.x, mouth.y, mouth.z, 4, 0.4, 0.4, 0.4, 0.05, false);
        if (stateTicks % 5 == 0) {
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRICITY, mouth.x, mouth.y, mouth.z, 6, 0.6, 0.6, 0.6, 0.1, false);
        }
        if (stateTicks >= State.BREATH_CHARGE.duration) {
            setState(ground ? State.GBREATH : State.BREATH);
            playSound(TechSounds.TECH_DRAGON_BREATH.get(), 4f * getModelScale(), 0.9f);
        }
    }

    protected void tickBreath(@Nullable LivingEntity target) {
        boolean ground = getState() == State.GBREATH;
        setDeltaMovement(ground ? getDeltaMovement().multiply(0.3, 1, 0.3) : getDeltaMovement().scale(0.8));
        Vec3 mouth = mouthPosition();
        if (target != null) {
            Vec3 wanted = target.getBoundingBox().getCenter().subtract(mouth).normalize();
            breathAim = breathAim.lerp(wanted, isPhaseTwo() ? 0.07 : 0.045).normalize();
            Vec3 lookPoint = mouth.add(breathAim.scale(10));
            turnBody(lookPoint, 4f);
            lookTowards(lookPoint);
        }
        breathBeam(mouth, breathAim, isBoss() ? 30 : 18, dmg(7f));
        if (stateTicks >= State.BREATH.duration) {
            breathCooldown = 160;
            if (ground) {
                afterGroundAttack(30);
            } else {
                endAttack(60);
            }
        }
    }

    protected void breathBeam(Vec3 mouth, Vec3 aim, double range, float damage) {
        Vec3 end = mouth.add(aim.scale(range));
        BlockHitResult blockHit = level().clip(new ClipContext(mouth, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        if (blockHit.getType() != HitResult.Type.MISS) {
            end = blockHit.getLocation();
        }
        if (stateTicks % 2 == 0) {
            Vec3 mid = mouth.lerp(end, 0.5).add((random.nextDouble() - 0.5) * 1.2, (random.nextDouble() - 0.5) * 1.2, (random.nextDouble() - 0.5) * 1.2);
            ((ServerLevel) level()).sendParticles(new ZapParticleOption(mid), mouth.x, mouth.y, mouth.z, 1, 0, 0, 0, 0);
            ((ServerLevel) level()).sendParticles(new ZapParticleOption(end), mid.x, mid.y, mid.z, 1, 0, 0, 0, 0);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, end.x, end.y, end.z, 6, 0.4, 0.4, 0.4, 0.25, false);
        }
        if (stateTicks % 3 == 0) {
            int steps = (int) (mouth.distanceTo(end) / 2);
            for (int i = 1; i <= steps; i++) {
                Vec3 p = mouth.lerp(end, i / (double) steps);
                MagicManager.spawnParticles(level(), ParticleHelper.ELECTRICITY, p.x, p.y, p.z, 1, 0.25, 0.25, 0.25, 0.02, false);
            }
        }
        if (isBoss() && blockHit.getType() != HitResult.Type.MISS && stateTicks % 3 == 0) {
            breakBlocks(new AABB(end, end).inflate(1.2), WEAK, 10);
        }
        if (stateTicks % 4 == 0) {
            AABB box = new AABB(mouth, end).inflate(1.5);
            for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, box, this::canHit)) {
                Vec3 c = victim.getBoundingBox().getCenter();
                if (distanceToSegment(c, mouth, end) <= victim.getBbWidth() * 0.5 + (isPhaseTwo() ? 1.4 : 1.0)) {
                    DamageSources.applyDamage(victim, damage, lightningSource());
                    victim.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 1), this);
                }
            }
            if (isBoss() && blockHit.getType() != HitResult.Type.MISS && random.nextInt(4) == 0) {
                visualLightning(end.x, end.z);
            }
        }
    }

    protected static double distanceToSegment(Vec3 p, Vec3 a, Vec3 b) {
        Vec3 ab = b.subtract(a);
        double t = Mth.clamp(p.subtract(a).dot(ab) / Math.max(1e-6, ab.lengthSqr()), 0, 1);
        return p.distanceTo(a.add(ab.scale(t)));
    }

    /* ---------------------------------------------------------------- air combat */

    protected void chooseAirAttack(LivingEntity target) {
        double distance = distanceTo(target);
        float s = Math.max(1, getModelScale() * 0.8f);
        State next;
        int roll = random.nextInt(100);
        if (isPhaseTwo() && roll < 14) {
            next = State.SKY_RISE;
        } else if (isPhaseTwo() && roll < 28) {
            next = random.nextBoolean() ? State.EMP : State.ARC_BARRAGE;
        } else if (roll < 38) {
            next = State.COG_SPIT;
        } else if (roll < 50) {
            next = State.BREATH_CHARGE;
        } else if (roll < 61) {
            next = State.SKY_BREATH;
        } else if (roll < 69) {
            next = State.STRAFE;
        } else if (roll < 77) {
            next = State.THUNDER;
        } else if (roll < 86) {
            next = State.DIVE_RISE;
        } else if (roll < 92) {
            next = State.SWOOP;
        } else if (roll < 97) {
            next = State.ROAR;
        } else {
            next = State.SUMMON;
        }
        if (next == State.SWOOP && distance > 36) {
            next = State.COG_SPIT;
        }
        if (next == lastAttack && next != State.COG_SPIT) {
            next = State.COG_SPIT;
        }
        if (next == State.SUMMON && countDrones() >= 4) {
            next = State.THUNDER;
        }
        if (next == State.BREATH_CHARGE && distance > 30 * s) {
            next = State.THUNDER;
        }
        if ((next == State.DIVE_RISE || next == State.SKY_RISE || next == State.STRAFE) && !targetOnGround(target)) {
            next = State.SWOOP;
        }
        lastAttack = next;
        airAttacksLeft--;
        setState(next);
        if (next == State.BREATH_CHARGE) {
            breathAim = target.getBoundingBox().getCenter().subtract(mouthPosition()).normalize();
            playSound(TechSounds.TECH_DRAGON_CHARGE.get(), 3f, 1f);
        }
    }

    protected void endAttack(int cooldown) {
        idleTicks = 0;
        setState(State.HOVER);
        attackCooldown = isPhaseTwo() ? cooldown * 2 / 3 : cooldown;
    }

    private void tickCogSpit(@Nullable LivingEntity target) {
        airDrift(target, 0.55);
        if (target != null) {
            if (stateTicks == 2 || stateTicks == 8 || stateTicks == 14) {
                int count = isBoss() ? (isPhaseTwo() ? 7 : 5) : 3;
                Vec3 mouth = mouthPosition();
                Vec3 aim = target.getBoundingBox().getCenter().add(target.getDeltaMovement().scale(6)).subtract(mouth).normalize();
                for (int i = 0; i < count; i++) {
                    GearProjectile gear = new GearProjectile(level(), this);
                    gear.setScale(1.6f * getModelScale() + 0.4f);
                    gear.setPos(mouth.x, mouth.y - gear.getBbHeight() * 0.5, mouth.z);
                    gear.shoot(aim.yRot((i - (count - 1) / 2f) * 9f * Mth.DEG_TO_RAD));
                    gear.setDamage(dmg(10f));
                    gear.setBlockBounces(1);
                    level().addFreshEntity(gear);
                }
                playSound(TechSounds.TECH_DRAGON_SPIT.get(), 3f * getModelScale(), 0.8f + random.nextFloat() * 0.2f);
                MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), mouth.x, mouth.y, mouth.z, 10, 0.3, 0.3, 0.3, 0.05, false);
            }
        }
        if (stateTicks >= State.COG_SPIT.duration) {
            endAttack(45);
        }
    }

    private void tickThunder(@Nullable LivingEntity target) {
        if (target != null) {
            flyTowards(clampToArena(target.position().add(forward().scale(-12)).add(0, 12, 0)), 0.4);
            faceTowards(target.getEyePosition(), 6f);
        } else {
            setDeltaMovement(getDeltaMovement().scale(0.85));
        }
        if (stateTicks == 10) {
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 4f * getModelScale(), 1.1f);
            shake(12);
        }
        int strikes = isBoss() ? (isPhaseTwo() ? 18 : 12) : 5;
        int interval = Math.max(2, 48 / strikes);
        if (target != null && stateTicks >= 16 && stateTicks < 16 + strikes * interval && (stateTicks - 16) % interval == 0) {
            int index = (stateTicks - 16) / interval;
            Vec3 at;
            if (index % 3 == 0) {
                at = target.position().add(target.getDeltaMovement().scale(18));
            } else {
                double a = random.nextDouble() * Math.PI * 2;
                double r = 2 + random.nextDouble() * 9;
                at = target.position().add(Math.cos(a) * r, 0, Math.sin(a) * r);
            }
            strike(at, dmg(10f));
        }
        if (stateTicks >= State.THUNDER.duration) {
            endAttack(55);
        }
    }

    protected void strike(Vec3 at, float damage) {
        strike(at, damage, surfaceUnder(at));
    }

    /** A lightning bolt from the sky (storm, thunder, roar): 1.10 - these never break blocks, only the lightning from
     * its jaws (breath, spit) does. */
    protected void strike(Vec3 at, float damage, double y) {
        LightningStrike strike = new LightningStrike(level());
        strike.setOwner(this);
        strike.setDamage(damage);
        strike.setPos(at.x, y, at.z);
        level().addFreshEntity(strike);
    }

    /** Floor under a point near the target's height (the storm hangs high above it: a ray from the dragon would stop
     * on tree tops and roofs). */
    protected double floorNear(Vec3 at, double y) {
        BlockHitResult hit = level().clip(new ClipContext(new Vec3(at.x, y + 6, at.z), new Vec3(at.x, y - 30, at.z), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        return hit.getType() == HitResult.Type.MISS ? groundY(at.x, at.z) : hit.getLocation().y;
    }

    private void stormStrike(LivingEntity target) {
        double a = random.nextDouble() * Math.PI * 2;
        Vec3 at = target.position().add(target.getDeltaMovement().scale(12)).add(Math.cos(a) * random.nextDouble() * 3, 0, Math.sin(a) * random.nextDouble() * 3);
        strike(at, 8f);
    }

    /** Thunder Roar: lightning ring around the dragon and a shock wave (air, or the rider's R key). */
    protected void tickRoar(@Nullable LivingEntity target) {
        setDeltaMovement(getDeltaMovement().scale(0.85));
        if (target != null && isBoss()) {
            faceTowards(target.getEyePosition(), 8f);
        }
        if (stateTicks == 8) {
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 6f * getModelScale(), 0.8f);
            shake(24);
        }
        if (stateTicks == 14) {
            thunderRoarBlast();
        }
        if (stateTicks >= State.ROAR.duration) {
            if (isBoss()) {
                endAttack(40);
            } else {
                onRiderActionEnd();
            }
        }
    }

    protected void thunderRoarBlast() {
        ring(position().add(0, 0.3, 0), (float) (8 * getModelScale() + 2), 14, 0);
        ring(position().add(0, 0.3, 0), (float) (5 * getModelScale() + 2), 10, 1);
        int bolts = isPhaseTwo() ? 10 : 7;
        double ring = 6 * getModelScale() + 2;
        for (int i = 0; i < bolts; i++) {
            double a = i * Math.PI * 2 / bolts + random.nextDouble() * 0.3;
            strike(new Vec3(getX() + Math.cos(a) * ring, 0, getZ() + Math.sin(a) * ring), dmg(8f));
        }
        double radius = 8 * getModelScale() + 2;
        Vector3f color = SchoolRegistry.LIGHTNING.get().getTargetingColor();
        ring(new Vec3(getX(), getY() + 1, getZ()), (float) radius, 0, 0);
        roarPush(radius * 1.15, 2.0);
        for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(radius), this::canHit)) {
            if (victim.distanceToSqr(this) > radius * radius * 1.4) {
                continue;
            }
            victim.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 50, 2), this);
            victim.addEffect(new MobEffectInstance(MobEffects.DIG_SLOWDOWN, 80, 1), this);
        }
    }

    /** Overridden by the drake: return to free riding after a rider-triggered action. */
    protected void onRiderActionEnd() {
        endAttack(30);
    }

    private void tickSwoop(@Nullable LivingEntity target) {
        float scale = Math.max(1, getModelScale() * 0.8f);
        if (stateTicks == 1) {
            Vec3 aimAt = target != null ? target.position().add(0, target.getBbHeight() * 0.5, 0) : position().add(forward().scale(12));
            rendDirection = aimAt.subtract(position().add(0, 2 * scale, 0)).normalize();
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 4f, 1.4f);
        }
        if (stateTicks < 22) {
            double speed = Math.min(1.8, 0.8 + stateTicks * 0.06) * Math.max(1, getModelScale() * 0.6);
            setDeltaMovement(rendDirection.scale(speed));
            turnBody(position().add(rendDirection.scale(10)), 8f);
            lookTowards(position().add(rendDirection.scale(10)));
            if (stateTicks >= 11 && stateTicks <= 18) {
                for (int p : new int[]{DragonTracks.HAND_L, DragonTracks.HAND_R}) {
                    for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, new AABB(track(p), track(p)).inflate(2.0 * scale), this::canHit)) {
                        if (hitThisAttack.add(victim.getId())) {
                            victim.hurt(damageSources().mobAttack(this), dmg(15f));
                            victim.push(rendDirection.x * 1.2, 0.5, rendDirection.z * 1.2);
                            victim.hurtMarked = true;
                            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, victim.getX(), victim.getY() + 1, victim.getZ(), 12, 0.5, 0.5, 0.5, 0.3, false);
                        }
                    }
                }
            }
            if (getY() - floorBelow(getX(), getY() + 1, getZ()) < 2.5 * scale) {
                rendDirection = new Vec3(rendDirection.x, Math.abs(rendDirection.y) * 0.5 + 0.2, rendDirection.z).normalize();
            }
        } else {
            setDeltaMovement(getDeltaMovement().lerp(forward().scale(0.6).add(0, 0.5, 0), 0.15));
        }
        if (stateTicks >= State.SWOOP.duration) {
            endAttack(35);
        }
    }

    /* ---- dive bomb and Skyfall */

    private void tickDiveRise(@Nullable LivingEntity target) {
        if (target == null) {
            endAttack(20);
            return;
        }
        flyTowards(clampToArena(target.position().add(0, 14 * getModelScale() + 4, 0).add(forward().scale(-6))), 0.9);
        faceTowards(target.position(), 10f);
        if (stateTicks >= State.DIVE_RISE.duration) {
            diveTarget = new Vec3(target.getX(), floorBelow(target.getX(), target.getY() + 1, target.getZ()), target.getZ());
            diveStartY = getY();
            setState(State.DIVE);
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 4f * getModelScale(), 1.3f);
        }
    }

    private void tickDive() {
        Vec3 delta = diveTarget.subtract(position());
        double speed = Math.min(2.4, (isPhaseTwo() ? 1.2 : 1.0) + stateTicks * 0.06);
        setDeltaMovement(delta.normalize().scale(Math.min(speed, delta.length())));
        faceTowards(diveTarget, 15f);
        if (stateTicks % 3 == 0) {
            Vector3f color = SchoolRegistry.LIGHTNING.get().getTargetingColor();
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + 1.5, getZ(), 8, 1.2, 1.2, 1.2, 0.2, true);
        }
        if (delta.length() < 1.5 || stateTicks >= State.DIVE.duration || getY() - floorBelow(getX(), getY() + 1, getZ()) < 0.6) {
            impactSlam(speed, diveStartY - getY(), false);
        }
    }

    /** Skyfall (phase two): climbs very high above the target... */
    private void tickSkyRise(@Nullable LivingEntity target) {
        if (target == null) {
            endAttack(20);
            return;
        }
        setDeltaMovement(getDeltaMovement().lerp(new Vec3(0, 1.0 * Math.max(1, getModelScale() * 0.6), 0).add(target.position().subtract(position()).multiply(0.02, 0, 0.02)), 0.15));
        lookTowards(target.position());
        if (stateTicks == 4) {
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 5f * getModelScale(), 1.0f);
        }
        double top = target.getY() + 34 * Math.max(1, getModelScale() * 0.7);
        if (getY() > top || stateTicks >= State.SKY_RISE.duration) {
            diveTarget = new Vec3(target.getX(), floorBelow(target.getX(), target.getY() + 1, target.getZ()), target.getZ());
            diveStartY = getY();
            setState(State.SKY_DIVE);
        }
    }

    /** ... then crashes straight down on it, and roars on the ground. */
    private void tickSkyDive() {
        Vec3 delta = diveTarget.subtract(position());
        double speed = Math.min(3.2, 1.2 + stateTicks * 0.12);
        setDeltaMovement(delta.normalize().scale(Math.min(speed, delta.length())));
        faceTowards(diveTarget, 20f);
        if (stateTicks % 2 == 0) {
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + 2, getZ(), 8, 1.5, 1.5, 1.5, 0.15, true);
        }
        if (delta.length() < 1.5 || stateTicks >= State.SKY_DIVE.duration || getY() - floorBelow(getX(), getY() + 1, getZ()) < 0.6) {
            impactSlam(speed, diveStartY - getY(), true);
        }
    }

    private void impactSlam(double speed, double drop, boolean skyfall) {
        setDeltaMovement(Vec3.ZERO);
        setPos(getX(), floorBelow(getX(), getY() + 1.5, getZ()), getZ());
        double power = Mth.clamp((speed - 1.0) / 1.4 * 0.6 + Mth.clamp(drop / 20.0, 0, 1) * 0.4, 0, 1);
        if (!skyfall && diveChainLeft > 1) {
            // between two dives of the chain: the blast, but it bounces straight back up
            diveChainLeft--;
            crashBlast(power * 0.8, false);
            setState(State.DIVE_BOUNCE);
            return;
        }
        diveChainLeft = 0;
        crash(skyfall ? 1.2 : power, skyfall);
    }

    /** Lands from the air in a fight: the blast and the crash_land animation (then back to the ground fight). */
    protected void crash(double power, boolean skyfall) {
        crashSkyfall = skyfall;
        crashBlast(power, skyfall);
        setState(State.CRASH);
    }

    /**
     * The landing blast (1.8): damage around the impact, then shock rings spreading one after another like a sound
     * wave (see tickRings), lightning arcing over the ground, chunks of the ground thrown up (visual only - no block
     * is broken or moved), a roll of thunder and a strong screen shake.
     */
    protected void crashBlast(double power, boolean skyfall) {
        power = Math.max(0.2, power);
        float sc = getModelScale();
        float damage = dmg((float) Mth.lerp(Math.min(1, power), 12, 26) * (skyfall ? 1.25f : 1f));
        double radius = Mth.lerp(Math.min(1, power), 6, 12) * Math.max(0.5, sc) * (skyfall ? 1.3 : 1);
        for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(radius, 4, radius), this::canHit)) {
            double d = victim.distanceTo(this);
            if (d > radius + 2) {
                continue;
            }
            float falloff = (float) Mth.clamp(1.2 - d / (radius + 2), 0.35, 1.0);
            victim.hurt(damageSources().mobAttack(this), damage * falloff);
            Vec3 push = victim.position().subtract(position()).multiply(1, 0, 1).normalize().scale(Mth.lerp(Math.min(1, power), 0.9, 2.2) * falloff);
            victim.push(push.x, 0.6 * falloff, push.z);
            victim.hurtMarked = true;
        }
        Vector3f color = SchoolRegistry.LIGHTNING.get().getTargetingColor();
        ring(new Vec3(getX(), getY() + 0.2, getZ()), (float) radius, 0, 0);
        MagicManager.spawnParticles(level(), ParticleTypes.EXPLOSION_EMITTER, getX(), getY() + 0.5, getZ(), skyfall ? 3 : 1, 2, 0, 2, 0, true);
        MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + 0.5, getZ(), 80, 3, 0.4, 3, 0.6, true);
        MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), getX(), getY() + 0.3, getZ(), 30, 3, 0.3, 3, 0.06, false);
        groundDust(radius);
        // shock rings, one after another, ever wider
        rings.clear();
        ringHit.clear();
        int n = skyfall ? 6 : 5;
        for (int k = 0; k < n; k++) {
            rings.add(new double[]{k * 3 + 1, radius * (0.35 + 0.3 * k), getX(), getY() + 0.25, getZ()});
        }
        throwDebris(radius * 0.8, (int) (10 + 14 * Math.min(1.2, power)));
        int bolts = skyfall ? 8 : 3;
        for (int i = 0; i < bolts; i++) {
            double a = i * Math.PI * 2 / bolts + random.nextDouble() * 0.5;
            double r = radius * (0.5 + random.nextDouble() * 0.4);
            if (skyfall) {
                strike(new Vec3(getX() + Math.cos(a) * r, 0, getZ() + Math.sin(a) * r), dmg(8f));
            } else {
                visualLightning(getX() + Math.cos(a) * r, getZ() + Math.sin(a) * r);
            }
        }
        shake(skyfall ? 60 : 40);
        playSound(TechSounds.TECH_DRAGON_SLAM.get(), 5f * sc, 0.8f);
        playSound(SoundEvents.GENERIC_EXPLODE, 4f, 0.65f);
        playSound(SoundEvents.LIGHTNING_BOLT_IMPACT, 4f, 0.8f);
        playSound(SoundEvents.LIGHTNING_BOLT_THUNDER, 5f, 0.75f);
    }

    /** Spreading shock rings: an electric ring, arcs racing out along the ground, dust; whoever stands on the ground
     * where a ring passes is jolted (a small hop and a slow, once per ring set). */
    private void tickRings() {
        if (rings.isEmpty()) {
            return;
        }
        Vector3f color = SchoolRegistry.LIGHTNING.get().getTargetingColor();
        for (int i = rings.size() - 1; i >= 0; i--) {
            double[] r = rings.get(i);
            if (--r[0] > 0) {
                continue;
            }
            rings.remove(i);
            double radius = r[1];
            Vec3 c = new Vec3(r[2], r[3], r[4]);
            ring(c.add(0, 0.15, 0), (float) radius, 10, 0);
            if (level() instanceof ServerLevel server) {
                for (int k = 0; k < 4; k++) {
                    double a = random.nextDouble() * Math.PI * 2;
                    Vec3 end = c.add(Math.cos(a) * radius, 0.2, Math.sin(a) * radius);
                    Vec3 from = c.add(Math.cos(a) * radius * 0.45, 0.3, Math.sin(a) * radius * 0.45);
                    server.sendParticles(new ZapParticleOption(end), from.x, from.y, from.z, 1, 0, 0, 0, 0);
                }
            }
            BlockState below = level().getBlockState(BlockPos.containing(c.x, c.y - 1, c.z));
            if (!below.isAir()) {
                for (int k = 0; k < 10; k++) {
                    double a = random.nextDouble() * Math.PI * 2;
                    MagicManager.spawnParticles(level(), new BlockParticleOption(ParticleTypes.BLOCK, below), c.x + Math.cos(a) * radius, c.y,
                            c.z + Math.sin(a) * radius, 4, 0.6, 0.1, 0.6, 0.25, false);
                }
            }
            for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, new AABB(c, c).inflate(radius + 1, 3, radius + 1), this::canHit)) {
                double d = Math.sqrt(victim.distanceToSqr(c.x, victim.getY(), c.z));
                if (Math.abs(d - radius) > 2.5 || !victim.onGround() || !ringHit.add(victim.getId())) {
                    continue;
                }
                victim.setDeltaMovement(victim.getDeltaMovement().add(0, 0.45, 0));
                victim.hurtMarked = true;
                victim.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 40, 1), this);
            }
        }
    }

    /** Chunks of the surface around the impact flung up and outward (DragonDebris: visual only). */
    private void throwDebris(double radius, int count) {
        for (int i = 0; i < count; i++) {
            double a = random.nextDouble() * Math.PI * 2;
            double r = (0.25 + random.nextDouble() * 0.75) * radius;
            double x = getX() + Math.cos(a) * r, z = getZ() + Math.sin(a) * r;
            double y = floorBelow(x, getY() + 3, z);
            BlockState block = level().getBlockState(BlockPos.containing(x, y - 0.5, z));
            if (block.isAir() || !block.getFluidState().isEmpty()) {
                continue;
            }
            double out = 0.15 + random.nextDouble() * 0.35;
            Vec3 v = new Vec3(Math.cos(a) * out, 0.55 + random.nextDouble() * 0.6, Math.sin(a) * out);
            level().addFreshEntity(new DragonDebris(level(), new Vec3(x, y + 0.1, z), block, v));
        }
    }

    private void groundDust(double radius) {
        BlockState below = level().getBlockState(blockPosition().below());
        if (below.isAir()) {
            return;
        }
        MagicManager.spawnParticles(level(), new BlockParticleOption(ParticleTypes.BLOCK, below), getX(), getY() + 0.2, getZ(), 60, radius * 0.5, 0.2, radius * 0.5, 0.3, false);
    }

    private void tickSlam() {
        setDeltaMovement(0, getDeltaMovement().y, 0);
        if (stateTicks >= State.SLAM.duration) {
            groundTicks = isPhaseTwo() ? 220 : 300;
            if (skyfallSlam) {
                setState(State.GROUND_ROAR);
            } else {
                setState(State.GROUND);
            }
        }
    }

    /* ---- drones, EMP, arc barrage */

    private int countDrones() {
        return level().getEntitiesOfClass(ClockworkAutomaton.class, getBoundingBox().inflate(40), a -> !a.isAssembled()).size();
    }

    private void tickSummon(@Nullable LivingEntity target) {
        airDrift(target, 0.45);
        if (stateTicks == 14) {
            Vec3 around = target != null ? target.position() : position();
            int count = isPhaseTwo() ? 3 : 2;
            for (int i = 0; i < count; i++) {
                double a = random.nextDouble() * Math.PI * 2;
                double x = around.x + Math.cos(a) * 6;
                double z = around.z + Math.sin(a) * 6;
                double y = floorBelow(x, around.y + 4, z);
                ClockworkAutomaton drone = TechEntities.CLOCKWORK_AUTOMATON.get().create(level());
                if (drone != null) {
                    drone.moveTo(x, y, z, random.nextFloat() * 360f, 0);
                    drone.finalizeSpawn((ServerLevel) level(), level().getCurrentDifficultyAt(drone.blockPosition()), MobSpawnType.MOB_SUMMONED, null, null);
                    if (target != null) {
                        drone.setTarget(target);
                    }
                    level().addFreshEntity(drone);
                    visualLightning(x, z);
                    MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), x, y + 0.5, z, 16, 0.5, 0.5, 0.5, 0.04, false);
                }
            }
        }
        if (stateTicks >= State.SUMMON.duration) {
            endAttack(50);
        }
    }

    private void tickEmp(@Nullable LivingEntity target) {
        if (target != null) {
            flyTowards(clampToArena(target.position().add(0, 7, 0)), 0.6);
            faceTowards(target.getEyePosition(), 8f);
        }
        if (stateTicks == 4) {
            playSound(TechSounds.TECH_DRAGON_CHARGE.get(), 4f, 1.4f);
        }
        if (stateTicks < 22 && stateTicks % 3 == 0) {
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRICITY, getX(), getY() + 2, getZ(), 12, 3, 2, 3, 0.05, false);
        }
        if (stateTicks == 22) {
            empBlast(10 * Math.max(1, getModelScale() * 0.6), TravelOpticsCompat.cast("em_pulse", 1, this) ? 5f : 9f);
        }
        if (stateTicks >= State.EMP.duration) {
            endAttack(45);
        }
    }

    protected void empBlast(double radius, float damage) {
        shake(25);
        ring(position().add(0, 0.4, 0), (float) radius, 16, 0);
        ring(position().add(0, 2.5 * getModelScale(), 0), (float) (radius * 0.7), 12, 1);
        playSound(SoundEvents.GENERIC_EXPLODE, 4f, 1.4f);
        playSound(SoundEvents.LIGHTNING_BOLT_THUNDER, 4f, 1.2f);
        Vector3f color = SchoolRegistry.LIGHTNING.get().getTargetingColor();
        ring(new Vec3(getX(), getY() + 1, getZ()), (float) radius, 0, 0);
        MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + 2, getZ(), 90, radius * 0.5, 2, radius * 0.5, 0.6, true);
        for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(radius), this::canHit)) {
            if (victim.distanceToSqr(this) > radius * radius * 1.4) {
                continue;
            }
            DamageSources.applyDamage(victim, damage * damageScale(), SpellRegistry.SHOCKWAVE_SPELL.get().getDamageSource(this, this));
            Vec3 push = victim.position().subtract(position()).normalize().scale(1.4);
            victim.push(push.x, 0.5, push.z);
            victim.hurtMarked = true;
            victim.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 2), this);
            victim.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 60, 0), this);
        }
    }

    private void tickArcBarrage(@Nullable LivingEntity target) {
        airDrift(target, 0.55);
        if (target == null) {
            endAttack(20);
            return;
        }
        if (stateTicks >= 8 && stateTicks % 6 == 2) {
            if (!TravelOpticsCompat.cast("rapid_laser", 4, this)) {
                ChainLightning chain = new ChainLightning(level(), this, target);
                chain.setDamage(dmg(7f));
                chain.range = 6f;
                chain.maxConnections = 5;
                level().addFreshEntity(chain);
                Vec3 mouth = mouthPosition();
                ((ServerLevel) level()).sendParticles(new ZapParticleOption(target.getBoundingBox().getCenter()), mouth.x, mouth.y, mouth.z, 1, 0, 0, 0, 0);
                playSound(SoundEvents.LIGHTNING_BOLT_IMPACT, 3f, 1.2f);
            }
        }
        if (stateTicks >= State.ARC_BARRAGE.duration) {
            endAttack(45);
        }
    }

    /* ---------------------------------------------------------------- v5: gap closers, dodge, sky skills */

    /** Pounce: crouch, spring (tick 8) on an arc that lands with the target between the forefeet and the jaws (tick
     * 19), jaws and claws strike on landing with a small shock wave. */
    private void tickPounce(@Nullable LivingEntity target) {
        float sc = getModelScale();
        if (stateTicks < 8) {
            holdStill();
            if (target != null) {
                faceTowards(target.getEyePosition(), 14f);
            }
            if (stateTicks == 3) {
                playSound(TechSounds.TECH_DRAGON_AMBIENT.get(), 3f * sc, 1.2f);
            }
            return;
        }
        if (stateTicks == 8) {
            Vec3 aim = target != null ? target.position().add(target.getDeltaMovement().multiply(1, 0, 1).scale(10)) : position().add(forward().scale(8 * sc));
            Vec3 flat = aim.subtract(position()).multiply(1, 0, 1);
            double d = flat.length();
            Vec3 dir = d < 1e-3 ? forward() : flat.scale(1 / d);
            double leap = Mth.clamp(d - 72 * sc / 16.0, 1.5 * sc, (POUNCE_MAX - 60) * sc / 16.0);
            leapFrom = position();
            Vec3 to = position().add(dir.scale(leap));
            leapTo = new Vec3(to.x, groundNear(to.x, to.z), to.z);
            leapHeight = 1.5 * sc + leap * 0.16;
            turnBody(aim, 40f);
            setNoGravity(true);
            playSound(SoundEvents.ENDER_DRAGON_FLAP, 4f, 0.7f);
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 3f * sc, 1.3f);
            groundDust(1.5 * sc);
        }
        if (stateTicks >= 8 && stateTicks < 19) {
            double k = (stateTicks - 7) / 11.0;
            Vec3 p = leapFrom.lerp(leapTo, k).add(0, 4 * leapHeight * k * (1 - k), 0);
            setDeltaMovement(p.subtract(position()));
            if (target != null) {
                lookTowards(target.getEyePosition());
            }
            return;
        }
        if (stateTicks == 19) {
            setNoGravity(false);
            setDeltaMovement(0, -0.4, 0);
            shake(14);
            playSound(TechSounds.TECH_DRAGON_SLAM.get(), 3f * sc, 1.1f);
            Vec3 front = track(DragonTracks.HAND_L).add(track(DragonTracks.HAND_R)).scale(0.5);
            double radius = 3 * sc;
            Vector3f color = SchoolRegistry.LIGHTNING.get().getTargetingColor();
            ring(new Vec3(front.x, getY() + 0.2, front.z), (float) radius, 0, 0);
            groundDust(radius);
            hitSphere(front, radius, dmg(12f), SpellRegistry.SHOCKWAVE_SPELL.get().getDamageSource(this, this), 1.0, 0.5);
        }
        if (stateTicks >= 19 && stateTicks <= 21) {
            Vec3 jaws = mouthPosition();
            hitSphere(jaws, 1.8 * sc, dmg(22f), null, 0.8, 0.3);
            for (int p : new int[]{DragonTracks.HAND_L, DragonTracks.HAND_R}) {
                hitSphere(track(p), 1.7 * sc, dmg(16f), null, 1.0, 0.4);
            }
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, jaws.x, jaws.y, jaws.z, 8, 0.6, 0.4, 0.6, 0.3, false);
        } else if (stateTicks > 21) {
            holdStill();
        }
        if (stateTicks >= State.POUNCE.duration) {
            if (combo(target, true, true, false)) {
                return;
            }
            afterGroundAttack(22);
        }
    }

    /** Dash claw: a surging rush (ticks 2-9) that stops short of the target and rakes it with a forefoot (tick 12). */
    private void tickDashClaw(@Nullable LivingEntity target) {
        float sc = getModelScale();
        boolean left = getAttackVariant() == 0;
        if (stateTicks < 2) {
            holdStill();
            if (target != null) {
                faceTowards(target.position(), 16f);
            }
            return;
        }
        if (stateTicks == 2) {
            double ahead = target != null ? local(target.position()).z : 120;
            double dist = Mth.clamp(ahead - 56, 0, DASH_MAX - 40) * sc / 16.0;
            dashDir = target != null ? target.position().subtract(position()).multiply(1, 0, 1).normalize() : forward();
            if (dashDir.lengthSqr() < 1e-4) {
                dashDir = forward();
            }
            dashSpeed = dist / 8.0;
            playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 3f, 0.6f);
            groundDust(1.5 * sc);
        }
        if (stateTicks < 10) {
            if (target != null) {
                Vec3 want = target.position().subtract(position()).multiply(1, 0, 1);
                if (want.lengthSqr() > 1e-4) {
                    dashDir = dashDir.lerp(want.normalize(), 0.12).normalize();
                }
            }
            setDeltaMovement(dashDir.x * dashSpeed, getDeltaMovement().y, dashDir.z * dashSpeed);
            turnBody(position().add(dashDir.scale(5)), 8f);
            if (stateTicks % 3 == 0) {
                MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + 0.3, getZ(), 4, 1.2, 0.2, 1.2, 0.2, false);
            }
        } else {
            holdStill();
        }
        if (stateTicks == 11) {
            playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 3f, 0.5f);
        }
        if (stateTicks >= 11 && stateTicks <= 14) {
            Vec3 paw = track(left ? DragonTracks.HAND_L : DragonTracks.HAND_R);
            hitSphere(paw, 1.8f * sc, dmg(18f), null, 1.4, 0.4);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, paw.x, paw.y + 0.5, paw.z, 6, 0.6, 0.3, 0.6, 0.25, false);
        }
        if (stateTicks >= State.DASH_CLAW.duration) {
            if (combo(target, true, true, false)) {
                return;
            }
            afterGroundAttack(18);
        }
    }

    /** Dodge: a sideways hop (tick 3) away from the target's side, then an immediate counter-attack. */
    private void tickDodge(@Nullable LivingEntity target) {
        float sc = getModelScale();
        if (stateTicks < 3) {
            holdStill();
            return;
        }
        if (stateTicks == 3) {
            Vec3 side = leftDir().scale(getAttackVariant() == 0 ? 1 : -1);
            double v = 0.55 * Math.max(1, sc * 0.6);
            setDeltaMovement(side.x * v, 0.42 * Math.max(1, sc * 0.45), side.z * v);
            playSound(SoundEvents.ENDER_DRAGON_FLAP, 3f, 0.9f);
            groundDust(1.2 * sc);
        }
        if (stateTicks >= 8 && target != null) {
            faceTowards(target.getEyePosition(), 14f);
        }
        if (stateTicks > 11 && onGround()) {
            holdStill();
        }
        if (stateTicks >= State.DODGE.duration) {
            counterAttack(target);
        }
    }

    /** Straight from a dodge or a hop into whatever attack the target's new position suits. */
    private void counterAttack(@Nullable LivingEntity target) {
        if (target == null) {
            afterGroundAttack(10);
            return;
        }
        Vec3 loc = local(target.position());
        double ahead = loc.z;
        attackCooldown = 0;
        if (ahead > BITE_MIN && ahead < BITE_MAX && Math.abs(loc.x) < 40) {
            setState(canGnaw(target) && grabCooldown <= 0 && random.nextInt(4) == 0 ? State.GRAB : State.BITE);
        } else if (ahead > CLAW_MIN && ahead <= BITE_MIN) {
            setAttackVariant(loc.x > 0 ? 0 : 1);
            setState(State.CLAW);
        } else if (ahead >= BITE_MAX && ahead <= DASH_MAX) {
            setAttackVariant(loc.x > 0 ? 0 : 1);
            setState(State.DASH_CLAW);
        } else if (ahead > DASH_MAX && ahead <= POUNCE_MAX) {
            setState(State.POUNCE);
        } else {
            afterGroundAttack(6);
        }
    }

    /** Ram: lowers its horns (8 ticks), then charges at up to ~18 blocks/s, homing a little; crashing into a wall
     * dazes it. */
    private void tickRam(@Nullable LivingEntity target) {
        float sc = getModelScale();
        if (stateTicks < 8) {
            holdStill();
            if (target != null) {
                rendDirection = target.position().subtract(position()).multiply(1, 0, 1).normalize();
                turnBody(target.position(), 14f);
            }
            if (stateTicks == 2) {
                playSound(TechSounds.TECH_DRAGON_ROAR.get(), 4f * sc, 1.15f);
                shake(8);
            }
            return;
        }
        if (rendDirection.lengthSqr() < 1e-4) {
            rendDirection = forward();
        }
        if (target != null) {
            Vec3 want = target.position().subtract(position()).multiply(1, 0, 1);
            if (want.lengthSqr() > 1e-4 && local(target.position()).z > 40) {
                rendDirection = rendDirection.lerp(want.normalize(), 0.035).normalize();
            }
        }
        double speed = Math.min(0.9, 0.3 + (stateTicks - 8) * 0.08) * Math.max(1, sc * 0.5);
        setDeltaMovement(rendDirection.x * speed, getDeltaMovement().y, rendDirection.z * speed);
        turnBody(position().add(rendDirection.scale(5)), 5f);
        if (stateTicks % 3 == 0) {
            groundDust(1.6 * sc);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + 0.3, getZ(), 5, 1.5, 0.2, 1.5, 0.2, false);
        }
        Vec3 head = track(DragonTracks.HEAD);
        Vec3 chest = track(DragonTracks.CHEST);
        hitSphere(head, 2.0 * sc, dmg(20f), null, 2.6, 0.7);
        hitSphere(chest, 1.8 * sc, dmg(16f), null, 2.2, 0.6);
        boolean passed = target != null && local(target.position()).z < -30;
        if (horizontalCollision && stateTicks > 12 && speed > 0.5) {
            shake(25);
            playSound(SoundEvents.ANVIL_LAND, 3f, 0.5f);
            playSound(TechSounds.TECH_DRAGON_SLAM.get(), 3f * sc, 0.9f);
            stun(30);
            return;
        }
        if (passed && stateTicks > 20 || stateTicks >= State.RAM.duration) {
            afterGroundAttack(20);
        }
    }

    /** Storm call, part one: climbs high over the target. */
    private void tickStormRise(@Nullable LivingEntity target) {
        float scale = Math.max(1, getModelScale() * 0.7f);
        Vec3 c = target != null ? target.position() : position();
        stormY = (target != null ? target.getY() : floorBelow(c.x, getY(), c.z)) + 18 * scale;
        Vec3 back = target != null ? position().subtract(target.position()).multiply(1, 0, 1) : Vec3.ZERO;
        back = back.lengthSqr() < 1e-4 ? Vec3.ZERO : back.normalize().scale(10 * scale);
        flyTowards(clampToArena(new Vec3(c.x + back.x, stormY, c.z + back.z)), 0.9 * scale);
        if (target != null) {
            faceTowards(target.getEyePosition(), 6f);
        }
        if (getY() >= stormY - 2 || stateTicks > 90) {
            setState(State.STORM);
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 6f * getModelScale(), 0.75f);
            shake(20);
        }
    }

    /** Storm call: hangs high over the fight for 8 s, roaring, while lightning rains on the target and all around it. */
    private void tickStorm(@Nullable LivingEntity target) {
        float scale = Math.max(1, getModelScale() * 0.7f);
        if (target != null) {
            Vec3 back = position().subtract(target.position()).multiply(1, 0, 1);
            back = back.lengthSqr() < 1e-4 ? Vec3.ZERO : back.normalize().scale(10 * scale);
            flyTowards(clampToArena(new Vec3(target.getX() + back.x, stormY, target.getZ() + back.z)), 0.25 * scale);
            faceTowards(target.getEyePosition(), 3f);
        } else {
            setDeltaMovement(getDeltaMovement().scale(0.85));
        }
        if (stateTicks % 76 == 18) {
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 6f * getModelScale(), 0.8f);
            playSound(SoundEvents.LIGHTNING_BOLT_THUNDER, 5f, 0.6f);
            shake(16);
        }
        if (stateTicks % 4 == 0) {
            for (int i = 0; i < 3; i++) {
                double a = random.nextDouble() * Math.PI * 2, r = 6 + random.nextDouble() * 10;
                MagicManager.spawnParticles(level(), ParticleTypes.LARGE_SMOKE, getX() + Math.cos(a) * r * scale, getY() + (5 + random.nextDouble() * 2) * scale,
                        getZ() + Math.sin(a) * r * scale, 4, 1.5, 0.4, 1.5, 0.01, true);
            }
        }
        if (stateTicks >= 20) {
            stormLightning(target);
        }
        if (isBoss() && target != null && stateTicks % 30 == 15) {
            Vec3 mouth = mouthPosition();
            ((ServerLevel) level()).sendParticles(new ZapParticleOption(target.getBoundingBox().getCenter()), mouth.x, mouth.y, mouth.z, 1, 0, 0, 0, 0);
            DamageSources.applyDamage(target, dmg(6f), lightningSource());
        }
        if (stateTicks >= State.STORM.duration) {
            if (target != null) {
                Vec3 spot = landingSpotFacing(target);
                if (spot != null) {
                    beginLanding(spot);
                    return;
                }
            }
            endAttack(30);
        }
    }

    /**
     * The storm's lightning (1.8): bolts falling all over the area (radius ~24 blocks around the target, ~30 in phase
     * two) and, every ~1.2 s, a bolt on each creature in it that the dragon would attack (the target gets one aimed
     * where it is running to). Area damage: a bolt hurts whatever it lands on.
     */
    private void stormLightning(@Nullable LivingEntity target) {
        float scale = Math.max(1, getModelScale() * 0.7f);
        Vec3 c = target != null ? target.position() : new Vec3(getX(), floorBelow(getX(), getY(), getZ()), getZ());
        double radius = (isPhaseTwo() ? 30 : 24) * (isBoss() ? 1 : 0.5);
        double floorY = target != null ? target.getY() : c.y;
        int every = isBoss() ? (isPhaseTwo() ? 2 : 3) : 8;
        if (stateTicks % every == 0) {
            double a = random.nextDouble() * Math.PI * 2, r = Math.sqrt(random.nextDouble()) * radius;
            Vec3 at = c.add(Math.cos(a) * r, 0, Math.sin(a) * r);
            strike(at, dmg(9f), floorNear(at, floorY));
        }
        if (stateTicks % 4 == 0 && isBoss()) {
            double a = random.nextDouble() * Math.PI * 2, r = radius * (0.6 + random.nextDouble() * 0.6);
            visualLightning(c.x + Math.cos(a) * r, c.z + Math.sin(a) * r);
        }
        if (stateTicks % 24 == 4) {
            List<LivingEntity> inside = level().getEntitiesOfClass(LivingEntity.class, new AABB(c, c).inflate(radius, 24 * scale, radius),
                    e -> isPrey(e) && e.distanceToSqr(c.x, e.getY(), c.z) < radius * radius);
            for (LivingEntity e : inside) {
                Vec3 at = e == target ? e.position().add(e.getDeltaMovement().multiply(1, 0, 1).scale(10)) : e.position();
                strike(at, dmg(9f), floorNear(at, e.getY()));
            }
        }
    }

    /** Dive chain: back up into the air between two dives. */
    private void tickDiveBounce(@Nullable LivingEntity target) {
        if (stateTicks < 7) {
            setDeltaMovement(Vec3.ZERO);
            if (target != null) {
                turnBody(target.position(), 8f);
            }
            return;
        }
        if (stateTicks == 7) {
            playSound(SoundEvents.ENDER_DRAGON_FLAP, 4f, 0.6f);
            groundDust(2.5 * getModelScale());
        }
        setDeltaMovement(getDeltaMovement().lerp(new Vec3(0, 0.9 * Math.max(1, getModelScale() * 0.6), 0), 0.3));
        if (stateTicks >= State.DIVE_BOUNCE.duration) {
            if (target == null) {
                diveChainLeft = 0;
                endAttack(20);
                return;
            }
            setState(State.DIVE_RISE);
        }
    }

    /* ---- 1.8: kiting and the crash */

    private Vec3 awayFrom(@Nullable LivingEntity target) {
        Vec3 away = target != null ? position().subtract(target.position()).multiply(1, 0, 1) : Vec3.ZERO;
        return away.lengthSqr() < 1e-4 ? forward().scale(-1) : away.normalize();
    }

    /** After a kiting move: spit lightning if the target is now at range, else back to the ground fight. */
    private void afterKite(@Nullable LivingEntity target, int cooldown) {
        if (target != null && target.isAlive() && spitCooldown <= 0 && distanceTo(target) > 7 * getModelScale()) {
            setState(State.SPIT);
            return;
        }
        afterGroundAttack(cooldown);
    }

    /** Backstep: one big forward wing beat throws it back ~7 blocks x scale on a low arc (ticks 6-17), facing the
     * target; the beat also shoves whatever is right in front of it. */
    private void tickBackstep(@Nullable LivingEntity target) {
        float sc = getModelScale();
        if (target != null) {
            faceTowards(target.getEyePosition(), stateTicks < 6 ? 14f : 6f);
        }
        if (stateTicks < 6) {
            holdStill();
            return;
        }
        if (stateTicks == 6) {
            Vec3 away = awayFrom(target);
            Vec3 to = position().add(away.scale(7 * sc));
            Vec3 clamped = clampToArena(to);
            leapFrom = position();
            leapTo = new Vec3(clamped.x, groundNear(clamped.x, clamped.z), clamped.z);
            leapHeight = 1.6 * sc;
            setNoGravity(true);
            playSound(SoundEvents.ENDER_DRAGON_FLAP, 5f, 0.55f);
            groundDust(2 * sc);
            Vec3 front = position().add(forward().scale(4 * sc));
            for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, new AABB(front, front).inflate(3.5 * sc, 2 * sc, 3.5 * sc), this::canHit)) {
                Vec3 push = victim.position().subtract(position()).multiply(1, 0, 1).normalize();
                victim.setDeltaMovement(victim.getDeltaMovement().add(push.x * 1.2, 0.3, push.z * 1.2));
                victim.hurtMarked = true;
            }
            MagicManager.spawnParticles(level(), ParticleTypes.CLOUD, front.x, getY() + 1, front.z, 30, 2 * sc, 0.6, 2 * sc, 0.25, true);
        }
        if (stateTicks >= 6 && stateTicks < 17) {
            double k = (stateTicks - 5) / 11.0;
            Vec3 p = leapFrom.lerp(leapTo, k).add(0, 4 * leapHeight * k * (1 - k), 0);
            setDeltaMovement(p.subtract(position()));
            if (stateTicks == 13) {
                playSound(SoundEvents.ENDER_DRAGON_FLAP, 4f, 0.65f);
            }
            return;
        }
        if (stateTicks == 17) {
            setNoGravity(false);
            setDeltaMovement(0, -0.3, 0);
            shake(8);
            playSound(TechSounds.TECH_DRAGON_SLAM.get(), 2f * sc, 1.2f);
            groundDust(2 * sc);
        } else {
            holdStill();
        }
        if (stateTicks >= State.BACKSTEP.duration) {
            afterKite(target, 12);
        }
    }

    /** Wing push: two beats forward (ticks 12 and 21) blowing everything in a wide cone in front far away, knocking
     * projectiles back; little damage - it is about distance. */
    private void tickWingPush(@Nullable LivingEntity target) {
        holdStill();
        float sc = getModelScale();
        if (target != null && stateTicks < 11) {
            faceTowards(target.getEyePosition(), 10f);
        }
        if (stateTicks == 6) {
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 4f * sc, 0.9f);
        }
        if (stateTicks == 12 || stateTicks == 21) {
            boolean first = stateTicks == 12;
            double range = 8 * sc + 2;
            playSound(SoundEvents.ENDER_DRAGON_FLAP, 6f, first ? 0.45f : 0.55f);
            shake(10);
            Vec3 c = position().add(0, getBbHeight() * 0.4, 0);
            Vec3 fwd = forward();
            for (Entity e : level().getEntities(this, getBoundingBox().inflate(range), e -> e != this && !(e instanceof TechDragonPart))) {
                Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
                double d = to.length();
                if (d > range || d < 1e-3 || to.scale(1 / d).dot(fwd) < 0.35) {
                    continue;
                }
                Vec3 push = to.scale(1 / d);
                double falloff = 1.25 - d / range;
                if (e instanceof Projectile projectile) {
                    projectile.setDeltaMovement(push.scale(1.6));
                    projectile.hurtMarked = true;
                } else if (e instanceof LivingEntity victim && canHit(victim)) {
                    if (first) {
                        victim.hurt(damageSources().mobAttack(this), dmg(4f));
                    }
                    double kb = 1 - victim.getAttributeValue(Attributes.KNOCKBACK_RESISTANCE) * 0.5;
                    victim.setDeltaMovement(victim.getDeltaMovement().add(push.x * 2.8 * falloff * kb, 0.45 + 0.25 * falloff, push.z * 2.8 * falloff * kb));
                    victim.hurtMarked = true;
                }
            }
            Vec3 mid = c.add(fwd.scale(range * 0.5));
            MagicManager.spawnParticles(level(), ParticleTypes.CLOUD, mid.x, mid.y, mid.z, 60, range * 0.35, 1.2, range * 0.35, 0.35, true);
            MagicManager.spawnParticles(level(), ParticleTypes.SWEEP_ATTACK, mid.x, mid.y, mid.z, 10, range * 0.3, 0.8, range * 0.3, 0, true);
            groundDust(2.5 * sc);
        }
        if (stateTicks >= State.WING_PUSH.duration) {
            afterKite(target, 16);
        }
    }

    /** Kite hop: a sideways hop that also backs off (dodge animation); 2-3 in a row from side to side, then the spit. */
    private void tickKiteHop(@Nullable LivingEntity target) {
        float sc = getModelScale();
        if (stateTicks < 3) {
            holdStill();
            return;
        }
        if (stateTicks == 3) {
            Vec3 side = leftDir().scale(getAttackVariant() == 0 ? 1 : -1);
            Vec3 back = awayFrom(target);
            double v = 0.5 * Math.max(1, sc * 0.6);
            Vec3 dir = side.add(back.scale(0.6)).normalize();
            setDeltaMovement(dir.x * v, 0.42 * Math.max(1, sc * 0.45), dir.z * v);
            playSound(SoundEvents.ENDER_DRAGON_FLAP, 3f, 1.0f);
            groundDust(1.2 * sc);
        }
        if (target != null && stateTicks >= 6) {
            faceTowards(target.getEyePosition(), 14f);
        }
        if (stateTicks > 11 && onGround()) {
            holdStill();
        }
        if (stateTicks >= State.KITE_HOP.duration) {
            if (--kiteHopsLeft > 0 && target != null) {
                setAttackVariant(1 - getAttackVariant());
                setState(State.KITE_HOP);
                return;
            }
            afterKite(target, 8);
        }
    }

    /** Lightning spit (like Ice and Fire's lightning dragons): the core and crest charge (ticks 2-11), then a bolt
     * from the jaws to where the target is heading (tick 12); phase two spits a second one (tick 17). */
    private void tickSpit(@Nullable LivingEntity target) {
        holdStill();
        if (target != null) {
            faceTowards(target.getEyePosition(), stateTicks < 12 ? 12f : 4f);
        }
        Vec3 mouth = mouthPosition();
        if (stateTicks == 2) {
            playSound(TechSounds.TECH_DRAGON_CHARGE.get(), 3f, 1.35f);
        }
        if (stateTicks == 4 || stateTicks == 8) {
            ringFacing(mouth, 1.2f * getModelScale(), 8, 0);
        }
        if (stateTicks >= 2 && stateTicks < 12 && stateTicks % 2 == 0) {
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, mouth.x, mouth.y, mouth.z, 6, 0.4, 0.4, 0.4, 0.15, false);
            Vec3 core = corePosition();
            if (level() instanceof ServerLevel server) {
                server.sendParticles(new ZapParticleOption(mouth), core.x, core.y, core.z, 1, 0, 0, 0, 0);
            }
        }
        if (stateTicks == 12 || stateTicks == 17 && isPhaseTwo()) {
            Vec3 aim = target != null ? target.getBoundingBox().getCenter().add(target.getDeltaMovement().multiply(1, 0, 1).scale(stateTicks == 12 ? 5 : 8))
                    : mouth.add(forward().scale(30));
            spitBolt(mouth, aim);
        }
        if (stateTicks >= State.SPIT.duration) {
            spitCooldown = isPhaseTwo() ? 100 : 140;
            afterGroundAttack(14);
        }
    }

    /** One spat bolt: a jagged lightning bolt from the jaws, stopped by blocks (they are not damaged) or by the first
     * creature in its path; it bursts on impact (radius ~1.6 x scale). */
    protected void spitBolt(Vec3 from, Vec3 aim) {
        Vec3 dir = aim.subtract(from);
        double len = Math.min(64, dir.length());
        dir = dir.lengthSqr() < 1e-6 ? forward() : dir.normalize();
        Vec3 end = from.add(dir.scale(len + 2));
        BlockHitResult wall = level().clip(new ClipContext(from, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        if (wall.getType() != HitResult.Type.MISS) {
            end = wall.getLocation();
        }
        double best = from.distanceTo(end);
        for (LivingEntity e : level().getEntitiesOfClass(LivingEntity.class, new AABB(from, end).inflate(1.5), this::canHit)) {
            var hit = e.getBoundingBox().inflate(0.4).clip(from, end);
            if (hit.isPresent() && from.distanceTo(hit.get()) < best) {
                best = from.distanceTo(hit.get());
            }
        }
        end = from.add(dir.scale(best));
        if (isBoss() && wall.getType() != HitResult.Type.MISS && from.distanceTo(end) >= from.distanceTo(wall.getLocation()) - 0.5) {
            breakBlocks(new AABB(end, end).inflate(1.6), WEAK, 16);
        }
        if (level() instanceof ServerLevel server) {
            // the bolt: a few jagged strands along the line
            for (int strand = 0; strand < 3; strand++) {
                Vec3 a = from;
                int segs = Math.max(2, (int) (best / 6));
                for (int k = 1; k <= segs; k++) {
                    Vec3 b = k == segs ? end : from.add(dir.scale(best * k / segs)).add((random.nextDouble() - 0.5) * 1.6, (random.nextDouble() - 0.5) * 1.6,
                            (random.nextDouble() - 0.5) * 1.6);
                    server.sendParticles(new ZapParticleOption(b), a.x, a.y, a.z, 1, 0, 0, 0, 0);
                    a = b;
                }
            }
        }
        float sc = getModelScale();
        double r = 1.6 * sc;
        for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, new AABB(end, end).inflate(r + 1), this::canHit)) {
            if (Math.sqrt(victim.getBoundingBox().distanceToSqr(end)) > r) {
                continue;
            }
            DamageSources.applyDamage(victim, dmg(14f), lightningSource());
            Vec3 push = victim.position().subtract(end).multiply(1, 0, 1);
            push = push.lengthSqr() < 1e-4 ? dir : push.normalize();
            victim.setDeltaMovement(victim.getDeltaMovement().add(push.x * 0.8, 0.35, push.z * 0.8));
            victim.hurtMarked = true;
        }
        Vector3f color = SchoolRegistry.LIGHTNING.get().getTargetingColor();
        ring(new Vec3(end.x, end.y, end.z), (float) (r + 1), 0, 0);
        MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, end.x, end.y, end.z, 40, 0.8, 0.8, 0.8, 0.5, true);
        MagicManager.spawnParticles(level(), ParticleTypes.EXPLOSION, end.x, end.y, end.z, 2, 0.4, 0.4, 0.4, 0, true);
        playSound(SoundEvents.LIGHTNING_BOLT_THUNDER, 3f, 1.5f);
        level().playSound(null, end.x, end.y, end.z, SoundEvents.LIGHTNING_BOLT_IMPACT, getSoundSource(), 3f, 1.1f);
    }

    /** After the crash: crouched in the dust, it roars (tick 11) - Skyfall goes on into its slowing roar. */
    private void tickCrash(@Nullable LivingEntity target) {
        setDeltaMovement(0, getDeltaMovement().y, 0);
        if (target != null && stateTicks > 8) {
            faceTowards(target.getEyePosition(), 6f);
        }
        if (stateTicks == 11) {
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 6f * getModelScale(), 0.8f);
            shake(16);
        }
        if (stateTicks >= State.CRASH.duration) {
            groundTicks = isPhaseTwo() ? 220 : 300;
            if (crashSkyfall) {
                crashSkyfall = false;
                skyfallSlam = true;
                setState(State.GROUND_ROAR);
            } else {
                afterGroundAttack(10);
            }
        }
    }

    /* ---- 1.10 */

    /**
     * The roar's blast: everything in the half sphere around it (on the ground or in the air above, not below the floor
     * it stands on) is shoved straight away from it, projectiles included; a dome of arcs shows the blast.
     */
    protected void roarPush(double radius, double strength) {
        Vec3 c = position().add(0, 0.5, 0);
        for (Entity e : level().getEntities(this, getBoundingBox().inflate(radius), e -> e != this && !(e instanceof TechDragonPart))) {
            Vec3 at = e.getBoundingBox().getCenter();
            if (at.y < getY() - 1.5) {
                continue;
            }
            Vec3 d = at.subtract(c);
            double len = d.length();
            if (len > radius || len < 1e-3) {
                continue;
            }
            Vec3 dir = d.scale(1 / len);
            double f = Mth.clamp(1.3 - len / radius, 0.3, 1.0);
            if (e instanceof Projectile projectile) {
                projectile.setDeltaMovement(dir.scale(1.6));
                projectile.hurtMarked = true;
            } else if (e instanceof LivingEntity victim && canHit(victim) && !hasPassenger(victim)) {
                double kb = 1 - victim.getAttributeValue(Attributes.KNOCKBACK_RESISTANCE) * 0.5;
                victim.setDeltaMovement(victim.getDeltaMovement().add(dir.x * strength * f * kb, Math.max(0.35, dir.y * strength * f) * kb, dir.z * strength * f * kb));
                victim.hurtMarked = true;
            }
        }
        if (level() instanceof ServerLevel server) {
            ElectricFx.dome(server, c, (float) radius);
        }
    }

    /** A spacing hop (1.10) that puts the target straight ahead at the middle of the jaws' reach. */
    private State hop(Vec3 loc) {
        double dx = loc.x, dz = loc.z - (BITE_MIN + BITE_MAX) * 0.5;
        int dir = Math.abs(dz) >= Math.abs(dx) ? (dz > 0 ? 0 : 1) : (dx > 0 ? 2 : 3);
        setAttackVariant(dir);
        hopShift = new Vec3(dx, 0, dz);
        hopCooldown = (isPhaseTwo() ? 50 : 80) + random.nextInt(40);
        return State.HOP;
    }

    /** Hop: crouch, a short jump (ticks 3-11) forward, back, left or right on a low arc, land facing the target and
     * strike at once. */
    private void tickHop(@Nullable LivingEntity target) {
        float sc = getModelScale();
        if (stateTicks < 3) {
            holdStill();
            if (target != null) {
                lookTowards(target.getEyePosition());
            }
            return;
        }
        if (stateTicks == 3) {
            Vec3 shift = leftDir().scale(hopShift.x).add(forward().scale(hopShift.z)).scale(sc / 16.0);
            double len = shift.length();
            double max = 7.5 * Math.max(1, sc * 0.6);
            if (len > max) {
                shift = shift.scale(max / len);
            } else if (len < 1.2) {
                Vec3 d = len < 1e-3 ? forward().scale(getAttackVariant() == 1 ? -1 : 1) : shift.scale(1 / len);
                shift = d.scale(1.2);
            }
            Vec3 to = clampToArena(position().add(shift));
            leapFrom = position();
            leapTo = new Vec3(to.x, groundNear(to.x, to.z), to.z);
            leapHeight = 0.8 * sc + shift.length() * 0.12;
            setNoGravity(true);
            playSound(SoundEvents.ENDER_DRAGON_FLAP, 3f, 1.0f);
            groundDust(1.2 * sc);
        }
        if (stateTicks >= 3 && stateTicks < 11) {
            double k = (stateTicks - 2) / 8.0;
            Vec3 p = leapFrom.lerp(leapTo, k).add(0, 4 * leapHeight * k * (1 - k), 0);
            setDeltaMovement(p.subtract(position()));
            if (target != null) {
                lookTowards(target.getEyePosition());
            }
            return;
        }
        if (stateTicks == 11) {
            setNoGravity(false);
            setDeltaMovement(0, -0.3, 0);
            groundDust(1.2 * sc);
        } else {
            holdStill();
        }
        if (target != null) {
            faceTowards(target.getEyePosition(), 12f);
        }
        if (stateTicks >= State.HOP.duration) {
            counterAttack(target);
        }
    }

    /**
     * Spin discharge (1.10): braced low, it whirls a full turn (ticks 8-24) - tail and wings sweep everything around it -
     * and at the height of the turn (tick 16) its whole body discharges: arcs race out along the ground and over its
     * back, everything around and on it is jolted and thrown away. It is also how it shakes off what climbed on it.
     */
    private void tickSpin() {
        holdStill();
        float sc = getModelScale();
        if (stateTicks == 3) {
            playSound(TechSounds.TECH_DRAGON_CHARGE.get(), 3f, 1.3f);
        }
        if (stateTicks == 8) {
            playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 5f, 0.4f);
        }
        if (stateTicks >= 8 && stateTicks <= 24) {
            float r = 2.0f * sc;
            for (int p : new int[]{DragonTracks.TAIL_TIP, DragonTracks.TAIL3, DragonTracks.TAIL2}) {
                hitSphere(track(p), r, dmg(15f), null, 2.0, 0.6);
            }
            if (stateTicks % 3 == 0 && level() instanceof ServerLevel server) {
                Vec3 tip = track(DragonTracks.TAIL_TIP);
                Vec3 core = corePosition();
                server.sendParticles(new ZapParticleOption(tip), core.x, core.y, core.z, 1, 0, 0, 0, 0);
                MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, tip.x, tip.y, tip.z, 6, 0.8, 0.4, 0.8, 0.3, false);
            }
        }
        if (stateTicks == 16) {
            double radius = 6.5 * sc;
            ring(position().add(0, 0.3, 0), (float) radius, 0, ElectricFx.CYAN);
            ring(position().add(0, getBbHeight() * 0.75, 0), (float) (radius * 0.55), 0, ElectricFx.VIOLET);
            playSound(SoundEvents.LIGHTNING_BOLT_IMPACT, 4f, 1.2f);
            playSound(SoundEvents.GENERIC_EXPLODE, 2f, 1.5f);
            shake(12);
            for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(radius, 3, radius), this::canHit)) {
                double d = Math.sqrt(victim.distanceToSqr(getX(), victim.getY(), getZ()));
                if (d > radius + 1 || hasPassenger(victim)) {
                    continue;
                }
                victim.invulnerableTime = 0;
                DamageSources.applyDamage(victim, dmg(10f), lightningSource());
                Vec3 push = victim.position().subtract(position()).multiply(1, 0, 1);
                push = push.lengthSqr() < 1e-4 ? forward() : push.normalize();
                double kb = 1 - victim.getAttributeValue(Attributes.KNOCKBACK_RESISTANCE) * 0.5;
                victim.setDeltaMovement(victim.getDeltaMovement().add(push.x * 1.6 * kb, 0.55, push.z * 1.6 * kb));
                victim.hurtMarked = true;
            }
            onBackTicks = 0;
        }
        if (stateTicks >= State.SPIN.duration) {
            afterGroundAttack(18);
        }
    }

    /**
     * Sky breath (1.10): it climbs and circles high above the target, facing it, and breathes lightning down on it as it
     * goes round (charge 1.2 s, breath ~4.8 s); then it comes back down into the fight.
     */
    private void tickSkyBreath(@Nullable LivingEntity target) {
        float sc = Math.max(1, getModelScale() * 0.7f);
        if (target == null) {
            endAttack(20);
            return;
        }
        Vec3 orbit = clampToArena(orbitPoint(target.position(), 10 * sc, 12 * sc, 0.03));
        flyTowards(orbit, 0.65 * sc);
        faceTowards(target.position(), 4f);
        Vec3 mouth = mouthPosition();
        Vec3 wanted = target.getBoundingBox().getCenter().subtract(mouth).normalize();
        if (stateTicks < 24) {
            breathAim = wanted;
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, mouth.x, mouth.y, mouth.z, 4, 0.4, 0.4, 0.4, 0.05, false);
            if (stateTicks == 4) {
                playSound(TechSounds.TECH_DRAGON_CHARGE.get(), 4f, 0.9f);
            }
            if (stateTicks == 23) {
                playSound(TechSounds.TECH_DRAGON_BREATH.get(), 4f * getModelScale(), 0.85f);
            }
            return;
        }
        breathAim = breathAim.lerp(wanted, isPhaseTwo() ? 0.12 : 0.08).normalize();
        lookTowards(mouth.add(breathAim.scale(10)));
        breathBeam(mouth, breathAim, 44, dmg(7f));
        if (stateTicks >= State.SKY_BREATH.duration) {
            breathCooldown = 160;
            Vec3 spot = isBoss() && targetOnGround(target) ? landingSpotFacing(target) : null;
            if (spot != null) {
                beginLanding(spot);
                return;
            }
            endAttack(40);
        }
    }

    /**
     * Strafing run (1.10): it swings out to one side of the target (up to ~1 s), then sweeps low and fast straight
     * across it, spitting lightning bolts down from its jaws as it passes over (three, four in phase two), and climbs away.
     */
    private void tickStrafe(@Nullable LivingEntity target) {
        float sc = Math.max(1, getModelScale() * 0.7f);
        if (target == null) {
            endAttack(20);
            return;
        }
        if (stateTicks == 1) {
            strafeSpits = isPhaseTwo() ? 4 : 3;
            Vec3 away = position().subtract(target.position()).multiply(1, 0, 1);
            away = away.lengthSqr() < 1e-4 ? forward().scale(-1) : away.normalize();
            leapFrom = clampToArena(target.position().add(away.scale(16 * sc)).add(0, 8 * sc, 0));
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 4f * getModelScale(), 1.2f);
        }
        if (stateTicks < 22) {
            steer(leapFrom, 1.0 * sc, 7f);
            lookTowards(target.getEyePosition());
            return;
        }
        if (stateTicks == 22) {
            Vec3 across = target.position().subtract(position()).multiply(1, 0, 1);
            rendDirection = across.lengthSqr() < 1e-4 ? forward() : across.normalize();
        }
        double speed = 1.15 * sc;
        double vertical = Mth.clamp((target.getY() + 4.5 * sc - getY()) * 0.15, -0.5, 0.5);
        setDeltaMovement(getDeltaMovement().lerp(new Vec3(rendDirection.x * speed, vertical, rendDirection.z * speed), 0.25));
        turnBody(position().add(rendDirection.scale(10)), 6f);
        lookTowards(target.getEyePosition());
        // the bolts: one every 5 ticks while it passes over the target (within ~12 blocks), three (four in phase two)
        double flat = Math.sqrt(target.distanceToSqr(getX(), target.getY(), getZ()));
        if (strafeSpits > 0 && flat < 12 * sc && stateTicks % 5 == 0) {
            strafeSpits--;
            Vec3 mouth = mouthPosition();
            spitBolt(mouth, target.getBoundingBox().getCenter().add(target.getDeltaMovement().multiply(1, 0, 1).scale(4)));
        }
        if (stateTicks >= State.STRAFE.duration) {
            endAttack(40);
        }
    }

    /* ---- 1.9 */

    /** 1.10: an instant electric burst along the ground (was a lingering shock ring); {@code life} is unused. */
    protected void ring(Vec3 at, float radius, int life, int style) {
        if (level() instanceof ServerLevel server) {
            ElectricFx.burst(server, at, radius, style);
        }
    }

    /** 1.10: an instant electric burst standing up, facing where the dragon looks (was a lingering ring). */
    protected void ringFacing(Vec3 at, float radius, int life, int style) {
        if (level() instanceof ServerLevel server) {
            ElectricFx.burstFacing(server, at, radius, style, yBodyRot);
        }
    }

    /** Block hardness the dragon's body shoves through (stone, cobble, planks, logs, bricks...). */
    public static final float BODY = 2.0f;
    /** What lightning blows apart (dirt, sand, gravel, grass, glass, leaves, snow...). */
    public static final float WEAK = 0.6f;
    /** What the core beam drills (up to stone bricks, deepslate, ores). */
    public static final float BEAM = 3.0f;

    /** mobGriefing (and Forge's event) decide whether it may break blocks at all. */
    protected boolean canGrief() {
        return level() instanceof ServerLevel && ForgeEventFactory.getMobGriefingEvent(level(), this);
    }

    /**
     * Breaks (no drops) up to {@code limit} blocks inside the box no harder than {@code maxHardness}: never unbreakable
     * blocks, blocks holding data (chests, furnaces, spawners...), wither/dragon-immune blocks or fluids. Returns how many.
     */
    protected int breakBlocks(AABB box, float maxHardness, int limit) {
        if (!canGrief()) {
            return 0;
        }
        int n = 0;
        for (BlockPos pos : BlockPos.betweenClosed(BlockPos.containing(box.minX, box.minY, box.minZ), BlockPos.containing(box.maxX, box.maxY, box.maxZ))) {
            if (n >= limit) {
                break;
            }
            BlockState state = level().getBlockState(pos);
            if (state.isAir() || !state.getFluidState().isEmpty() && state.getBlock() instanceof net.minecraft.world.level.block.LiquidBlock) {
                continue;
            }
            float hardness = state.getDestroySpeed(level(), pos);
            if (hardness < 0 || hardness > maxHardness || state.hasBlockEntity() || state.is(BlockTags.WITHER_IMMUNE) || state.is(BlockTags.DRAGON_IMMUNE)
                    || !state.canEntityDestroy(level(), pos, this) || !ForgeEventFactory.onEntityDestroyBlock(this, pos, state)) {
                continue;
            }
            level().destroyBlock(pos.immutable(), false, this);
            n++;
        }
        return n;
    }

    /**
     * Like Ice and Fire's dragons it does not go around things: whatever its head, neck, body and legs push into on the
     * way to its target is smashed (above its feet - it never digs the floor it stands on), at most ~24 blocks a tick.
     */
    private void breakThrough() {
        State st = getState();
        if (st == State.DEATH || st == State.SPAWN || st == State.PERCH || st == State.SLEEP || st == State.STUNNED || st == State.EMP_STUN
                || horizontalSpeedSqr() < 0.0004 && getDeltaMovement().y > -0.05 && st.grounded() && st != State.RAM && st != State.REND) {
            return;
        }
        double floor = getY() + 0.5;
        int budget = 24;
        for (int i = 0; i <= DragonTracks.R_LEG_HR && budget > 0; i++) {
            AABB box = parts[i].getBoundingBox();
            if (box.maxY <= floor) {
                continue;
            }
            budget -= breakBlocks(new AABB(box.minX, Math.max(box.minY, floor), box.minZ, box.maxX, box.maxY, box.maxZ).inflate(0.3), BODY, budget);
        }
    }

    /** Pinned and gnawed: anything the jaws can hold, and a little wider (1.10: a Warden fits). */
    public boolean canBePinned(LivingEntity e) {
        float f = Math.max(0.85f, getModelScale() / BOSS_SCALE);
        return e.getBbWidth() <= 2.0f * f && e.getBbHeight() <= 3.6f * f && !e.isPassenger() && !e.isVehicle() && !(e instanceof TechDragon)
                && !e.isMultipartEntity() && !e.getType().is(Tags.EntityTypes.BOSSES);
    }

    /** EMP seizure: drained grey, twitching on the ground for the stun, then back up. */
    private void tickEmpStun() {
        setNoGravity(false);
        this.noPhysics = false;
        setDeltaMovement(getDeltaMovement().multiply(0.5, 1, 0.5));
        float sc = getModelScale();
        if (stateTicks % 9 == 2) {
            Vec3 c = position().add(0, getBbHeight() * 0.35, 0);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, c.x, c.y, c.z, 14, 2.2 * sc, 0.8 * sc, 2.2 * sc, 0.25, false);
            if (level() instanceof ServerLevel server) {
                for (int k = 0; k < 3; k++) {
                    Vec3 a = c.add((random.nextDouble() - 0.5) * 6 * sc, (random.nextDouble() - 0.3) * 2 * sc, (random.nextDouble() - 0.5) * 6 * sc);
                    Vec3 b = a.add((random.nextDouble() - 0.5) * 3 * sc, (random.nextDouble() - 0.5) * 1.5 * sc, (random.nextDouble() - 0.5) * 3 * sc);
                    server.sendParticles(new ZapParticleOption(b), a.x, a.y, a.z, 1, 0, 0, 0, 0);
                }
            }
            playSound(SoundEvents.REDSTONE_TORCH_BURNOUT, 2f, 0.6f + random.nextFloat() * 0.4f);
        }
        if (stateTicks == 8) {
            shake(10);
            playSound(TechSounds.TECH_DRAGON_SLAM.get(), 2f * sc, 1.3f);
            ring(position().add(0, 0.2, 0), 4 * sc, 10, 2);
        }
        if (stateTicks >= stunLength) {
            groundTicks = 160;
            setState(isBoss() ? State.GROUND : State.TAKEOFF);
        }
    }

    /** Pin and gnaw: the left forefoot comes down on the prey (tick 8), the jaws gnaw it four times, a kick (tick 56). */
    private void tickPin(@Nullable LivingEntity target) {
        holdStill();
        float sc = getModelScale();
        if (stateTicks < 7 && target != null) {
            faceTowards(target.getEyePosition(), 12f);
        }
        if (stateTicks == 8 && grabbed == null) {
            Vec3 paw = track(DragonTracks.HAND_L);
            LivingEntity prey = level().getEntitiesOfClass(LivingEntity.class, new AABB(paw, paw).inflate(2.4 * sc, 2.0 * sc, 2.4 * sc),
                    e -> canHit(e) && canBePinned(e)).stream().min(Comparator.comparingDouble(e -> e.distanceToSqr(paw))).orElse(null);
            shake(10);
            playSound(TechSounds.TECH_DRAGON_SLAM.get(), 2.5f * sc, 1.25f);
            groundDust(1.5 * sc);
            ring(new Vec3(paw.x, getY() + 0.2, paw.z), 2.5f * sc, 8, 0);
            if (prey != null && prey.startRiding(this, true)) {
                grabbed = prey;
                this.entityData.set(DATA_GRABBED, prey.getId());
                prey.hurt(damageSources().mobAttack(this), dmg(8f));
            } else {
                afterGroundAttack(16);
                return;
            }
        }
        if (stateTicks > 8 && (grabbed == null || !grabbed.isAlive() || grabbed.getVehicle() != this)) {
            releaseGrabbed(Vec3.ZERO);
            afterGroundAttack(16);
            return;
        }
        for (int bite : new int[]{17, 26, 35, 44}) {
            if (stateTicks == bite && grabbed != null) {
                grabbed.invulnerableTime = 0;
                grabbed.hurt(damageSources().mobAttack(this), dmg(9f));
                Vec3 jaws = mouthPosition();
                MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, jaws.x, jaws.y, jaws.z, 10, 0.5, 0.4, 0.5, 0.3, false);
                playSound(SoundEvents.EVOKER_FANGS_ATTACK, 2.5f, 0.55f + random.nextFloat() * 0.1f);
                playSound(SoundEvents.PLAYER_HURT_SWEET_BERRY_BUSH, 2f, 0.5f);
            }
        }
        if (stateTicks == 56 && grabbed != null) {
            LivingEntity victim = grabbed;
            releaseGrabbed(forward().scale(1.6).add(leftDir().scale(-0.8)).add(0, 0.7, 0));
            victim.hurt(damageSources().mobAttack(this), dmg(5f));
        }
        if (stateTicks >= State.PIN.duration) {
            afterGroundAttack(20);
        }
    }

    /** Carry: climbs hard with the prey in its jaws (about 18 blocks x scale up), worrying it, then lets go: the fall
     * does the rest. It stays in the air afterwards and comes back down crashing. */
    private void tickCarry() {
        float sc = Math.max(1, getModelScale() * 0.6f);
        if (grabbed == null || !grabbed.isAlive() || grabbed.getVehicle() != this) {
            releaseGrabbed(Vec3.ZERO);
            endAttack(20);
            return;
        }
        double climb = getY() < carryTop ? 0.55 * sc : 0.05;
        setDeltaMovement(getDeltaMovement().multiply(0.7, 0, 0.7).add(forward().scale(0.08)).add(0, climb, 0));
        if (stateTicks % 14 == 6) {
            grabbed.invulnerableTime = 0;
            grabbed.hurt(damageSources().mobAttack(this), dmg(4f));
        }
        if (getY() >= carryTop - 1 || stateTicks >= State.CARRY.duration) {
            LivingEntity victim = grabbed;
            releaseGrabbed(new Vec3(0, -0.4, 0));
            victim.fallDistance = Math.max(victim.fallDistance, 4f);
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 5f * getModelScale(), 1.1f);
            airAttacksLeft = 0;
            endAttack(30);
        }
    }

    /** Core charge: rears and the chest core swells, energy streaming into it, rings closing in (1.5 s). */
    private void tickCoreCharge(@Nullable LivingEntity target) {
        holdStill();
        if (target != null) {
            faceTowards(target.getEyePosition(), 8f);
        }
        Vec3 core = corePosition();
        if (stateTicks == 1) {
            playSound(TechSounds.TECH_DRAGON_CHARGE.get(), 5f, 0.7f);
            playSound(SoundEvents.BEACON_POWER_SELECT, 4f, 0.5f);
        }
        if (stateTicks % 6 == 3) {
            ringFacing(core, (3.2f - stateTicks * 0.06f) * getModelScale(), 6, 1);
        }
        if (level() instanceof ServerLevel server && stateTicks % 2 == 0) {
            for (int k = 0; k < 3; k++) {
                Vec3 from = core.add((random.nextDouble() - 0.5) * 10, (random.nextDouble() - 0.2) * 6, (random.nextDouble() - 0.5) * 10);
                server.sendParticles(new ZapParticleOption(core), from.x, from.y, from.z, 1, 0, 0, 0, 0);
            }
            MagicManager.spawnParticles(level(), ParticleTypes.END_ROD, core.x, core.y, core.z, 4, 1.5, 1.5, 1.5, 0.05, false);
        }
        if (stateTicks >= State.CORE_CHARGE.duration) {
            beamAim = target != null ? target.getBoundingBox().getCenter().subtract(core).normalize() : forward();
            shake(20);
            playSound(SoundEvents.GENERIC_EXPLODE, 3f, 1.6f);
            setState(State.CORE_BEAM);
        }
    }

    /**
     * Core beam (2.8 s): a thick hextech beam from the chest core, slowly tracking the target. Whatever stands in it takes
     * heavy damage every 4 ticks and catches fire; where it hits the ground or a wall it drills through stone-hard
     * blocks (mobGriefing). Then the core burns out: OVERLOAD.
     */
    private void tickCoreBeam(@Nullable LivingEntity target) {
        holdStill();
        Vec3 core = corePosition();
        if (target != null) {
            Vec3 want = target.getBoundingBox().getCenter().subtract(core).normalize();
            beamAim = beamAim.lerp(want, 0.06).normalize();
            faceTowards(core.add(beamAim.scale(10)), 3f);
        }
        if (beamAim.lengthSqr() < 1e-4) {
            beamAim = forward();
        }
        double range = 48;
        Vec3 end = core.add(beamAim.scale(range));
        BlockHitResult wall = level().clip(new ClipContext(core, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        boolean hitWall = wall.getType() != HitResult.Type.MISS;
        if (hitWall) {
            end = wall.getLocation();
        }
        this.entityData.set(DATA_BEAM, new Vector3f((float) end.x, (float) end.y, (float) end.z));
        float sc = getModelScale();
        if (stateTicks % 4 == 0) {
            for (LivingEntity victim : level().getEntitiesOfClass(LivingEntity.class, new AABB(core, end).inflate(2), this::canHit)) {
                if (distanceToSegment(victim.getBoundingBox().getCenter(), core, end) <= victim.getBbWidth() * 0.5 + 0.9 * sc) {
                    victim.invulnerableTime = 0;
                    DamageSources.applyDamage(victim, dmg(10f), SpellRegistry.FIREBOLT_SPELL.get().getDamageSource(this, this));
                    victim.setSecondsOnFire(8);
                }
            }
        }
        if (hitWall && stateTicks % 3 == 0) {
            breakBlocks(new AABB(end, end).inflate(1.3), BEAM, 24);
        }
        if (stateTicks % 2 == 0) {
            MagicManager.spawnParticles(level(), ParticleTypes.FLAME, end.x, end.y, end.z, 10, 0.6, 0.6, 0.6, 0.08, false);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, end.x, end.y, end.z, 8, 0.6, 0.6, 0.6, 0.3, false);
        }
        if (stateTicks % 7 == 0) {
            ringFacing(core.add(beamAim.scale(2 * sc)), 1.6f * sc, 6, 1);
            ring(new Vec3(end.x, end.y + 0.1, end.z), 2.5f * sc, 8, 1);
            playSound(SoundEvents.BEACON_AMBIENT, 4f, 1.6f);
            level().playSound(null, end.x, end.y, end.z, SoundEvents.FIRECHARGE_USE, getSoundSource(), 2.5f, 0.6f);
        }
        if (stateTicks % 10 == 0) {
            shake(8);
        }
        if (stateTicks >= State.CORE_BEAM.duration) {
            playSound(SoundEvents.FIRE_EXTINGUISH, 4f, 0.5f);
            setState(State.OVERLOAD);
        }
    }

    /** Overload: the core is spent - the glow dies (drained texture), it slumps venting steam, open to punishment. */
    private void tickOverload() {
        holdStill();
        if (stateTicks == 1) {
            Vec3 core = corePosition();
            ring(position().add(0, 0.3, 0), 5 * getModelScale(), 12, 2);
            MagicManager.spawnParticles(level(), ParticleTypes.LARGE_SMOKE, core.x, core.y, core.z, 30, 1.5, 1, 1.5, 0.05, true);
            playSound(SoundEvents.REDSTONE_TORCH_BURNOUT, 4f, 0.5f);
        }
        if (stateTicks % 4 == 0) {
            MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), getX(), getY() + getBbHeight() * 0.6, getZ(), 6, 2 * getModelScale(), 0.5, 2 * getModelScale(), 0.05, false);
        }
        if (stateTicks >= State.OVERLOAD.duration) {
            afterGroundAttack(10);
        }
    }

    /** Something the dragon would attack within reach of its tail (the hitbox of the back half of the tail, plus the
     * sweep of a lash), or null. */
    @Nullable
    protected LivingEntity preyAtTail() {
        // each tail segment on its own (a union of the boxes plus a wide margin reached the flanks beside the hips),
        // a margin of a lash's reach, and well behind the body's centre
        float sc = getModelScale();
        LivingEntity best = null;
        double bestD = Double.MAX_VALUE;
        for (int i = DragonTracks.R_TAIL_B; i <= DragonTracks.R_TAIL_D; i++) {
            AABB zone = parts[i].getBoundingBox().inflate(1.2 * sc, 1.0 * sc, 1.2 * sc);
            for (LivingEntity e : level().getEntitiesOfClass(LivingEntity.class, zone, this::isPrey)) {
                if (local(e.position()).z > -30) {
                    continue;   // beside the hips or further forward: not the tail's business
                }
                double d = distanceToSqr(e);
                if (d < bestD) {
                    bestD = d;
                    best = e;
                }
            }
        }
        return best;
    }

    /** Rider's bite while flying (the drake). */
    protected void tickAirBite() {
        if (stateTicks >= 6 && stateTicks <= 8) {
            Vec3 jaws = mouthPosition();
            hitSphere(jaws, 1.8 * getModelScale(), dmg(20f), null, 0.6, 0.2);
        }
        if (stateTicks == 6) {
            playSound(SoundEvents.EVOKER_FANGS_ATTACK, 2f, 0.7f);
        }
        if (stateTicks >= State.AIR_BITE.duration) {
            onRiderActionEnd();
        }
    }

    /* ---------------------------------------------------------------- phase two, pylons, stun */

    private void tickPhaseTwo() {
        if (!onGround()) {
            setDeltaMovement(getDeltaMovement().multiply(0.6, 1, 0.6).add(0, -0.08, 0));
        } else {
            holdStill();
        }
        if (stateTicks % 8 == 0) {
            shake(12);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRICITY, getX(), getY() + 3, getZ(), 30, 3, 2, 3, 0.2, true);
            double a = random.nextDouble() * Math.PI * 2;
            visualLightning(getX() + Math.cos(a) * 7, getZ() + Math.sin(a) * 7);
        }
        if (stateTicks == 20) {
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 6f, 0.7f);
        }
        if (stateTicks == 52) {
            empBlast(14, 10f);
        }
        if (stateTicks >= State.PHASE_TWO.duration) {
            groundTicks = 200;
            attackCooldown = 10;
            setState(State.GROUND);
        }
    }

    private Vec3 pylonCentre() {
        Vec3 c = home != null ? Vec3.atBottomCenterOf(home) : position();
        if (c.distanceTo(position()) > 80) {
            c = position();
        }
        return new Vec3(c.x, floorBelow(c.x, c.y + 4, c.z), c.z);
    }

    private void tickPylonGo() {
        Vec3 centre = pylonCentre();
        float scale = Math.max(1, getModelScale());
        if (stateTicks == 1 && getState().grounded()) {
            setDeltaMovement(getDeltaMovement().add(0, 0.6, 0));
        }
        Vec3 flat = new Vec3(centre.x - getX(), 0, centre.z - getZ());
        if (flat.length() > 3 * scale && stateTicks < 200) {
            steer(centre.add(0, 8 * scale, 0), 0.8 * scale, 6f);
        } else {
            setDeltaMovement(getDeltaMovement().multiply(0.7, 0, 0.7).add(flat.scale(0.04)).add(0, -0.25 * scale, 0));
            double ground = groundBelow();
            if (getY() - ground <= 0.3 || stateTicks > 300) {
                setPos(getX(), ground, getZ());
                setDeltaMovement(Vec3.ZERO);
                crashBlast(0.7, false);
                raisePylons();
                setState(State.PYLON_CHARGE);
            }
        }
    }

    private void raisePylons() {
        pylons.clear();
        double r = 28;
        for (int i = 0; i < 4; i++) {
            double a = Math.toRadians(getYRot() + 45 + i * 90);
            double x = getX() + Math.cos(a) * r;
            double z = getZ() + Math.sin(a) * r;
            level().getChunkAt(BlockPos.containing(x, getY(), z));
            HextechPylon pylon = new HextechPylon(level(), this);
            pylon.moveTo(x, groundNear(x, z), z, 0, 0);
            level().addFreshEntity(pylon);
            pylons.add(pylon.getUUID());
            visualLightning(x, z);
        }
        playSound(TechSounds.TECH_DRAGON_ROAR.get(), 6f, 0.6f);
        playSound(SoundEvents.BEACON_ACTIVATE, 6f, 0.5f);
        shake(40);
        pylonEvent.setVisible(true);
        pylonEvent.setProgress(1f);
    }

    private List<HextechPylon> livePylons() {
        List<HextechPylon> out = new ArrayList<>();
        if (level() instanceof ServerLevel server) {
            for (UUID id : pylons) {
                if (server.getEntity(id) instanceof HextechPylon p && p.isAlive() && !p.isCollapsing()) {
                    out.add(p);
                }
            }
        }
        return out;
    }

    private void tickPylonCharge(@Nullable LivingEntity target) {
        holdStill();
        if (target != null) {
            lookTowards(target.getEyePosition());
        }
        List<HextechPylon> alive = livePylons();
        int timeLeft = State.PYLON_CHARGE.duration - stateTicks;
        pylonEvent.setName(Component.translatable("bossbar.iss_technomancy.pylons", alive.size(), 4, Math.max(0, timeLeft / 20)));
        pylonEvent.setProgress(Mth.clamp(timeLeft / (float) PYLON_TIME, 0, 1));
        if (stateTicks % 10 == 0) {
            Vec3 core = corePosition();
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRICITY, core.x, core.y, core.z, 10, 1.5, 1.5, 1.5, 0.2, false);
        }
        if (stateTicks > PYLON_RISE && alive.isEmpty()) {
            // every pylon down: the shield shatters and the dragon reels
            setShielded(false);
            pylonEvent.setVisible(false);
            playSound(SoundEvents.GLASS_BREAK, 6f, 0.5f);
            playSound(SoundEvents.ANVIL_LAND, 4f, 0.4f);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + getBbHeight() * 0.6, getZ(), 150, 6, 4, 6, 0.6, true);
            MagicManager.spawnParticles(level(), ParticleTypes.END_ROD, getX(), getY() + getBbHeight() * 0.6, getZ(), 120, 8, 5, 8, 0.3, true);
            shake(30);
            stun(80);
            return;
        }
        if (stateTicks >= State.PYLON_CHARGE.duration) {
            int n = alive.size();
            heal(getMaxHealth() * 0.08f * n);
            for (HextechPylon p : alive) {
                p.collapse();
            }
            setShielded(false);
            pylonEvent.setVisible(false);
            empBlast(22, 14f);
            for (int i = 0; i < 10; i++) {
                double a = i * Math.PI / 5;
                strike(new Vec3(getX() + Math.cos(a) * 14, 0, getZ() + Math.sin(a) * 14), 10f);
            }
            setState(State.PYLON_FAIL);
        }
    }

    private void tickPylonFail(@Nullable LivingEntity target) {
        holdStill();
        if (target != null && stateTicks < 20) {
            faceTowards(target.getEyePosition(), 6f);
        }
        if (stateTicks == 10) {
            playSound(TechSounds.TECH_DRAGON_ROAR.get(), 6f, 0.75f);
            shake(25);
        }
        if (stateTicks >= State.PYLON_FAIL.duration) {
            groundTicks = 200;
            setState(State.GROUND);
        }
    }

    private void tickStunned() {
        setNoGravity(false);
        this.noPhysics = false;
        if (stateTicks % 4 == 0) {
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + getBbHeight() * 0.4, getZ(), 6, 2, 1, 2, 0.15, false);
        }
        setDeltaMovement(getDeltaMovement().multiply(0.6, 1, 0.6));
        if (stateTicks >= stunLength) {
            groundTicks = 160;
            setState(isBoss() ? State.GROUND : State.TAKEOFF);
        }
    }

    protected void visualLightning(double x, double z) {
        LightningBolt bolt = EntityType.LIGHTNING_BOLT.create(level());
        if (bolt != null) {
            bolt.moveTo(x, surfaceUnder(new Vec3(x, getY(), z)), z);
            bolt.setVisualOnly(true);
            level().addFreshEntity(bolt);
        }
    }

    /* ---------------------------------------------------------------- client */

    private void clientEffects() {
        State state = getState();
        float s = getModelScale();
        if (state == State.DEATH) {
            if (random.nextInt(2) == 0) {
                Vec3 c = position().add(0, 1.5 * s, 0);
                level().addParticle(ParticleTypes.ELECTRIC_SPARK, c.x + (random.nextDouble() - 0.5) * 6 * s, c.y + random.nextDouble() * 2 * s,
                        c.z + (random.nextDouble() - 0.5) * 6 * s, 0, 0.05, 0);
            }
            return;
        }
        if (random.nextInt(isPhaseTwo() ? 2 : 5) == 0) {
            level().addParticle(TechParticles.ARC_MOTE.get(), getRandomX(2.0), getY() + (1 + random.nextDouble() * 2.5) * s, getRandomZ(2.0), 0, 0.02, 0);
        }
        if (isShielded() && random.nextInt(2) == 0) {
            double a = random.nextDouble() * Math.PI * 2, b = random.nextDouble() * Math.PI;
            double r = 7.5 * s;
            Vec3 c = position().add(0, 2.0 * s, 0);
            level().addParticle(ParticleTypes.END_ROD, c.x + Math.cos(a) * Math.sin(b) * r, c.y + Math.cos(b) * r * 0.8, c.z + Math.sin(a) * Math.sin(b) * r, 0, 0, 0);
        }
    }

    /* ---------------------------------------------------------------- damage & death */

    @Override
    public boolean hurt(@NotNull DamageSource source, float amount) {
        if (isShielded() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            if (!level().isClientSide && source.getEntity() != null && tickCount % 4 == 0) {
                playSound(SoundEvents.SHIELD_BLOCK, 2f, 0.6f);
                Vec3 at = source.getSourcePosition() != null ? source.getSourcePosition() : position();
                MagicManager.spawnParticles(level(), ParticleTypes.END_ROD, at.x, at.y + 1, at.z, 6, 0.5, 0.5, 0.5, 0.05, false);
            }
            return false;
        }
        if (isInvulnerableState() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return false;
        }
        if (source.getEntity() == this || source.is(DamageTypeTags.IS_LIGHTNING) || source.is(DamageTypeTags.IS_FALL) || source.getEntity() instanceof HextechPylon
                || source.is(net.minecraft.world.damagesource.DamageTypes.IN_WALL) || source.is(net.minecraft.world.damagesource.DamageTypes.CRAMMING)
                || source.is(net.minecraft.world.damagesource.DamageTypes.DROWN)) {
            return false;
        }
        Entity attacker = source.getEntity();
        if (attacker != null && (isAlliedTo(attacker) || hasPassenger(attacker) && !isCarrying(attacker))) {
            return false;
        }
        if (getState() == State.STUNNED || getState() == State.EMP_STUN || getState() == State.OVERLOAD) {
            amount *= 1.3f;
        }
        if (!level().isClientSide && attacker instanceof LivingEntity living && living != this && canHit(living)) {
            aggroTarget = living;
            aggroTicks = 600;
            if (getState() == State.GROUND && dodgeCooldown <= 0 && source.getDirectEntity() == living && random.nextInt(4) == 0) {
                pendingDodge = 10;
            }
            if (getState() == State.SLEEP) {
                setTarget(living);
                setState(State.WAKE);
            } else if (getState() == State.PERCH || getState() == State.LIE_DOWN) {
                setTarget(living);
                leavePerch(State.GROUND_ROAR);
            }
        }
        return super.hurt(source, Math.min(amount, MAX_DAMAGE_PER_HIT));
    }

    /** Pull and grab effects (Rocket Grab, magnetic pulls, ...) cannot move it. */
    @Override
    public void push(double x, double y, double z) {
    }

    @Override
    public boolean isPushedByFluid() {
        return false;
    }

    @Override
    public boolean isAlliedTo(@NotNull Entity entity) {
        return super.isAlliedTo(entity) || (isBoss() && (entity instanceof ClockworkAutomaton drone && !drone.isAssembled() || entity instanceof HextechPylon
                || entity instanceof TechDragon other && other.isBoss()));
    }

    @Override
    public void die(@NotNull DamageSource source) {
        releaseGrabbed(Vec3.ZERO);
        deathSource = source;
        if (isBoss()) {
            for (HextechPylon p : livePylons()) {
                p.collapse();
            }
            pylonEvent.setVisible(false);
        }
        super.die(source);
        setShielded(false);
        setState(State.DEATH);
        setNoGravity(false);
        this.noPhysics = false;
        bossEvent.setProgress(0f);
        playSound(TechSounds.TECH_DRAGON_DEATH.get(), 6f * getModelScale(), 0.8f);
        shake(40);
    }

    @Override
    protected boolean shouldDropLoot() {
        return !isBoss() || lootReleased;
    }

    @Override
    protected void tickDeath() {
        deathTime++;
        setDeltaMovement(getDeltaMovement().multiply(0.6, 1, 0.6));
        if (level().isClientSide) {
            return;
        }
        if (!isBoss()) {
            if (deathTime >= 40) {
                MagicManager.spawnParticles(level(), ParticleTypes.EXPLOSION, getX(), getY() + 1, getZ(), 3, 1, 1, 1, 0, true);
                remove(RemovalReason.KILLED);
            }
            return;
        }
        if (deathTime % 10 == 0 && deathTime < 90) {
            Vec3 c = position().add(0, getBbHeight() * 0.4, 0);
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, c.x, c.y, c.z, 24, 3, 2, 3, 0.3, true);
            playSound(SoundEvents.LIGHTNING_BOLT_IMPACT, 3f, 0.8f + random.nextFloat() * 0.3f);
        }
        if (deathTime == 90 && !shellSpawned) {
            shellSpawned = true;
            Vec3 centre = DragonTracks.toWorld(new Vec3(-4, 24, -16), position(), yBodyRot, 0, getModelScale());
            HextechShell shell = new HextechShell(level(), this);
            shell.moveTo(centre.x, centre.y - HextechShell.RADIUS, centre.z, yBodyRot, 0);
            level().addFreshEntity(shell);
        }
        if (deathTime >= 90 + HextechShell.LIFETIME + 20) {
            releaseLoot();
            remove(RemovalReason.KILLED);
        }
    }

    /** Called by the shell when it bursts: the hoard drops after the explosion, not inside it. */
    public void releaseLoot() {
        if (lootReleased || level().isClientSide) {
            return;
        }
        lootReleased = true;
        lastHurtByPlayerTime = 100;
        dropAllDeathLoot(deathSource != null ? deathSource : damageSources().generic());
    }

    @Override
    public void remove(@NotNull RemovalReason reason) {
        releaseGrabbed(Vec3.ZERO);
        super.remove(reason);
        if (!level().isClientSide) {
            bossEvent.removeAllPlayers();
            pylonEvent.removeAllPlayers();
        }
    }

    @Override
    public boolean causeFallDamage(float distance, float multiplier, @NotNull DamageSource source) {
        return false;
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public boolean canChangeDimensions() {
        return false;
    }

    @Override
    public boolean canBeAffected(@NotNull MobEffectInstance effect) {
        return effect.getEffect().isBeneficial() && super.canBeAffected(effect);
    }

    @Override
    protected boolean shouldDespawnInPeaceful() {
        return false;
    }

    public boolean shouldShowName() {
        return !isBoss() && hasCustomName();
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return TechSounds.TECH_DRAGON_AMBIENT.get();
    }

    @Override
    protected SoundEvent getHurtSound(@NotNull DamageSource source) {
        return TechSounds.TECH_DRAGON_HURT.get();
    }

    @Override
    protected SoundEvent getDeathSound() {
        return null;
    }

    @Override
    protected float getSoundVolume() {
        return 4f * getModelScale();
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() / Math.max(0.5f, getModelScale());
    }

    @Override
    public int getAmbientSoundInterval() {
        return 180;
    }

    /* ---------------------------------------------------------------- persistence */

    @Override
    public void addAdditionalSaveData(@NotNull CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (home != null) {
            tag.put("Home", NbtUtils.writeBlockPos(home));
        }
        tag.putBoolean("PhaseTwo", isPhaseTwo());
        tag.putBoolean("PylonsDone", pylonsDone);
        tag.putInt("State", getState() == State.SPAWN ? State.SPAWN.ordinal() : State.HOVER.ordinal());
    }

    @Override
    public void readAdditionalSaveData(@NotNull CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.contains("Home")) {
            home = NbtUtils.readBlockPos(tag.getCompound("Home"));
        }
        setPhaseTwo(tag.getBoolean("PhaseTwo"));
        pylonsDone = tag.getBoolean("PylonsDone");
        if (tag.contains("State")) {
            setState(State.values()[Mth.clamp(tag.getInt("State"), 0, State.values().length - 1)]);
        }
        if (hasCustomName()) {
            bossEvent.setName(getDisplayName());
        }
        if (isPhaseTwo()) {
            bossEvent.setColor(BossEvent.BossBarColor.BLUE);
        }
    }

    /* ---------------------------------------------------------------- animation */

    /** The animation for the current state (the same on the client, which plays it, and the server, which samples its
     * baked tracks for hitboxes and attacks). */
    public String animationName() {
        State s = getState();
        double speed = horizontalSpeedSqr() / Math.max(0.25, getModelScale() * getModelScale() / 4);
        boolean air = !onGround() && !s.grounded() || s == State.RIDDEN && isFlyingMount();
        return switch (s) {
            case SPAWN -> "roar_air";
            case HOVER, PYLON_GO, SKY_RISE -> flightAnimation();
            case LANDING -> isBoss() && getAttackVariant() == 1 ? (getY() - groundBelow() < 3 * getModelScale() + 4 ? "dive" : flightAnimation())
                    : getY() - groundBelow() < 7 * getModelScale() ? "land" : flightAnimation();
            case TAKEOFF -> "takeoff";
            case PERCH -> speed > 0.004 ? "walk" : switch (getIdleVariant()) {
                case 1 -> "sit";
                case 2 -> "rest";
                default -> "ground_idle";
            };
            case LIE_DOWN -> "lie_down";
            case REST_UP -> "rest_up";
            case SLEEP -> "sleep";
            case WAKE -> "wake";
            case GROUND -> speed > 0.03 ? "run" : speed > 0.002 ? "walk" : "ground_idle";
            case BITE -> "bite";
            case BITE_SWEEP -> "bite_sweep";
            case CLAW -> getAttackVariant() == 1 ? "claw_right" : "claw_left";
            case GRAB -> "grab";
            case GRAB_HOLD -> "grab_shake";
            case GRAB_TOSS -> "grab_toss";
            case TAIL_WHIP -> getAttackVariant() == 1 ? "tail_whip_right" : "tail_whip";
            case TAIL_SWEEP -> "tail_sweep";
            case STOMP -> "stomp";
            case WING_GUST -> "wing_gust";
            case FIELD_ROAR -> "field_roar";
            case REND -> stateTicks < 10 || stateTicks >= 40 ? "ground_idle" : "rend";
            case GBREATH_CHARGE -> "breath_charge_ground";
            case GBREATH -> "breath_ground";
            case GROUND_ROAR, PYLON_FAIL -> "roar";
            case SLAM -> "slam";
            case COG_SPIT, ARC_BARRAGE -> "cog_spit";
            case BREATH_CHARGE -> air ? "breath_charge" : "breath_charge_ground";
            case BREATH -> air ? "breath" : "breath_ground";
            case THUNDER -> "thunder";
            case ROAR -> air ? "roar_air" : "roar";
            case SWOOP -> "swoop";
            case DIVE_RISE -> "fly_fast";
            case DIVE, SKY_DIVE -> "dive";
            case SUMMON, EMP -> "roar_air";
            case AIR_BITE -> "air_bite";
            case POUNCE -> "pounce";
            case DASH_CLAW -> getAttackVariant() == 1 ? "dash_claw_right" : "dash_claw_left";
            case DODGE -> getAttackVariant() == 1 ? "dodge_right" : "dodge_left";
            case RAM -> stateTicks < 8 ? "ground_idle" : "ram";
            case STORM_RISE -> "fly_fast";
            case STORM -> "storm";
            case DIVE_BOUNCE -> "dive_bounce";
            case PHASE_TWO -> "phase_two";
            case PYLON_CHARGE -> "pylon_charge";
            case STUNNED -> "stunned";
            case RIDDEN -> isFlyingMount() ? (flightPitch < -40 ? "dive" : flightAnimation()) : speed > 0.03 ? "run" : speed > 0.002 ? "walk" : "ground_idle";
            case DEATH -> "death";
            case BACKSTEP -> "backstep";
            case WING_PUSH -> "wing_push";
            case KITE_HOP -> getAttackVariant() == 1 ? "dodge_right" : "dodge_left";
            case SPIT -> "spit";
            case CRASH -> "crash_land";
            case EMP_STUN -> "emp_stunned";
            case PIN -> "pin_gnaw";
            case CARRY -> "carry";
            case CORE_CHARGE -> "core_charge";
            case CORE_BEAM -> "core_beam";
            case OVERLOAD -> "overload";
            case SPIN -> "spin_discharge";
            case HOP -> switch (getAttackVariant()) {
                case 1 -> "hop_back";
                case 2 -> "dodge_left";
                case 3 -> "dodge_right";
                default -> "hop_forward";
            };
            case SKY_BREATH -> stateTicks < 24 ? "breath_charge" : "breath_down";
            case STRAFE -> stateTicks < 22 ? flightAnimation() : "strafe";
            case RIDER_LAND -> "land";
        };
    }

    private String flightAnim = "fly";
    private int flightAnimTicks;
    private int flightAnimTick = -1;

    protected String flightAnimation() {
        if (flightAnimTick == tickCount) {
            return flightAnim;
        }
        flightAnimTick = tickCount;
        flightAnimTicks++;
        double s = Math.max(0.5, getModelScale());
        double v = Math.sqrt(horizontalSpeedSqr()) / s;
        double climb = (getY() - yo) / s;
        String want = v > 0.62 || climb > 0.22 ? "fly_fast" : v > 0.1 ? (climb < -0.05 ? "glide" : "fly") : "hover";
        if (!want.equals(flightAnim) && flightAnimTicks > 30) {
            flightAnim = want;
            flightAnimTicks = 0;
        }
        return flightAnim;
    }

    /** Playback speed so feet match the ground speed. */
    protected double animationSpeed(String anim) {
        double v = Math.sqrt(horizontalSpeedSqr());
        double unit = getModelScale() / 16.0 / 20.0;
        return switch (anim) {
            case "walk" -> Mth.clamp(v / (13.75 * unit), 0.5, 2.2);
            case "run" -> Mth.clamp(v / (42.5 * unit), 0.6, 1.8);
            case "rend" -> Mth.clamp(v / (45.7 * unit), 0.6, 1.8);
            case "ram" -> Mth.clamp(v / (63.3 * unit), 0.6, 1.8);
            default -> 1.0;
        };
    }

    protected double horizontalSpeedSqr() {
        double dx = getX() - xo;
        double dz = getZ() - zo;
        return dx * dx + dz * dz;
    }

    private static RawAnimation raw(String name) {
        return ANIMS.computeIfAbsent(name, n -> switch (n) {
            case "ground_idle", "walk", "run", "rest", "sleep", "sit", "fly", "fly_fast", "glide", "hover", "dive", "rend", "grab_shake",
                    "breath", "breath_ground", "pylon_charge", "stunned", "ram", "storm", "carry", "core_beam" -> RawAnimation.begin().thenLoop(n);
            default -> RawAnimation.begin().thenPlayAndHold(n);
        });
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 5, state -> {
            int serial = this.entityData.get(DATA_SERIAL);
            String name = animationName();
            if (serial != clientSerial) {
                clientSerial = serial;
                state.getController().forceAnimationReset();
            }
            state.getController().setAnimationSpeed(animationSpeed(name));
            return state.setAndContinue(raw(name));
        }));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
