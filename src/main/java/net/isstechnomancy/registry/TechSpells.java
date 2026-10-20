package net.isstechnomancy.registry;

import io.redspace.ironsspellbooks.api.registry.SpellRegistry;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.spells.ArcWelderSpell;
import net.isstechnomancy.spells.AssembleAutomatonSpell;
import net.isstechnomancy.spells.DeployBrassSentrySpell;
import net.isstechnomancy.spells.EmpScreechSpell;
import net.isstechnomancy.spells.MagneticFieldSpell;
import net.isstechnomancy.spells.RocketGrabSpell;
import net.isstechnomancy.spells.SummonTechDrakeSpell;
import net.isstechnomancy.spells.GearBarrageSpell;
import net.isstechnomancy.spells.OverdriveProtocolSpell;
import net.isstechnomancy.spells.SteamVentSpell;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public class TechSpells {
    private static final DeferredRegister<AbstractSpell> SPELLS = DeferredRegister.create(SpellRegistry.SPELL_REGISTRY_KEY, ISSTechnomancy.MODID);

    // Registry names must equal AbstractSpell#getSpellName (the path of getSpellResource)
    public static final RegistryObject<AbstractSpell> GEAR_BARRAGE = SPELLS.register("gear_barrage", GearBarrageSpell::new);
    public static final RegistryObject<AbstractSpell> ARC_WELDER = SPELLS.register("arc_welder", ArcWelderSpell::new);
    public static final RegistryObject<AbstractSpell> DEPLOY_BRASS_SENTRY = SPELLS.register("deploy_brass_sentry", DeployBrassSentrySpell::new);
    public static final RegistryObject<AbstractSpell> STEAM_VENT = SPELLS.register("steam_vent", SteamVentSpell::new);
    public static final RegistryObject<AbstractSpell> OVERDRIVE_PROTOCOL = SPELLS.register("overdrive_protocol", OverdriveProtocolSpell::new);
    public static final RegistryObject<AbstractSpell> ASSEMBLE_AUTOMATON = SPELLS.register("assemble_automaton", AssembleAutomatonSpell::new);
    public static final RegistryObject<AbstractSpell> ROCKET_GRAB = SPELLS.register("rocket_grab", RocketGrabSpell::new);
    public static final RegistryObject<AbstractSpell> MAGNETIC_FIELD = SPELLS.register("magnetic_field", MagneticFieldSpell::new);
    public static final RegistryObject<AbstractSpell> EMP_SCREECH = SPELLS.register("emp_screech", EmpScreechSpell::new);
    public static final RegistryObject<AbstractSpell> SUMMON_TECH_DRAKE = SPELLS.register("summon_tech_drake", SummonTechDrakeSpell::new);

    public static void register(IEventBus modEventBus) {
        SPELLS.register(modEventBus);
    }
}
