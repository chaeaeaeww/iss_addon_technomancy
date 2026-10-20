package net.isstechnomancy.client;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.client.particle.ArcMoteParticle;
import net.isstechnomancy.client.particle.BrassSparkParticle;
import net.isstechnomancy.client.particle.CogSigilParticle;
import net.isstechnomancy.client.particle.SteamPuffParticle;
import net.isstechnomancy.client.renderer.ArcWelderBeamRenderer;
import net.isstechnomancy.client.renderer.BrassSentryRenderer;
import net.isstechnomancy.client.renderer.ClockworkAutomatonRenderer;
import net.isstechnomancy.client.renderer.GearProjectileRenderer;
import net.isstechnomancy.client.renderer.SiegeSentryRenderer;
import net.isstechnomancy.client.renderer.TechDragonRenderer;
import net.isstechnomancy.client.renderer.HextechPylonRenderer;
import net.isstechnomancy.client.renderer.ArcRingRenderer;
import net.isstechnomancy.client.renderer.DragonDebrisRenderer;
import net.isstechnomancy.client.renderer.HextechShellRenderer;
import net.isstechnomancy.client.renderer.MagneticFieldRenderer;
import net.isstechnomancy.client.renderer.RocketHandRenderer;
import net.isstechnomancy.client.renderer.TechnomancerRenderer;
import net.isstechnomancy.client.screen.StaffModuleScreen;
import net.isstechnomancy.registry.TechMenus;
import net.minecraft.client.gui.screens.MenuScreens;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechParticles;
import net.minecraft.client.renderer.entity.NoopRenderer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.client.event.RegisterParticleProvidersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(modid = ISSTechnomancy.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public class ClientSetup {

    @SubscribeEvent
    public static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(TechEntities.GEAR_PROJECTILE.get(), GearProjectileRenderer::new);
        event.registerBlockEntityRenderer(net.isstechnomancy.registry.TechBlockEntities.HEXTECH_FORGE.get(), net.isstechnomancy.client.renderer.HextechForgeRenderer::new);
        event.registerEntityRenderer(TechEntities.ARC_WELDER_BEAM.get(), ArcWelderBeamRenderer::new);
        event.registerEntityRenderer(TechEntities.BRASS_SENTRY.get(), BrassSentryRenderer::new);
        // The bolt is drawn entirely by its arc-mote particle trail.
        event.registerEntityRenderer(TechEntities.SENTRY_BOLT.get(), NoopRenderer::new);
        event.registerEntityRenderer(TechEntities.SIEGE_SENTRY.get(), SiegeSentryRenderer::new);
        // Shells are drawn by their smoke and spark trail.
        event.registerEntityRenderer(TechEntities.SIEGE_SHELL.get(), NoopRenderer::new);
        event.registerEntityRenderer(TechEntities.CLOCKWORK_AUTOMATON.get(), ClockworkAutomatonRenderer::new);
        event.registerEntityRenderer(TechEntities.TECH_DRAGON.get(), TechDragonRenderer::new);
        event.registerEntityRenderer(TechEntities.TECH_DRAKE.get(), TechDragonRenderer::new);
        event.registerEntityRenderer(TechEntities.HEXTECH_PYLON.get(), HextechPylonRenderer::new);
        event.registerEntityRenderer(TechEntities.HEXTECH_SHELL.get(), HextechShellRenderer::new);
        event.registerEntityRenderer(TechEntities.DRAGON_DEBRIS.get(), DragonDebrisRenderer::new);
        event.registerEntityRenderer(TechEntities.ARC_RING.get(), ArcRingRenderer::new);
        event.registerEntityRenderer(TechEntities.ROCKET_HAND.get(), RocketHandRenderer::new);
        event.registerEntityRenderer(TechEntities.MAGNETIC_FIELD.get(), MagneticFieldRenderer::new);
        event.registerEntityRenderer(TechEntities.TECHNOMANCER.get(), TechnomancerRenderer::new);
    }

    @SubscribeEvent
    public static void clientSetup(FMLClientSetupEvent event) {
        event.enqueueWork(() -> MenuScreens.register(TechMenus.STAFF_MODULES.get(), StaffModuleScreen::new));
    }

    @SubscribeEvent
    public static void registerParticles(RegisterParticleProvidersEvent event) {
        event.registerSpriteSet(TechParticles.BRASS_SPARK.get(), BrassSparkParticle.Provider::new);
        event.registerSpriteSet(TechParticles.STEAM_PUFF.get(), SteamPuffParticle.Provider::new);
        event.registerSpriteSet(TechParticles.ARC_MOTE.get(), ArcMoteParticle.Provider::new);
        event.registerSpriteSet(TechParticles.COG_SIGIL.get(), CogSigilParticle.Provider::new);
    }
}
