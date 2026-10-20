package net.isstechnomancy.client.renderer;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.MagneticField;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import org.jetbrains.annotations.NotNull;
import org.joml.Matrix3f;
import org.joml.Matrix4f;

/**
 * Two counter-rotating emissive sigils on the ground (textures/entity/magnetic_field.png and _inner.png) under a
 * translucent hemisphere (magnetic_field_dome.png) that marks the area the field acts on, fading in and out.
 */
public class MagneticFieldRenderer extends EntityRenderer<MagneticField> {
    private static final ResourceLocation OUTER = ISSTechnomancy.id("textures/entity/magnetic_field.png");
    private static final ResourceLocation INNER = ISSTechnomancy.id("textures/entity/magnetic_field_inner.png");
    private static final ResourceLocation DOME = ISSTechnomancy.id("textures/entity/magnetic_field_dome.png");
    private static final int SEGMENTS = 40;
    private static final int RINGS = 10;

    public MagneticFieldRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    @Override
    public void render(MagneticField field, float yaw, float partialTick, @NotNull PoseStack poseStack, @NotNull MultiBufferSource buffers, int light) {
        float age = field.tickCount + partialTick;
        float fadeIn = Mth.clamp(age / 10f, 0, 1);
        float fadeOut = Mth.clamp((field.getDuration() - age) / 15f, 0, 1);
        float alpha = fadeIn * fadeOut;
        float r = field.getRadius();
        poseStack.pushPose();
        poseStack.translate(0, 0.06, 0);
        poseStack.pushPose();
        poseStack.mulPose(Axis.YP.rotationDegrees(age * 1.2f));
        disc(poseStack, buffers.getBuffer(RenderType.entityTranslucentEmissive(OUTER)), r, alpha);
        poseStack.popPose();
        poseStack.translate(0, 0.02, 0);
        poseStack.mulPose(Axis.YP.rotationDegrees(-age * 2.4f));
        disc(poseStack, buffers.getBuffer(RenderType.entityTranslucentEmissive(INNER)), r * 0.55f, alpha);
        poseStack.popPose();
        // the dome itself: the field only acts inside this upper hemisphere
        float pulse = 0.85f + 0.15f * Mth.sin(age * 0.15f);
        dome(poseStack, buffers.getBuffer(RenderType.entityTranslucentEmissive(DOME)), r, alpha * pulse, age * 0.004f, field.isOvercharged());
        super.render(field, yaw, partialTick, poseStack, buffers, light);
    }

    private static void disc(PoseStack poseStack, VertexConsumer vc, float r, float alpha) {
        Matrix4f m = poseStack.last().pose();
        Matrix3f n = poseStack.last().normal();
        int a = (int) (alpha * 220);
        int light = LightTexture.FULL_BRIGHT;
        vc.vertex(m, -r, 0, -r).color(255, 255, 255, a).uv(0, 0).overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(n, 0, 1, 0).endVertex();
        vc.vertex(m, -r, 0, r).color(255, 255, 255, a).uv(0, 1).overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(n, 0, 1, 0).endVertex();
        vc.vertex(m, r, 0, r).color(255, 255, 255, a).uv(1, 1).overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(n, 0, 1, 0).endVertex();
        vc.vertex(m, r, 0, -r).color(255, 255, 255, a).uv(1, 0).overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(n, 0, 1, 0).endVertex();
        // opposite winding so the sigil is visible whichever way the render type culls
        vc.vertex(m, r, 0, -r).color(255, 255, 255, a).uv(1, 0).overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(n, 0, 1, 0).endVertex();
        vc.vertex(m, r, 0, r).color(255, 255, 255, a).uv(1, 1).overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(n, 0, 1, 0).endVertex();
        vc.vertex(m, -r, 0, r).color(255, 255, 255, a).uv(0, 1).overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(n, 0, 1, 0).endVertex();
        vc.vertex(m, -r, 0, -r).color(255, 255, 255, a).uv(0, 0).overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(n, 0, 1, 0).endVertex();
    }

    /** Latitude/longitude hemisphere; the texture scrolls around it and fades towards the top. */
    private static void dome(PoseStack poseStack, VertexConsumer vc, float r, float alpha, float scroll, boolean overcharged) {
        Matrix4f m = poseStack.last().pose();
        Matrix3f n = poseStack.last().normal();
        int light = LightTexture.FULL_BRIGHT;
        int red = overcharged ? 255 : 200;
        int green = overcharged ? 190 : 255;
        int blue = overcharged ? 120 : 255;
        for (int ring = 0; ring < RINGS; ring++) {
            float t0 = ring / (float) RINGS;
            float t1 = (ring + 1) / (float) RINGS;
            float p0 = t0 * Mth.HALF_PI;
            float p1 = t1 * Mth.HALF_PI;
            // strongest at the ground rim, fading near the top
            int a0 = (int) (alpha * 200 * (1f - t0 * 0.7f));
            int a1 = (int) (alpha * 200 * (1f - t1 * 0.7f));
            for (int seg = 0; seg < SEGMENTS; seg++) {
                float s0 = seg / (float) SEGMENTS;
                float s1 = (seg + 1) / (float) SEGMENTS;
                float q0 = s0 * Mth.TWO_PI;
                float q1 = s1 * Mth.TWO_PI;
                float u0 = s0 * 4 + scroll;
                float u1 = s1 * 4 + scroll;
                domeVertex(vc, m, n, r, p0, q0, u0, 1 - t0, red, green, blue, a0, light);
                domeVertex(vc, m, n, r, p0, q1, u1, 1 - t0, red, green, blue, a0, light);
                domeVertex(vc, m, n, r, p1, q1, u1, 1 - t1, red, green, blue, a1, light);
                domeVertex(vc, m, n, r, p1, q0, u0, 1 - t1, red, green, blue, a1, light);
            }
        }
    }

    private static void domeVertex(VertexConsumer vc, Matrix4f m, Matrix3f n, float r, float lat, float lon, float u, float v,
                                   int red, int green, int blue, int a, int light) {
        float horizontal = Mth.cos(lat);
        float x = horizontal * Mth.cos(lon);
        float y = Mth.sin(lat);
        float z = horizontal * Mth.sin(lon);
        vc.vertex(m, x * r, y * r, z * r).color(red, green, blue, a).uv(u, v).overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(n, x, y, z).endVertex();
    }

    @Override
    public boolean shouldRender(@NotNull MagneticField field, @NotNull net.minecraft.client.renderer.culling.Frustum frustum, double x, double y, double z) {
        float r = field.getRadius();
        return frustum.isVisible(new net.minecraft.world.phys.AABB(field.getX() - r, field.getY() - 0.5, field.getZ() - r, field.getX() + r, field.getY() + r, field.getZ() + r));
    }

    @Override
    public @NotNull ResourceLocation getTextureLocation(@NotNull MagneticField field) {
        return OUTER;
    }
}
