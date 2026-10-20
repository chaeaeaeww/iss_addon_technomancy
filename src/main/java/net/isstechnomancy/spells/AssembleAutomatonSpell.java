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
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.effect.OverdriveEffect;
import net.isstechnomancy.entity.ClockworkAutomaton;
import net.isstechnomancy.module.ModuleStats;
import net.isstechnomancy.module.StaffModules;
import net.isstechnomancy.registry.TechAnimations;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSchools;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.Optional;

/**
 * Long Cast (2s) · Rare · max level 5.
 * Assembles a Clockwork Automaton ally next to the caster. Spell power = 6 + 2/level:
 * melee = power × 0.6, gear volley = 3 gears × power × 0.3, HP = 30 + 8/level, lifetime = 60s + 15s/level.
 * One automaton per caster. Overdrive: Mk.II (1.35x size, 1.6x HP, 1.5x damage, 5-gear volleys, faster volleys).
 */
public class AssembleAutomatonSpell extends AbstractSpell {
    public static final float MK2_HEALTH = 1.6f;
    public static final float MK2_DAMAGE = 1.5f;

    private final ResourceLocation spellId = ISSTechnomancy.id("assemble_automaton");

    private final DefaultConfig defaultConfig = new DefaultConfig()
            .setMinRarity(SpellRarity.RARE)
            .setSchoolResource(TechSchools.TECHNOMANCY_RESOURCE)
            .setMaxLevel(5)
            .setCooldownSeconds(90)
            .build();

    public AssembleAutomatonSpell() {
        this.manaCostPerLevel = 15;
        this.baseSpellPower = 6;
        this.spellPowerPerLevel = 2;
        this.castTime = 40;
        this.baseManaCost = 70;
    }

    @Override
    public List<MutableComponent> getUniqueInfo(int spellLevel, LivingEntity caster) {
        return List.of(
                Component.translatable("ui.irons_spellbooks.damage", Utils.stringTruncation(getMeleeDamage(spellLevel, caster), 2)),
                Component.translatable("ui.iss_technomancy.damage_per_gear", Utils.stringTruncation(getGearDamage(spellLevel, caster), 2)),
                Component.translatable("ui.irons_spellbooks.hp", getHealth(spellLevel)),
                Component.translatable("ui.iss_technomancy.sentry_lifetime", Utils.stringTruncation(getLifetimeTicks(spellLevel) / 20f, 0))
        );
    }

    @Override
    public CastType getCastType() {
        return CastType.LONG;
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
        return Optional.of(TechSounds.SENTRY_WINDUP.get());
    }

    @Override
    public Optional<SoundEvent> getCastFinishSound() {
        return Optional.of(TechSounds.AUTOMATON_ASSEMBLE.get());
    }

    @Override
    public AnimationHolder getCastStartAnimation() {
        return TechAnimations.DEPLOY_SENTRY;
    }

    @Override
    public AnimationHolder getCastFinishAnimation() {
        return TechAnimations.DEPLOY_SENTRY_FINISH;
    }

    @Override
    public void onServerCastTick(Level level, int spellLevel, LivingEntity entity, @Nullable MagicData playerMagicData) {
        super.onServerCastTick(level, spellLevel, entity, playerMagicData);
        if (entity.tickCount % 10 == 0) {
            Vec3 spot = findAssemblyPosition(level, entity);
            MagicManager.spawnParticles(level, TechParticles.COG_SIGIL.get(), spot.x, spot.y + 0.05, spot.z, 1, 0, 0, 0, 0, true);
            MagicManager.spawnParticles(level, TechParticles.STEAM_PUFF.get(), spot.x, spot.y + 0.2, spot.z, 3, 0.4, 0.05, 0.4, 0.02, false);
        }
    }

    @Override
    public void onCast(Level level, int spellLevel, LivingEntity entity, CastSource castSource, MagicData playerMagicData) {
        boolean mk2 = OverdriveEffect.consume(entity);
        level.getEntitiesOfClass(ClockworkAutomaton.class, entity.getBoundingBox().inflate(64),
                        automaton -> entity.getUUID().equals(automaton.getOwnerUUID()))
                .forEach(ClockworkAutomaton::disassemble);

        ModuleStats modules = StaffModules.of(entity);
        float melee = getMeleeDamage(spellLevel, entity) * (mk2 ? MK2_DAMAGE : 1f) * modules.damageMultiplier();
        float gear = getGearDamage(spellLevel, entity) * (mk2 ? MK2_DAMAGE : 1f) * modules.damageMultiplier();
        int health = (int) (getHealth(spellLevel) * (mk2 ? MK2_HEALTH : 1f) * modules.constructHealthMultiplier());
        int count = 1 + modules.extraConstructs() / 2;
        Vec3 base = findAssemblyPosition(level, entity);
        Vec3 side = new Vec3(-entity.getLookAngle().z, 0, entity.getLookAngle().x).normalize().scale(mk2 ? 2.4 : 1.8);
        for (int i = 0; i < count; i++) {
            Vec3 spot = i == 0 ? base : Utils.moveToRelativeGroundLevel(level, base.add(side.scale(i == 1 ? 1 : -1)), 3, 5);
            ClockworkAutomaton automaton = new ClockworkAutomaton(level, entity, melee, gear, health, getLifetimeTicks(spellLevel), mk2);
            automaton.setModules(modules.extraProjectiles(), modules.teslaJumps());
            automaton.moveTo(spot.x, spot.y, spot.z, entity.getYRot(), 0);
            automaton.setYBodyRot(entity.getYRot());
            automaton.setYHeadRot(entity.getYRot());
            level.addFreshEntity(automaton);
            MagicManager.spawnParticles(level, TechParticles.STEAM_PUFF.get(), spot.x, spot.y + 0.5, spot.z, 16, 0.5, 0.5, 0.5, 0.03, false);
            MagicManager.spawnParticles(level, TechParticles.BRASS_SPARK.get(), spot.x, spot.y + 1, spot.z, 24, 0.4, 0.6, 0.4, 0.25, false);
        }
        super.onCast(level, spellLevel, entity, castSource, playerMagicData);
    }

    private static Vec3 findAssemblyPosition(Level level, LivingEntity caster) {
        Vec3 forward = caster.getLookAngle().multiply(1, 0, 1).normalize().scale(2);
        return Utils.moveToRelativeGroundLevel(level, caster.position().add(forward).add(0, 1, 0), 3, 5);
    }

    public float getMeleeDamage(int spellLevel, @Nullable LivingEntity caster) {
        return getSpellPower(spellLevel, caster) * 0.45f; // 1.4: -25%
    }

    public float getGearDamage(int spellLevel, @Nullable LivingEntity caster) {
        return getSpellPower(spellLevel, caster) * 0.225f; // 1.4: -25%
    }

    public int getHealth(int spellLevel) {
        return 30 + 8 * (spellLevel - 1);
    }

    public int getLifetimeTicks(int spellLevel) {
        return (60 + 15 * (spellLevel - 1)) * 20;
    }

    @Override
    public boolean shouldAIStopCasting(int spellLevel, Mob mob, LivingEntity target) {
        return false;
    }
}
