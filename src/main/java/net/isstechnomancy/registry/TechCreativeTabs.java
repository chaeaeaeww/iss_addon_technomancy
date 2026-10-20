package net.isstechnomancy.registry;

import net.isstechnomancy.ISSTechnomancy;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public class TechCreativeTabs {
    private static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, ISSTechnomancy.MODID);

    public static final RegistryObject<CreativeModeTab> TECHNOMANCY_TAB = TABS.register("technomancy", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.iss_technomancy.technomancy"))
            .icon(() -> new ItemStack(TechItems.ARCANE_COG.get()))
            .displayItems((parameters, output) -> {
                output.accept(TechItems.ARCANE_COG.get());
                output.accept(TechItems.TECHNOMANCY_RUNE.get());
                output.accept(TechItems.TECHNOMANCY_UPGRADE_ORB.get());
                output.accept(TechItems.CLOCKWORK_SCEPTER.get());
                output.accept(TechItems.CLOCKWORK_ENGINEER_HELMET.get());
                output.accept(TechItems.CLOCKWORK_ENGINEER_CHESTPLATE.get());
                output.accept(TechItems.CLOCKWORK_ENGINEER_LEGGINGS.get());
                output.accept(TechItems.CLOCKWORK_ENGINEER_BOOTS.get());
                output.accept(TechItems.CLOCKWORK_SPELLBOOK.get());
                output.accept(TechItems.HEXTECH_UPGRADE_TEMPLATE.get());
                output.accept(TechItems.HEXTECH_SCEPTER.get());
                output.accept(TechItems.HEXTECH_SCEPTER_1.get());
                output.accept(TechItems.HEXTECH_SCEPTER_2.get());
                output.accept(TechItems.HEXTECH_SCEPTER_3.get());
                output.accept(TechItems.HEXTECH_ENGINEER_HELMET.get());
                output.accept(TechItems.HEXTECH_ENGINEER_CHESTPLATE.get());
                output.accept(TechItems.HEXTECH_ENGINEER_LEGGINGS.get());
                output.accept(TechItems.HEXTECH_ENGINEER_BOOTS.get());
                output.accept(TechItems.CLOCKWORK_CODEX.get());
                TechItems.MODULES.values().forEach(tiers -> tiers.forEach(module -> output.accept(module.get())));
                output.accept(TechItems.OVERCHARGED_DYNAMO_CORE.get());
                output.accept(TechItems.TECH_DRAGON_CORE.get());
                output.accept(TechItems.CLOCKWORK_ALTAR.get());
                output.accept(TechItems.CLOCKWORK_AUTOMATON_SPAWN_EGG.get());
                output.accept(TechItems.TECH_DRAGON_SPAWN_EGG.get());
                output.accept(TechItems.TECHNOMANCER_SPAWN_EGG.get());
            })
            .build());

    public static void register(IEventBus modEventBus) {
        TABS.register(modEventBus);
    }
}
