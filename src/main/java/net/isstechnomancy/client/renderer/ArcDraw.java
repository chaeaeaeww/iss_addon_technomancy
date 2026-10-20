package net.isstechnomancy.client.renderer;

import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix4f;

/**
 * Jagged lightning arcs drawn as crossed double-sided quads in the additive lightning render type (no texture): the
 * pylon power beams and the dragon's shield sparks.
 */
public final class ArcDraw {
    private ArcDraw() {
    }

    public static Vec3[] arc(Vec3 start, Vec3 end, int segments, float jitter, RandomSource random) {
        Vec3[] points = new Vec3[segments + 1];
        points[0] = start;
        points[segments] = end;
        for (int i = 1; i < segments; i++) {
            float t = i / (float) segments;
            float envelope = Mth.sin(t * Mth.PI) * jitter;
            Vec3 j = new Vec3(random.nextFloat() * 2 - 1, random.nextFloat() * 2 - 1, random.nextFloat() * 2 - 1).scale(envelope);
            points[i] = start.lerp(end, t).add(j);
        }
        return points;
    }

    public static void strip(VertexConsumer consumer, Matrix4f matrix, Vec3[] points, Vec3 origin, float width, float r, float g, float b, float a) {
        for (int i = 0; i + 1 < points.length; i++) {
            segment(consumer, matrix, points[i].subtract(origin), points[i + 1].subtract(origin), width, r, g, b, a);
        }
    }

    public static void segment(VertexConsumer consumer, Matrix4f matrix, Vec3 a, Vec3 b, float width, float r, float g, float bl, float alpha) {
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
        vertex(consumer, matrix, a1, r, g, bl, alpha);
        vertex(consumer, matrix, a2, r, g, bl, alpha);
        vertex(consumer, matrix, b2, r, g, bl, alpha);
        vertex(consumer, matrix, b1, r, g, bl, alpha);
        vertex(consumer, matrix, b1, r, g, bl, alpha);
        vertex(consumer, matrix, b2, r, g, bl, alpha);
        vertex(consumer, matrix, a2, r, g, bl, alpha);
        vertex(consumer, matrix, a1, r, g, bl, alpha);
    }

    private static void vertex(VertexConsumer consumer, Matrix4f matrix, Vec3 p, float r, float g, float b, float alpha) {
        consumer.vertex(matrix, (float) p.x, (float) p.y, (float) p.z).color(r, g, b, alpha).endVertex();
    }
}
