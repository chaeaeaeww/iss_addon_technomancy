# Art Style Preset: "Premium Fantasy"

Default for every Minecraft texture / model made for this user from 2026-10-18 on. Learned by studying T.O Magic 'n
Extras, Hazen 'n Stuff and Create item art (style only: their assets are All Rights Reserved, never copy pixels or
model files). Implemented in `tools/premium.py`.

## Format
- Item icons: **32x32** (user's choice). Empty smithing-slot icons may stay 16x16 (vanilla style).
- GeckoLib models: per-face UV, texture density 2 px per model px where the texture budget allows; glowmask for every
  emissive part.
- Weapons/staffs lie on the diagonal bottom-left -> top-right and use the whole slot; armor icons fill the slot.

## Colour
- Hue-shifted ramps of 6-8 steps per material: shadows go darker AND cooler (toward blue/purple), highlights lighter
  AND warmer (toward yellow/white). Never darken by mixing with black.
- Strong value contrast: the darkest ramp step is near-black of the material's hue; one or two near-white specular
  pixels per material, top-left.
- Glow accents: fully saturated 1-px lines and gems (cyan/violet for Hextech, amber/orange/wine for Clockwork),
  with a 1-px darker-saturated rim so they "burn" against the dark outline.
- Ordered (Bayer) dithering only on large gradients (cloth, plates), never on small parts.

## Shading ("fake 3D")
- Every shape is bevelled: height from the distance to its edge, normal from that height, lit by a key light from the
  top-left, a weak cool rim light from the bottom-right and ambient occlusion in creases (where shapes overlap).
- Specular pixel on convex highlights; inner contour lines between materials one step darker than the darker side.

## Line
- Outline every silhouette with a *coloured* dark line (the material's darkest step), not pure black; the outline is
  lighter (selective outline) where the light hits on the top-left edge of large shapes.
- Spikes, horns, filigree and blade tips taper to 1-px points; ornate edges (crenellations, teeth, fins).

## Magic
- "Magical particles": 1-px and plus-shaped sparkles in the glow colour around glowing parts (2-6 per icon), a few
  floating rune glyphs (3x3/3x5 patterns) on big flat areas.
- Runes / engraved circuitry on plates and pages in the glow colour.

## Tiers in this mod
- Clockwork (tier 1): brass, copper, walnut, leather, cream parchment, andesite; glow = warm amber / furnace orange /
  wine red. Must NOT look hextech.
- Hextech (dragon-core tier): navy plate, brass trim, cyan crystal + violet energy glow, runes.
