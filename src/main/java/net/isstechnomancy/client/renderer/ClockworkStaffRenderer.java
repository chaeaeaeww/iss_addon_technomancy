package net.isstechnomancy.client.renderer;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.item.ClockworkStaffItem;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import software.bernie.geckolib.model.DefaultedItemGeoModel;
import software.bernie.geckolib.renderer.GeoItemRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/**
 * Model: geo/item/clockwork_staff.geo.json, animation "idle". The GUI uses the flat icon through the
 * forge:separate_transforms item model, so this renderer only runs in hands, on the ground and in item frames.
 */
public final class ClockworkStaffRenderer {
    private ClockworkStaffRenderer() {
    }

    public static BlockEntityWithoutLevelRenderer create() {
        GeoItemRenderer<ClockworkStaffItem> renderer = new GeoItemRenderer<>(new DefaultedItemGeoModel<ClockworkStaffItem>(ISSTechnomancy.id("clockwork_staff")) {
            // 1.9: each staff item (clockwork, hextech and its star levels) has its own model and texture
            @Override
            public net.minecraft.resources.ResourceLocation getModelResource(ClockworkStaffItem item) {
                return ISSTechnomancy.id("geo/item/" + item.getModelName() + ".geo.json");
            }

            @Override
            public net.minecraft.resources.ResourceLocation getTextureResource(ClockworkStaffItem item) {
                return ISSTechnomancy.id("textures/item/" + item.getModelName() + ".png");
            }

            @Override
            public net.minecraft.resources.ResourceLocation getAnimationResource(ClockworkStaffItem item) {
                return ISSTechnomancy.id("animations/item/" + item.getModelName() + ".animation.json");
            }
        });
        renderer.addRenderLayer(new AutoGlowingGeoLayer<>(renderer));
        return renderer;
    }
}
