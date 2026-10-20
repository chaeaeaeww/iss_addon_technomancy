package net.isstechnomancy.item;

import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.api.registry.AttributeRegistry;
import io.redspace.ironsspellbooks.capabilities.magic.CooldownInstance;
import io.redspace.ironsspellbooks.capabilities.magic.PlayerCooldowns;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.boss.ArcRing;
import net.isstechnomancy.registry.TechEffects;
import net.minecraft.ChatFormatting;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraftforge.event.entity.living.LivingDamageEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.ArrayList;
import java.util.List;

/**
 * Glorious Evolution (Hextech Engineer full set, 1.9): every time the wearer's health drops below half, the armour
 * evolves one random buff for 10 s (never the same twice in a row), then needs 30 s before it can evolve again.
 *
 * <ul>
 *     <li>speed: Speed II.</li>
 *     <li>overdrive: the Technomancy Overdrive effect.</li>
 *     <li>focus: every running spell cooldown cut by 40% at once, then +25% cooldown reduction and +15% cast speed.</li>
 *     <li>power: +15% spell power.</li>
 *     <li>mana: 30% of max mana back.</li>
 *     <li>plating: Absorption II (4 hearts).</li>
 *     <li>repair: Regeneration II.</li>
 * </ul>
 */
@Mod.EventBusSubscriber(modid = ISSTechnomancy.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class HextechArmorEvents {
    public static final int COOLDOWN_SECONDS = 30;
    public static final int DURATION = 200;
    private static final String TAG = "iss_technomancy.evolution";
    public static final String[] BUFFS = {"speed", "overdrive", "focus", "power", "mana", "plating", "repair"};

    private HextechArmorEvents() {
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void onDamage(LivingDamageEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player) || event.getAmount() <= 0 || !HextechArmorItem.wearsFullSet(player)) {
            return;
        }
        float half = player.getMaxHealth() * 0.5f;
        float before = player.getHealth();
        float after = before - event.getAmount();
        if (before < half || after >= half || after <= 0) {
            return;
        }
        CompoundTag data = player.getPersistentData().getCompound(TAG);
        long now = player.level().getGameTime();
        if (now < data.getLong("Ready")) {
            return;
        }
        int last = data.contains("Last") ? data.getInt("Last") : -1;
        List<Integer> pool = new ArrayList<>();
        for (int i = 0; i < BUFFS.length; i++) {
            if (i != last) {
                pool.add(i);
            }
        }
        int pick = pool.get(player.getRandom().nextInt(pool.size()));
        evolve(player, pick);
        data.putLong("Ready", now + COOLDOWN_SECONDS * 20L);
        data.putInt("Last", pick);
        player.getPersistentData().put(TAG, data);
    }

    public static void evolve(ServerPlayer player, int buff) {
        switch (BUFFS[buff]) {
            case "speed" -> player.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, DURATION, 1));
            case "overdrive" -> player.addEffect(new MobEffectInstance(TechEffects.OVERDRIVE.get(), DURATION, 0));
            case "focus" -> {
                PlayerCooldowns cooldowns = MagicData.getPlayerMagicData(player).getPlayerCooldowns();
                for (CooldownInstance cd : new ArrayList<>(cooldowns.getSpellCooldowns().values())) {
                    cd.decrementBy((int) (cd.getCooldownRemaining() * 0.4f));
                }
                cooldowns.syncToPlayer(player);
                player.addEffect(new MobEffectInstance(TechEffects.EVOLVED_FOCUS.get(), DURATION, 0));
            }
            case "power" -> player.addEffect(new MobEffectInstance(TechEffects.EVOLVED_POWER.get(), DURATION, 0));
            case "mana" -> {
                MagicData magic = MagicData.getPlayerMagicData(player);
                float max = (float) player.getAttributeValue(AttributeRegistry.MAX_MANA.get());
                magic.setMana(Math.min(max, magic.getMana() + max * 0.3f));
            }
            case "plating" -> player.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, DURATION, 1));
            default -> player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, DURATION, 1));
        }
        player.displayClientMessage(Component.translatable("message.iss_technomancy.evolution",
                Component.translatable("message.iss_technomancy.evolution." + BUFFS[buff])).withStyle(ChatFormatting.AQUA), true);
        player.level().playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1.2f, 1.6f);
        player.level().playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.5f, 1.2f);
        if (player.level() instanceof net.minecraft.server.level.ServerLevel server) {
            net.isstechnomancy.entity.boss.ElectricFx.burst(server, player.position().add(0, 0.1, 0), 3.5f, 0);
        }
    }
}
