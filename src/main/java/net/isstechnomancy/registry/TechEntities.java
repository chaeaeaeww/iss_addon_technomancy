package net.isstechnomancy.registry;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.ArcWelderBeam;
import net.isstechnomancy.entity.BrassSentry;
import net.isstechnomancy.entity.ClockworkAutomaton;
import net.isstechnomancy.entity.GearProjectile;
import net.isstechnomancy.entity.SentryBolt;
import net.isstechnomancy.entity.SiegeSentry;
import net.isstechnomancy.entity.SiegeShell;
import net.isstechnomancy.entity.boss.TechDragon;
import net.isstechnomancy.entity.boss.TechDrake;
import net.isstechnomancy.entity.boss.HextechPylon;
import net.isstechnomancy.entity.boss.ArcRing;
import net.isstechnomancy.entity.boss.DragonDebris;
import net.isstechnomancy.entity.boss.HextechShell;
import net.isstechnomancy.entity.MagneticField;
import net.isstechnomancy.entity.RocketHand;
import net.isstechnomancy.entity.TechnomancerEntity;
import net.minecraft.world.entity.SpawnPlacements;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.event.entity.SpawnPlacementRegisterEvent;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public class TechEntities {
    private static final DeferredRegister<EntityType<?>> ENTITIES = DeferredRegister.create(Registries.ENTITY_TYPE, ISSTechnomancy.MODID);

    public static final RegistryObject<EntityType<GearProjectile>> GEAR_PROJECTILE = ENTITIES.register("gear_projectile",
            () -> EntityType.Builder.<GearProjectile>of(GearProjectile::new, MobCategory.MISC)
                    .sized(0.4f, 0.4f)
                    .clientTrackingRange(6)
                    .updateInterval(1)
                    .build(ISSTechnomancy.id("gear_projectile").toString()));

    public static final RegistryObject<EntityType<ArcWelderBeam>> ARC_WELDER_BEAM = ENTITIES.register("arc_welder_beam",
            () -> EntityType.Builder.<ArcWelderBeam>of(ArcWelderBeam::new, MobCategory.MISC)
                    .sized(0.25f, 0.25f)
                    .clientTrackingRange(6)
                    .updateInterval(1)
                    .noSave()
                    .build(ISSTechnomancy.id("arc_welder_beam").toString()));

    public static final RegistryObject<EntityType<BrassSentry>> BRASS_SENTRY = ENTITIES.register("brass_sentry",
            () -> EntityType.Builder.<BrassSentry>of(BrassSentry::new, MobCategory.MISC)
                    .sized(0.9f, 1.25f)
                    .clientTrackingRange(10)
                    .noSave()
                    .build(ISSTechnomancy.id("brass_sentry").toString()));

    public static final RegistryObject<EntityType<SentryBolt>> SENTRY_BOLT = ENTITIES.register("sentry_bolt",
            () -> EntityType.Builder.<SentryBolt>of(SentryBolt::new, MobCategory.MISC)
                    .sized(0.25f, 0.25f)
                    .clientTrackingRange(6)
                    .updateInterval(1)
                    .build(ISSTechnomancy.id("sentry_bolt").toString()));

    public static final RegistryObject<EntityType<SiegeSentry>> SIEGE_SENTRY = ENTITIES.register("siege_sentry",
            () -> EntityType.Builder.<SiegeSentry>of(SiegeSentry::new, MobCategory.MISC)
                    .sized(2.6f, 3.2f)
                    .clientTrackingRange(10)
                    .noSave()
                    .build(ISSTechnomancy.id("siege_sentry").toString()));

    public static final RegistryObject<EntityType<SiegeShell>> SIEGE_SHELL = ENTITIES.register("siege_shell",
            () -> EntityType.Builder.<SiegeShell>of(SiegeShell::new, MobCategory.MISC)
                    .sized(0.35f, 0.35f)
                    .clientTrackingRange(6)
                    .updateInterval(1)
                    .build(ISSTechnomancy.id("siege_shell").toString()));

    public static final RegistryObject<EntityType<ClockworkAutomaton>> CLOCKWORK_AUTOMATON = ENTITIES.register("clockwork_automaton",
            () -> EntityType.Builder.<ClockworkAutomaton>of(ClockworkAutomaton::new, MobCategory.MONSTER)
                    .sized(0.95f, 2.05f)
                    .clientTrackingRange(10)
                    .build(ISSTechnomancy.id("clockwork_automaton").toString()));

    public static final RegistryObject<EntityType<TechDragon>> TECH_DRAGON = ENTITIES.register("tech_dragon",
            () -> EntityType.Builder.<TechDragon>of(TechDragon::new, MobCategory.MONSTER)
                    .sized(3.4f, 2.9f)
                    .fireImmune()
                    .clientTrackingRange(16)
                    .updateInterval(1)
                    .build(ISSTechnomancy.id("tech_dragon").toString()));

    public static final RegistryObject<EntityType<TechDrake>> TECH_DRAKE = ENTITIES.register("tech_drake",
            () -> EntityType.Builder.<TechDrake>of(TechDrake::new, MobCategory.MISC)
                    .sized(3.4f, 2.9f)
                    .fireImmune()
                    .clientTrackingRange(12)
                    .updateInterval(1)
                    .build(ISSTechnomancy.id("tech_drake").toString()));

    public static final RegistryObject<EntityType<HextechPylon>> HEXTECH_PYLON = ENTITIES.register("hextech_pylon",
            () -> EntityType.Builder.<HextechPylon>of(HextechPylon::new, MobCategory.MISC)
                    .sized(3.0f, 18.0f)
                    .fireImmune()
                    .clientTrackingRange(16)
                    .build(ISSTechnomancy.id("hextech_pylon").toString()));

    public static final RegistryObject<EntityType<HextechShell>> HEXTECH_SHELL = ENTITIES.register("hextech_shell",
            () -> EntityType.Builder.<HextechShell>of(HextechShell::new, MobCategory.MISC)
                    .sized(18.0f, 18.0f)
                    .fireImmune()
                    .clientTrackingRange(16)
                    .updateInterval(1)
                    .noSave()
                    .build(ISSTechnomancy.id("hextech_shell").toString()));

    /** Visual-only ground chunks thrown up by the Tech Dragon's crash landings (never placed as blocks). */
    public static final RegistryObject<EntityType<DragonDebris>> DRAGON_DEBRIS = ENTITIES.register("dragon_debris",
            () -> EntityType.Builder.<DragonDebris>of(DragonDebris::new, MobCategory.MISC)
                    .sized(0.7f, 0.7f)
                    .fireImmune()
                    .clientTrackingRange(10)
                    .updateInterval(10)
                    .noSave()
                    .build(ISSTechnomancy.id("dragon_debris").toString()));

    /** Visual-only electric shock rings (the Tech Dragon's skills, 1.9). */
    public static final RegistryObject<EntityType<ArcRing>> ARC_RING = ENTITIES.register("arc_ring",
            () -> EntityType.Builder.<ArcRing>of(ArcRing::new, MobCategory.MISC)
                    .sized(0.5f, 0.5f)
                    .fireImmune()
                    .clientTrackingRange(12)
                    .updateInterval(20)
                    .noSave()
                    .build(ISSTechnomancy.id("arc_ring").toString()));

    public static final RegistryObject<EntityType<RocketHand>> ROCKET_HAND = ENTITIES.register("rocket_hand",
            () -> EntityType.Builder.<RocketHand>of(RocketHand::new, MobCategory.MISC)
                    .sized(0.6f, 0.6f)
                    .clientTrackingRange(8)
                    .updateInterval(1)
                    .noSave()
                    .build(ISSTechnomancy.id("rocket_hand").toString()));

    public static final RegistryObject<EntityType<MagneticField>> MAGNETIC_FIELD = ENTITIES.register("magnetic_field",
            () -> EntityType.Builder.<MagneticField>of(MagneticField::new, MobCategory.MISC)
                    .sized(1f, 0.25f)
                    .clientTrackingRange(10)
                    .updateInterval(20)
                    .build(ISSTechnomancy.id("magnetic_field").toString()));

    public static final RegistryObject<EntityType<TechnomancerEntity>> TECHNOMANCER = ENTITIES.register("technomancer",
            () -> EntityType.Builder.<TechnomancerEntity>of(TechnomancerEntity::new, MobCategory.CREATURE)
                    .sized(0.6f, 1.8f)
                    .clientTrackingRange(10)
                    .build(ISSTechnomancy.id("technomancer").toString()));

    public static void register(IEventBus modEventBus) {
        ENTITIES.register(modEventBus);
        modEventBus.addListener(TechEntities::createAttributes);
        modEventBus.addListener(TechEntities::spawnPlacements);
    }

    private static void createAttributes(EntityAttributeCreationEvent event) {
        event.put(BRASS_SENTRY.get(), BrassSentry.createAttributes().build());
        event.put(SIEGE_SENTRY.get(), SiegeSentry.createSiegeAttributes().build());
        event.put(CLOCKWORK_AUTOMATON.get(), ClockworkAutomaton.createAttributes().build());
        event.put(TECH_DRAGON.get(), TechDragon.createAttributes().build());
        event.put(TECH_DRAKE.get(), TechDrake.createDrakeAttributes().build());
        event.put(HEXTECH_PYLON.get(), HextechPylon.createAttributes().build());
        event.put(TECHNOMANCER.get(), TechnomancerEntity.prepareAttributes().build());
    }

    private static void spawnPlacements(SpawnPlacementRegisterEvent event) {
        event.register(TECHNOMANCER.get(), SpawnPlacements.Type.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                Mob::checkMobSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
    }
}
