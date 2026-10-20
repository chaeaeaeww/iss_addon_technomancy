package net.isstechnomancy.client.particle;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.core.particles.SimpleParticleType;
import org.jetbrains.annotations.NotNull;

/**
 * Emissive cyan mote: no gravity, flickers and shrinks to nothing.
 */
public class ArcMoteParticle extends TextureSheetParticle {
    private final float startSize;

    protected ArcMoteParticle(ClientLevel level, double x, double y, double z, double xd, double yd, double zd, SpriteSet sprites) {
        super(level, x, y, z, xd, yd, zd);
        this.xd = xd;
        this.yd = yd;
        this.zd = zd;
        this.gravity = 0;
        this.friction = 0.85f;
        this.lifetime = 8 + random.nextInt(7);
        this.startSize = this.quadSize * (0.35f + random.nextFloat() * 0.3f);
        this.quadSize = startSize;
        this.hasPhysics = false;
        this.pickSprite(sprites);
        // #4FE3F0 tinted slightly toward white for the hot core
        this.setColor(0.45f + random.nextFloat() * 0.2f, 0.9f, 0.95f);
    }

    @Override
    public void tick() {
        super.tick();
        float progress = age / (float) lifetime;
        this.quadSize = startSize * (1.0f - progress);
        this.alpha = (age % 2 == 0 ? 1.0f : 0.6f) * (1.0f - progress * 0.5f);
    }

    @Override
    protected int getLightColor(float partialTick) {
        return 0xF000F0;
    }

    @Override
    public @NotNull ParticleRenderType getRenderType() {
        return ParticleRenderType.PARTICLE_SHEET_TRANSLUCENT;
    }

    public static class Provider implements ParticleProvider<SimpleParticleType> {
        private final SpriteSet sprites;

        public Provider(SpriteSet sprites) {
            this.sprites = sprites;
        }

        @Override
        public Particle createParticle(@NotNull SimpleParticleType type, @NotNull ClientLevel level, double x, double y, double z, double xd, double yd, double zd) {
            return new ArcMoteParticle(level, x, y, z, xd, yd, zd, sprites);
        }
    }
}
