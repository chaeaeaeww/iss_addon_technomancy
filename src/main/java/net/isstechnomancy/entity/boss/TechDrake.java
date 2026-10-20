package net.isstechnomancy.entity.boss;

import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.entity.mobs.AntiMagicSusceptible;
import io.redspace.ironsspellbooks.entity.mobs.IMagicSummon;
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.UUID;

/**
 * Summoned Tech Dragon ("Stage 3": ~11 blocks long against the boss's 26), called by the boss-only scroll.
 * Lives for 3/4/5 minutes (spell level), one per caster, about 40% of the boss's damage.
 *
 * <p>Riding (owner right-clicks it): WASD moves (holding forward speeds up into a run / fast flight), Space takes off and climbs, the Descend key
 * (Left Ctrl by default) sinks and lands; 1.10: tapping Space when flying low lands it (the landing animation), and
 * diving (looking steeply down) builds up speed that carries into the pull-up, the body pitching down with the dive.
 * Left click bites or rakes (bites in the air), hold Right click (or C) for the lightning breath, Z bites, X rakes,
 * V calls a lightning storm around it (30 s cooldown), R for Thunder Roar, G to seize something in the jaws and shake it. The rider's client moves
 * the dragon (like a horse or boat); the server runs the attacks from the packets in
 * {@link net.isstechnomancy.network.TechNetwork}.</p>
 *
 * <p>Without a rider it fights whatever its owner fights from the air and settles down near the owner otherwise.</p>
 */
public class TechDrake extends TechDragon implements OwnableEntity, AntiMagicSusceptible {
    public static final float SCALE = 0.85f;
    public static final float OVERCHARGED_SCALE = 1.0f;

    public enum Action { ATTACK, ROAR, GRAB, BITE, CLAW, STORM }

    /** Synced so the rider's client knows it controls this drake. */
    private static final net.minecraft.network.syncher.EntityDataAccessor<java.util.Optional<UUID>> DATA_OWNER =
            net.minecraft.network.syncher.SynchedEntityData.defineId(TechDrake.class, net.minecraft.network.syncher.EntityDataSerializers.OPTIONAL_UUID);

    @Nullable
    private UUID ownerUUID;
    @Nullable
    private LivingEntity cachedOwner;
    private int lifeTicks = 20 * 180;
    private float power = 1f;
    /* rider input: set on the server by packets, on the rider's client by the input handler */
    public boolean inputUp, inputDown, inputSprint, inputBreath;
    private int roarCooldown, attackCooldownR, landTicks;
    /** Ticks the rider has held forward: walking turns into running, flying into fast flight (no sprint key needed). */
    private int forwardTicks;
    private boolean clawNext;
    /* 1.10 */
    private int flyTicks, takeoffLock, stormTicks, stormCooldown;
    private boolean prevInputUp;
    /** Speed built up by diving (client side, where the rider moves the drake). */
    private double diveBoost;

    public TechDrake(EntityType<? extends TechDrake> type, Level level) {
        super(type, level);
        this.xpReward = 0;
    }

