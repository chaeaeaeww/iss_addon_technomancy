package net.isstechnomancy.module;

import java.util.EnumMap;
import java.util.Map;

/**
 * Aggregated module levels of a Clockwork Staff (each family capped at {@link ModuleType#MAX_LEVEL}), plus the derived
 * numbers every Technomancy spell uses.
 */
public final class ModuleStats {
    public static final ModuleStats NONE = new ModuleStats(new EnumMap<>(ModuleType.class));

    private final Map<ModuleType, Integer> levels;

    ModuleStats(Map<ModuleType, Integer> levels) {
        this.levels = levels;
    }

    public int level(ModuleType type) {
        return Math.min(ModuleType.MAX_LEVEL, levels.getOrDefault(type, 0));
    }

    public boolean isEmpty() {
        return levels.values().stream().allMatch(v -> v <= 0);
    }

    /** Splitter: one extra projectile (or fork / sentry bolt / volley gear) per level. */
    public int extraProjectiles() {
        return level(ModuleType.SPLITTER);
    }

    /** Caliber: +10% damage per level. */
    public float damageMultiplier() {
        return 1f + 0.10f * level(ModuleType.CALIBER);
    }

    /** Caliber: +20% projectile size per level. */
    public float sizeMultiplier() {
        return 1f + 0.20f * level(ModuleType.CALIBER);
    }

    /** Assembler: one extra construct every level (sentries are capped by the spell itself). */
    public int extraConstructs() {
        return level(ModuleType.ASSEMBLER);
    }

    /** Assembler: +10% construct health per level. */
    public float constructHealthMultiplier() {
        return 1f + 0.10f * level(ModuleType.ASSEMBLER);
    }

    /** Tesla: number of chain jumps on hit (0 = no tesla). */
    public int teslaJumps() {
        return level(ModuleType.TESLA);
    }

    /** Tesla: share of the hit damage dealt by each chain jump. */
    public static float teslaDamageShare(int teslaLevel) {
        return 0.20f + 0.06f * teslaLevel;
    }
}
