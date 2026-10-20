package net.isstechnomancy.entity.boss;

import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.particle.ZapParticleOption;
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;

/**
 * 1.10: instant electric bursts. They replace the lingering expanding shock rings (ArcRing, the ISS shock wave
 * particle) the user found looked like sound waves stuck under the dragon: jagged lightning arcs race out from a point
 * in one tick and are gone, with sparks where they end. Effects only (nothing is damaged here).
 */
public final class ElectricFx {
    /** Style 0 cyan (plain arcs), 1 hextech violet (arcs and end-rod motes), 2 ember (arcs and smoke). */
    public static final int CYAN = 0, VIOLET = 1, EMBER = 2;

    private ElectricFx() {
    }

    /** Arcs racing out flat along the ground from {@code c} to about {@code radius}. */
    public static void burst(ServerLevel level, Vec3 c, float radius, int style) {
        burst(level, c, radius, style, new Vec3(1, 0, 0), new Vec3(0, 0, 1));
    }

    /** Arcs racing out in the upright plane facing {@code yawDeg} (a burst in front of the jaws or the core). */
    public static void burstFacing(ServerLevel level, Vec3 c, float radius, int style, float yawDeg) {
        double yaw = Math.toRadians(yawDeg);
        burst(level, c, radius, style, new Vec3(Math.cos(yaw), 0, Math.sin(yaw)), new Vec3(0, 1, 0));
    }

    /** Arcs racing out in the plane spanned by {@code u} and {@code v} (unit vectors). */
    public static void burst(ServerLevel level, Vec3 c, float radius, int style, Vec3 u, Vec3 v) {
        RandomSource random = level.getRandom();
        int arcs = Mth.clamp((int) (radius * 1.5f) + 6, 6, 26);
        Vec3 normal = u.cross(v);
        for (int k = 0; k < arcs; k++) {
            double a = (k + random.nextDouble() * 0.7) * Math.PI * 2 / arcs;
            Vec3 dir = u.scale(Math.cos(a)).add(v.scale(Math.sin(a)));
            Vec3 side = dir.cross(normal);
            Vec3 p = c;
            for (int s = 1; s <= 3; s++) {
                double r = radius * s / 3.0 * (0.75 + random.nextDouble() * 0.35);
                Vec3 q = c.add(dir.scale(r)).add(side.scale((random.nextDouble() - 0.5) * radius * 0.22))
                        .add(normal.scale(random.nextDouble() * 0.35 * (s == 3 ? 0.4 : 1)));
                level.sendParticles(new ZapParticleOption(q), p.x, p.y, p.z, 1, 0, 0, 0, 0);
                p = q;
            }
            MagicManager.spawnParticles(level, ParticleHelper.ELECTRIC_SPARKS, p.x, p.y, p.z, 2, 0.15, 0.1, 0.15, 0.12, false);
            if (style == VIOLET && k % 2 == 0) {
                MagicManager.spawnParticles(level, ParticleTypes.END_ROD, p.x, p.y, p.z, 1, 0.1, 0.1, 0.1, 0.02, false);
            } else if (style == EMBER && k % 2 == 0) {
                MagicManager.spawnParticles(level, ParticleTypes.LARGE_SMOKE, p.x, p.y, p.z, 1, 0.2, 0.1, 0.2, 0.01, false);
            }
        }
        MagicManager.spawnParticles(level, ParticleHelper.ELECTRIC_SPARKS, c.x, c.y, c.z, 6 + (int) radius, radius * 0.15, 0.2, radius * 0.15, 0.3, false);
    }

    /** A dome of sparks and arcs over a half sphere (the roar's blast). */
    public static void dome(ServerLevel level, Vec3 c, float radius) {
        RandomSource random = level.getRandom();
        int n = Mth.clamp((int) (radius * 2), 10, 36);
        for (int k = 0; k < n; k++) {
            double a = random.nextDouble() * Math.PI * 2;
            double b = random.nextDouble() * Math.PI * 0.5;
            Vec3 dir = new Vec3(Math.cos(a) * Math.cos(b), Math.sin(b), Math.sin(a) * Math.cos(b));
            Vec3 from = c.add(dir.scale(radius * 0.35));
            Vec3 to = c.add(dir.scale(radius * (0.85 + random.nextDouble() * 0.2)));
            level.sendParticles(new ZapParticleOption(to), from.x, from.y, from.z, 1, 0, 0, 0, 0);
            MagicManager.spawnParticles(level, ParticleHelper.ELECTRIC_SPARKS, to.x, to.y, to.z, 2, 0.2, 0.2, 0.2, 0.15, false);
        }
    }
}
