package net.isstechnomancy.client.renderer;

import com.mojang.blaze3d.vertex.PoseStack;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.boss.HextechShell;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.culling.Frustum;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/** The sphere of hextech plates around the dying dragon (2x: 9 block radius). */
public class HextechShellRenderer extends GeoEntityRenderer<HextechShell> {
    public HextechShellRenderer(EntityRendererProvider.Context context) {
        super(context, new DefaultedEntityGeoModel<>(ISSTechnomancy.id("hextech_shell")));
        this.shadowRadius = 0f;
        addRenderLayer(new AutoGlowingGeoLayer<>(this));
    }

    @Override
    public boolean shouldRender(HextechShell entity, Frustum frustum, double x, double y, double z) {
        return true;
    }

    @Override
    public void render(HextechShell entity, float entityYaw, float partialTick, PoseStack poseStack, MultiBufferSource buffers, int packedLight) {
        poseStack.pushPose();
        poseStack.scale(HextechShell.SCALE, HextechShell.SCALE, HextechShell.SCALE);
        super.render(entity, entityYaw, partialTick, poseStack, buffers, packedLight);
        poseStack.popPose();
    }

    @Override
    public RenderType getRenderType(HextechShell animatable, ResourceLocation texture, @Nullable MultiBufferSource bufferSource, float partialTick) {
        return RenderType.entityCutoutNoCull(texture);
    }
}
