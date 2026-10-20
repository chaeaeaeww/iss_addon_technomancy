package net.isstechnomancy.compat;

import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.api.registry.SpellRegistry;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import io.redspace.ironsspellbooks.api.spells.CastSource;
import net.isstechnomancy.ISSTechnomancy;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.LivingEntity;
import net.minecraftforge.fml.ModList;

/**
 * Soft integration with T.O Magic 'n Extras (traveloptics). The Tech Dragon borrows a few of its Lightning spells when
 * the mod is installed; nothing here is loaded or required otherwise.
 */
public final class TravelOpticsCompat {
    public static final String MODID = "traveloptics";
    private static Boolean loaded;

    private TravelOpticsCompat() {
    }

    public static boolean isLoaded() {
        if (loaded == null) {
            loaded = ModList.get().isLoaded(MODID);
        }
        return loaded;
    }

    /**
     * Casts traveloptics:{@code spellPath} instantly from {@code caster} (as a mob cast).
     *
     * @return false if the mod or spell is missing, or the cast failed
     */
    public static boolean cast(String spellPath, int spellLevel, LivingEntity caster) {
        if (!isLoaded()) {
            return false;
        }
        AbstractSpell spell = SpellRegistry.getSpell(new ResourceLocation(MODID, spellPath));
        if (spell == null || spell == SpellRegistry.none()) {
            return false;
        }
        try {
            spell.onCast(caster.level(), spellLevel, caster, CastSource.MOB, new MagicData(true));
            return true;
        } catch (RuntimeException e) {
            ISSTechnomancy.LOGGER.debug("Tech Dragon could not cast {}", spellPath, e);
            return false;
        }
    }
}
