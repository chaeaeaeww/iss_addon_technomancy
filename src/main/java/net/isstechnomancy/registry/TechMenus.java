package net.isstechnomancy.registry;

import net.isstechnomancy.ISSTechnomancy;
import net.isstechnomancy.menu.StaffModuleMenu;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.inventory.MenuType;
import net.minecraftforge.common.extensions.IForgeMenuType;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public class TechMenus {
    private static final DeferredRegister<MenuType<?>> MENUS = DeferredRegister.create(Registries.MENU, ISSTechnomancy.MODID);

    public static final RegistryObject<MenuType<StaffModuleMenu>> STAFF_MODULES = MENUS.register("staff_modules",
            () -> IForgeMenuType.create(StaffModuleMenu::new));

    public static void register(IEventBus modEventBus) {
        MENUS.register(modEventBus);
    }
}
