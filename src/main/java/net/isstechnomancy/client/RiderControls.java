package net.isstechnomancy.client;

import com.mojang.blaze3d.platform.InputConstants;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.boss.TechDrake;
import net.isstechnomancy.network.TechNetwork;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.InputEvent;
import net.minecraftforge.client.event.RegisterKeyMappingsEvent;
import net.minecraftforge.client.settings.KeyConflictContext;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.lwjgl.glfw.GLFW;

/**
 * Riding the Tech Drake: Space climbs / takes off (a tap when flying low lands), Descend (Left Ctrl) sinks / lands,
 * holding forward speeds up, left click bites or rakes, holding right click (or C) breathes lightning, Z bites, X rakes,
 * V calls the lightning storm, R roars, G grabs. While riding, clicks go to the drake
 * instead of breaking blocks or using items.
 */
public final class RiderControls {
    private static final String CATEGORY = "key.categories.iss_technomancy";
    public static final KeyMapping DESCEND = new KeyMapping("key.iss_technomancy.drake_descend", KeyConflictContext.IN_GAME,
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_LEFT_CONTROL, CATEGORY);
    public static final KeyMapping ROAR = new KeyMapping("key.iss_technomancy.drake_roar", KeyConflictContext.IN_GAME,
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_R, CATEGORY);
    public static final KeyMapping GRAB = new KeyMapping("key.iss_technomancy.drake_grab", KeyConflictContext.IN_GAME,
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_G, CATEGORY);
    public static final KeyMapping BITE = new KeyMapping("key.iss_technomancy.drake_bite", KeyConflictContext.IN_GAME,
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_Z, CATEGORY);
    public static final KeyMapping CLAW = new KeyMapping("key.iss_technomancy.drake_claw", KeyConflictContext.IN_GAME,
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_X, CATEGORY);
    public static final KeyMapping BREATH = new KeyMapping("key.iss_technomancy.drake_breath", KeyConflictContext.IN_GAME,
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_C, CATEGORY);
    public static final KeyMapping STORM = new KeyMapping("key.iss_technomancy.drake_storm", KeyConflictContext.IN_GAME,
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_V, CATEGORY);

    private static int lastFlags = -1;

    private RiderControls() {
    }

    private static TechDrake ridden() {
        LocalPlayer p = Minecraft.getInstance().player;
        return p != null && p.getVehicle() instanceof TechDrake d && d.isOwnedBy(p) ? d : null;
    }

    @Mod.EventBusSubscriber(modid = ISSTechnomancy.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static final class Keys {
        @SubscribeEvent
        public static void register(RegisterKeyMappingsEvent event) {
            event.register(DESCEND);
            event.register(ROAR);
            event.register(GRAB);
            event.register(BITE);
            event.register(CLAW);
            event.register(BREATH);
            event.register(STORM);
        }
    }

    @Mod.EventBusSubscriber(modid = ISSTechnomancy.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
    public static final class Events {
        @SubscribeEvent
        public static void onTick(TickEvent.ClientTickEvent event) {
            if (event.phase != TickEvent.Phase.START) {
                return;
            }
            Minecraft mc = Minecraft.getInstance();
            TechDrake drake = ridden();
            if (drake == null || mc.screen != null) {
                lastFlags = -1;
                if (drake != null) {
                    drake.inputUp = drake.inputDown = drake.inputBreath = false;
                }
                return;
            }
            drake.inputUp = mc.options.keyJump.isDown();
            drake.inputDown = DESCEND.isDown();
            drake.inputBreath = mc.options.keyUse.isDown() || BREATH.isDown();
            int flags = (drake.inputUp ? TechNetwork.RiderInput.UP : 0) | (drake.inputDown ? TechNetwork.RiderInput.DOWN : 0)
                    | (drake.inputSprint ? TechNetwork.RiderInput.SPRINT : 0) | (drake.inputBreath ? TechNetwork.RiderInput.BREATH : 0);
            if (flags != lastFlags) {
                lastFlags = flags;
                TechNetwork.CHANNEL.sendToServer(new TechNetwork.RiderInput(flags));
            }
            while (ROAR.consumeClick()) {
                TechNetwork.CHANNEL.sendToServer(new TechNetwork.RiderAction(TechDrake.Action.ROAR.ordinal()));
            }
            while (GRAB.consumeClick()) {
                TechNetwork.CHANNEL.sendToServer(new TechNetwork.RiderAction(TechDrake.Action.GRAB.ordinal()));
            }
            while (BITE.consumeClick()) {
                TechNetwork.CHANNEL.sendToServer(new TechNetwork.RiderAction(TechDrake.Action.BITE.ordinal()));
            }
            while (CLAW.consumeClick()) {
                TechNetwork.CHANNEL.sendToServer(new TechNetwork.RiderAction(TechDrake.Action.CLAW.ordinal()));
            }
            while (STORM.consumeClick()) {
                TechNetwork.CHANNEL.sendToServer(new TechNetwork.RiderAction(TechDrake.Action.STORM.ordinal()));
            }
        }

        @SubscribeEvent
        public static void onClick(InputEvent.InteractionKeyMappingTriggered event) {
            if (ridden() == null) {
                return;
            }
            if (event.isAttack()) {
                TechNetwork.CHANNEL.sendToServer(new TechNetwork.RiderAction(TechDrake.Action.ATTACK.ordinal()));
                event.setSwingHand(false);
                event.setCanceled(true);
            } else if (event.isUseItem()) {
                // held right click is read every tick as the breath control
                event.setSwingHand(false);
                event.setCanceled(true);
            }
        }
    }
}
