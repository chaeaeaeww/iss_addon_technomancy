package net.isstechnomancy.registry;

import net.isstechnomancy.ISSTechnomancy;
import net.minecraft.core.particles.ParticleType;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.Registries;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public class TechParticles {
    private static final DeferredRegister<ParticleType<?>> PARTICLES = DeferredRegister.create(Registries.PARTICLE_TYPE, ISSTechnomancy.MODID);

    /** Hot brass/orange spark with gravity. Gear impacts, welding contact point, sentry muzzle. */
    public static final RegistryObject<SimpleParticleType> BRASS_SPARK = PARTICLES.register("brass_spark", () -> new SimpleParticleType(true));
    /** Grey steam puff that grows and rises. Sentry vents, deploy, despawn. */
    public static final RegistryObject<SimpleParticleType> STEAM_PUFF = PARTICLES.register("steam_puff", () -> new SimpleParticleType(false));
    /** Emissive cyan arc mote. Welder beam, sentry bolts, overclock. */
    public static final RegistryObject<SimpleParticleType> ARC_MOTE = PARTICLES.register("arc_mote", () -> new SimpleParticleType(true));
    /** Flat spinning cog rune drawn on the ground. Long-cast circle for Deploy Brass Sentry. */
    public static final RegistryObject<SimpleParticleType> COG_SIGIL = PARTICLES.register("cog_sigil", () -> new SimpleParticleType(true));

    public static void register(IEventBus modEventBus) {
        PARTICLES.register(modEventBus);
    }
}
