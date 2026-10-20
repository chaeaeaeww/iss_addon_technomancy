package net.isstechnomancy.client.renderer;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.BrassSentry;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/**
 * Model: geo/entity/brass_sentry.geo.json. The "head" bone follows the entity's look direction
 * (DefaultedEntityGeoModel with head turning enabled) while the tripod base stays fixed.
 * The coil and muzzle glow through textures/entity/brass_sentry_glowmask.png.
 */
public class BrassSentryRenderer extends GeoEntityRenderer<BrassSentry> {
    public BrassSentryRenderer(EntityRendererProvider.Context context) {
        super(context, new DefaultedEntityGeoModel<>(ISSTechnomancy.id("brass_sentry"), true));
        this.shadowRadius = 0.5f;
        addRenderLayer(new AutoGlowingGeoLayer<>(this));
    }
}
