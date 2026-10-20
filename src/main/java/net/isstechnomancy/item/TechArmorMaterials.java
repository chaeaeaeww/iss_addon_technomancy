package net.isstechnomancy.item;

import io.redspace.ironsspellbooks.api.registry.AttributeRegistry;
import io.redspace.ironsspellbooks.item.armor.IronsExtendedArmorMaterial;
import io.redspace.ironsspellbooks.registries.ItemRegistry;
import net.isstechnomancy.registry.TechAttributes;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.LazyLoadedValue;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.crafting.Ingredient;

import java.util.EnumMap;
import java.util.Map;
import java.util.function.Supplier;

/**
 * Same numbers as the Iron's Spells school sets (Pyromancer, Electromancer, ...):
 * 3/8/6/3 armor, durability multiplier 38, enchantability 15, repaired with Magic Cloth,
 * and per piece +125 max mana, +10% school power, +5% spell power.
 *
 * <p>1.9 Hextech Engineer (smithing: Hextech upgrade template + Clockwork piece + Tech Dragon Core): 4/10/7/4 armor,
 * 3.5 toughness, 0.1 knockback resistance, and per piece +150 max mana, +15% Technomancy power, +10% Lightning power,
 * +5% spell power, +3% cooldown reduction. Full set: Glorious Evolution (HextechArmorEvents).</p>
 */
public enum TechArmorMaterials implements IronsExtendedArmorMaterial {
    CLOCKWORK_ENGINEER("iss_technomancy:clockwork_engineer", 38, 15, SoundEvents.ARMOR_EQUIP_IRON, 0.0F, 0.0F,
            () -> Ingredient.of(ItemRegistry.MAGIC_CLOTH.get()),
            () -> Map.of(
                    AttributeRegistry.MAX_MANA.get(), new AttributeModifier("Max Mana", 125, AttributeModifier.Operation.ADDITION),
                    TechAttributes.TECHNOMANCY_SPELL_POWER.get(), new AttributeModifier("Technomancy Power", 0.10, AttributeModifier.Operation.MULTIPLY_BASE),
                    AttributeRegistry.SPELL_POWER.get(), new AttributeModifier("Base Power", 0.05, AttributeModifier.Operation.MULTIPLY_BASE)
            ), SchoolArmor.SCHOOL),
    HEXTECH_ENGINEER("iss_technomancy:hextech_engineer", 42, 18, SoundEvents.ARMOR_EQUIP_NETHERITE, 3.5F, 0.1F,
            () -> Ingredient.of(net.minecraft.world.item.Items.NETHERITE_INGOT),
            () -> Map.of(
                    AttributeRegistry.MAX_MANA.get(), new AttributeModifier("Max Mana", 150, AttributeModifier.Operation.ADDITION),
                    TechAttributes.TECHNOMANCY_SPELL_POWER.get(), new AttributeModifier("Technomancy Power", 0.15, AttributeModifier.Operation.MULTIPLY_BASE),
                    AttributeRegistry.LIGHTNING_SPELL_POWER.get(), new AttributeModifier("Lightning Power", 0.10, AttributeModifier.Operation.MULTIPLY_BASE),
                    AttributeRegistry.SPELL_POWER.get(), new AttributeModifier("Base Power", 0.05, AttributeModifier.Operation.MULTIPLY_BASE),
                    AttributeRegistry.COOLDOWN_REDUCTION.get(), new AttributeModifier("Cooldown Reduction", 0.03, AttributeModifier.Operation.MULTIPLY_BASE)
            ), SchoolArmor.HEXTECH);

    private enum SchoolArmor {
        SCHOOL(3, 8, 6, 3), HEXTECH(4, 10, 7, 4);

        final EnumMap<ArmorItem.Type, Integer> values;

        SchoolArmor(int helmet, int chest, int legs, int boots) {
            values = new EnumMap<>(Map.of(ArmorItem.Type.HELMET, helmet, ArmorItem.Type.CHESTPLATE, chest, ArmorItem.Type.LEGGINGS, legs,
                    ArmorItem.Type.BOOTS, boots));
        }
    }

    private static final EnumMap<ArmorItem.Type, Integer> DURABILITY_PER_TYPE = new EnumMap<>(Map.of(
            ArmorItem.Type.BOOTS, 13,
            ArmorItem.Type.LEGGINGS, 15,
            ArmorItem.Type.CHESTPLATE, 16,
            ArmorItem.Type.HELMET, 11));

    private final String name;
    private final int durabilityMultiplier;
    private final int enchantmentValue;
    private final SoundEvent equipSound;
    private final float toughness;
    private final float knockbackResistance;
    private final LazyLoadedValue<Ingredient> repairIngredient;
    private final LazyLoadedValue<Map<Attribute, AttributeModifier>> additionalAttributes;
    private final SchoolArmor armor;

    TechArmorMaterials(String name, int durabilityMultiplier, int enchantmentValue, SoundEvent equipSound, float toughness, float knockbackResistance,
                       Supplier<Ingredient> repairIngredient, Supplier<Map<Attribute, AttributeModifier>> additionalAttributes, SchoolArmor armor) {
        this.armor = armor;
        this.name = name;
        this.durabilityMultiplier = durabilityMultiplier;
        this.enchantmentValue = enchantmentValue;
        this.equipSound = equipSound;
        this.toughness = toughness;
        this.knockbackResistance = knockbackResistance;
        this.repairIngredient = new LazyLoadedValue<>(repairIngredient);
        this.additionalAttributes = new LazyLoadedValue<>(additionalAttributes);
    }

    @Override
    public Map<Attribute, AttributeModifier> getAdditionalAttributes() {
        return additionalAttributes.get();
    }

    @Override
    public int getDurabilityForType(ArmorItem.Type type) {
        return DURABILITY_PER_TYPE.get(type) * durabilityMultiplier;
    }

    @Override
    public int getDefenseForType(ArmorItem.Type type) {
        return armor.values.get(type);
    }

    @Override
    public int getEnchantmentValue() {
        return enchantmentValue;
    }

    @Override
    public SoundEvent getEquipSound() {
        return equipSound;
    }

    @Override
    public Ingredient getRepairIngredient() {
        return repairIngredient.get();
    }

    @Override
    public String getName() {
        return name;
    }

    @Override
    public float getToughness() {
        return toughness;
    }

    @Override
    public float getKnockbackResistance() {
        return knockbackResistance;
    }
}
