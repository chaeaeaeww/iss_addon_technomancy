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
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.effect.OverdriveEffect;
import net.isstechnomancy.entity.MagneticField;
import net.isstechnomancy.module.ModuleStats;
import net.isstechnomancy.module.StaffModules;
import net.isstechnomancy.registry.TechAnimations;
import net.isstechnomancy.registry.TechParticles;
import net.isstechnomancy.registry.TechSchools;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.Optional;

/**
 * Long cast (1s) · Epic · max level 5. Plants a Magnetic Field on the caster's position: radius 7 + 0.6/level
 * (7-9.4 blocks), lasting 6s + 1s/level. It is a dome (the upper half of a sphere): everything inside except the
 * caster is slowed and pinned to the ground, flyers are pulled down, projectiles bend down. It deals no damage.
 * Overdrive: +3 radius, stronger slow. Caliber modules widen it. One field per caster.
 */
public class MagneticFieldSpell extends AbstractSpell {
    private final ResourceLocation spellId = ISSTechnomancy.id("magnetic_field");
    private final DefaultConfig defaultConfig = new DefaultConfig()
            .setMinRarity(SpellRarity.EPIC)
            .setSchoolResource(TechSchools.TECHNOMANCY_RESOURCE)
            .setMaxLevel(5)
            .setCooldownSeconds(45)
            .build();

    public MagneticFieldSpell() {
        this.manaCostPerLevel = 15;
        this.baseSpellPower = 8;
        this.spellPowerPerLevel = 2;
        this.castTime = 20;
        this.baseManaCost = 90;
    }

    @Override
    public List<MutableComponent> getUniqueInfo(int spellLevel, LivingEntity caster) {
        return List.of(
                Component.translatable("ui.irons_spellbooks.radius", Utils.stringTruncation(getRadius(spellLevel), 1)),
                Component.translatable("ui.irons_spellbooks.effect_length", Utils.timeFromTicks(getDuration(spellLevel), 1)));
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
        return Optional.of(SoundEvents.BEACON_POWER_SELECT);
    }

    @Override
    public Optional<SoundEvent> getCastFinishSound() {
        return Optional.of(SoundEvents.BEACON_ACTIVATE);
    }

    @Override
    public AnimationHolder getCastStartAnimation() {
        return TechAnimations.FIELD_CHANNEL;
    }

    @Override
    public AnimationHolder getCastFinishAnimation() {
        return TechAnimations.DEPLOY_SENTRY_FINISH;
    }

    @Override
    public void onServerCastTick(Level level, int spellLevel, LivingEntity entity, @Nullable MagicData playerMagicData) {
        super.onServerCastTick(level, spellLevel, entity, playerMagicData);
        if (entity.tickCount % 4 == 0) {
            MagicManager.spawnParticles(level, TechParticles.COG_SIGIL.get(), entity.getX(), entity.getY() + 0.05, entity.getZ(), 1, 0, 0, 0, 0, true);
            MagicManager.spawnParticles(level, ParticleHelper.ELECTRIC_SPARKS, entity.getX(), entity.getY() + 0.3, entity.getZ(), 6, 1.5, 0.1, 1.5, 0.05, false);
        }
    }

    @Override
    public void onCast(Level level, int spellLevel, LivingEntity entity, CastSource castSource, MagicData playerMagicData) {
        boolean overdrive = OverdriveEffect.consume(entity);
        ModuleStats modules = StaffModules.of(entity);
        level.getEntitiesOfClass(MagneticField.class, entity.getBoundingBox().inflate(64), f -> f.getOwner() == entity).forEach(MagneticField::discard);
        float radius = getRadius(spellLevel) * (0.85f + 0.15f * modules.sizeMultiplier()) + (overdrive ? 3f : 0f);
        Vec3 spot = Utils.moveToRelativeGroundLevel(level, entity.position(), 2, 4);
        MagneticField field = new MagneticField(level, entity, radius, getDuration(spellLevel), overdrive);
        field.moveTo(spot.x, spot.y, spot.z);
        level.addFreshEntity(field);
        MagicManager.spawnParticles(level, ParticleHelper.ELECTRIC_SPARKS, spot.x, spot.y + 0.5, spot.z, 50, radius * 0.4, 0.3, radius * 0.4, 0.25, false);
        super.onCast(level, spellLevel, entity, castSource, playerMagicData);
    }

    public float getRadius(int spellLevel) {
        return 7f + 0.6f * (spellLevel - 1);
    }

    public int getDuration(int spellLevel) {
        return (6 + spellLevel) * 20;
    }

    @Override
    public boolean shouldAIStopCasting(int spellLevel, Mob mob, LivingEntity target) {
        return false;
    }
}
