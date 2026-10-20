package net.isstechnomancy.effect;

import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

/**
 * Glorious Evolution buffs of the Hextech Engineer set (1.9). Their attribute modifiers come from other mods' registries
 * (Iron's Spells attributes), which may not exist yet when effects are registered, so they are attached on first use.
 */
public class EvolutionEffect extends MobEffect {
    private record Mod(Supplier<Attribute> attribute, String uuid, double amount, AttributeModifier.Operation operation) {
    }

    private final List<Mod> pending = new ArrayList<>();
    private boolean attached;

    public EvolutionEffect(int color) {
        super(MobEffectCategory.BENEFICIAL, color);
    }

    public EvolutionEffect with(Supplier<Attribute> attribute, String uuid, double amount, AttributeModifier.Operation operation) {
        pending.add(new Mod(attribute, uuid, amount, operation));
        return this;
    }

    @Override
    public Map<Attribute, AttributeModifier> getAttributeModifiers() {
        if (!attached) {
            attached = true;
            for (Mod m : pending) {
                addAttributeModifier(m.attribute().get(), m.uuid(), m.amount(), m.operation());
            }
        }
        return super.getAttributeModifiers();
    }

    @Override
    public void addAttributeModifiers(net.minecraft.world.entity.LivingEntity entity, net.minecraft.world.entity.ai.attributes.AttributeMap map, int amplifier) {
        getAttributeModifiers();
        super.addAttributeModifiers(entity, map, amplifier);
    }

    @Override
    public void removeAttributeModifiers(net.minecraft.world.entity.LivingEntity entity, net.minecraft.world.entity.ai.attributes.AttributeMap map, int amplifier) {
        getAttributeModifiers();
        super.removeAttributeModifiers(entity, map, amplifier);
    }
}
