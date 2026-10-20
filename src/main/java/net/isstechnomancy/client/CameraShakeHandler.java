package net.isstechnomancy.client;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.boss.HextechShell;
import net.isstechnomancy.entity.boss.TechDragon;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.Entity;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ViewportEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * Screen shake near the Tech Dragon: its slam, roars, phase change and death set a synced shake timer.
 */
@Mod.EventBusSubscriber(modid = ISSTechnomancy.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public class CameraShakeHandler {
    private static final double RANGE = 60;

    @SubscribeEvent
    public static void onCameraAngles(ViewportEvent.ComputeCameraAngles event) {
        Minecraft mc = Minecraft.getInstance();
        Entity viewer = mc.getCameraEntity();
        if (viewer == null || mc.level == null || mc.isPaused()) {
            return;
        }
        float strength = 0;
        for (TechDragon dragon : mc.level.getEntitiesOfClass(TechDragon.class, viewer.getBoundingBox().inflate(RANGE))) {
            int shake = dragon.getShake();
            if (shake <= 0) {
                continue;
            }
            double falloff = 1 - Math.min(1, viewer.distanceTo(dragon) / RANGE);
            strength = Math.max(strength, (float) (Math.min(1, shake / 15f) * falloff));
        }
        // the death sphere: a long build-up rumble and the blast
        for (HextechShell shell : mc.level.getEntitiesOfClass(HextechShell.class, viewer.getBoundingBox().inflate(HextechShell.BLAST_RADIUS * 1.5))) {
            int shake = shell.getShake();
            if (shake > 0) {
                double falloff = 1 - Math.min(1, viewer.distanceTo(shell) / (HextechShell.BLAST_RADIUS * 1.5));
                strength = Math.max(strength, (float) (Math.min(1.6, shake / 15f) * falloff));
            }
        }
        if (strength <= 0.01f) {
            return;
        }
        double t = (viewer.tickCount + event.getPartialTick()) * 1.7;
        float amp = 2.2f * strength;
        event.setYaw(event.getYaw() + (float) Math.sin(t * 2.3) * amp);
        event.setPitch(event.getPitch() + (float) Math.cos(t * 3.1) * amp);
        event.setRoll(event.getRoll() + (float) Math.sin(t * 1.9) * amp * 0.6f);
    }
}
