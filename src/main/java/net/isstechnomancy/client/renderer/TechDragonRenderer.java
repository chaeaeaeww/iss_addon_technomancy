package net.isstechnomancy.client.renderer;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.client.model.TechDragonModel;
import net.isstechnomancy.entity.boss.TechDragon;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.culling.Frustum;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/**
 * Tech Dragon and the summoned Tech Drake (scaled by {@link TechDragon#getModelScale()}). Phase two / overdrive swap to
 * the overcharged texture. Membranes are alpha cut-outs, so the model renders with a no-cull cutout type. While the
 * pylons feed it, a scrolling blue-white hexagon shield sphere surrounds it.
 */
public class TechDragonRenderer extends GeoEntityRenderer<TechDragon> {
    private static final ResourceLocation SHIELD = ISSTechnomancy.id("textures/entity/dragon_shield.png");
    private static final int RINGS = 18, SEGMENTS = 32;

    public TechDragonRenderer(EntityRendererProvider.Context context) {
        super(context, new TechDragonModel());
        this.shadowRadius = 3.5f;
        addRenderLayer(new AutoGlowingGeoLayer<>(this));
    }

    @Override
    public boolean shouldRender(TechDragon entity, Frustum frustum, double x, double y, double z) {
        return entity.distanceToSqr(x, y, z) < 256 * 256;
    }

    @Override
    public void render(TechDragon entity, float entityYaw, float partialTick, PoseStack poseStack, MultiBufferSource bufferSource, int packedLight) {
        float scale = entity.getModelScale();
        this.shadowRadius = 3.0f * scale;
        poseStack.pushPose();
        poseStack.scale(scale, scale, scale);
        super.render(entity, entityYaw, partialTick, poseStack, bufferSource, packedLight);
        poseStack.popPose();
        if (entity.isShielded()) {
            renderShield(entity, partialTick, poseStack, bufferSource, scale);
        }
        if (entity.getState() == TechDragon.State.CORE_BEAM) {
            renderCoreBeam(entity, partialTick, poseStack, bufferSource, scale);
        }
    }

    /** 1.9: the hextech core beam - a violet glow sheath, a cyan body and a white-hot core, three crackling arcs winding
     * around it and a flare where it lands. Additive, so it lights up the dark. */
    private void renderCoreBeam(TechDragon entity, float partialTick, PoseStack poseStack, MultiBufferSource buffers, float scale) {
        Vec3 origin = new Vec3(Mth.lerp(partialTick, entity.xo, entity.getX()), Mth.lerp(partialTick, entity.yo, entity.getY()), Mth.lerp(partialTick, entity.zo, entity.getZ()));
        Vec3 from = entity.corePosition().subtract(origin);
        Vec3 to = entity.getBeamEnd().subtract(origin);
        if (to.subtract(from).lengthSqr() < 1) {
            return;
        }
        float t = entity.tickCount + partialTick;
        float pulse = 1f + 0.15f * Mth.sin(t * 1.7f);
        VertexConsumer vc = buffers.getBuffer(RenderType.lightning());
        Matrix4f m = poseStack.last().pose();
        ArcDraw.segment(vc, m, from, to, 2.6f * scale * 0.5f * pulse, 0.55f, 0.25f, 1.0f, 0.22f);
        ArcDraw.segment(vc, m, from, to, 1.5f * scale * 0.5f * pulse, 0.3f, 0.8f, 1.0f, 0.45f);
        ArcDraw.segment(vc, m, from, to, 0.6f * scale * 0.5f, 0.95f, 0.98f, 1.0f, 0.95f);
        Vec3 dir = to.subtract(from).normalize();
        Vec3 side = dir.cross(new Vec3(0, 1, 0));
        side = side.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : side.normalize();
        Vec3 up = dir.cross(side).normalize();
        double len = to.subtract(from).length();
        RandomSource random = RandomSource.create(entity.getId() * 131L + entity.tickCount / 2);
        for (int k = 0; k < 3; k++) {
            int n = Math.max(6, (int) (len * 1.5));
            Vec3[] pts = new Vec3[n + 1];
            for (int i = 0; i <= n; i++) {
                double u = i / (double) n;
                double a = u * len * 1.3 + k * Math.PI * 2 / 3 + t * 0.4;
                double r = 1.1 * scale * 0.5 * (0.8 + 0.4 * random.nextFloat());
                pts[i] = from.add(dir.scale(u * len)).add(side.scale(Math.cos(a) * r)).add(up.scale(Math.sin(a) * r));
            }
            ArcDraw.strip(vc, m, pts, Vec3.ZERO, 0.08f * scale, 0.8f, 0.6f, 1.0f, 0.75f);
        }
        for (int k = 0; k < 6; k++) {
            Vec3 tip = to.add((random.nextFloat() - 0.5) * 3 * scale, random.nextFloat() * 2 * scale, (random.nextFloat() - 0.5) * 3 * scale);
            ArcDraw.strip(vc, m, ArcDraw.arc(to, tip, 4, 0.5f, random), Vec3.ZERO, 0.1f * scale, 0.9f, 0.85f, 1.0f, 0.8f);
        }
    }

