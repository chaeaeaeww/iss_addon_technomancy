package net.isstechnomancy.spells;

import io.redspace.ironsspellbooks.api.config.DefaultConfig;
import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import io.redspace.ironsspellbooks.api.spells.CastSource;
import io.redspace.ironsspellbooks.api.spells.CastType;
import io.redspace.ironsspellbooks.api.spells.SpellRarity;
import io.redspace.ironsspellbooks.api.util.AnimationHolder;
import io.redspace.ironsspellbooks.api.util.Utils;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.damage.DamageSources;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.effect.OverdriveEffect;
import net.isstechnomancy.module.ModuleStats;
import net.isstechnomancy.module.StaffModules;
import net.isstechnomancy.registry.TechAnimations;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSchools;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.Optional;

/**
 * Instant · Uncommon · max level 8.
 * Blasts scalding steam in a 60° cone (5 blocks): damage = spell power × 0.375 (power 4 + 1/level),
 * strong knockback and 2s Blindness. Overdrive: superheated, 7 blocks, 80° cone, ignites for 4s, 1.6x knockback.
 * A defensive tool to peel enemies off a sentry or automaton.
 */
public class SteamVentSpell extends AbstractSpell {
    public static final float RANGE = 5f;
    public static final float OVERDRIVE_RANGE = 7f;
    public static final float HALF_ANGLE = 30f;
    public static final float OVERDRIVE_HALF_ANGLE = 40f;
    public static final int BLIND_TICKS = 40;
    public static final int OVERDRIVE_FIRE_SECONDS = 4;

    private final ResourceLocation spellId = ISSTechnomancy.id("steam_vent");

    private final DefaultConfig defaultConfig = new DefaultConfig()
            .setMinRarity(SpellRarity.UNCOMMON)
            .setSchoolResource(TechSchools.TECHNOMANCY_RESOURCE)
            .setMaxLevel(8)
            .setCooldownSeconds(8)
            .build();

    public SteamVentSpell() {
        this.manaCostPerLevel = 3;
        this.baseSpellPower = 4;
        this.spellPowerPerLevel = 1;
        this.castTime = 0;
        this.baseManaCost = 25;
    }

    @Override
    public List<MutableComponent> getUniqueInfo(int spellLevel, LivingEntity caster) {
        return List.of(
                Component.translatable("ui.irons_spellbooks.damage", Utils.stringTruncation(getDamage(spellLevel, caster), 2)),
                Component.translatable("ui.irons_spellbooks.distance", Utils.stringTruncation(RANGE, 1)),
                Component.translatable("ui.iss_technomancy.knockback", Utils.stringTruncation(getKnockback(spellLevel), 2))
        );
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
        return Optional.of(TechSounds.STEAM_VENT_CAST.get());
    }

    @Override
    public AnimationHolder getCastStartAnimation() {
        return TechAnimations.STEAM_PUSH;
    }

    @Override
    public AnimationHolder getCastFinishAnimation() {
        return AnimationHolder.pass();
    }

    @Override
    public void onCast(Level level, int spellLevel, LivingEntity entity, CastSource castSource, MagicData playerMagicData) {
        boolean superheated = OverdriveEffect.consume(entity);
        ModuleStats modules = StaffModules.of(entity);
        float range = (superheated ? OVERDRIVE_RANGE : RANGE) * (0.5f + 0.5f * modules.sizeMultiplier());
        float halfAngle = Math.min(75f, (superheated ? OVERDRIVE_HALF_ANGLE : HALF_ANGLE) + 6f * modules.extraProjectiles());
        float knockback = getKnockback(spellLevel) * (superheated ? 1.6f : 1f);
        float damage = getDamage(spellLevel, entity) * modules.damageMultiplier();
        Vec3 eye = entity.getEyePosition();
        Vec3 look = entity.getLookAngle();
        double minDot = Math.cos(halfAngle * Mth.DEG_TO_RAD);

        for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, entity.getBoundingBox().inflate(range))) {
            if (target == entity || DamageSources.isFriendlyFireBetween(entity, target)) {
                continue;
            }
            Vec3 toTarget = target.getBoundingBox().getCenter().subtract(eye);
            double distance = toTarget.length();
            if (distance > range + target.getBbWidth() * 0.5 || toTarget.normalize().dot(look) < minDot || !entity.hasLineOfSight(target)) {
                continue;
            }
            DamageSources.applyDamage(target, damage, getDamageSource(entity));
            Vec3 push = toTarget.multiply(1, 0, 1).normalize().scale(knockback);
            target.push(push.x, 0.25 + knockback * 0.15, push.z);
            target.hurtMarked = true;
            target.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, BLIND_TICKS, 0), entity);
            if (superheated) {
                target.setSecondsOnFire(OVERDRIVE_FIRE_SECONDS);
            }
            net.isstechnomancy.module.TeslaHelper.arc(entity, entity, target, damage, modules.teslaJumps());
        }

        // Steam jets: count 0 makes the deltas a velocity, so every puff flies along the cone.
        Vec3 nozzle = eye.add(look.scale(0.6)).add(0, -0.2, 0);
        int puffs = superheated ? 36 : 24;
        for (int i = 0; i < puffs; i++) {
            float yaw = (entity.getRandom().nextFloat() * 2 - 1) * halfAngle * Mth.DEG_TO_RAD;
            float pitch = (entity.getRandom().nextFloat() * 2 - 1) * halfAngle * 0.6f * Mth.DEG_TO_RAD;
            Vec3 direction = look.yRot(yaw).xRot(pitch);
            double speed = 0.25 + entity.getRandom().nextFloat() * 0.25 * (range / RANGE);
            MagicManager.spawnParticles(level, TechParticles.STEAM_PUFF.get(), nozzle.x, nozzle.y, nozzle.z, 0, direction.x, direction.y, direction.z, speed, false);
            if (superheated && i % 3 == 0) {
                MagicManager.spawnParticles(level, ParticleTypes.FLAME, nozzle.x, nozzle.y, nozzle.z, 0, direction.x, direction.y, direction.z, speed * 1.2, false);
            }
        }
        super.onCast(level, spellLevel, entity, castSource, playerMagicData);
    }

    public float getDamage(int spellLevel, LivingEntity caster) {
        return getSpellPower(spellLevel, caster) * 0.375f; // 1.4: -25%
    }

    public float getKnockback(int spellLevel) {
        return 0.9f + 0.08f * spellLevel;
    }

    @Override
    public boolean shouldAIStopCasting(int spellLevel, Mob mob, LivingEntity target) {
        return mob.distanceToSqr(target) > RANGE * RANGE;
    }
}
