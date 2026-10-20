package net.isstechnomancy.block;

import io.redspace.ironsspellbooks.capabilities.magic.MagicManager;
import io.redspace.ironsspellbooks.particle.ZapParticleOption;
import io.redspace.ironsspellbooks.util.ParticleHelper;
import net.isstechnomancy.entity.boss.ElectricFx;
import net.isstechnomancy.entity.boss.TechDragon;
import net.isstechnomancy.registry.TechBlockEntities;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechSounds;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.NotNull;
import software.bernie.geckolib.animatable.GeoBlockEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * 1.10: the Hextech Thunderforge (the Tech Dragon's summoning altar, registry id clockwork_altar). Its clockwork runs
 * (idle animation). Given an Overcharged Dynamo Core it sets it in the cradle on top and the summoning begins (6 s):
 * rolls of thunder coming closer, lightning striking around it, arcs leaping from its four crystals into a ball of
 * lightning that swells over the cradle around the core - then the ball bursts and the dragon is there.
 */
public class HextechForgeBlockEntity extends BlockEntity implements GeoBlockEntity {
    public static final int SUMMON_TICKS = 120;
    /** The ball of lightning's centre above the block's floor (blocks). */
    public static final double ORB_HEIGHT = 2.7;
    private static final RawAnimation IDLE = RawAnimation.begin().thenLoop("idle");
    private static final RawAnimation CHARGING = RawAnimation.begin().thenLoop("charging");

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private boolean hasCore;
    private int summonTicks = -1;

    public HextechForgeBlockEntity(BlockPos pos, BlockState state) {
        super(TechBlockEntities.HEXTECH_FORGE.get(), pos, state);
    }

    public boolean hasCore() {
        return hasCore;
    }

    public boolean isSummoning() {
        return summonTicks >= 0;
    }

    public int getSummonTicks() {
        return summonTicks;
    }

    /** Radius of the ball of lightning {@code ticks} into the summoning (it swells faster and faster). */
    public static float orbRadius(float ticks) {
        float k = Mth.clamp(ticks / SUMMON_TICKS, 0f, 1f);
        return 0.15f + 2.6f * (float) Math.pow(k, 1.6);
    }

    /** Where the four crystal tips are (block-local, x/z from the block's centre). */
    public static final double[][] CRYSTALS = {{6 / 16.0, 17.6 / 16.0, 6 / 16.0}, {-6 / 16.0, 17.6 / 16.0, 6 / 16.0},
            {-6 / 16.0, 17.6 / 16.0, -6 / 16.0}, {6 / 16.0, 17.6 / 16.0, -6 / 16.0}};

    /** Server: the core goes into the cradle and the summoning begins. */
    public void startSummon(Player player) {
        if (level == null || isSummoning()) {
            return;
        }
        hasCore = true;
        summonTicks = 0;
        setChanged();
        sync();
        level.playSound(null, worldPosition, SoundEvents.END_PORTAL_FRAME_FILL, SoundSource.BLOCKS, 1.5f, 0.6f);
        level.playSound(null, worldPosition, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 2f, 0.5f);
        for (Player nearby : level.getEntitiesOfClass(Player.class, new AABB(worldPosition).inflate(48))) {
            nearby.displayClientMessage(Component.translatable("message.iss_technomancy.altar_charging").withStyle(ChatFormatting.AQUA), true);
        }
    }

    public static void tick(Level level, BlockPos pos, BlockState state, HextechForgeBlockEntity be) {
        if (be.summonTicks < 0) {
            return;
        }
        be.summonTicks++;
        if (level instanceof ServerLevel server) {
            be.serverSummonTick(server, pos);
        }
    }

    private void serverSummonTick(ServerLevel server, BlockPos pos) {
        int t = summonTicks;
        Vec3 base = Vec3.atBottomCenterOf(pos);
        Vec3 orb = base.add(0, ORB_HEIGHT, 0);
        float r = orbRadius(t);
        var random = server.getRandom();
        // thunder rolling in, closer and closer
        if (t == 8 || t == 36 || t == 62 || t == 84 || t == 100 || t == 112) {
            float k = t / (float) SUMMON_TICKS;
            server.playSound(null, pos, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.WEATHER, 2f + 4f * k, 0.6f + 0.3f * k);
        }
        // lightning striking around the forge
        if (t >= 24 && t % 14 == 3) {
            double a = random.nextDouble() * Math.PI * 2, d = 5 + random.nextDouble() * 7;
            LightningBolt bolt = EntityType.LIGHTNING_BOLT.create(server);
            if (bolt != null) {
                double x = base.x + Math.cos(a) * d, z = base.z + Math.sin(a) * d;
                bolt.moveTo(x, server.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, Mth.floor(x), Mth.floor(z)), z);
                bolt.setVisualOnly(true);
                server.addFreshEntity(bolt);
            }
        }
        // arcs leaping from the crystals into the swelling ball, sparks crawling over it
        if (t % 3 == 0) {
            double[] c = CRYSTALS[(t / 3) % 4];
            Vec3 tip = base.add(c[0], c[1], c[2]);
            Vec3 to = orb.add(tip.subtract(orb).normalize().scale(r));
            server.sendParticles(new ZapParticleOption(to), tip.x, tip.y, tip.z, 1, 0, 0, 0, 0);
        }
        if (t % 2 == 0) {
            MagicManager.spawnParticles(server, ParticleHelper.ELECTRIC_SPARKS, orb.x, orb.y, orb.z, 2 + t / 20, r * 0.6, r * 0.6, r * 0.6, 0.15, false);
        }
        if (t % 20 == 10) {
            server.playSound(null, pos, SoundEvents.BEACON_AMBIENT, SoundSource.BLOCKS, 2f, 0.6f + t / (float) SUMMON_TICKS);
        }
        if (t >= SUMMON_TICKS) {
            burst(server, pos, orb);
        }
    }

    /** The ball bursts and the dragon is there. */
    private void burst(ServerLevel server, BlockPos pos, Vec3 orb) {
        hasCore = false;
        summonTicks = -1;
        setChanged();
        sync();
        ElectricFx.burst(server, orb, 8f, ElectricFx.VIOLET);
        ElectricFx.burst(server, Vec3.atBottomCenterOf(pos).add(0, 1.05, 0), 10f, ElectricFx.CYAN);
        ElectricFx.dome(server, Vec3.atBottomCenterOf(pos).add(0, 1, 0), 9f);
        MagicManager.spawnParticles(server, ParticleTypes.EXPLOSION_EMITTER, orb.x, orb.y, orb.z, 2, 0.5, 0.5, 0.5, 0, true);
        MagicManager.spawnParticles(server, ParticleTypes.END_ROD, orb.x, orb.y, orb.z, 80, 1.5, 1.5, 1.5, 0.35, true);
        server.playSound(null, pos, SoundEvents.GENERIC_EXPLODE, SoundSource.BLOCKS, 4f, 0.7f);
        server.playSound(null, pos, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.WEATHER, 5f, 0.6f);
        LightningBolt bolt = EntityType.LIGHTNING_BOLT.create(server);
        if (bolt != null) {
            bolt.moveTo(orb.x, pos.getY() + 1, orb.z);
            bolt.setVisualOnly(true);
            server.addFreshEntity(bolt);
        }
        TechDragon dragon = TechEntities.TECH_DRAGON.get().create(server);
        if (dragon == null) {
            return;
        }
        Player nearest = server.getNearestPlayer(orb.x, orb.y, orb.z, 32, false);
        float yaw = nearest != null ? (float) (Mth.atan2(nearest.getZ() - orb.z, nearest.getX() - orb.x) * Mth.RAD_TO_DEG) - 90f : 0f;
        dragon.moveTo(orb.x, pos.getY() + 1.2, orb.z, yaw, 0);
        dragon.finalizeSpawn(server, server.getCurrentDifficultyAt(pos), MobSpawnType.TRIGGERED, null, null);
        server.addFreshEntity(dragon);
        server.playSound(null, pos, TechSounds.TECH_DRAGON_ROAR.get(), SoundSource.HOSTILE, 6f, 0.7f);
        for (Player nearby : server.getEntitiesOfClass(Player.class, new AABB(pos).inflate(64))) {
            nearby.displayClientMessage(Component.translatable("message.iss_technomancy.dragon_awakens").withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.BOLD), false);
        }
    }

    private void sync() {
        if (level != null) {
            level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), 3);
        }
    }

    @Override
    protected void saveAdditional(@NotNull CompoundTag tag) {
        super.saveAdditional(tag);
        tag.putBoolean("HasCore", hasCore);
        tag.putInt("SummonTicks", summonTicks);
    }

    @Override
    public void load(@NotNull CompoundTag tag) {
        super.load(tag);
        hasCore = tag.getBoolean("HasCore");
        summonTicks = tag.contains("SummonTicks") ? tag.getInt("SummonTicks") : -1;
    }

    @Override
    public @NotNull CompoundTag getUpdateTag() {
        CompoundTag tag = super.getUpdateTag();
        saveAdditional(tag);
        return tag;
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }

    @Override
    public AABB getRenderBoundingBox() {
        return new AABB(worldPosition).inflate(4, 6, 4);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 6, state -> state.setAndContinue(isSummoning() ? CHARGING : IDLE)));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
