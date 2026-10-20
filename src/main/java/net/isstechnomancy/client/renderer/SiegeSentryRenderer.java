package net.isstechnomancy.client.renderer;

import com.mojang.blaze3d.vertex.PoseStack;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.SiegeSentry;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/**
 * Model: geo/entity/siege_sentry.geo.json — armored twin-cannon turret. The "head" bone (whole turret housing)
 * tracks targets; the stabilizer base stays planted. Glow: textures/entity/siege_sentry_glowmask.png.
 */
public class SiegeSentryRenderer extends GeoEntityRenderer<SiegeSentry> {
    public SiegeSentryRenderer(EntityRendererProvider.Context context) {
        super(context, new DefaultedEntityGeoModel<>(ISSTechnomancy.id("siege_sentry"), true));
        this.shadowRadius = 2.0f;
        addRenderLayer(new AutoGlowingGeoLayer<>(this));
    }

    @Override
    public void render(SiegeSentry entity, float entityYaw, float partialTick, PoseStack poseStack, MultiBufferSource bufferSource, int packedLight) {
        poseStack.pushPose();
        poseStack.scale(SiegeSentry.RENDER_SCALE, SiegeSentry.RENDER_SCALE, SiegeSentry.RENDER_SCALE);
        super.render(entity, entityYaw, partialTick, poseStack, bufferSource, packedLight);
        poseStack.popPose();
    }
}
