package net.isstechnomancy.client.renderer;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.ArcWelderBeam;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.culling.Frustum;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix4f;

/**
 * Draws the welding arc as a jagged two-layer bolt between the caster's hand and the trace end point.
 * The zig-zag is re-seeded every 2 ticks so the arc crackles. Uses the additive lightning render type,
 * so no texture is required.
 */
public class ArcWelderBeamRenderer extends EntityRenderer<ArcWelderBeam> {
    private static final ResourceLocation UNUSED_TEXTURE = ISSTechnomancy.id("textures/entity/arc_welder_beam.png");
    private static final int SEGMENTS = 8;
    private static final float MAX_JITTER = 0.18f;

    // Outer glow: cyan arc color
    private static final float OUTER_R = 0x4F / 255f, OUTER_G = 0xE3 / 255f, OUTER_B = 0xF0 / 255f, OUTER_A = 0.35f, OUTER_WIDTH = 0.14f;
    // Core: near-white
    private static final float CORE_R = 0.9f, CORE_G = 1.0f, CORE_B = 1.0f, CORE_A = 0.9f, CORE_WIDTH = 0.05f;

    public ArcWelderBeamRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    @Override
    public boolean shouldRender(ArcWelderBeam entity, Frustum frustum, double camX, double camY, double camZ) {
        return true;
    }

    @Override
    public void render(ArcWelderBeam beam, float entityYaw, float partialTick, PoseStack poseStack, MultiBufferSource bufferSource, int packedLight) {
        LivingEntity owner = beam.getOwner();
        if (owner == null) {
            return;
        }
        Vec3 origin = new Vec3(Mth.lerp(partialTick, beam.xo, beam.getX()), Mth.lerp(partialTick, beam.yo, beam.getY()), Mth.lerp(partialTick, beam.zo, beam.getZ()));
        Vec3 look = owner.getViewVector(partialTick);
        Vec3 right = look.cross(new Vec3(0, 1, 0));
        right = right.lengthSqr() < 1.0E-4 ? new Vec3(1, 0, 0) : right.normalize();
        Vec3 start = owner.getEyePosition(partialTick).add(look.scale(0.6)).add(right.scale(0.25)).add(0, -0.3, 0);
        Vec3 end = ArcWelderBeam.trace(beam.level(), owner, partialTick).getLocation();

        Vec3[] points = buildArc(start, end, RandomSource.create(beam.getId() * 31L + beam.tickCount / 2));

        VertexConsumer consumer = bufferSource.getBuffer(RenderType.lightning());
        Matrix4f matrix = poseStack.last().pose();
        for (int i = 0; i < SEGMENTS; i++) {
            Vec3 a = points[i].subtract(origin);
            Vec3 b = points[i + 1].subtract(origin);
            drawSegment(consumer, matrix, a, b, OUTER_WIDTH, OUTER_R, OUTER_G, OUTER_B, OUTER_A);
            drawSegment(consumer, matrix, a, b, CORE_WIDTH, CORE_R, CORE_G, CORE_B, CORE_A);
        }
        super.render(beam, entityYaw, partialTick, poseStack, bufferSource, packedLight);
    }

    private static Vec3[] buildArc(Vec3 start, Vec3 end, RandomSource random) {
        Vec3[] points = new Vec3[SEGMENTS + 1];
        points[0] = start;
        points[SEGMENTS] = end;
        for (int i = 1; i < SEGMENTS; i++) {
            float t = i / (float) SEGMENTS;
            // Jitter is strongest mid-arc and pinned at both ends.
            float envelope = Mth.sin(t * Mth.PI) * MAX_JITTER;
            Vec3 jitter = new Vec3(random.nextFloat() * 2 - 1, random.nextFloat() * 2 - 1, random.nextFloat() * 2 - 1).scale(envelope);
            points[i] = start.lerp(end, t).add(jitter);
        }
        return points;
    }

    /**
     * Two perpendicular double-sided quads ("cross" billboard) so the arc reads from any angle.
     */
    private static void drawSegment(VertexConsumer consumer, Matrix4f matrix, Vec3 a, Vec3 b, float width, float r, float g, float bl, float alpha) {
        Vec3 direction = b.subtract(a);
        if (direction.lengthSqr() < 1.0E-6) {
            return;
        }
        direction = direction.normalize();
        Vec3 side = direction.cross(new Vec3(0, 1, 0));
        side = side.lengthSqr() < 1.0E-4 ? new Vec3(1, 0, 0) : side.normalize();
        Vec3 up = direction.cross(side).normalize();
        quad(consumer, matrix, a, b, side.scale(width * 0.5), r, g, bl, alpha);
        quad(consumer, matrix, a, b, up.scale(width * 0.5), r, g, bl, alpha);
    }

    private static void quad(VertexConsumer consumer, Matrix4f matrix, Vec3 a, Vec3 b, Vec3 offset, float r, float g, float bl, float alpha) {
        Vec3 a1 = a.add(offset), a2 = a.subtract(offset), b1 = b.add(offset), b2 = b.subtract(offset);
        // front
        vertex(consumer, matrix, a1, r, g, bl, alpha);
        vertex(consumer, matrix, a2, r, g, bl, alpha);
        vertex(consumer, matrix, b2, r, g, bl, alpha);
        vertex(consumer, matrix, b1, r, g, bl, alpha);
        // back
        vertex(consumer, matrix, b1, r, g, bl, alpha);
        vertex(consumer, matrix, b2, r, g, bl, alpha);
        vertex(consumer, matrix, a2, r, g, bl, alpha);
        vertex(consumer, matrix, a1, r, g, bl, alpha);
    }

    private static void vertex(VertexConsumer consumer, Matrix4f matrix, Vec3 position, float r, float g, float b, float alpha) {
        consumer.vertex(matrix, (float) position.x, (float) position.y, (float) position.z).color(r, g, b, alpha).endVertex();
    }

    @Override
    public ResourceLocation getTextureLocation(ArcWelderBeam entity) {
        return UNUSED_TEXTURE;
    }
}