    private void renderShield(TechDragon entity, float partialTick, PoseStack poseStack, MultiBufferSource buffers, float scale) {
        float t = entity.tickCount + partialTick;
        float radius = 7.6f * scale * (1f + 0.015f * Mth.sin(t * 0.3f));
        VertexConsumer vc = buffers.getBuffer(RenderType.energySwirl(SHIELD, t * 0.004f % 1f, t * 0.002f % 1f));
        poseStack.pushPose();
        poseStack.translate(0, 2.2 * scale, 0);
        Matrix4f m = poseStack.last().pose();
        Matrix3f n = poseStack.last().normal();
        float pulse = 0.55f + 0.2f * Mth.sin(t * 0.25f);
        for (int i = 0; i < RINGS; i++) {
            float v0 = i / (float) RINGS, v1 = (i + 1) / (float) RINGS;
            float th0 = v0 * Mth.PI, th1 = v1 * Mth.PI;
            for (int j = 0; j < SEGMENTS; j++) {
                float u0 = j / (float) SEGMENTS, u1 = (j + 1) / (float) SEGMENTS;
                float ph0 = u0 * Mth.TWO_PI, ph1 = u1 * Mth.TWO_PI;
                vertex(vc, m, n, radius, th0, ph0, u0 * 6, v0 * 3, pulse);
                vertex(vc, m, n, radius, th1, ph0, u0 * 6, v1 * 3, pulse);
                vertex(vc, m, n, radius, th1, ph1, u1 * 6, v1 * 3, pulse);
                vertex(vc, m, n, radius, th0, ph1, u1 * 6, v0 * 3, pulse);
            }
        }
        poseStack.popPose();
    }

    private static void vertex(VertexConsumer vc, Matrix4f m, Matrix3f n, float r, float theta, float phi, float u, float v, float a) {
        float sx = Mth.sin(theta) * Mth.cos(phi), sy = Mth.cos(theta) * 0.8f, sz = Mth.sin(theta) * Mth.sin(phi);
        vc.vertex(m, sx * r, sy * r, sz * r).color(0.55f * a, 0.8f * a, 1.0f * a, 1f).uv(u, v).overlayCoords(OverlayTexture.NO_OVERLAY)
                .uv2(LightTexture.FULL_BRIGHT).normal(n, sx, sy, sz).endVertex();
    }

    @Override
    public RenderType getRenderType(TechDragon animatable, ResourceLocation texture, @Nullable MultiBufferSource bufferSource, float partialTick) {
        return RenderType.entityCutoutNoCull(texture);
    }

    @Override
    protected float getDeathMaxRotation(TechDragon animatable) {
        return 0f;
    }

    @Override
    public boolean shouldShowName(TechDragon animatable) {
        return animatable.shouldShowName();
    }
}
