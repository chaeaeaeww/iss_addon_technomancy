package net.isstechnomancy.registry;

import net.isstechnomancy.ISSTechnomancy;
import net.minecraft.core.registries.Registries;
import net.minecraft.sounds.SoundEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public class TechSounds {
    private static final DeferredRegister<SoundEvent> SOUNDS = DeferredRegister.create(Registries.SOUND_EVENT, ISSTechnomancy.MODID);

    // School default cast sound
    public static final RegistryObject<SoundEvent> TECHNOMANCY_CAST = register("cast.technomancy");

    // Gear Barrage
    public static final RegistryObject<SoundEvent> GEAR_BARRAGE_CAST = register("cast.gear_barrage");
    public static final RegistryObject<SoundEvent> GEAR_RICOCHET = register("entity.gear.ricochet");
    public static final RegistryObject<SoundEvent> GEAR_IMPACT = register("entity.gear.impact");

    // Arc Welder
    public static final RegistryObject<SoundEvent> ARC_WELDER_START = register("cast.arc_welder.start");
    public static final RegistryObject<SoundEvent> ARC_WELDER_LOOP = register("cast.arc_welder.loop");
    public static final RegistryObject<SoundEvent> ARC_WELDER_END = register("cast.arc_welder.end");

    // Brass Sentry
    public static final RegistryObject<SoundEvent> SENTRY_WINDUP = register("cast.brass_sentry.windup");
    public static final RegistryObject<SoundEvent> SENTRY_DEPLOY = register("entity.brass_sentry.deploy");
    public static final RegistryObject<SoundEvent> SENTRY_SHOOT = register("entity.brass_sentry.shoot");
    public static final RegistryObject<SoundEvent> SENTRY_OVERCLOCK = register("entity.brass_sentry.overclock");
    public static final RegistryObject<SoundEvent> SENTRY_DESTROYED = register("entity.brass_sentry.destroyed");
    public static final RegistryObject<SoundEvent> SENTRY_BOLT_IMPACT = register("entity.sentry_bolt.impact");

    // Steam Vent / Overdrive
    public static final RegistryObject<SoundEvent> STEAM_VENT_CAST = register("cast.steam_vent");
    public static final RegistryObject<SoundEvent> OVERDRIVE_CAST = register("cast.overdrive");
    public static final RegistryObject<SoundEvent> OVERDRIVE_TRIGGER = register("overdrive.trigger");

    // Siege Sentry
    public static final RegistryObject<SoundEvent> SIEGE_SENTRY_SHOOT = register("entity.siege_sentry.shoot");
    public static final RegistryObject<SoundEvent> SIEGE_SHELL_EXPLODE = register("entity.siege_shell.explode");

    // Clockwork Automaton
    public static final RegistryObject<SoundEvent> AUTOMATON_ASSEMBLE = register("cast.assemble_automaton");
    public static final RegistryObject<SoundEvent> AUTOMATON_AMBIENT = register("entity.clockwork_automaton.ambient");
    public static final RegistryObject<SoundEvent> AUTOMATON_HURT = register("entity.clockwork_automaton.hurt");
    public static final RegistryObject<SoundEvent> AUTOMATON_DEATH = register("entity.clockwork_automaton.death");
    public static final RegistryObject<SoundEvent> AUTOMATON_STEP = register("entity.clockwork_automaton.step");
    public static final RegistryObject<SoundEvent> AUTOMATON_ATTACK = register("entity.clockwork_automaton.attack");
    public static final RegistryObject<SoundEvent> AUTOMATON_VOLLEY = register("entity.clockwork_automaton.volley");

    // Tech Dragon
    public static final RegistryObject<SoundEvent> TECH_DRAGON_AMBIENT = register("entity.tech_dragon.ambient");
    public static final RegistryObject<SoundEvent> TECH_DRAGON_ROAR = register("entity.tech_dragon.roar");
    public static final RegistryObject<SoundEvent> TECH_DRAGON_HURT = register("entity.tech_dragon.hurt");
    public static final RegistryObject<SoundEvent> TECH_DRAGON_DEATH = register("entity.tech_dragon.death");
    public static final RegistryObject<SoundEvent> TECH_DRAGON_CHARGE = register("entity.tech_dragon.charge");
    public static final RegistryObject<SoundEvent> TECH_DRAGON_BREATH = register("entity.tech_dragon.breath");
    public static final RegistryObject<SoundEvent> TECH_DRAGON_SPIT = register("entity.tech_dragon.spit");
    public static final RegistryObject<SoundEvent> TECH_DRAGON_SLAM = register("entity.tech_dragon.slam");

    private static RegistryObject<SoundEvent> register(String name) {
        return SOUNDS.register(name, () -> SoundEvent.createVariableRangeEvent(ISSTechnomancy.id(name)));
    }

    public static void register(IEventBus modEventBus) {
        SOUNDS.register(modEventBus);
    }
}
