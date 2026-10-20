package net.isstechnomancy.item;

import io.redspace.ironsspellbooks.api.events.SpellDamageEvent;
import io.redspace.ironsspellbooks.api.events.SpellOnCastEvent;
import io.redspace.ironsspellbooks.api.registry.SchoolRegistry;
import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.entity.spells.LightningStrike;
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.registry.TechSchools;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * 1.10: the Hextech Scepter evolves like TravelOptics' weapons (one scepter, Evolution 0-3 by smithing; each level
 * unlocks an ability shown in the tooltip as stars):
 * <ul>
 *     <li>Evo 1 - Static Charge: the holder's spells charge what they hit; the 5th charge calls a lightning bolt down
 *     from the sky onto it.</li>
 *     <li>Evo 2 - +10% cooldown reduction and +15% mana regeneration (item attributes); 4 charges are enough.</li>
 *     <li>Evo 3 - Overload: every 20 s the next Technomancy or Lightning spell is cast one level higher.</li>
 * </ul>
 */
@Mod.EventBusSubscriber(modid = ISSTechnomancy.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class ScepterEvolutionEvents {
    private static final String CHARGE = "iss_technomancy.static_charge";
    private static final String OVERLOAD_READY = "iss_technomancy.evo_overload_at";
    public static final int OVERLOAD_COOLDOWN = 400;

    private ScepterEvolutionEvents() {
    }

    /** Evolution level of the scepter the entity holds (main hand first), 0 if none. */
    public static int evolution(LivingEntity entity) {
        for (ItemStack stack : new ItemStack[]{entity.getMainHandItem(), entity.getOffhandItem()}) {
            if (stack.getItem() instanceof ClockworkStaffItem staff && staff.getModelName().startsWith("hextech")) {
                return staff.getStars();
            }
        }
        return 0;
    }

    @SubscribeEvent
    public static void onSpellDamage(SpellDamageEvent event) {
        LivingEntity victim = event.getEntity();
        if (victim.level().isClientSide || event.getSpellDamageSource().getDirectEntity() instanceof LightningStrike) {
            return;
        }
        if (!(event.getSpellDamageSource().getEntity() instanceof LivingEntity caster) || caster == victim) {
            return;
        }
        int evo = evolution(caster);
        if (evo < 1) {
            return;
        }
        CompoundTag data = victim.getPersistentData();
        long now = victim.level().getGameTime();
        // charges fade if the target is left alone for 8 s
        int charges = now - data.getLong(CHARGE + "_t") > 160 ? 0 : data.getInt(CHARGE);
        charges++;
        data.putLong(CHARGE + "_t", now);
        int needed = evo >= 2 ? 4 : 5;
        if (charges >= needed) {
            charges = 0;
            LightningStrike bolt = new LightningStrike(victim.level());
            bolt.setOwner(caster);
            bolt.setDamage(5f + 1.5f * evo);
            bolt.setPos(victim.getX(), victim.getY(), victim.getZ());
            victim.level().addFreshEntity(bolt);
        } else {
            MagicManager.spawnParticles(victim.level(), ParticleHelper.ELECTRIC_SPARKS, victim.getX(), victim.getY() + victim.getBbHeight() * 0.6, victim.getZ(),
                    3 + charges * 2, 0.3, 0.3, 0.3, 0.15, false);
        }
        data.putInt(CHARGE, charges);
    }

    @SubscribeEvent
    public static void onSpellCast(SpellOnCastEvent event) {
        Player player = event.getEntity();
        if (player.level().isClientSide || evolution(player) < 3) {
            return;
        }
        var school = event.getSchoolType();
        if (school != SchoolRegistry.LIGHTNING.get() && school != TechSchools.TECHNOMANCY.get()) {
            return;
        }
        CompoundTag data = player.getPersistentData();
        long now = player.level().getGameTime();
        if (now < data.getLong(OVERLOAD_READY)) {
            return;
        }
        event.setSpellLevel(event.getSpellLevel() + 1);
        data.putLong(OVERLOAD_READY, now + OVERLOAD_COOLDOWN);
        player.level().playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 0.8f, 1.6f);
        MagicManager.spawnParticles(player.level(), ParticleHelper.ELECTRIC_SPARKS, player.getX(), player.getY() + 1.2, player.getZ(), 16, 0.4, 0.5, 0.4, 0.25, false);
    }
}
