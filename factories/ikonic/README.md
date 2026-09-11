# ikonic (icon kit factory)

the icon kit factory. not "an icon," an icon *kit*: a full vocabulary of icons in one consistent style, the way a brand system does it. the consistency is the product. anyone can draw one icon; keeping forty icons on the same grid, stroke weight, corner language, and palette is the actual work, and it's exactly the kind of thing that should be enforced by a system rather than by eyeballing.

## what it makes

- icon sets in a shared style recipe: a semantic vocabulary (arrows, media, commerce, weather, whatever) stamped from one kit definition
- each icon an editable preset: layered vector, per-icon overrides allowed but kit invariants flagged
- kit-level restyling: change the recipe once, every icon in the kit follows

## the kit recipe (sketch)

a kit definition is itself an editable preset: grid size and keyline shapes, stroke weight and caps, corner radius language, shape simplification level, fill vs outline vs duotone mode, palette and color zones, texture layers. individual icons are instances of that recipe, so kit-wide restyle is one edit, and the system can measure drift when someone's per-icon override breaks the style.

## why this is very illustrace

consistency is a measurable invariant, which makes this the most stylebench-shaped factory: "these 40 icons share a style" is a claim the existing factor metrics can actually test (stroke width cv, edge language, palette). a kit factory is a style decomposition with a particularly crisp contract.

## studio role

icon kits are the brand-kit half of the studio: kit plus typeface plus mark equals a starter identity, all editable.

## status

parked. readme only, no build.
