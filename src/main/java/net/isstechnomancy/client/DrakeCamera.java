package net.isstechnomancy.client;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.boss.TechDrake;
import net.minecraft.client.Camera;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ViewportEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.util.ObfuscationReflectionHelper;
import org.joml.Vector3f;

import java.lang.reflect.Method;

/**
 * Camera while riding the Tech Drake: switches to the third-person view on mounting (the previous view comes back on
 * dismounting) and pulls the camera further back than vanilla's 4 blocks, so the whole dragon and what it fights stay in
 * view. The extra distance is ray-cast against blocks so the camera never ends up inside a wall.
 *
 * <p>Forge 1.20.1 has no camera-distance event: the protected {@code Camera.move} (SRG m_90568_) is called through
 * reflection after vanilla placed the camera.</p>
 */
@Mod.EventBusSubscriber(modid = ISSTechnomancy.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class DrakeCamera {
    private static boolean riding;
    private static CameraType before = CameraType.FIRST_PERSON;
    private static Method move;
    private static boolean failed;

    private DrakeCamera() {
    }

    private static TechDrake ridden() {
        LocalPlayer p = Minecraft.getInstance().player;
        return p != null && p.getVehicle() instanceof TechDrake d && d.isOwnedBy(p) ? d : null;
    }

    @SubscribeEvent
    public static void onTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        boolean now = ridden() != null;
        if (now && !riding) {
            before = mc.options.getCameraType();
            mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
        } else if (!now && riding) {
            if (mc.options.getCameraType() == CameraType.THIRD_PERSON_BACK) {
                mc.options.setCameraType(before);
            }
        }
        riding = now;
    }

    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void onCamera(ViewportEvent.ComputeCameraAngles event) {
        TechDrake drake = ridden();
        Camera camera = event.getCamera();
        if (drake == null || !camera.isDetached() || failed) {
            return;
        }
        double extra = 3.5 + 4.0 * drake.getModelScale();
        Vector3f look = camera.getLookVector();
        Vec3 from = camera.getPosition();
        Vec3 to = from.subtract(look.x() * extra, look.y() * extra, look.z() * extra);
        BlockHitResult hit = drake.level().clip(new ClipContext(from, to, ClipContext.Block.VISUAL, ClipContext.Fluid.NONE, camera.getEntity()));
        double distance = hit.getType() == HitResult.Type.MISS ? extra : Math.max(0, hit.getLocation().distanceTo(from) - 0.4);
        if (distance <= 0.05) {
            return;
        }
        try {
            if (move == null) {
                move = ObfuscationReflectionHelper.findMethod(Camera.class, "m_90568_", double.class, double.class, double.class);
            }
            move.invoke(camera, -distance, 0.0, 0.0);
        } catch (Exception e) {
            failed = true;
            ISSTechnomancy.LOGGER.warn("Tech Drake camera: could not move the camera back", e);
        }
    }
}
