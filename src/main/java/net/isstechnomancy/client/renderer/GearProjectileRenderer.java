package net.isstechnomancy.client.renderer;

import com.mojang.blaze3d.vertex.PoseStack;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.GearProjectile;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;

/**
 * Model: geo/entity/gear_projectile.geo.json, animation: animations/entity/gear_projectile.animation.json ("spin").
 * GeckoLib applies the entity yaw, which keeps the gear's disk aligned with its direction of travel.
 */
public class GearProjectileRenderer extends GeoEntityRenderer<GearProjectile> {
    public GearProjectileRenderer(EntityRendererProvider.Context context) {
        super(context, new DefaultedEntityGeoModel<>(ISSTechnomancy.id("gear_projectile")));
        this.shadowRadius = 0.1f;
    }

    @Override
    public void render(GearProjectile entity, float entityYaw, float partialTick, PoseStack poseStack, MultiBufferSource bufferSource, int packedLight) {
        float scale = entity.getScale();
        poseStack.pushPose();
        poseStack.scale(scale, scale, scale);
        super.render(entity, entityYaw, partialTick, poseStack, bufferSource, packedLight);
        poseStack.popPose();
    }
}
