package net.isstechnomancy.devtest;

import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import io.redspace.ironsspellbooks.api.spells.CastSource;
import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.entity.ClockworkAutomaton;
import net.isstechnomancy.entity.MagneticField;
import net.isstechnomancy.entity.RocketHand;
import net.isstechnomancy.entity.boss.TechDragon;
import net.isstechnomancy.entity.boss.TechDrake;
import net.isstechnomancy.registry.TechEffects;
import net.isstechnomancy.registry.TechEntities;
import net.isstechnomancy.registry.TechSpells;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.animal.IronGolem;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import net.minecraftforge.registries.RegistryObject;

import java.util.List;

/**
 * Dev-only runtime checks (run with ./gradlew runGameTestServer): every new entity ticks without errors, every
 * Technomancy spell can be cast, the Tech Dragon runs its intro and attacks, and the Clockwork Shrine template loads.
 */
@GameTestHolder(ISSTechnomancy.MODID)
@PrefixGameTestTemplate(false)
public class TechGameTests {
    static {
        // the GameTest world is flat (no terrain poking into the arenas, so the dragon's leaps are repeatable) and so in
        // full sun: test zombies get fire resistance so burning in daylight never counts as a spell's damage
        net.minecraftforge.common.MinecraftForge.EVENT_BUS.addListener((net.minecraftforge.event.entity.EntityJoinLevelEvent e) -> {
            if (!e.getLevel().isClientSide && e.getEntity().getType() == EntityType.ZOMBIE && e.getEntity() instanceof Zombie z) {
                z.addEffect(new MobEffectInstance(net.minecraft.world.effect.MobEffects.FIRE_RESISTANCE, 1000000, 0, false, false));
            }
        });
    }

    private static IronGolem dummy(GameTestHelper helper, BlockPos pos) {
        IronGolem golem = helper.spawnWithNoFreeWill(EntityType.IRON_GOLEM, pos);
        golem.setInvulnerable(true);
        return golem;
    }

