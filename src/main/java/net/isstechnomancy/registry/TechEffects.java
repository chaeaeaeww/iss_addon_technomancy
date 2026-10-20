package net.isstechnomancy.registry;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.effect.OverdriveEffect;
import net.isstechnomancy.effect.StunnedEffect;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.effect.MobEffect;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public class TechEffects {
    private static final DeferredRegister<MobEffect> EFFECTS = DeferredRegister.create(Registries.MOB_EFFECT, ISSTechnomancy.MODID);

    public static final RegistryObject<MobEffect> OVERDRIVE = EFFECTS.register("overdrive", OverdriveEffect::new);
    public static final RegistryObject<MobEffect> STUNNED = EFFECTS.register("short_circuit", StunnedEffect::new);
    /** Glorious Evolution (Hextech set, 1.9): +25% cooldown reduction, +15% cast speed. */
    public static final RegistryObject<MobEffect> EVOLVED_FOCUS = EFFECTS.register("evolved_focus", () -> new net.isstechnomancy.effect.EvolutionEffect(0x4FE3F0)
            .with(io.redspace.ironsspellbooks.api.registry.AttributeRegistry.COOLDOWN_REDUCTION, "6c3f2a1e-5b1d-4c7e-9f41-1a2b3c4d5e01", 0.25,
                    net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.MULTIPLY_BASE)
            .with(io.redspace.ironsspellbooks.api.registry.AttributeRegistry.CAST_TIME_REDUCTION, "6c3f2a1e-5b1d-4c7e-9f41-1a2b3c4d5e02", 0.15,
                    net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.MULTIPLY_BASE));
    /** Glorious Evolution: +15% spell power. */
    public static final RegistryObject<MobEffect> EVOLVED_POWER = EFFECTS.register("evolved_power", () -> new net.isstechnomancy.effect.EvolutionEffect(0xB487FF)
            .with(io.redspace.ironsspellbooks.api.registry.AttributeRegistry.SPELL_POWER, "6c3f2a1e-5b1d-4c7e-9f41-1a2b3c4d5e03", 0.15,
                    net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.MULTIPLY_BASE));

    public static void register(IEventBus modEventBus) {
        EFFECTS.register(modEventBus);
    }
}
