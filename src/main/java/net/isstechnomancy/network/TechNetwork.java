package net.isstechnomancy.network;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.boss.TechDrake;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.network.NetworkDirection;
import net.minecraftforge.network.NetworkEvent;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.simple.SimpleChannel;

import java.util.Optional;
import java.util.function.Supplier;

/**
 * Packets from a player riding their Tech Drake: held controls (climb, descend, sprint, breath) and one-shot actions
 * (bite/claw, Thunder Roar, jaw grab). The rider's client moves the drake itself; the server only runs attacks.
 */
public final class TechNetwork {
    private static final String VERSION = "1";
    public static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(ISSTechnomancy.id("main"), () -> VERSION, VERSION::equals, VERSION::equals);

    private TechNetwork() {
    }

    public static void register() {
        CHANNEL.registerMessage(0, RiderInput.class, RiderInput::encode, RiderInput::decode, RiderInput::handle, Optional.of(NetworkDirection.PLAY_TO_SERVER));
        CHANNEL.registerMessage(1, RiderAction.class, RiderAction::encode, RiderAction::decode, RiderAction::handle, Optional.of(NetworkDirection.PLAY_TO_SERVER));
    }

    private static TechDrake ownDrake(ServerPlayer player) {
        return player != null && player.getVehicle() instanceof TechDrake drake && drake.isOwnedBy(player) ? drake : null;
    }

    public record RiderInput(int flags) {
        public static final int UP = 1, DOWN = 2, SPRINT = 4, BREATH = 8;

        public void encode(FriendlyByteBuf buf) {
            buf.writeByte(flags);
        }

        public static RiderInput decode(FriendlyByteBuf buf) {
            return new RiderInput(buf.readByte());
        }

        public void handle(Supplier<NetworkEvent.Context> ctx) {
            ctx.get().enqueueWork(() -> {
                TechDrake drake = ownDrake(ctx.get().getSender());
                if (drake != null) {
                    drake.inputUp = (flags & UP) != 0;
                    drake.inputDown = (flags & DOWN) != 0;
                    drake.inputSprint = (flags & SPRINT) != 0;
                    drake.inputBreath = (flags & BREATH) != 0;
                }
            });
            ctx.get().setPacketHandled(true);
        }
    }

    public record RiderAction(int action) {
        public void encode(FriendlyByteBuf buf) {
            buf.writeByte(action);
        }

        public static RiderAction decode(FriendlyByteBuf buf) {
            return new RiderAction(buf.readByte());
        }

        public void handle(Supplier<NetworkEvent.Context> ctx) {
            ctx.get().enqueueWork(() -> {
                TechDrake drake = ownDrake(ctx.get().getSender());
                TechDrake.Action[] all = TechDrake.Action.values();
                if (drake != null && action >= 0 && action < all.length) {
                    drake.riderAction(all[action]);
                }
            });
            ctx.get().setPacketHandled(true);
        }
    }
}
