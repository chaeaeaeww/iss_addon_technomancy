package net.isstechnomancy.client.renderer;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.boss.ArcRing;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.culling.Frustum;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;
import org.joml.Matrix4f;

/**
 * The electric shock ring: an outer ring of crackling lightning (re-jagged every 2 ticks), a wider soft glow band just
 * behind it, a thin bright inner echo and short sparks leaping off the edge. It eases out as it grows and fades.
 */
public class ArcRingRenderer extends EntityRenderer<ArcRing> {
    private static final ResourceLocation UNUSED = ISSTechnomancy.id("textures/entity/arc_welder_beam.png");
    private static final float[][] CORE = {{0.85f, 1.0f, 1.0f}, {0.95f, 0.85f, 1.0f}, {1.0f, 0.8f, 0.55f}};
    private static final float[][] GLOW = {{0.25f, 0.75f, 1.0f}, {0.55f, 0.3f, 1.0f}, {1.0f, 0.35f, 0.1f}};

    public ArcRingRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    @Override
    public boolean shouldRender(@NotNull ArcRing ring, @NotNull Frustum frustum, double x, double y, double z) {
        return ring.distanceToSqr(x, y, z) < 160 * 160;
    }

    @Override
    public void render(@NotNull ArcRing ring, float yaw, float partialTick, @NotNull PoseStack pose, @NotNull MultiBufferSource buffers, int light) {
        float p = ring.progress(partialTick);
        float grow = 1f - (1f - p) * (1f - p) * (1f - p);
        float radius = Math.max(0.2f, ring.getRadius() * grow);
        float fade = 1f - p * p;
        int style = Mth.clamp(ring.getStyle(), 0, 2);
        float[] core = CORE[style], glow = GLOW[style];
        pose.pushPose();
        pose.mulPose(Axis.YP.rotationDegrees(-ring.getRingYaw()));
        pose.mulPose(Axis.XP.rotationDegrees(ring.getRingPitch() - 90f));
        VertexConsumer vc = buffers.getBuffer(RenderType.lightning());
        Matrix4f m = pose.last().pose();
        RandomSource random = RandomSource.create(ring.getId() * 7919L + ring.tickCount / 2);
        int n = Mth.clamp((int) (radius * 5), 18, 96);
        float jitter = Math.min(0.9f, 0.25f + radius * 0.04f);
        Vec3[] outer = new Vec3[n + 1];
        for (int i = 0; i <= n; i++) {
            double a = i * Math.PI * 2 / n;
            double r = radius + (i == n ? 0 : (random.nextFloat() - 0.5f) * jitter);
            outer[i] = new Vec3(Math.cos(a) * r, (random.nextFloat() - 0.5f) * jitter * 0.5, Math.sin(a) * r);
        }
        outer[n] = outer[0];
        float w = 0.08f + radius * 0.012f;
        ArcDraw.strip(vc, m, outer, Vec3.ZERO, w * 3.2f, glow[0], glow[1], glow[2], 0.28f * fade);
        ArcDraw.strip(vc, m, outer, Vec3.ZERO, w, core[0], core[1], core[2], 0.9f * fade);
        // soft band trailing behind the front
        Vec3[] band = new Vec3[n + 1];
        double inner = radius * 0.82;
        for (int i = 0; i <= n; i++) {
            double a = i * Math.PI * 2 / n;
            band[i] = new Vec3(Math.cos(a) * inner, 0, Math.sin(a) * inner);
        }
        ArcDraw.strip(vc, m, band, Vec3.ZERO, w * 5f, glow[0], glow[1], glow[2], 0.12f * fade);
        // thin echo further in
        Vec3[] echo = new Vec3[n + 1];
        double er = radius * 0.6;
        for (int i = 0; i <= n; i++) {
            double a = i * Math.PI * 2 / n;
            echo[i] = new Vec3(Math.cos(a) * (er + (random.nextFloat() - 0.5f) * jitter * 0.6), 0, Math.sin(a) * (er + (random.nextFloat() - 0.5f) * jitter * 0.6));
        }
        echo[n] = echo[0];
        ArcDraw.strip(vc, m, echo, Vec3.ZERO, w * 0.6f, core[0], core[1], core[2], 0.45f * fade * (1f - p));
        // sparks leaping off the edge (upward from the ring plane)
        int sparks = Math.max(4, n / 6);
        for (int s = 0; s < sparks; s++) {
            Vec3 base = outer[random.nextInt(n)];
            Vec3 tip = base.add((random.nextFloat() - 0.5f) * 0.6, (0.4 + random.nextFloat() * 1.2) * (0.4 + radius * 0.06), (random.nextFloat() - 0.5f) * 0.6);
            ArcDraw.strip(vc, m, ArcDraw.arc(base, tip, 3, 0.25f, random), Vec3.ZERO, w * 0.7f, core[0], core[1], core[2], 0.7f * fade);
        }
        pose.popPose();
    }

    @Override
    public @NotNull ResourceLocation getTextureLocation(@NotNull ArcRing ring) {
        return UNUSED;
    }
}
