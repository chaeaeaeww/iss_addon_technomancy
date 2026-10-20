package net.isstechnomancy.spells;

import io.redspace.ironsspellbooks.api.config.DefaultConfig;
import io.redspace.ironsspellbooks.api.entity.IMagicEntity;
import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import io.redspace.ironsspellbooks.api.spells.CastSource;
import io.redspace.ironsspellbooks.api.spells.CastType;
import io.redspace.ironsspellbooks.api.spells.SpellRarity;
import io.redspace.ironsspellbooks.api.util.AnimationHolder;
import io.redspace.ironsspellbooks.api.util.Utils;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.damage.DamageSources;
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.effect.OverdriveEffect;
import net.isstechnomancy.entity.boss.TechDragon;
import net.isstechnomancy.registry.TechAnimations;
import net.isstechnomancy.registry.TechEffects;
import net.isstechnomancy.registry.TechSchools;
import net.isstechnomancy.registry.TechTags;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.Optional;

/**
 * Instant · Rare · single level. A screeching electromagnetic sonic wave (18 blocks) that deals no damage: machines and
 * electric creatures (tag iss_technomancy:mechanical: automatons, sentries, iron golems, the Harbinger and its
 * watchers/prowlers, Alex's Caves magnetic creatures, the Tech Dragon...) are stunned for 3s and stop casting.
 * Everything else is unaffected. Overdrive: the wave bursts in every direction (radius 10).
 */
public class EmpScreechSpell extends AbstractSpell {
    public static final double RANGE = 18;
    public static final double BURST_RADIUS = 10;

    private final ResourceLocation spellId = ISSTechnomancy.id("emp_screech");
    private final DefaultConfig defaultConfig = new DefaultConfig()
            .setMinRarity(SpellRarity.RARE)
            .setSchoolResource(TechSchools.TECHNOMANCY_RESOURCE)
            .setMaxLevel(1)
            .setCooldownSeconds(20)
            .build();

    public EmpScreechSpell() {
        this.manaCostPerLevel = 0;
        this.baseSpellPower = 1;
        this.spellPowerPerLevel = 0;
        this.castTime = 0;
        this.baseManaCost = 50;
    }

    @Override
    public List<MutableComponent> getUniqueInfo(int spellLevel, LivingEntity caster) {
        return List.of(
                Component.translatable("ui.iss_technomancy.stun_duration", Utils.stringTruncation(getStunTicks(spellLevel) / 20f, 2)),
                Component.translatable("ui.irons_spellbooks.distance", Utils.stringTruncation(RANGE, 1)));
    }

    @Override
    public CastType getCastType() {
        return CastType.INSTANT;
    }

    @Override
    public DefaultConfig getDefaultConfig() {
        return defaultConfig;
    }

    @Override
    public ResourceLocation getSpellResource() {
        return spellId;
    }

    @Override
    public Optional<SoundEvent> getCastStartSound() {
        return Optional.empty();
    }

    @Override
    public Optional<SoundEvent> getCastFinishSound() {
        return Optional.of(SoundEvents.WARDEN_SONIC_BOOM);
    }

    @Override
    public AnimationHolder getCastStartAnimation() {
        return TechAnimations.EMP_SCREECH;
    }

    @Override
    public AnimationHolder getCastFinishAnimation() {
        return AnimationHolder.pass();
    }

    @Override
    public void onCast(Level level, int spellLevel, LivingEntity entity, CastSource castSource, MagicData playerMagicData) {
        boolean burst = OverdriveEffect.consume(entity);
        int stun = getStunTicks(spellLevel);
        Vec3 eye = entity.getEyePosition();
        if (burst) {
            for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, entity.getBoundingBox().inflate(BURST_RADIUS),
                    t -> t != entity && t.distanceToSqr(entity) <= BURST_RADIUS * BURST_RADIUS && entity.hasLineOfSight(t))) {
                affect(entity, target, stun);
            }
            for (int ring = 1; ring <= 5; ring++) {
                for (int i = 0; i < 12; i++) {
                    double a = i * Math.PI / 6;
                    double r = ring * 2;
                    MagicManager.spawnParticles(level, ParticleTypes.SONIC_BOOM, entity.getX() + Math.cos(a) * r, entity.getY() + 1, entity.getZ() + Math.sin(a) * r, 1, 0, 0, 0, 0, false);
                }
            }
        } else {
            Vec3 look = entity.getLookAngle();
            Vec3 end = eye.add(look.scale(RANGE));
            BlockHitResult blockHit = level.clip(new ClipContext(eye, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, entity));
            if (blockHit.getType() != HitResult.Type.MISS) {
                end = blockHit.getLocation();
            }
            Vec3 finalEnd = end;
            for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, new AABB(eye, end).inflate(2),
                    t -> t != entity && distanceToSegment(t.getBoundingBox().getCenter(), eye, finalEnd) <= t.getBbWidth() * 0.5 + 1.4)) {
                affect(entity, target, stun);
            }
            double length = eye.distanceTo(end);
            for (double d = 1.5; d < length; d += 1.6) {
                Vec3 p = eye.add(look.scale(d));
                MagicManager.spawnParticles(level, ParticleTypes.SONIC_BOOM, p.x, p.y, p.z, 1, 0, 0, 0, 0, false);
                MagicManager.spawnParticles(level, ParticleHelper.ELECTRIC_SPARKS, p.x, p.y, p.z, 2, 0.4, 0.4, 0.4, 0.05, false);
            }
        }
        super.onCast(level, spellLevel, entity, castSource, playerMagicData);
    }

    private void affect(LivingEntity caster, LivingEntity target, int stun) {
        // only machines and electric creatures react; everything else is untouched and nothing takes damage
        if (!isMechanical(target) || caster.isAlliedTo(target) || DamageSources.isFriendlyFireBetween(caster, target) || !target.isAlive()) {
            return;
        }
        if (target instanceof IMagicEntity magicEntity) {
            magicEntity.cancelCast();
        }
        if (target instanceof TechDragon dragon) {
            dragon.applyStun(stun);
        }
        target.addEffect(new MobEffectInstance(TechEffects.STUNNED.get(), stun, 0), caster);
        MagicManager.spawnParticles(caster.level(), ParticleHelper.ELECTRICITY, target.getX(), target.getY() + target.getBbHeight() * 0.5, target.getZ(),
                16, target.getBbWidth() * 0.5, target.getBbHeight() * 0.4, target.getBbWidth() * 0.5, 0.1, false);
        MagicManager.spawnParticles(caster.level(), ParticleHelper.ELECTRIC_SPARKS, target.getX(), target.getY() + target.getBbHeight() * 0.7, target.getZ(),
                10, target.getBbWidth() * 0.4, 0.2, target.getBbWidth() * 0.4, 0.2, false);
    }

    public static boolean isMechanical(Entity entity) {
        return entity.getType().is(TechTags.MECHANICAL);
    }

    private static double distanceToSegment(Vec3 p, Vec3 a, Vec3 b) {
        Vec3 ab = b.subtract(a);
        double t = Math.max(0, Math.min(1, p.subtract(a).dot(ab) / Math.max(1e-6, ab.lengthSqr())));
        return p.distanceTo(a.add(ab.scale(t)));
    }

    public int getStunTicks(int spellLevel) {
        return 60;
    }

    @Override
    public boolean shouldAIStopCasting(int spellLevel, Mob mob, LivingEntity target) {
        return mob.distanceToSqr(target) > RANGE * RANGE;
    }
}