    public TechDrake(Level level, LivingEntity owner, float power, int health, int lifetime, boolean overcharged) {
        this(TechEntities.TECH_DRAKE.get(), level);
        setOwnerId(owner.getUUID());
        this.cachedOwner = owner;
        this.power = power;
        this.lifeTicks = lifetime;
        setModelScale(overcharged ? OVERCHARGED_SCALE : SCALE);
        setPhaseTwo(overcharged);
        AttributeInstance hp = getAttribute(Attributes.MAX_HEALTH);
        if (hp != null) {
            hp.setBaseValue(health);
        }
        setHealth(health);
        setState(State.TAKEOFF);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_OWNER, java.util.Optional.empty());
    }

    private void setOwnerId(@Nullable UUID id) {
        ownerUUID = id;
        this.entityData.set(DATA_OWNER, java.util.Optional.ofNullable(id));
    }

    public static AttributeSupplier.Builder createDrakeAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 120)
                .add(Attributes.ARMOR, 10)
                .add(Attributes.ARMOR_TOUGHNESS, 4)
                .add(Attributes.ATTACK_DAMAGE, 8)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.9)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 40);
    }

    @Override
    public SpawnGroupData finalizeSpawn(@NotNull ServerLevelAccessor level, @NotNull DifficultyInstance difficulty, @NotNull MobSpawnType reason,
                                        @Nullable SpawnGroupData data, @Nullable CompoundTag tag) {
        home = blockPosition();
        if (getModelScale() > OVERCHARGED_SCALE + 0.01f) {
            setModelScale(SCALE);
        }
        setState(State.TAKEOFF);
        return data;
    }

    @Override
    protected float defaultScale() {
        return SCALE;
    }

    /** ~40% of the boss at base spell power; overcharged x1.3. */
    @Override
    protected float damageScale() {
        return 0.4f * power * (isPhaseTwo() ? 1.3f : 1f);
    }

    @Override
    protected boolean isBoss() {
        return false;
    }

    /* ---------------------------------------------------------------- ownership */

    @Nullable
    @Override
    public UUID getOwnerUUID() {
        return level().isClientSide ? this.entityData.get(DATA_OWNER).orElse(null) : ownerUUID;
    }

    @Nullable
    @Override
    public LivingEntity getOwner() {
        if (cachedOwner != null && !cachedOwner.isRemoved()) {
            return cachedOwner;
        }
        if (ownerUUID != null && level() instanceof ServerLevel server && server.getEntity(ownerUUID) instanceof LivingEntity living) {
            cachedOwner = living;
            return living;
        }
        if (getOwnerUUID() != null && level().isClientSide) {
            Player p = level().getPlayerByUUID(getOwnerUUID());
            if (p != null) {
                cachedOwner = p;
            }
            return p;
        }
        return null;
    }

    public boolean isOwnedBy(Entity e) {
        UUID id = getOwnerUUID();
        return e != null && id != null && id.equals(e.getUUID());
    }

    @Override
    public void onAntiMagic(MagicData playerMagicData) {
        dismiss();
    }

    public void dismiss() {
        if (!level().isClientSide && !isRemoved()) {
            ejectPassengers();
            MagicManager.spawnParticles(level(), ParticleHelper.ELECTRIC_SPARKS, getX(), getY() + 1, getZ(), 30, 1, 1, 1, 0.3, false);
            MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), getX(), getY() + 1, getZ(), 16, 1, 0.6, 1, 0.04, false);
            discard();
        }
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

    /* ---------------------------------------------------------------- riding */

    public boolean isRiddenByOwner() {
        return getControllingPassenger() != null;
    }

    @Nullable
    @Override
    public LivingEntity getControllingPassenger() {
        for (Entity e : getPassengers()) {
            if (e instanceof Player p && isOwnedBy(p) && !isCarrying(p)) {
                return p;
            }
        }
        return null;
    }

    @Override
    protected boolean isVehicleRider(Entity passenger) {
        return isOwnedBy(passenger);
    }

    @Override
    protected boolean canAddPassenger(@NotNull Entity passenger) {
        if (isOwnedBy(passenger)) {
            return getControllingPassenger() == null;
        }
        return super.canAddPassenger(passenger);
    }

    @Override
    public @NotNull InteractionResult mobInteract(@NotNull Player player, @NotNull InteractionHand hand) {
        if (isOwnedBy(player) && !player.isSecondaryUseActive() && !isVehicle() && getState() != State.DEATH) {
            if (!level().isClientSide) {
                player.startRiding(this);
                setState(State.RIDDEN);
                setTarget(null);
            }
            return InteractionResult.sidedSuccess(level().isClientSide);
        }
        return super.mobInteract(player, hand);
    }

    @Override
    protected void removePassenger(@NotNull Entity passenger) {
        super.removePassenger(passenger);
        if (!level().isClientSide && isOwnedBy(passenger) && getState() == State.RIDDEN) {
            setState(isFlyingMount() ? State.HOVER : State.PERCH);
            this.entityData.set(DATA_FLYING, false);
        }
    }

    @Override
    protected void applyPhysics(State state) {
        if (isRiddenByOwner()) {
            setNoGravity(isFlyingMount());
            this.noPhysics = false;
            setMaxUpStep(1.0f + getModelScale() * 0.6f);
            return;
        }
        super.applyPhysics(state);
    }

    /** The drake follows where the rider looks, turning at a dragon-ish rate. */
    @Override
    protected void tickRidden(@NotNull Player player, @NotNull Vec3 input) {
        super.tickRidden(player, input);
        float yaw = Mth.approachDegrees(getYRot(), player.getYRot(), isFlyingMount() ? 6f : 9f);
        setYRot(yaw);
        yBodyRot = yaw;
        yHeadRot = player.getYHeadRot();
        setXRot(player.getXRot() * 0.5f);
    }

    @Override
    protected @NotNull Vec3 getRiddenInput(@NotNull Player player, @NotNull Vec3 input) {
        float forward = player.zza;
        if (forward < 0) {
            forward *= 0.35f;
        }
        return new Vec3(player.xxa * 0.4f, 0, forward);
    }

    @Override
    protected float getRiddenSpeed(@NotNull Player player) {
        float base = (float) getAttributeValue(Attributes.MOVEMENT_SPEED);
        float boost = Mth.clamp((forwardTicks - 10) / 30f, 0f, 1f);
        return base * Mth.lerp(boost, 0.6f, 1.3f) * Math.max(1f, getModelScale());
    }

    @Override
    public void travel(@NotNull Vec3 input) {
        if (isRiddenByOwner() && isControlledByLocalInstance()) {
            forwardTicks = input.z > 0.1 ? forwardTicks + 1 : 0;
        }
        if (isRiddenByOwner() && isFlyingMount() && isControlledByLocalInstance()) {
            Player rider = (Player) getControllingPassenger();
            if (getState() == State.RIDER_LAND) {
                // settling down: drift on and sink to the ground
                setDeltaMovement(getDeltaMovement().multiply(0.85, 0, 0.85).add(0, -0.32 * Math.max(1, getModelScale()), 0));
                move(MoverType.SELF, getDeltaMovement());
                calculateEntityAnimation(true);
                return;
            }
            float pitch = rider.getXRot();
            // like Saint's Dragons: looking steeply down dives (the body follows, see updatePose) and the dive builds up
            // speed; pulling out keeps the momentum for a while
            if (pitch > 25 && input.z > 0) {
                diveBoost = Math.min(1.6, diveBoost + 0.045 * (pitch - 25) / 65.0);
            } else {
                diveBoost = Math.max(0, diveBoost - (pitch < -5 ? 0.012 : 0.02));
            }
            Vec3 look = Vec3.directionFromRotation(pitch > 25 ? pitch : pitch * 0.7f, getYRot());
            double speed = Mth.lerp(Mth.clamp((forwardTicks - 10) / 40.0, 0, 1), 0.7, 1.25) * Math.max(1, getModelScale()) * (1 + diveBoost);
            Vec3 want = look.scale(input.z * speed).add(leftDir().scale(-input.x * 0.6));
            double vertical = inputUp ? 0.5 : inputDown ? -0.55 : (input.z == 0 ? 0.0 : 0);
            want = want.add(0, vertical, 0);
            setDeltaMovement(getDeltaMovement().lerp(want, diveBoost > 0.2 ? 0.14 : 0.09));
            move(MoverType.SELF, getDeltaMovement());
            calculateEntityAnimation(true);
            return;
        }
        super.travel(input);
    }

    /* ---------------------------------------------------------------- rider actions (server) */

    /** Packet from the rider: one-shot actions. */
    public void riderAction(Action action) {
        if (!isRiddenByOwner() || getState() != State.RIDDEN && action != Action.STORM) {
            // the storm is called on top of whatever it is doing; the attacks wait for free riding
            return;
        }
        switch (action) {
            case ATTACK -> {
                if (attackCooldownR > 0) {
                    return;
                }
                attackCooldownR = 14;
                if (isFlyingMount()) {
                    setState(State.AIR_BITE);
                } else if (clawNext) {
                    setAttackVariant(random.nextBoolean() ? 0 : 1);
                    setState(State.CLAW);
                } else {
                    setState(State.BITE);
                }
                clawNext = !clawNext;
            }
            case ROAR -> {
                if (roarCooldown > 0) {
                    return;
                }
                roarCooldown = 240;
                setState(State.ROAR);
            }
            case GRAB -> {
                if (isFlyingMount() || grabCooldown > 0) {
                    return;
                }
                setState(State.GRAB);
            }
            case BITE, CLAW -> {
                if (attackCooldownR > 0) {
                    return;
                }
                attackCooldownR = 14;
                if (isFlyingMount()) {
                    setState(State.AIR_BITE);
                } else if (action == Action.CLAW) {
                    setAttackVariant(random.nextBoolean() ? 0 : 1);
                    setState(State.CLAW);
                } else {
                    setState(State.BITE);
                }
            }
            case STORM -> {
                if (stormCooldown > 0) {
                    return;
                }
                stormCooldown = 600;
                stormTicks = 100;
                playSound(TechSounds.TECH_DRAGON_ROAR.get(), 3f, 0.8f);
                playSound(SoundEvents.LIGHTNING_BOLT_THUNDER, 3f, 0.7f);
                ring(position().add(0, 0.5, 0), 4 * getModelScale() + 2, 0, ElectricFx.VIOLET);
            }
        }
    }

    /** Seconds left before the rider's storm can be called again (for the HUD/tests). */
    public int getStormCooldown() {
        return stormCooldown;
    }

    /** The rider's storm (1.10, V): for 5 s bolts fall around the drake - on hostile mobs and on whatever its owner is
     * fighting within ~18 blocks - while the rider keeps flying. */
    private void tickRiderStorm() {
        if (stormTicks <= 0) {
            return;
        }
        stormTicks--;
        if (stormTicks % 5 == 0) {
            LivingEntity owner = getOwner();
            LivingEntity foe = owner != null ? owner.getLastHurtMob() : null;
            java.util.List<LivingEntity> foes = level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(18, 24, 18),
                    e -> canHit(e) && !isAlliedTo(e) && (e instanceof net.minecraft.world.entity.monster.Enemy || e == foe));
            if (!foes.isEmpty()) {
                LivingEntity e = foes.get(random.nextInt(foes.size()));
                strike(e.position(), dmg(9f), floorNear(e.position(), e.getY()));
            } else {
                double a = random.nextDouble() * Math.PI * 2, r = 4 + random.nextDouble() * 12;
                visualLightning(getX() + Math.cos(a) * r, getZ() + Math.sin(a) * r);
            }
        }
        if (stormTicks % 12 == 6) {
            double a = random.nextDouble() * Math.PI * 2, r = 6 + random.nextDouble() * 10;
            visualLightning(getX() + Math.cos(a) * r, getZ() + Math.sin(a) * r);
        }
    }

    @Override
    protected void afterGroundAttack(int cooldown) {
        if (isRiddenByOwner()) {
            setState(State.RIDDEN);
            return;
        }
        super.afterGroundAttack(cooldown);
    }

    @Override
    protected void endAttack(int cooldown) {
        if (isRiddenByOwner()) {
            setState(State.RIDDEN);
            return;
        }
        setState(State.HOVER);
        attackCooldown = cooldown + 20;
    }

    @Override
    protected void onRiderActionEnd() {
        endAttack(30);
    }

    @Override
    protected void tickBreath(@Nullable LivingEntity target) {
        if (isRiddenByOwner()) {
            LivingEntity rider = getControllingPassenger();
            if (rider != null) {
                breathAim = rider.getLookAngle();
            }
            breathBeam(mouthPosition(), breathAim, 20, dmg(7f));
            if (!inputBreath || stateTicks > 90) {
                breathCooldown = 60;
                setState(State.RIDDEN);
            }
            return;
        }
        super.tickBreath(target);
    }

    /* ---------------------------------------------------------------- AI */

    @Override
    public void aiStep() {
        super.aiStep();
        if (level().isClientSide || !isAlive()) {
            return;
        }
        roarCooldown = Math.max(0, roarCooldown - 1);
        attackCooldownR = Math.max(0, attackCooldownR - 1);
        stormCooldown = Math.max(0, stormCooldown - 1);
        takeoffLock = Math.max(0, takeoffLock - 1);
        tickRiderStorm();
        LivingEntity owner = getOwner();
        if (owner == null || !owner.isAlive() || --lifeTicks <= 0) {
            dismiss();
            return;
        }
        if (!isVehicle() && distanceToSqr(owner) > 56 * 56) {
            teleportTo(owner.getX(), owner.getY() + 4, owner.getZ());
        }
        if (isRiddenByOwner()) {
            tickRiderControl();
        }
    }

    private void tickRiderControl() {
        State s = getState();
        boolean flying = isFlyingMount();
        boolean upPressed = inputUp && !prevInputUp;
        prevInputUp = inputUp;
        flyTicks = flying ? flyTicks + 1 : 0;
        if (s == State.RIDER_LAND) {
            if (onGround() || stateTicks > State.RIDER_LAND.duration && getY() - groundBelow() < 0.5) {
                this.entityData.set(DATA_FLYING, false);
                setState(State.RIDDEN);
                applyPhysics(State.RIDDEN);
                takeoffLock = 12;
                playSound(TechSounds.TECH_DRAGON_SLAM.get(), 1.2f, 1.3f);
                MagicManager.spawnParticles(level(), TechParticles.STEAM_PUFF.get(), getX(), getY() + 0.3, getZ(), 10, 1.2, 0.2, 1.2, 0.03, false);
            } else if (stateTicks > 100) {
                setState(State.RIDDEN);
            }
            return;
        }
        // 1.10: flying low, a tap of Space settles it down with the landing animation
        if (flying && s == State.RIDDEN && upPressed && flyTicks > 30 && !onGround() && getY() - groundBelow() < 3.5 * getModelScale() + 1.5) {
            setState(State.RIDER_LAND);
            applyPhysics(State.RIDER_LAND);
            playSound(SoundEvents.ENDER_DRAGON_FLAP, 2f, 0.7f);
            return;
        }
        if (!flying && inputUp && takeoffLock <= 0 && (onGround() || s == State.RIDDEN)) {
            this.entityData.set(DATA_FLYING, true);
            applyPhysics(s);
            playSound(SoundEvents.ENDER_DRAGON_FLAP, 2f, 0.8f);
            landTicks = 0;
        } else if (flying && onGround()) {
            if (inputDown || ++landTicks > 12 && !inputUp) {
                this.entityData.set(DATA_FLYING, false);
                applyPhysics(s);
                playSound(TechSounds.TECH_DRAGON_SLAM.get(), 1f, 1.4f);
            }
        } else {
            landTicks = 0;
        }
        if (s == State.RIDDEN && inputBreath && breathCooldown <= 0) {
            setState(isFlyingMount() ? State.BREATH_CHARGE : State.GBREATH_CHARGE);
            playSound(TechSounds.TECH_DRAGON_CHARGE.get(), 1.5f, 1.2f);
        }
        if ((s == State.BREATH_CHARGE || s == State.GBREATH_CHARGE) && !inputBreath) {
            setState(State.RIDDEN);
        }
        if (s != State.RIDDEN && s != State.RIDER_LAND && s != State.BITE && s != State.CLAW && s != State.AIR_BITE && s != State.ROAR && s != State.GRAB && s != State.GRAB_HOLD
                && s != State.GRAB_TOSS && s != State.BREATH_CHARGE && s != State.GBREATH_CHARGE && s != State.BREATH && s != State.GBREATH
                && s != State.STUNNED && s != State.DEATH) {
            setState(State.RIDDEN);
        }
    }

    @Override
    protected void tickState(State state, @Nullable LivingEntity target) {
        if (isRiddenByOwner() && (state == State.RIDDEN || state == State.RIDER_LAND)) {
            yBodyRot = getYRot();
            return;
        }
        super.tickState(state, target);
    }

    @Nullable
    @Override
    protected LivingEntity findTarget() {
        if (isRiddenByOwner()) {
            return null;
        }
        LivingEntity owner = getOwner();
        if (owner == null) {
            return null;
        }
        LivingEntity current = getTarget();
        if (current != null && current.isAlive() && canHit(current) && distanceToSqr(owner) < 32 * 32) {
            return current;
        }
        LivingEntity hurtBy = owner.getLastHurtByMob();
        if (hurtBy != null && hurtBy.isAlive() && canHit(hurtBy)) {
            return hurtBy;
        }
        LivingEntity hit = owner.getLastHurtMob();
        if (hit != null && hit.isAlive() && canHit(hit) && owner.tickCount - owner.getLastHurtMobTimestamp() < 200) {
            return hit;
        }
        return null;
    }

    @Override
    protected void tickHover(@Nullable LivingEntity target) {
        LivingEntity owner = getOwner();
        if (target == null) {
            if (owner == null) {
                return;
            }
            if (ownerGrounded(owner) && distanceToSqr(owner) < 28 * 28 && ++idleTicks > 40) {
                Vec3 behind = owner.position().add(owner.getLookAngle().multiply(1, 0, 1).normalize().scale(-5))
                        .add(Vec3.directionFromRotation(0, owner.getYRot() + 90).scale(random.nextBoolean() ? 3.5 : -3.5));
                Vec3 spot = findLandingSpot(behind, 5);
                if (spot != null) {
                    beginLanding(spot);
                    return;
                }
                idleTicks = 20;
            }
            steer(orbitPoint(owner.position(), 8, 6 + Math.sin(tickCount * 0.05) * 0.6, 0.025), 0.7, 7f);
            yHeadRot = Mth.approachDegrees(yHeadRot, yBodyRot, 8f);
            return;
        }
        idleTicks = 0;
        steer(orbitPoint(target.position(), 10, 6, 0.03), 0.8, 8f);
        lookTowards(target.getEyePosition());
        if (--attackCooldown <= 0) {
            chooseAirAttack(target);
        }
    }

    private static boolean ownerGrounded(LivingEntity owner) {
        return owner.onGround() && !owner.isFallFlying() && !owner.isPassenger();
    }

    @Override
    protected void tickPerch(@Nullable LivingEntity target) {
        LivingEntity owner = getOwner();
        if (target != null || owner == null || !ownerGrounded(owner) && distanceToSqr(owner) > 6 * 6 || distanceToSqr(owner) > 26 * 26) {
            leavePerch(State.TAKEOFF);
            return;
        }
        perchTicks++;
        double distance = distanceTo(owner);
        if (distance > 8) {
            if (getIdleVariant() != 0) {
                setIdleVariant(0);
            }
            Vec3 dir = owner.position().subtract(position()).multiply(1, 0, 1).normalize();
            double speed = distance > 14 ? 0.32 : 0.16;
            setDeltaMovement(dir.x * speed, getDeltaMovement().y, dir.z * speed);
            turnBody(owner.position(), 10f);
            lookTowards(owner.getEyePosition());
            if (horizontalCollision && onGround()) {
                setDeltaMovement(getDeltaMovement().add(0, 0.45, 0));
            }
        } else {
            setDeltaMovement(getDeltaMovement().multiply(0.5, 1, 0.5));
            cycleIdle();
            if (perchTicks % 60 == 0) {
                lookTowards(owner.getEyePosition());
            }
        }
    }

    @Override
    protected void chooseAirAttack(LivingEntity target) {
        int roll = random.nextInt(100);
        State next;
        if (roll < 40) {
            next = State.COG_SPIT;
        } else if (roll < 65) {
            next = State.BREATH_CHARGE;
        } else if (roll < 85) {
            next = State.SWOOP;
        } else {
            next = State.ROAR;
        }
        setState(next);
    }

    @Override
    public boolean applyStun(int ticks) {
        if (isRiddenByOwner()) {
            return false;
        }
        return super.applyStun(ticks);
    }

    @Override
    public boolean hurt(@NotNull DamageSource source, float amount) {
        if (source.getEntity() != null && isOwnedBy(source.getEntity())) {
            return false;
        }
        return super.hurt(source, amount);
    }

    @Override
    protected boolean isInvulnerableState() {
        return getState() == State.DEATH;
    }

    @Override
    protected boolean shouldDropLoot() {
        return false;
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }

    @Override
    public boolean causeFallDamage(float distance, float multiplier, @NotNull DamageSource source) {
        return false;
    }

    /* ---------------------------------------------------------------- persistence */

    @Override
    public void addAdditionalSaveData(@NotNull CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (ownerUUID != null) {
            tag.putUUID("Owner", ownerUUID);
        }
        tag.putInt("LifeTicks", lifeTicks);
        tag.putFloat("Power", power);
        tag.putFloat("Scale", getModelScale());
    }

    @Override
    public void readAdditionalSaveData(@NotNull CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.hasUUID("Owner")) {
            setOwnerId(tag.getUUID("Owner"));
        }
        lifeTicks = tag.getInt("LifeTicks");
        power = tag.contains("Power") ? tag.getFloat("Power") : 1f;
        setModelScale(tag.contains("Scale") ? tag.getFloat("Scale") : SCALE);
    }
}