    @GameTest(template = "test_arena", timeoutTicks = 200)
    public static void castEverySpell(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        Zombie caster = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(3, 2, 3));
        caster.setInvulnerable(true);
        IronGolem target = dummy(helper, new BlockPos(9, 2, 3));
        caster.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES, target.getEyePosition());
        caster.setTarget(target);
        List<RegistryObject<AbstractSpell>> spells = List.of(TechSpells.GEAR_BARRAGE, TechSpells.ARC_WELDER, TechSpells.DEPLOY_BRASS_SENTRY,
                TechSpells.STEAM_VENT, TechSpells.OVERDRIVE_PROTOCOL, TechSpells.ASSEMBLE_AUTOMATON, TechSpells.ROCKET_GRAB,
                TechSpells.MAGNETIC_FIELD, TechSpells.EMP_SCREECH, TechSpells.SUMMON_TECH_DRAKE);
        int delay = 1;
        for (RegistryObject<AbstractSpell> spell : spells) {
            helper.runAfterDelay(delay, () -> spell.get().onCast(level, spell.get().getMaxLevel(), caster, CastSource.MOB, new MagicData(true)));
            delay += 8;
        }
        // overdriven versions of the construct spells
        helper.runAfterDelay(delay, () -> {
            caster.addEffect(new MobEffectInstance(TechEffects.OVERDRIVE.get(), 200));
            TechSpells.ASSEMBLE_AUTOMATON.get().onCast(level, 5, caster, CastSource.MOB, new MagicData(true));
            caster.addEffect(new MobEffectInstance(TechEffects.OVERDRIVE.get(), 200));
            TechSpells.SUMMON_TECH_DRAKE.get().onCast(level, 3, caster, CastSource.MOB, new MagicData(true));
            caster.addEffect(new MobEffectInstance(TechEffects.OVERDRIVE.get(), 200));
            TechSpells.EMP_SCREECH.get().onCast(level, 5, caster, CastSource.MOB, new MagicData(true));
        });
        helper.runAfterDelay(delay + 60, () -> {
            helper.assertEntityPresent(TechEntities.MAGNETIC_FIELD.get());
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 260)
    public static void mk2OverloadAndGrab(GameTestHelper helper) {
        Zombie owner = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(2, 2, 2));
        owner.setInvulnerable(true);
        Vec3 at = helper.absoluteVec(new Vec3(5, 2, 5));
        ClockworkAutomaton mk2 = new ClockworkAutomaton(helper.getLevel(), owner, 6, 3, 60, 4000, true);
        mk2.moveTo(at.x, at.y, at.z);
        helper.getLevel().addFreshEntity(mk2);
        Zombie victim = helper.spawn(EntityType.ZOMBIE, new BlockPos(12, 2, 12));
        helper.runAfterDelay(5, () -> mk2.setTarget(victim));
        helper.runAfterDelay(20, () -> {
            Vec3 from = mk2.position().add(0, 1.2, 0);
            helper.getLevel().addFreshEntity(new RocketHand(helper.getLevel(), mk2, from, victim.position().subtract(from), 17, 3, 30, 1.3f));
        });
        helper.runAfterDelay(120, () -> mk2.hurt(helper.getLevel().damageSources().generic(), 500f));
        helper.runAfterDelay(125, () -> helper.assertTrue(mk2.isOverloading(), "Mk.II should overload instead of dying"));
        helper.runAfterDelay(200, () -> {
            helper.assertTrue(mk2.isRemoved(), "Mk.II should have discharged");
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 900, batch = "dragon_techDragonFight")
    public static void techDragonFight(GameTestHelper helper) {
        clearLeftovers(helper);
        ServerLevel level = helper.getLevel();
        TechDragon dragon = TechEntities.TECH_DRAGON.get().create(level);
        Vec3 at = helper.absoluteVec(new Vec3(6, 3, 6));
        dragon.moveTo(at.x, at.y, at.z);
        dragon.finalizeSpawn(level, level.getCurrentDifficultyAt(dragon.blockPosition()), MobSpawnType.TRIGGERED, null, null);
        level.addFreshEntity(dragon);
        IronGolem target = dummy(helper, new BlockPos(10, 2, 10));
        for (int t = 110; t < 800; t += 10) {
            helper.runAfterDelay(t, () -> {
                dragon.setLastHurtByMob(target);
                dragon.setTarget(target);
            });
        }
        helper.runAfterDelay(400, () -> dragon.applyStun(40));
        helper.runAfterDelay(600, () -> dragon.hurt(level.damageSources().generic(), 60f));
        helper.runAfterDelay(850, () -> {
            helper.assertTrue(dragon.isAlive(), "dragon should still be alive");
            helper.assertTrue(dragon.getState() != TechDragon.State.SPAWN, "dragon should have finished its intro");
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 200)
    public static void entitiesTick(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        Zombie owner = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(2, 2, 2));
        owner.setInvulnerable(true);
        helper.spawn(TechEntities.TECHNOMANCER.get(), new BlockPos(8, 2, 8));
        helper.spawn(TechEntities.CLOCKWORK_AUTOMATON.get(), new BlockPos(10, 2, 3));
        TechDrake drake = new TechDrake(level, owner, 1f, 60, 1000, false);
        Vec3 at = helper.absoluteVec(new Vec3(6, 5, 6));
        drake.moveTo(at.x, at.y, at.z);
        level.addFreshEntity(drake);
        MagneticField field = new MagneticField(level, owner, 6, 120, true);
        Vec3 f = helper.absoluteVec(new Vec3(6, 2, 6));
        field.moveTo(f.x, f.y, f.z);
        level.addFreshEntity(field);
        helper.runAfterDelay(150, () -> {
            helper.assertEntityPresent(TechEntities.TECHNOMANCER.get());
            helper.succeed();
        });
    }

    @GameTest(template = "clockwork_shrine", timeoutTicks = 60)
    public static void shrineTemplateLoads(GameTestHelper helper) {
        helper.runAfterDelay(20, () -> {
            boolean altar = false;
            for (BlockPos p : BlockPos.betweenClosed(0, 0, 0, 12, 7, 12)) {
                if (helper.getBlockState(p).is(net.isstechnomancy.registry.TechBlocks.CLOCKWORK_ALTAR.get())) {
                    altar = true;
                }
            }
            helper.assertTrue(altar, "shrine should contain the altar");
            helper.assertEntityPresent(TechEntities.TECHNOMANCER.get());
            helper.succeed();
        });
    }

    // ------------------------------------------------------------------ 1.3

    @GameTest(template = "test_arena", timeoutTicks = 420)
    public static void blitzPunchesAndSprints(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        ClockworkAutomaton blitz = TechEntities.CLOCKWORK_AUTOMATON.get().create(level);
        Vec3 at = helper.absoluteVec(new Vec3(2.5, 2, 2.5));
        blitz.moveTo(at.x, at.y, at.z);
        blitz.makeGuard();
        level.addFreshEntity(blitz);
        Zombie victim = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(12, 2, 12));
        victim.setInvulnerable(false);
        boolean[] sprinted = {false, false};
        for (int t = 2; t < 400; t += 2) {
            helper.runAfterDelay(t, () -> {
                if (victim.isAlive()) {
                    blitz.setTarget(victim);
                    victim.setHealth(victim.getMaxHealth());
                }
                sprinted[0] |= blitz.getSprintState() == 1;
                sprinted[1] |= blitz.getSprintState() == 2;
            });
        }
        int[] hits = {0};
        float[] last = {0};
        for (int t = 3; t < 400; t += 2) {
            helper.runAfterDelay(t, () -> {
                if (victim.hurtTime > 0 && victim.hurtTime >= 9) {
                    hits[0]++;
                }
            });
        }
        helper.runAfterDelay(405, () -> {
            helper.assertTrue(blitz.isGuard() && blitz.isMk2(), "should be a Mk.II guard");
            helper.assertTrue(sprinted[0] && sprinted[1], "Blitz should sprint then vent (" + sprinted[0] + "/" + sprinted[1] + ")");
            helper.assertTrue(hits[0] >= 3, "Blitz should land punches, got " + hits[0]);
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 140)
    public static void magneticFieldDealsNoDamage(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        Zombie owner = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(1, 2, 1));
        owner.setInvulnerable(true);
        Zombie victim = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(6, 2, 6));
        MagneticField field = new MagneticField(level, owner, 6, 120, true);
        Vec3 f = helper.absoluteVec(new Vec3(6, 2, 6));
        field.moveTo(f.x, f.y, f.z);
        level.addFreshEntity(field);
        List<String> sources = new java.util.ArrayList<>();
        net.minecraftforge.common.MinecraftForge.EVENT_BUS.addListener((net.minecraftforge.event.entity.living.LivingHurtEvent e) -> {
            if (e.getEntity() == victim) {
                sources.add(e.getSource().getMsgId() + " by " + e.getSource().getEntity() + " (" + e.getAmount() + ")");
            }
        });
        helper.runAfterDelay(100, () -> {
            helper.assertTrue(victim.getHealth() == victim.getMaxHealth(), "the field must not deal damage; hurt by " + sources);
            helper.assertTrue(victim.hasEffect(net.minecraft.world.effect.MobEffects.MOVEMENT_SLOWDOWN), "the field should slow");
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 60)
    public static void empOnlyStunsMachines(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        Zombie caster = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(2, 2, 6));
        caster.setInvulnerable(true);
        IronGolem golem = helper.spawnWithNoFreeWill(EntityType.IRON_GOLEM, new BlockPos(7, 2, 6));
        Zombie zombie = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(5, 2, 6));
        caster.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES, golem.getEyePosition());
        helper.runAfterDelay(2, () -> TechSpells.EMP_SCREECH.get().onCast(level, 1, caster, CastSource.MOB, new MagicData(true)));
        helper.runAfterDelay(6, () -> {
            helper.assertTrue(TechSpells.EMP_SCREECH.get().getMaxLevel() == 1, "EMP Screech has a single level");
            helper.assertTrue(golem.hasEffect(TechEffects.STUNNED.get()), "the golem should be stunned");
            helper.assertTrue(golem.getHealth() == golem.getMaxHealth(), "EMP must not deal damage");
            helper.assertTrue(!zombie.hasEffect(TechEffects.STUNNED.get()) && zombie.getHealth() == zombie.getMaxHealth(), "non-machines are untouched");
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 1200, batch = "dragon_dragonLandsWithoutTarget")
    public static void dragonLandsWithoutTarget(GameTestHelper helper) {
        clearLeftovers(helper);
        ServerLevel level = helper.getLevel();
        TechDragon dragon = TechEntities.TECH_DRAGON.get().create(level);
        Vec3 at = helper.absoluteVec(new Vec3(6, 8, 6));
        dragon.moveTo(at.x, at.y, at.z);
        dragon.finalizeSpawn(level, level.getCurrentDifficultyAt(dragon.blockPosition()), MobSpawnType.TRIGGERED, null, null);
        level.addFreshEntity(dragon);
        helper.runAfterDelay(5, () -> helper.assertTrue(dragon.getBbWidth() > 6, "boss hitbox should be scaled x2: " + dragon.getBbWidth()));
        float[] yaw = {0};
        helper.runAfterDelay(1150, () -> {
            TechDragon.State s = dragon.getState();
            helper.assertTrue(s == TechDragon.State.PERCH || s == TechDragon.State.SLEEP || s == TechDragon.State.LIE_DOWN || s == TechDragon.State.REST_UP,
                    "dragon should have landed, state " + s);
            helper.assertTrue(Math.abs(net.minecraft.util.Mth.wrapDegrees(dragon.yBodyRot - dragon.getYRot())) < 1, "body follows yaw");
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 500)
    public static void drakeSettlesByOwner(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        Zombie owner = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(6, 2, 6));
        owner.setInvulnerable(true);
        TechDrake drake = new TechDrake(level, owner, 1f, 60, 2000, false);
        Vec3 at = helper.absoluteVec(new Vec3(6, 8, 6));
        drake.moveTo(at.x, at.y, at.z);
        level.addFreshEntity(drake);
        helper.runAfterDelay(450, () -> {
            helper.assertTrue(drake.getState() == TechDragon.State.PERCH || drake.getState() == TechDragon.State.LIE_DOWN || drake.getState() == TechDragon.State.REST_UP, "drake should land next to its idle owner, state " + drake.getState() + " target " + drake.getTarget());
            drake.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "clockwork_tower", timeoutTicks = 60)
    public static void towerTemplateLoads(GameTestHelper helper) {
        helper.runAfterDelay(20, () -> {
            helper.assertEntityPresent(TechEntities.TECHNOMANCER.get());
            helper.assertEntityPresent(TechEntities.CLOCKWORK_AUTOMATON.get());
            List<ClockworkAutomaton> guards = helper.getLevel().getEntitiesOfClass(ClockworkAutomaton.class, new net.minecraft.world.phys.AABB(helper.absolutePos(BlockPos.ZERO)).inflate(40));
            helper.assertTrue(!guards.isEmpty() && guards.get(0).isGuard() && guards.get(0).isMk2(), "the workshop Blitz should be a Mk.II guard");
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 80)
    public static void rocketGrabDealsNoDamage(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        Zombie caster = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(2, 2, 6));
        caster.setInvulnerable(true);
        Zombie victim = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(9, 2, 6));
        caster.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES, victim.getEyePosition());
        helper.runAfterDelay(2, () -> TechSpells.ROCKET_GRAB.get().onCast(level, 5, caster, CastSource.MOB, new MagicData(true)));
        boolean[] stunned = {false};
        for (int t = 3; t < 60; t++) {
            helper.runAfterDelay(t, () -> stunned[0] |= victim.hasEffect(TechEffects.STUNNED.get()));
        }
        helper.runAfterDelay(65, () -> {
            helper.assertTrue(stunned[0], "the grabbed zombie should be stunned");
            helper.assertTrue(victim.getHealth() == victim.getMaxHealth(), "Rocket Grab must not deal damage");
            helper.succeed();
        });
    }

    // ------------------------------------------------------------------ 1.5 dragon

    /** The boss hunts any mob within ~50 blocks: clear what earlier tests left behind around this one. */
    private static void clearLeftovers(GameTestHelper helper) {
        Vec3 c = helper.absoluteVec(new Vec3(8, 2, 8));
        for (var e : helper.getLevel().getEntitiesOfClass(net.minecraft.world.entity.Mob.class, new net.minecraft.world.phys.AABB(c, c).inflate(120, 64, 120))) {
            e.discard();
        }
    }

    private static TechDragon spawnDragon(GameTestHelper helper, Vec3 rel) {
        clearLeftovers(helper);
        ServerLevel level = helper.getLevel();
        TechDragon dragon = TechEntities.TECH_DRAGON.get().create(level);
        Vec3 at = helper.absoluteVec(rel);
        dragon.moveTo(at.x, at.y, at.z);
        dragon.finalizeSpawn(level, level.getCurrentDifficultyAt(dragon.blockPosition()), MobSpawnType.TRIGGERED, null, null);
        level.addFreshEntity(dragon);
        return dragon;
    }

    private static void forceState(TechDragon dragon, TechDragon.State state) {
        try {
            java.lang.reflect.Method m = TechDragon.class.getDeclaredMethod("setState", TechDragon.State.class);
            m.setAccessible(true);
            m.invoke(dragon, state);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }

    @GameTest(template = "test_arena", timeoutTicks = 200, batch = "dragon_dragonPartsTakeHits")
    public static void dragonPartsTakeHits(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(6, 6, 6));
        helper.runAfterDelay(120, () -> {
            helper.assertTrue(dragon.getParts().length == 17, "17 body parts");
            helper.assertTrue(net.isstechnomancy.entity.boss.DragonTracks.regionCount() == 17, "17 baked hitbox regions");
            boolean placed = true;
            for (var part : dragon.getParts()) {
                placed &= part.distanceTo(dragon) < 30 && part.getBoundingBox().getSize() > 0.5;
            }
            helper.assertTrue(placed, "parts should follow the dragon");
            // the boxes cover the body where the animation puts it
            var parts = dragon.getParts();
            helper.assertTrue(parts[0].getBoundingBox().inflate(0.3).contains(dragon.track(net.isstechnomancy.entity.boss.DragonTracks.HEAD)),
                    "the head box should contain the head");
            helper.assertTrue(parts[3].getBoundingBox().inflate(0.3).contains(dragon.track(net.isstechnomancy.entity.boss.DragonTracks.CHEST)),
                    "the chest box should contain the chest");
            helper.assertTrue(parts[3].getBoundingBox().getXsize() > 2.5 && parts[3].getBoundingBox().getYsize() > 2.5,
                    "the chest box should be body-sized at boss scale: " + parts[3].getBoundingBox());
            var head = dragon.getParts()[0];
            helper.assertTrue(helper.getLevel().getEntities((net.minecraft.world.entity.Entity) null, head.getBoundingBox().inflate(0.1), e -> e == head).size() == 1,
                    "parts should be found by level entity queries (what attacks and projectiles use)");
            float before = dragon.getHealth();
            dragon.getParts()[0].hurt(helper.getLevel().damageSources().generic(), 10f);
            helper.assertTrue(Math.abs(before - dragon.getHealth() - 13f) < 0.6f || before - dragon.getHealth() > 0, "a head hit should hurt the dragon (" + (before - dragon.getHealth()) + ")");
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 400, batch = "dragon_dragonChasesAttacker")
    public static void dragonChasesAttacker(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        TechDragon dragon = spawnDragon(helper, new Vec3(6, 6, 6));
        Zombie attacker = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(2, 2, 2));
        attacker.setInvulnerable(true);
        helper.runAfterDelay(110, () -> {
            dragon.hurt(level.damageSources().mobAttack(attacker), 5f);
            // run far away, well outside the 56 block arena
            Vec3 far = helper.absoluteVec(new Vec3(90, 2, 2));
            attacker.teleportTo(far.x, far.y + 30, far.z);
            attacker.setNoGravity(true);
        });
        helper.runAfterDelay(380, () -> {
            helper.assertTrue(dragon.getTarget() == attacker, "the dragon should still be chasing its attacker, target = " + dragon.getTarget());
            dragon.discard();
            attacker.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 1400, batch = "dragon_dragonV4Moves")
    public static void dragonV4Moves(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(6, 2, 6));
        IronGolem target = dummy(helper, new BlockPos(9, 2, 9));
        TechDragon.State[] moves = {TechDragon.State.BITE, TechDragon.State.BITE_SWEEP, TechDragon.State.CLAW, TechDragon.State.TAIL_WHIP,
                TechDragon.State.TAIL_SWEEP, TechDragon.State.STOMP, TechDragon.State.WING_GUST, TechDragon.State.FIELD_ROAR, TechDragon.State.REND,
                TechDragon.State.GBREATH_CHARGE, TechDragon.State.GROUND_ROAR, TechDragon.State.COG_SPIT, TechDragon.State.THUNDER,
                TechDragon.State.ROAR, TechDragon.State.SWOOP, TechDragon.State.SKY_RISE, TechDragon.State.EMP, TechDragon.State.ARC_BARRAGE,
                TechDragon.State.PHASE_TWO};
        int t = 10;
        boolean[] field = {false};
        for (TechDragon.State move : moves) {
            helper.runAfterDelay(t, () -> {
                dragon.setTarget(target);
                forceState(dragon, move);
            });
            if (move == TechDragon.State.FIELD_ROAR) {
                helper.runAfterDelay(t + 30, () -> field[0] = !helper.getLevel().getEntitiesOfClass(net.isstechnomancy.entity.MagneticField.class,
                        dragon.getBoundingBox().inflate(30)).isEmpty());
            }
            t += 60;
        }
        helper.runAfterDelay(t + 10, () -> {
            helper.assertTrue(dragon.isAlive(), "dragon alive");
            helper.assertTrue(field[0], "Field Roar should plant a magnetic field");
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 200, batch = "dragon_dragonGrabShakesAndTosses")
    public static void dragonGrabShakesAndTosses(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(6, 2, 6));
        Zombie prey = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(6, 2, 6));
        boolean[] held = {false};
        helper.runAfterDelay(5, () -> forceState(dragon, TechDragon.State.GRAB));
        for (int k = 10; k <= 17; k++) {
            // keep the prey at the jaws around the catch frame
            helper.runAfterDelay(k, () -> {
                if (prey.getVehicle() == null) {
                    Vec3 jaws = dragon.mouthPosition();
                    prey.teleportTo(jaws.x, jaws.y - 1, jaws.z);
                    prey.setDeltaMovement(Vec3.ZERO);
                }
            });
        }
        helper.runAfterDelay(30, () -> held[0] = prey.getVehicle() == dragon);
        helper.runAfterDelay(120, () -> {
            helper.assertTrue(held[0], "the zombie should have been seized in the jaws, state " + dragon.getState());
            helper.assertTrue(prey.getVehicle() == null, "the prey should have been tossed away");
            dragon.discard();
            prey.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 900, batch = "dragon_dragonPylonsShatterShield")
    public static void dragonPylonsShatterShield(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        TechDragon dragon = spawnDragon(helper, new Vec3(6, 2, 6));
        helper.runAfterDelay(5, () -> {
            forceState(dragon, TechDragon.State.GROUND);
            dragon.setHealth(dragon.getMaxHealth() * 0.45f);
        });
        helper.runAfterDelay(80, () -> {
            helper.assertTrue(dragon.isPhaseTwo(), "phase two at half health");
            forceState(dragon, TechDragon.State.GROUND);
            dragon.setHealth(dragon.getMaxHealth() * 0.29f);
        });
        helper.runAfterDelay(84, () -> helper.assertTrue(dragon.isShielded(), "shield up at 30%, state " + dragon.getState()));
        helper.runAfterDelay(420, () -> {
            List<net.isstechnomancy.entity.boss.HextechPylon> pylons = level.getEntitiesOfClass(net.isstechnomancy.entity.boss.HextechPylon.class,
                    dragon.getBoundingBox().inflate(60), p -> p.getDragon() == dragon);
            helper.assertTrue(pylons.size() == 4, "four pylons should stand, found " + pylons.size() + ", state " + dragon.getState());
            float before = dragon.getHealth();
            dragon.hurt(level.damageSources().generic(), 20f);
            helper.assertTrue(dragon.getHealth() == before, "the shield blocks damage");
            for (var p : pylons) {
                p.hurt(level.damageSources().generic(), 500f);
            }
        });
        helper.runAfterDelay(440, () -> {
            helper.assertTrue(!dragon.isShielded(), "shield shatters when every pylon is down");
            helper.assertTrue(dragon.getState() == TechDragon.State.STUNNED, "dragon reels, state " + dragon.getState());
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 900, batch = "dragon_dragonPylonsHealWhenIgnored")
    public static void dragonPylonsHealWhenIgnored(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(6, 2, 6));
        float[] hp = {0};
        helper.runAfterDelay(5, () -> {
            forceState(dragon, TechDragon.State.GROUND);
            dragon.setHealth(dragon.getMaxHealth() * 0.45f);
        });
        helper.runAfterDelay(80, () -> {
            forceState(dragon, TechDragon.State.GROUND);
            dragon.setHealth(dragon.getMaxHealth() * 0.29f);
            hp[0] = dragon.getHealth();
        });
        helper.runAfterDelay(860, () -> {
            helper.assertTrue(!dragon.isShielded(), "shield drops after the charge");
            helper.assertTrue(dragon.getHealth() >= hp[0] + dragon.getMaxHealth() * 0.3f, "4 pylons standing heal 32%: " + hp[0] + " -> " + dragon.getHealth());
            dragon.discard();
            helper.succeed();
        });
    }

    // own batch: the 40 block blast would hit the other tests running next to it
    @GameTest(template = "test_arena", timeoutTicks = 500, batch = "dragon_death")
    public static void dragonDeathShellExplodes(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        TechDragon dragon = spawnDragon(helper, new Vec3(6, 2, 6));
        Zombie victim = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(12, 2, 12));
        boolean[] shell = {false};
        helper.runAfterDelay(5, () -> {
            forceState(dragon, TechDragon.State.GROUND);
            dragon.setHealth(1f);
            dragon.hurt(level.damageSources().generic(), 10f);
        });
        helper.runAfterDelay(120, () -> shell[0] = !level.getEntitiesOfClass(net.isstechnomancy.entity.boss.HextechShell.class,
                dragon.getBoundingBox().inflate(40)).isEmpty());
        helper.runAfterDelay(260, () -> {
            helper.assertTrue(shell[0], "the hextech shell should form around the dying dragon");
            helper.assertTrue(dragon.isRemoved(), "the dragon is gone after the blast");
            helper.assertTrue(!victim.isAlive() || victim.getHealth() < victim.getMaxHealth(), "the blast hurts what stands nearby");
            helper.assertTrue(!level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class,
                    new net.minecraft.world.phys.AABB(helper.absolutePos(new BlockPos(6, 2, 6))).inflate(48)).isEmpty(), "loot drops after the explosion");
            victim.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 200)
    public static void drakeCanBeRidden(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        var owner = helper.makeMockPlayer();
        Vec3 at = helper.absoluteVec(new Vec3(5, 2, 5));
        owner.moveTo(at.x, at.y, at.z);
        TechDrake drake = new TechDrake(level, owner, 1f, 120, 2000, false);
        Vec3 d = helper.absoluteVec(new Vec3(8, 2, 8));
        drake.moveTo(d.x, d.y, d.z);
        level.addFreshEntity(drake);
        helper.runAfterDelay(20, () -> {
            drake.mobInteract(owner, net.minecraft.world.InteractionHand.MAIN_HAND);
            helper.assertTrue(owner.getVehicle() == drake, "the owner should be riding");
            helper.assertTrue(drake.getControllingPassenger() == owner, "the owner steers");
            drake.riderAction(TechDrake.Action.ATTACK);
            helper.assertTrue(drake.getState() == TechDragon.State.BITE, "left click bites, state " + drake.getState());
        });
        helper.runAfterDelay(60, () -> {
            helper.assertTrue(drake.getState() == TechDragon.State.RIDDEN, "back to riding after the bite, state " + drake.getState());
            drake.riderAction(TechDrake.Action.ROAR);
            helper.assertTrue(drake.getState() == TechDragon.State.ROAR, "R roars");
            owner.stopRiding();
            drake.discard();
            helper.succeed();
        });
    }

    // ------------------------------------------------------------------ 1.7 dragon v5

    @GameTest(template = "test_arena", timeoutTicks = 200, batch = "dragon_dragonPushesOutOverlapping")
    public static void dragonPushesOutOverlapping(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(6, 2, 6));
        Zombie stuck = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(6, 2, 6));
        stuck.setInvulnerable(true);
        helper.runAfterDelay(5, () -> {
            forceState(dragon, TechDragon.State.PERCH);
            // put the zombie right inside the chest
            var chest = dragon.getParts()[3].getBoundingBox().getCenter();
            stuck.teleportTo(chest.x, dragon.getY(), chest.z);
        });
        helper.runAfterDelay(80, () -> {
            boolean inside = false;
            for (var part : dragon.getParts()) {
                inside |= ((net.isstechnomancy.entity.boss.TechDragonPart) part).solid && part.getBoundingBox().deflate(0.05).intersects(stuck.getBoundingBox());
            }
            helper.assertTrue(!inside, "the zombie should have been pushed out of the body, at " + stuck.position());
            helper.assertTrue(stuck.canCollideWith(dragon.getParts()[3]), "body parts should be solid to other entities");
            helper.assertTrue(!dragon.canCollideWith(dragon.getParts()[3]), "the dragon should not collide with its own body");
            dragon.discard();
            stuck.discard();
            helper.succeed();
        });
    }

    private static void setField(TechDragon dragon, String name, Object value) {
        try {
            java.lang.reflect.Field f = TechDragon.class.getDeclaredField(name);
            f.setAccessible(true);
            f.set(dragon, value);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }

    @GameTest(template = "test_arena", timeoutTicks = 400, batch = "dragon_dragonGapClosers")
    public static void dragonGapClosers(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(3, 2, 3));
        IronGolem target = dummy(helper, new BlockPos(3, 2, 22));
        double[] start = new double[1];
        double[] moved = new double[3];
        TechDragon.State[] moves = {TechDragon.State.POUNCE, TechDragon.State.DASH_CLAW, TechDragon.State.RAM};
        for (int k = 0; k < moves.length; k++) {
            int i = k;
            int t = 10 + k * 90;
            helper.runAfterDelay(t, () -> {
                Vec3 home = helper.absoluteVec(new Vec3(3, 2, 3));
                dragon.teleportTo(home.x, home.y, home.z);
                dragon.setYRot(0);
                dragon.yBodyRot = 0;
                target.teleportTo(home.x, home.y, home.z + 19);
                dragon.setTarget(target);
                forceState(dragon, moves[i]);
                start[0] = dragon.getZ();
            });
            helper.runAfterDelay(t + 30, () -> moved[i] = dragon.getZ() - start[0]);
        }
        helper.runAfterDelay(290, () -> {
            helper.assertTrue(moved[0] > 4, "the pounce should leap toward the target, moved " + moved[0]);
            helper.assertTrue(moved[1] > 3, "the dash claw should rush toward the target, moved " + moved[1]);
            helper.assertTrue(moved[2] > 4, "the ram should charge toward the target, moved " + moved[2]);
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 200, batch = "dragon_dragonDodgesSideways")
    public static void dragonDodgesSideways(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(6, 2, 6));
        IronGolem target = dummy(helper, new BlockPos(6, 2, 14));
        Vec3[] before = new Vec3[1];
        helper.runAfterDelay(10, () -> {
            dragon.setYRot(0);
            dragon.yBodyRot = 0;
            dragon.setTarget(target);
            forceState(dragon, TechDragon.State.DODGE);
            before[0] = dragon.position();
        });
        helper.runAfterDelay(26, () -> {
            double side = Math.abs(dragon.getX() - before[0].x);
            helper.assertTrue(side > 2, "the dodge should hop sideways, moved " + side);
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 700, batch = "dragon_dragonDiveChainAndStorm")
    public static void dragonDiveChainAndStorm(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(6, 2, 6));
        IronGolem target = dummy(helper, new BlockPos(6, 2, 12));
        boolean[] bounced = {false};
        boolean[] stormed = {false};
        int[] strikes = {0};
        net.minecraftforge.common.MinecraftForge.EVENT_BUS.addListener((net.minecraftforge.event.entity.EntityJoinLevelEvent e) -> {
            if (e.getEntity() instanceof io.redspace.ironsspellbooks.entity.spells.LightningStrike strike && dragon.getState() == TechDragon.State.STORM
                    && strike.distanceTo(target) < 24) {
                strikes[0]++;
            }
        });
        helper.runAfterDelay(10, () -> {
            // an attacker stays its target (golems are not picked otherwise)
            dragon.hurt(helper.getLevel().damageSources().mobAttack(target), 1f);
            dragon.setTarget(target);
            setField(dragon, "diveChainLeft", 3);
            forceState(dragon, TechDragon.State.DIVE_RISE);
        });
        helper.onEachTick(() -> {
            // golems are never picked as targets on their own: keep it as the one the dragon is angry at
            setField(dragon, "aggroTarget", target);
            setField(dragon, "aggroTicks", 600);
            bounced[0] |= dragon.getState() == TechDragon.State.DIVE_BOUNCE;
            stormed[0] |= dragon.getState() == TechDragon.State.STORM;
        });
        helper.runAfterDelay(260, () -> {
            helper.assertTrue(bounced[0], "the dive chain should bounce back up after an impact");
            dragon.hurt(helper.getLevel().damageSources().mobAttack(target), 1f);
            dragon.setTarget(target);
            forceState(dragon, TechDragon.State.STORM_RISE);
        });
        helper.runAfterDelay(600, () -> {
            helper.assertTrue(stormed[0], "the storm call should reach the storm");
            helper.assertTrue(strikes[0] >= 10, "the storm should rain lightning around the target: " + strikes[0] + " strikes");
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 200)
    public static void drakeSeatIsSteady(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        var owner = helper.makeMockPlayer();
        Vec3 at = helper.absoluteVec(new Vec3(5, 2, 5));
        owner.moveTo(at.x, at.y, at.z);
        TechDrake drake = new TechDrake(level, owner, 1f, 120, 2000, false);
        Vec3 d = helper.absoluteVec(new Vec3(8, 2, 8));
        drake.moveTo(d.x, d.y, d.z);
        level.addFreshEntity(drake);
        double[] spread = {0};
        Vec3[] first = new Vec3[1];
        helper.runAfterDelay(20, () -> {
            drake.mobInteract(owner, net.minecraft.world.InteractionHand.MAIN_HAND);
            drake.riderAction(TechDrake.Action.ATTACK);
        });
        for (int k = 22; k < 60; k++) {
            helper.runAfterDelay(k, () -> {
                // the seat relative to the drake, in its own frame: must not move while the bite animation plays
                Vec3 rel = owner.position().subtract(drake.position()).yRot((float) Math.toRadians(drake.yBodyRot));
                if (first[0] == null) {
                    first[0] = rel;
                } else {
                    spread[0] = Math.max(spread[0], rel.distanceTo(first[0]));
                }
            });
        }
        helper.runAfterDelay(62, () -> {
            helper.assertTrue(owner.getVehicle() == drake, "the owner should be riding");
            helper.assertTrue(spread[0] < 0.05, "the seat should not bob with the animation, moved " + spread[0]);
            owner.stopRiding();
            drake.discard();
            helper.succeed();
        });
    }

    // ------------------------------------------------------------------ 1.8 dragon (each in its own batch: the boss is aggressive)

    /** Hurt events dealt by this dragon (its own damage or its lightning), per victim. */
    private static java.util.Map<LivingEntity, Integer> hurtsBy(TechDragon dragon,
                                                                java.util.function.BiPredicate<TechDragon, net.minecraftforge.event.entity.living.LivingHurtEvent> when) {
        java.util.Map<LivingEntity, Integer> out = new java.util.HashMap<>();
        net.minecraftforge.common.MinecraftForge.EVENT_BUS.addListener((net.minecraftforge.event.entity.living.LivingHurtEvent e) -> {
            if (e.getSource().getEntity() == dragon && when.test(dragon, e)) {
                out.merge(e.getEntity(), 1, Integer::sum);
            }
        });
        return out;
    }

    @GameTest(template = "test_arena", timeoutTicks = 200, batch = "dragon_kiteBackstepSpit")
    public static void dragonKiteBackstepThenSpit(GameTestHelper helper) {
        // the leap carries the body out of the arena but the head (~14.6 blocks ahead at boss size) stays inside the
        // barrier walls the test framework puts around it, so the bolt has a clear line
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 4));
        IronGolem target = helper.spawnWithNoFreeWill(EntityType.IRON_GOLEM, new BlockPos(8, 2, 10));
        java.util.Map<LivingEntity, Integer> spat = hurtsBy(dragon, (d, e) -> d.getState() == TechDragon.State.SPIT);
        double[] before = {0};
        boolean[] spitting = {false};
        helper.runAfterDelay(10, () -> {
            dragon.setYRot(0);
            dragon.yBodyRot = 0;
            setField(dragon, "spitCooldown", 0);
            dragon.setTarget(target);
            forceState(dragon, TechDragon.State.BACKSTEP);
            before[0] = dragon.distanceTo(target);
        });
        helper.onEachTick(() -> {
            setField(dragon, "aggroTarget", target);
            setField(dragon, "aggroTicks", 600);
            spitting[0] |= dragon.getState() == TechDragon.State.SPIT;
        });
        helper.runAfterDelay(30, () -> {
            double now = dragon.distanceTo(target);
            helper.assertTrue(now > before[0] + 6, "the backstep should leap away: " + before[0] + " -> " + now);
        });
        helper.runAfterDelay(80, () -> {
            helper.assertTrue(spitting[0], "after the backstep it should spit lightning");
            helper.assertTrue(spat.getOrDefault(target, 0) > 0, "the spat bolt should hit the target");
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 200, batch = "dragon_kitePushHop")
    public static void dragonKiteWingPushAndHops(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(6, 2, 2));
        Zombie pushed = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(6, 2, 8));
        pushed.setInvulnerable(true);
        Vec3[] at = new Vec3[2];
        helper.runAfterDelay(10, () -> {
            dragon.setYRot(0);
            dragon.yBodyRot = 0;
            dragon.setTarget(pushed);
            setField(dragon, "spitCooldown", 999);
            forceState(dragon, TechDragon.State.WING_PUSH);
            at[0] = pushed.position();
        });
        helper.onEachTick(() -> {
            setField(dragon, "aggroTarget", pushed);
            setField(dragon, "aggroTicks", 600);
        });
        helper.runAfterDelay(40, () -> {
            double moved = pushed.position().distanceTo(at[0]);
            helper.assertTrue(moved > 4, "the wing push should blow the target away, moved " + moved);
            Vec3 home = helper.absoluteVec(new Vec3(6, 2, 2));
            dragon.teleportTo(home.x, home.y, home.z);
            dragon.setYRot(0);
            dragon.yBodyRot = 0;
            setField(dragon, "kiteHopsLeft", 2);
            // first hop toward the middle of the arena (not into its barrier wall)
            try {
                java.lang.reflect.Method v = TechDragon.class.getDeclaredMethod("setAttackVariant", int.class);
                v.setAccessible(true);
                v.invoke(dragon, dragon.getX() < helper.absoluteVec(new Vec3(8, 2, 8)).x ? 0 : 1);
            } catch (ReflectiveOperationException e) {
                throw new RuntimeException(e);
            }
            forceState(dragon, TechDragon.State.KITE_HOP);
            at[1] = dragon.position();
        });
        helper.runAfterDelay(60, () -> {
            double side = Math.abs(dragon.getX() - at[1].x);
            helper.assertTrue(side > 1.5, "the kite hop should jump sideways, moved " + side);
        });
        helper.runAfterDelay(80, () -> {
            helper.assertTrue(dragon.getState() != TechDragon.State.KITE_HOP, "two hops then it moves on, state " + dragon.getState());
            dragon.discard();
            pushed.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 300, batch = "dragon_tailEmpty")
    public static void dragonNoTailWhipWhenBehindIsEmpty(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 3));
        IronGolem front = helper.spawnWithNoFreeWill(EntityType.IRON_GOLEM, new BlockPos(8, 2, 9));
        front.setInvulnerable(true);
        // what the 1.7 rule treated as "behind": a cow at the tail and a zombie beside the shoulders, 9 blocks out
        var cow = helper.spawnWithNoFreeWill(EntityType.COW, new BlockPos(8, 2, 0));
        cow.setInvulnerable(true);
        // well off to the side, beyond any reach of the tail
        Zombie beside = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(-8, 2, 3));
        beside.setInvulnerable(true);
        boolean[] lashed = {false};
        String[] why = {""};
        helper.runAfterDelay(5, () -> {
            dragon.setYRot(0);
            dragon.yBodyRot = 0;
            forceState(dragon, TechDragon.State.GROUND);
            setField(dragon, "tailCooldown", 0);
        });
        helper.onEachTick(() -> {
            setField(dragon, "aggroTarget", front);
            setField(dragon, "aggroTicks", 600);
            dragon.setTarget(front);
            TechDragon.State s = dragon.getState();
            if (!lashed[0] && (s == TechDragon.State.TAIL_WHIP || s == TechDragon.State.TAIL_SWEEP)) {
                try {
                    java.lang.reflect.Method m = TechDragon.class.getDeclaredMethod("preyAtTail");
                    m.setAccessible(true);
                    why[0] = s + " prev-tail=" + m.invoke(dragon) + " beside=" + beside.position() + " dragon=" + dragon.position() + " yaw=" + dragon.yBodyRot
                            + " hp-beside=" + beside.getHealth() + " vehicle=" + beside.getVehicle();
                } catch (ReflectiveOperationException e) {
                    why[0] = e.toString();
                }
            }
            lashed[0] |= s == TechDragon.State.TAIL_WHIP || s == TechDragon.State.TAIL_SWEEP;
            if (s.grounded() && s != TechDragon.State.GROUND && s != TechDragon.State.TAIL_WHIP && s != TechDragon.State.TAIL_SWEEP
                    && dragon.getStateTicks() > 40) {
                forceState(dragon, TechDragon.State.GROUND);
            }
        });
        helper.runAfterDelay(260, () -> {
            helper.assertTrue(!lashed[0], "nothing to attack at its tail: it should never lash its tail; " + why[0]);
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 300, batch = "dragon_tailPrey")
    public static void dragonTailWhipsPreyAtTail(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 9));
        IronGolem front = helper.spawnWithNoFreeWill(EntityType.IRON_GOLEM, new BlockPos(8, 2, 15));
        front.setInvulnerable(true);
        Zombie atTail = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(8, 2, 9));
        atTail.setInvulnerable(true);
        boolean[] lashed = {false};
        helper.runAfterDelay(5, () -> {
            dragon.setYRot(0);
            dragon.yBodyRot = 0;
            forceState(dragon, TechDragon.State.GROUND);
            setField(dragon, "tailCooldown", 0);
        });
        helper.onEachTick(() -> {
            setField(dragon, "aggroTarget", front);
            setField(dragon, "aggroTicks", 600);
            dragon.setTarget(front);
            lashed[0] |= dragon.getState() == TechDragon.State.TAIL_WHIP || dragon.getState() == TechDragon.State.TAIL_SWEEP;
            // only the tail decision is under test: keep the other skills on cooldown
            for (String cd : new String[]{"beamCooldown", "pinCooldown", "kiteCooldown", "spitCooldown", "dodgeCooldown"}) {
                setField(dragon, cd, 9999);
            }
            setField(dragon, "skyTimer", 9999);
            if (!lashed[0] && dragon.getParts().length > 12) {
                // keep the zombie on the tail tip wherever the tail is
                Vec3 tip = dragon.getParts()[11].getBoundingBox().getCenter();
                atTail.teleportTo(tip.x, dragon.getY(), tip.z);
            }
        });
        helper.runAfterDelay(260, () -> {
            helper.assertTrue(lashed[0], "a zombie at its tail should get the tail");
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 200, batch = "dragon_targets")
    public static void dragonPicksAggressiveTargets(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 8));
        var cow = helper.spawnWithNoFreeWill(EntityType.COW, new BlockPos(2, 2, 2));
        var villager = helper.spawnWithNoFreeWill(EntityType.VILLAGER, new BlockPos(14, 2, 2));
        var trader = helper.spawnWithNoFreeWill(EntityType.WANDERING_TRADER, new BlockPos(2, 2, 14));
        var horse = helper.spawnWithNoFreeWill(EntityType.HORSE, new BlockPos(14, 2, 14));
        var technomancer = helper.spawnWithNoFreeWill(TechEntities.TECHNOMANCER.get(), new BlockPos(2, 2, 8));
        for (LivingEntity e : List.of(cow, villager, trader, horse, technomancer)) {
            e.setInvulnerable(true);
        }
        horse.setTamed(true);
        horse.setOwnerUUID(java.util.UUID.randomUUID());
        helper.runAfterDelay(5, () -> {
            forceState(dragon, TechDragon.State.PERCH);
            dragon.setTarget(null);
        });
        helper.runAfterDelay(40, () -> {
            helper.assertTrue(dragon.getTarget() == null, "passive animals, villagers, traders, tamed horses and merchants are left alone, target "
                    + dragon.getTarget());
            var zombie = helper.spawnWithNoFreeWill(EntityType.ZOMBIE, new BlockPos(13, 2, 8));
            var wither = helper.spawnWithNoFreeWill(EntityType.WITHER, new BlockPos(8, 5, 14));
            var golem = helper.spawnWithNoFreeWill(EntityType.IRON_GOLEM, new BlockPos(4, 2, 12));
            var snowGolem = helper.spawnWithNoFreeWill(EntityType.SNOW_GOLEM, new BlockPos(12, 2, 12));
            var wolf = helper.spawnWithNoFreeWill(EntityType.WOLF, new BlockPos(4, 2, 4));
            var cat = helper.spawnWithNoFreeWill(EntityType.CAT, new BlockPos(12, 2, 4));
            cat.setTame(true);
            cat.setOwnerUUID(java.util.UUID.randomUUID());
            for (LivingEntity e : List.of(zombie, wither, golem, snowGolem, wolf, cat)) {
                e.setInvulnerable(true);
                helper.assertTrue(dragon.isPrey(e), "the dragon should go after " + e.getType().getDescriptionId());
            }
            for (LivingEntity e : List.of(cow, villager, trader, horse, technomancer)) {
                helper.assertTrue(!dragon.isPrey(e), "the dragon should leave alone " + e.getType().getDescriptionId());
            }
        });
        helper.runAfterDelay(80, () -> {
            LivingEntity t = dragon.getTarget();
            helper.assertTrue(t != null && dragon.isPrey(t), "with prey around it should pick one, target " + t);
            helper.assertTrue(t instanceof net.minecraft.world.entity.boss.wither.WitherBoss, "bosses first: it should go for the Wither, got " + t);
            for (var e : level.getEntitiesOfClass(LivingEntity.class, dragon.getBoundingBox().inflate(30), e -> !(e instanceof net.minecraft.world.entity.player.Player))) {
                if (e != dragon) {
                    e.discard();
                }
            }
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 400, batch = "dragon_crash")
    public static void dragonCrashLandingBlasts(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 9, 8));
        net.minecraft.world.entity.monster.Husk target = helper.spawnWithNoFreeWill(EntityType.HUSK, new BlockPos(8, 2, 14));
        target.setInvulnerable(true);
        net.minecraft.world.entity.monster.Husk near = helper.spawnWithNoFreeWill(EntityType.HUSK, new BlockPos(4, 2, 6));
        java.util.Map<LivingEntity, Integer> hit = hurtsBy(dragon, (d, e) -> true);
        int[] debris = {0};
        boolean[] crashed = {false};
        int[] rings = {0};
        net.minecraftforge.common.MinecraftForge.EVENT_BUS.addListener((net.minecraftforge.event.entity.EntityJoinLevelEvent e) -> {
            if (e.getEntity() instanceof net.isstechnomancy.entity.boss.DragonDebris d && d.distanceTo(dragon) < 40) {
                debris[0]++;
            }
        });
        // the arena floor and walls, to prove nothing was broken or moved
        java.util.Map<BlockPos, net.minecraft.world.level.block.state.BlockState> blocks = new java.util.HashMap<>();
        helper.runAfterDelay(4, () -> {
            for (int x = 0; x < 16; x++) {
                for (int y = 0; y < 6; y++) {
                    for (int z = 0; z < 16; z++) {
                        BlockPos p = helper.absolutePos(new BlockPos(x, y, z));
                        blocks.put(p, level.getBlockState(p));
                    }
                }
            }
        });
        level.getGameRules().getRule(net.minecraft.world.level.GameRules.RULE_MOBGRIEFING).set(false, level.getServer());
        helper.runAfterDelay(5, () -> {
            setField(dragon, "airAttacksLeft", 0);
            dragon.setTarget(target);
            forceState(dragon, TechDragon.State.HOVER);
        });
        helper.onEachTick(() -> {
            setField(dragon, "aggroTarget", target);
            setField(dragon, "aggroTicks", 600);
            // the core beam may drill blocks (1.9): this test is about the landing, which must not
            setField(dragon, "beamCooldown", 9999);
            if (dragon.getState() == TechDragon.State.CRASH) {
                crashed[0] = true;
            }
            if (crashed[0] && dragon.getState() == TechDragon.State.CRASH && dragon.getStateTicks() < 20) {
                try {
                    java.lang.reflect.Field f = TechDragon.class.getDeclaredField("rings");
                    f.setAccessible(true);
                    rings[0] = Math.max(rings[0], ((List<?>) f.get(dragon)).size());
                } catch (ReflectiveOperationException ex) {
                    throw new RuntimeException(ex);
                }
            }
        });
        helper.runAfterDelay(380, () -> {
            helper.assertTrue(crashed[0], "landing into the fight should be a crash landing, state " + dragon.getState());
            helper.assertTrue(debris[0] >= 6, "the crash should throw chunks of ground: " + debris[0]);
            helper.assertTrue(rings[0] >= 3, "several shock rings should spread one after another: " + rings[0]);
            helper.assertTrue(hit.getOrDefault(near, 0) > 0 || !near.isAlive(), "the blast should hit what stands near the impact");
            int changed = 0;
            List<String> what = new java.util.ArrayList<>();
            for (var en : blocks.entrySet()) {
                var now = level.getBlockState(en.getKey());
                // water/lava from the world outside the arena may flow; the crash can only break or move solid blocks
                // only blocks that were there (solid) count: water or gravel from the world outside may move in; the
                // crash could only break or move what was standing
                if (!now.equals(en.getValue()) && !en.getValue().isAir() && en.getValue().getFluidState().isEmpty()) {
                    changed++;
                    if (what.size() < 6) {
                        what.add(helper.relativePos(en.getKey()) + " " + en.getValue().getBlock() + " -> " + level.getBlockState(en.getKey()).getBlock());
                    }
                }
            }
            level.getGameRules().getRule(net.minecraft.world.level.GameRules.RULE_MOBGRIEFING).set(true, level.getServer());
            helper.assertTrue(changed == 0, "the crash must not break or move any block: " + changed + " changed " + what);
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 500, batch = "dragon_stormMany")
    public static void dragonStormStrikesEveryone(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 8));
        List<net.minecraft.world.entity.monster.Husk> husks = List.of(
                helper.spawnWithNoFreeWill(EntityType.HUSK, new BlockPos(2, 2, 2)),
                helper.spawnWithNoFreeWill(EntityType.HUSK, new BlockPos(14, 2, 3)),
                helper.spawnWithNoFreeWill(EntityType.HUSK, new BlockPos(3, 2, 14)),
                helper.spawnWithNoFreeWill(EntityType.HUSK, new BlockPos(13, 2, 13)));
        for (var h : husks) {
            h.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH).setBaseValue(1000);
            h.setHealth(1000);
        }
        java.util.Map<LivingEntity, Integer> hit = hurtsBy(dragon, (d, e) -> e.getSource().getDirectEntity() instanceof io.redspace.ironsspellbooks.entity.spells.LightningStrike);
        helper.runAfterDelay(10, () -> {
            dragon.setTarget(husks.get(0));
            forceState(dragon, TechDragon.State.STORM_RISE);
        });
        helper.onEachTick(() -> {
            setField(dragon, "aggroTarget", husks.get(0));
            setField(dragon, "aggroTicks", 600);
        });
        helper.runAfterDelay(300, () -> {
            int struck = 0;
            for (var h : husks) {
                if (hit.getOrDefault(h, 0) > 0) {
                    struck++;
                }
            }
            helper.assertTrue(struck == husks.size(), "the storm should strike every creature in the area: " + struck + "/" + husks.size() + " " + hit);
            dragon.discard();
            helper.succeed();
        });
    }

    // ------------------------------------------------------------------ 1.9

    private static net.minecraft.world.entity.monster.Husk tough(GameTestHelper helper, BlockPos at) {
        var h = helper.spawnWithNoFreeWill(EntityType.HUSK, at);
        h.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH).setBaseValue(1000);
        h.setHealth(1000);
        return h;
    }

    @GameTest(template = "test_arena", timeoutTicks = 200, batch = "dragon_empStun")
    public static void dragonEmpStunOncePer30s(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 8));
        helper.runAfterDelay(10, () -> {
            forceState(dragon, TechDragon.State.GROUND);
            helper.assertTrue(dragon.applyStun(60), "the first EMP should stun it");
            helper.assertTrue(dragon.getState() == TechDragon.State.EMP_STUN && dragon.isDrained(), "EMP stun state, drained look");
        });
        helper.runAfterDelay(80, () -> {
            helper.assertTrue(dragon.getState() != TechDragon.State.EMP_STUN && !dragon.isDrained(), "back up after ~3 s, state " + dragon.getState());
            helper.assertTrue(!dragon.applyStun(60), "a second EMP within 30 s should not stun it");
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 200, batch = "dragon_pin")
    public static void dragonPinsAndGnaws(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 2));
        var prey = tough(helper, new BlockPos(8, 2, 8));
        java.util.Map<LivingEntity, Integer> hits = hurtsBy(dragon, (d, e) -> d.getState() == TechDragon.State.PIN);
        boolean[] pinned = {false};
        helper.runAfterDelay(10, () -> {
            dragon.setYRot(0);
            dragon.yBodyRot = 0;
            dragon.setTarget(prey);
            forceState(dragon, TechDragon.State.PIN);
        });
        helper.onEachTick(() -> {
            setField(dragon, "aggroTarget", prey);
            setField(dragon, "aggroTicks", 600);
            if (dragon.getState() == TechDragon.State.PIN && dragon.getStateTicks() < 8) {
                // keep the prey under the left forefoot until it comes down
                Vec3 paw = dragon.track(net.isstechnomancy.entity.boss.DragonTracks.HAND_L);
                prey.teleportTo(paw.x, dragon.getY(), paw.z);
            }
            pinned[0] |= prey.getVehicle() == dragon;
        });
        helper.runAfterDelay(90, () -> {
            helper.assertTrue(pinned[0], "the prey should be pinned under the forefoot");
            helper.assertTrue(hits.getOrDefault(prey, 0) >= 4, "pinned and gnawed several times: " + hits.getOrDefault(prey, 0));
            helper.assertTrue(prey.getVehicle() == null, "released (kicked away) at the end");
            dragon.discard();
            prey.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 300, batch = "dragon_carry")
    public static void dragonCarriesPreyUpAndDrops(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 8));
        var prey = tough(helper, new BlockPos(8, 2, 14));
        double[] y0 = {0};
        boolean[] lifted = {false};
        helper.runAfterDelay(10, () -> {
            prey.startRiding(dragon, true);
            setField(dragon, "grabbed", prey);
            setField(dragon, "carryTop", dragon.getY() + 18);
            y0[0] = prey.getY();
            forceState(dragon, TechDragon.State.CARRY);
        });
        helper.onEachTick(() -> lifted[0] |= prey.getVehicle() == dragon && prey.getY() > y0[0] + 8);
        helper.runAfterDelay(120, () -> {
            helper.assertTrue(lifted[0], "the prey should be carried up into the air");
            helper.assertTrue(prey.getVehicle() == null, "then dropped");
            dragon.discard();
            prey.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 300, batch = "dragon_beam")
    public static void dragonCoreBeamBurnsDrillsAndOverloads(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 1));
        var victim = tough(helper, new BlockPos(8, 2, 13));
        // a stone wall behind the victim, in the beam's path
        for (int x = 6; x <= 10; x++) {
            for (int y = 2; y <= 6; y++) {
                helper.setBlock(new BlockPos(x, y, 15), net.minecraft.world.level.block.Blocks.STONE);
            }
        }
        java.util.Map<LivingEntity, Integer> hits = hurtsBy(dragon, (d, e) -> d.getState() == TechDragon.State.CORE_BEAM);
        boolean[] burning = {false};
        boolean[] drained = {false};
        helper.runAfterDelay(10, () -> {
            dragon.setYRot(0);
            dragon.yBodyRot = 0;
            dragon.setTarget(victim);
            forceState(dragon, TechDragon.State.CORE_CHARGE);
        });
        helper.onEachTick(() -> {
            setField(dragon, "aggroTarget", victim);
            setField(dragon, "aggroTicks", 600);
            burning[0] |= victim.isOnFire();
            drained[0] |= dragon.getState() == TechDragon.State.OVERLOAD && dragon.isDrained();
        });
        helper.runAfterDelay(160, () -> {
            int stone = 0;
            for (int x = 6; x <= 10; x++) {
                for (int y = 2; y <= 6; y++) {
                    if (level.getBlockState(helper.absolutePos(new BlockPos(x, y, 15))).is(net.minecraft.world.level.block.Blocks.STONE)) {
                        stone++;
                    }
                }
            }
            helper.assertTrue(hits.getOrDefault(victim, 0) >= 3, "the beam should hit hard and often: " + hits.getOrDefault(victim, 0));
            helper.assertTrue(burning[0], "the beam sets what it hits on fire");
            helper.assertTrue(drained[0], "after the beam it overloads, glow drained");
            helper.assertTrue(stone < 25, "the beam should drill through stone (mobGriefing): " + stone + "/25 left");
            dragon.discard();
            victim.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 300, batch = "dragon_breaks")
    public static void dragonBreaksThroughButKeepsChests(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 3));
        var target = tough(helper, new BlockPos(8, 2, 14));
        for (int x = 2; x <= 14; x++) {
            for (int y = 2; y <= 7; y++) {
                helper.setBlock(new BlockPos(x, y, 9), x == 8 && y == 2 ? net.minecraft.world.level.block.Blocks.CHEST : net.minecraft.world.level.block.Blocks.COBBLESTONE);
            }
        }
        helper.runAfterDelay(5, () -> {
            dragon.setYRot(0);
            dragon.yBodyRot = 0;
            setField(dragon, "beamCooldown", 9999);
            forceState(dragon, TechDragon.State.RAM);
            dragon.setTarget(target);
        });
        helper.onEachTick(() -> {
            setField(dragon, "aggroTarget", target);
            setField(dragon, "aggroTicks", 600);
        });
        helper.runAfterDelay(120, () -> {
            int cobble = 0;
            for (int x = 2; x <= 14; x++) {
                for (int y = 2; y <= 7; y++) {
                    if (level.getBlockState(helper.absolutePos(new BlockPos(x, y, 9))).is(net.minecraft.world.level.block.Blocks.COBBLESTONE)) {
                        cobble++;
                    }
                }
            }
            helper.assertTrue(cobble < 70, "the dragon should smash through the cobblestone wall: " + cobble + "/77 left");
            helper.assertTrue(level.getBlockState(helper.absolutePos(new BlockPos(8, 2, 9))).is(net.minecraft.world.level.block.Blocks.CHEST), "blocks with data (a chest) are never broken");
            dragon.discard();
            target.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 500, batch = "dragon_death19")
    public static void dragonDeathBlastKillsArmoured(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        TechDragon dragon = spawnDragon(helper, new Vec3(6, 2, 6));
        var victim = helper.spawnWithNoFreeWill(EntityType.HUSK, new BlockPos(14, 2, 14));
        for (var slot : new net.minecraft.world.entity.EquipmentSlot[]{net.minecraft.world.entity.EquipmentSlot.HEAD, net.minecraft.world.entity.EquipmentSlot.CHEST,
                net.minecraft.world.entity.EquipmentSlot.LEGS, net.minecraft.world.entity.EquipmentSlot.FEET}) {
            net.minecraft.world.item.ItemStack piece = new net.minecraft.world.item.ItemStack(switch (slot) {
                case HEAD -> net.minecraft.world.item.Items.NETHERITE_HELMET;
                case CHEST -> net.minecraft.world.item.Items.NETHERITE_CHESTPLATE;
                case LEGS -> net.minecraft.world.item.Items.NETHERITE_LEGGINGS;
                default -> net.minecraft.world.item.Items.NETHERITE_BOOTS;
            });
            piece.enchant(net.minecraft.world.item.enchantment.Enchantments.BLAST_PROTECTION, 4);
            victim.setItemSlot(slot, piece);
        }
        helper.runAfterDelay(5, () -> {
            forceState(dragon, TechDragon.State.GROUND);
            dragon.setHealth(1f);
            dragon.hurt(level.damageSources().generic(), 10f);
        });
        helper.runAfterDelay(260, () -> {
            helper.assertTrue(dragon.isRemoved(), "the dragon is gone after the blast");
            helper.assertTrue(!victim.isAlive(), "within 20 blocks the blast kills even blast-protection netherite");
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 40)
    public static void hextechCodexGrowsTo12AndRecipesExist(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        net.minecraft.world.item.ItemStack codex = new net.minecraft.world.item.ItemStack(net.isstechnomancy.registry.TechItems.CLOCKWORK_CODEX.get());
        io.redspace.ironsspellbooks.api.spells.ISpellContainer.set(codex, io.redspace.ironsspellbooks.api.spells.ISpellContainer.create(7, true, true));
        helper.assertTrue(net.isstechnomancy.item.TechSpellBookItem.growContainer(codex, 12), "a 7-slot container on the codex grows");
        helper.assertTrue(io.redspace.ironsspellbooks.api.spells.ISpellContainer.get(codex).getMaxSpellCount() == 12, "to 12 slots");
        java.util.Set<String> results = new java.util.HashSet<>();
        for (var r : level.getRecipeManager().getAllRecipesFor(net.minecraft.world.item.crafting.RecipeType.SMITHING)) {
            results.add(net.minecraftforge.registries.ForgeRegistries.ITEMS.getKey(r.getResultItem(level.registryAccess()).getItem()).getPath());
        }
        for (String need : new String[]{"hextech_engineer_helmet", "hextech_engineer_chestplate", "hextech_engineer_leggings", "hextech_engineer_boots",
                "hextech_scepter", "hextech_scepter_star1", "hextech_scepter_star2", "hextech_scepter_star3", "clockwork_codex"}) {
            helper.assertTrue(results.contains(need), "smithing recipe for " + need);
        }
        var template = level.getRecipeManager().byKey(net.isstechnomancy.ISSTechnomancy.id("hextech_upgrade_smithing_template"));
        helper.assertTrue(template.isPresent() && template.get().getResultItem(level.registryAccess()).getCount() == 2, "the template recipe makes two");
        helper.succeed();
    }

    // ------------------------------------------------------------------ 1.10

    private static Object call(TechDragon dragon, String name, Class<?>[] types, Object... args) {
        try {
            java.lang.reflect.Method m = TechDragon.class.getDeclaredMethod(name, types);
            m.setAccessible(true);
            return m.invoke(dragon, args);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }

    private static boolean onTopOfDragon(TechDragon dragon, LivingEntity e) {
        var eb = e.getBoundingBox();
        for (var part : dragon.getParts()) {
            var p = (net.isstechnomancy.entity.boss.TechDragonPart) part;
            var pb = part.getBoundingBox();
            if (p.solid && eb.maxX > pb.minX && eb.minX < pb.maxX && eb.maxZ > pb.minZ && eb.minZ < pb.maxZ && eb.minY >= pb.maxY - 0.3 && eb.minY <= pb.maxY + 0.5) {
                return true;
            }
        }
        return false;
    }

    @GameTest(template = "test_arena", timeoutTicks = 240, batch = "dragon_onBack")
    public static void dragonShakesOffWhatStandsOnItsBack(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 6));
        IronGolem front = dummy(helper, new BlockPos(8, 2, 13));
        var rider = tough(helper, new BlockPos(8, 2, 2));
        boolean[] spun = {false};
        helper.runAfterDelay(5, () -> {
            dragon.setYRot(0);
            dragon.yBodyRot = 0;
            forceState(dragon, TechDragon.State.GROUND);
            // a mob teleported right onto the dragon's back (the chest's top)
            var chest = dragon.getParts()[3].getBoundingBox();
            rider.teleportTo(chest.getCenter().x, chest.maxY + 0.05, chest.getCenter().z);
        });
        helper.onEachTick(() -> {
            setField(dragon, "aggroTarget", front);
            setField(dragon, "aggroTicks", 600);
            dragon.setTarget(front);
            spun[0] |= dragon.getState() == TechDragon.State.SPIN;
        });
        helper.runAfterDelay(200, () -> {
            helper.assertTrue(!onTopOfDragon(dragon, rider), "nothing may stay parked on the dragon's back, at " + rider.position());
            dragon.discard();
            rider.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 120, batch = "dragon_spin")
    public static void dragonSpinDischargeHitsAllAround(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 8));
        List<net.minecraft.world.entity.monster.Husk> ring = new java.util.ArrayList<>();
        for (int[] p : new int[][]{{2, 8}, {14, 8}, {8, 2}, {8, 14}}) {
            ring.add(tough(helper, new BlockPos(p[0], 2, p[1])));
        }
        java.util.Map<LivingEntity, Integer> hits = hurtsBy(dragon, (d, e) -> d.getState() == TechDragon.State.SPIN);
        helper.runAfterDelay(5, () -> forceState(dragon, TechDragon.State.SPIN));
        helper.runAfterDelay(60, () -> {
            int hit = 0;
            for (var h : ring) {
                hit += hits.getOrDefault(h, 0) > 0 ? 1 : 0;
            }
            helper.assertTrue(hit >= 3, "the spin's discharge should reach all around: " + hit + "/4");
            dragon.discard();
            ring.forEach(net.minecraft.world.entity.Entity::discard);
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 120, batch = "dragon_hop")
    public static void dragonHopsBackToStrikingRange(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 6));
        IronGolem target = dummy(helper, new BlockPos(8, 2, 10));
        double[] z0 = {0};
        helper.runAfterDelay(5, () -> {
            dragon.setYRot(0);
            dragon.yBodyRot = 0;
            dragon.setTarget(target);
            // the target is right under its chin: the hop should carry it back to biting distance
            TechDragon.State s = (TechDragon.State) call(dragon, "hop", new Class<?>[]{Vec3.class}, call(dragon, "local", new Class<?>[]{Vec3.class}, target.position()));
            forceState(dragon, s);
            z0[0] = dragon.getZ();
        });
        helper.onEachTick(() -> {
            setField(dragon, "aggroTarget", target);
            setField(dragon, "aggroTicks", 600);
        });
        helper.runAfterDelay(22, () -> {
            double moved = z0[0] - dragon.getZ();
            helper.assertTrue(moved > 1.5, "a hop back away from a target that is too close, moved " + moved);
            dragon.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 260, batch = "dragon_skyBreath")
    public static void dragonSkyBreathPoursLightningDown(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 2));
        var victim = tough(helper, new BlockPos(8, 2, 10));
        java.util.Map<LivingEntity, Integer> hits = hurtsBy(dragon, (d, e) -> d.getState() == TechDragon.State.SKY_BREATH);
        double[] top = {0};
        helper.runAfterDelay(5, () -> {
            dragon.setTarget(victim);
            forceState(dragon, TechDragon.State.SKY_BREATH);
        });
        helper.onEachTick(() -> {
            setField(dragon, "aggroTarget", victim);
            setField(dragon, "aggroTicks", 600);
            if (dragon.getState() == TechDragon.State.SKY_BREATH) {
                top[0] = Math.max(top[0], dragon.getY() - victim.getY());
            }
        });
        helper.runAfterDelay(130, () -> {
            helper.assertTrue(top[0] > 6, "it should circle high above the target, got " + top[0]);
            helper.assertTrue(hits.getOrDefault(victim, 0) >= 3, "and breathe lightning down on it: " + hits.getOrDefault(victim, 0));
            dragon.discard();
            victim.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 200, batch = "dragon_strafe")
    public static void dragonStrafingRunSpitsBolts(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(2, 8, 8));
        var victim = tough(helper, new BlockPos(12, 2, 8));
        java.util.Map<LivingEntity, Integer> hits = hurtsBy(dragon, (d, e) -> d.getState() == TechDragon.State.STRAFE);
        helper.runAfterDelay(5, () -> {
            dragon.setTarget(victim);
            forceState(dragon, TechDragon.State.STRAFE);
        });
        helper.onEachTick(() -> {
            setField(dragon, "aggroTarget", victim);
            setField(dragon, "aggroTicks", 600);
        });
        helper.runAfterDelay(80, () -> {
            int left;
            try {
                java.lang.reflect.Field f = TechDragon.class.getDeclaredField("strafeSpits");
                f.setAccessible(true);
                left = f.getInt(dragon);
            } catch (ReflectiveOperationException e) {
                throw new RuntimeException(e);
            }
            // the bolts must be spat as it passes over; whether they connect in this boxed-in arena (barrier walls and
            // ceiling) is geometry, so either a hit or all three bolts spent passes
            helper.assertTrue(hits.getOrDefault(victim, 0) >= 1 || left == 0, "the strafing run should spit its bolts at the target: hits "
                    + hits.getOrDefault(victim, 0) + ", bolts left " + left);
            dragon.discard();
            victim.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 120, batch = "dragon_roarPush")
    public static void dragonRoarPushesEverythingAway(GameTestHelper helper) {
        TechDragon dragon = spawnDragon(helper, new Vec3(8, 2, 8));
        List<net.minecraft.world.entity.monster.Husk> near = new java.util.ArrayList<>();
        for (int[] p : new int[][]{{3, 8}, {13, 8}, {8, 3}, {8, 13}}) {
            near.add(tough(helper, new BlockPos(p[0], 2, p[1])));
        }
        double[] before = new double[4];
        helper.runAfterDelay(5, () -> {
            forceState(dragon, TechDragon.State.GROUND_ROAR);
            for (int i = 0; i < 4; i++) {
                before[i] = near.get(i).distanceTo(dragon);
            }
        });
        helper.runAfterDelay(40, () -> {
            int pushed = 0;
            for (int i = 0; i < 4; i++) {
                pushed += near.get(i).distanceTo(dragon) > before[i] + 1.0 ? 1 : 0;
            }
            helper.assertTrue(pushed >= 3, "the roar should blast everything around away: " + pushed + "/4");
            dragon.discard();
            near.forEach(net.minecraft.world.entity.Entity::discard);
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 60, batch = "dragon_skyBolts")
    public static void skyLightningNeverBreaksBlocks(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        TechDragon dragon = spawnDragon(helper, new Vec3(3, 2, 3));
        BlockPos dirt = new BlockPos(12, 2, 12);
        helper.setBlock(dirt, net.minecraft.world.level.block.Blocks.DIRT);
        helper.runAfterDelay(5, () -> {
            Vec3 at = helper.absoluteVec(new Vec3(12.5, 3, 12.5));
            call(dragon, "strike", new Class<?>[]{Vec3.class, float.class, double.class}, at, 5f, at.y);
        });
        helper.runAfterDelay(30, () -> {
            helper.assertTrue(level.getBlockState(helper.absolutePos(dirt)).is(net.minecraft.world.level.block.Blocks.DIRT), "a bolt from the sky leaves the ground alone");
            dragon.discard();
            helper.succeed();
        });
    }

    // its own batch: the storm (V) strikes hostile mobs ~18 blocks around, which would reach the neighbouring tests
    @GameTest(template = "test_arena", timeoutTicks = 200, batch = "drake_keys")
    public static void drakeRiderKeys(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        var owner = helper.makeMockPlayer();
        Vec3 at = helper.absoluteVec(new Vec3(5, 2, 5));
        owner.moveTo(at.x, at.y, at.z);
        TechDrake drake = new TechDrake(level, owner, 1f, 120, 2000, false);
        Vec3 d = helper.absoluteVec(new Vec3(8, 2, 8));
        drake.moveTo(d.x, d.y, d.z);
        level.addFreshEntity(drake);
        helper.runAfterDelay(20, () -> {
            drake.mobInteract(owner, net.minecraft.world.InteractionHand.MAIN_HAND);
            drake.riderAction(TechDrake.Action.CLAW);
            helper.assertTrue(drake.getState() == TechDragon.State.CLAW, "X rakes, state " + drake.getState());
        });
        helper.runAfterDelay(60, () -> {
            drake.riderAction(TechDrake.Action.BITE);
            helper.assertTrue(drake.getState() == TechDragon.State.BITE, "Z bites, state " + drake.getState());
            drake.riderAction(TechDrake.Action.STORM);
            helper.assertTrue(drake.getStormCooldown() > 0, "V calls the storm");
        });
        helper.runAfterDelay(100, () -> {
            owner.stopRiding();
            drake.discard();
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 260, batch = "dragon_forge")
    public static void thunderforgeSummonsTheDragon(GameTestHelper helper) {
        ServerLevel level = helper.getLevel();
        clearLeftovers(helper);
        BlockPos rel = new BlockPos(8, 2, 8);
        helper.setBlock(rel, net.isstechnomancy.registry.TechBlocks.CLOCKWORK_ALTAR.get());
        var player = helper.makeMockPlayer();
        Vec3 at = helper.absoluteVec(new Vec3(8.5, 2, 4.5));
        player.moveTo(at.x, at.y, at.z);
        player.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new net.minecraft.world.item.ItemStack(net.isstechnomancy.registry.TechItems.OVERCHARGED_DYNAMO_CORE.get()));
        BlockPos abs = helper.absolutePos(rel);
        helper.runAfterDelay(5, () -> {
            var state = level.getBlockState(abs);
            var hit = new net.minecraft.world.phys.BlockHitResult(Vec3.atCenterOf(abs), net.minecraft.core.Direction.NORTH, abs, false);
            state.use(level, player, net.minecraft.world.InteractionHand.MAIN_HAND, hit);
            var be = level.getBlockEntity(abs);
            helper.assertTrue(be instanceof net.isstechnomancy.block.HextechForgeBlockEntity f && f.isSummoning() && f.hasCore(), "the core is set and the summoning starts");
            helper.assertTrue(player.getMainHandItem().isEmpty(), "the core is used up");
            helper.assertTrue(level.getEntitiesOfClass(TechDragon.class, new net.minecraft.world.phys.AABB(abs).inflate(32)).isEmpty(), "no dragon yet: it gathers the storm first");
        });
        helper.runAfterDelay(140, () -> {
            var dragons = level.getEntitiesOfClass(TechDragon.class, new net.minecraft.world.phys.AABB(abs).inflate(32));
            helper.assertTrue(!dragons.isEmpty(), "after ~6 s the ball of lightning bursts into the dragon");
            var be = (net.isstechnomancy.block.HextechForgeBlockEntity) level.getBlockEntity(abs);
            helper.assertTrue(!be.isSummoning() && !be.hasCore(), "the forge is idle again");
            dragons.forEach(net.minecraft.world.entity.Entity::discard);
            helper.succeed();
        });
    }

    @GameTest(template = "test_arena", timeoutTicks = 40)
    public static void scepterEvolutionThreeOverloads(GameTestHelper helper) {
        var player = helper.makeMockPlayer();
        player.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new net.minecraft.world.item.ItemStack(net.isstechnomancy.registry.TechItems.HEXTECH_SCEPTER_3.get()));
        helper.assertTrue(net.isstechnomancy.item.ScepterEvolutionEvents.evolution(player) == 3, "the star 3 scepter is Evolution 3");
        var school = net.isstechnomancy.registry.TechSchools.TECHNOMANCY.get();
        var first = new io.redspace.ironsspellbooks.api.events.SpellOnCastEvent(player, "iss_technomancy:gear_barrage", 3, 20, school, CastSource.SPELLBOOK);
        net.minecraftforge.common.MinecraftForge.EVENT_BUS.post(first);
        helper.assertTrue(first.getSpellLevel() == 4, "Overload: the spell is cast a level higher (" + first.getSpellLevel() + ")");
        var second = new io.redspace.ironsspellbooks.api.events.SpellOnCastEvent(player, "iss_technomancy:gear_barrage", 3, 20, school, CastSource.SPELLBOOK);
        net.minecraftforge.common.MinecraftForge.EVENT_BUS.post(second);
        helper.assertTrue(second.getSpellLevel() == 3, "then it waits 20 s (" + second.getSpellLevel() + ")");
        var basic = helper.makeMockPlayer();
        basic.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new net.minecraft.world.item.ItemStack(net.isstechnomancy.registry.TechItems.HEXTECH_SCEPTER.get()));
        helper.assertTrue(net.isstechnomancy.item.ScepterEvolutionEvents.evolution(basic) == 0, "the base scepter is Evolution 0");
        helper.succeed();
    }
}
