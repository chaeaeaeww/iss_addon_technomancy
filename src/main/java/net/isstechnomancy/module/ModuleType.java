package net.isstechnomancy.module;

import net.minecraft.ChatFormatting;

/**
 * Staff module families. Each slotted module adds its tier (1-3) to the family level; levels of the same family stack
 * up to {@link #MAX_LEVEL}. Only Technomancy spells cast while holding a Clockwork Staff read these levels.
 */
public enum ModuleType {
    /** Extra projectiles / forks / wider cones. */
    SPLITTER("splitter", ChatFormatting.GOLD),
    /** Bigger projectiles and more damage. */
    CALIBER("caliber", ChatFormatting.RED),
    /** More constructs per cast and tougher constructs. */
    ASSEMBLER("assembler", ChatFormatting.GREEN),
    /** Staff attributes: cooldown reduction, cast speed and Technomancy power. */
    CAPACITOR("capacitor", ChatFormatting.YELLOW),
    /** Technomancy hits arc chain lightning to nearby enemies. */
    TESLA("tesla", ChatFormatting.AQUA);

    public static final int MAX_LEVEL = 5;

    private final String id;
    private final ChatFormatting color;

    ModuleType(String id, ChatFormatting color) {
        this.id = id;
        this.color = color;
    }

    public String id() {
        return id;
    }

    public ChatFormatting color() {
        return color;
    }

    public String translationKey() {
        return "module.iss_technomancy." + id;
    }
}
