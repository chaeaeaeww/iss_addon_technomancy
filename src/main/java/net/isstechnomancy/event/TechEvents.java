package net.isstechnomancy.event;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.boss.TechDragon;
import net.minecraftforge.event.entity.EntityMountEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(modid = ISSTechnomancy.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public class TechEvents {

    /**
     * A target held by the Tech Dragon's Talon Snatch cannot sneak out of its grip.
     */
    @SubscribeEvent
    public static void onMount(EntityMountEvent event) {
        if (event.isDismounting() && event.getEntityBeingMounted() instanceof TechDragon dragon && dragon.isAlive()
                && dragon.isCarrying(event.getEntityMounting())) {
            event.setCanceled(true);
        }
    }
}
