# analogistry (print process factory)

the analog-process factory. it takes an asset and subjects it to a simulated physical print process: lino/woodcut (linostamped), emboss and deboss, cyanotype, letterpress, risograph, screenprint, foil. these processes are loved precisely because of their imperfection, ink bleed, misregistration, paper texture, pressure artifacts, but "loved imperfection" is still a parameter space, and a surprisingly measurable one.

## what it makes

- process treatments as recipe-layer stacks over any editable asset: the source stays live underneath, the process is a layer
- per-process physics as parameters: ink bleed radius, registration offset, impression depth (emboss/deboss), exposure and wash (cyanotype), halftone or misregistration behavior (riso/letterpress)
- paper stock as a base layer: grain, tooth, absorbency, deckled edges, honest to real paper behavior

## the recipe-layer contract

an embossed blob is a blob with an emboss recipe layer, not a baked emboss png. swap the blob, keep the emboss. stack cyanotype under grain under a deboss, reorder layers, dial strengths. same composition model as the style composer, applied to process instead of style factors.

## why this is measurable

ink bleed and misregistration have real spatial statistics; a lino cut has a specific edge roughness signature. each process treatment is a claim about a measurable factor transform, which keeps this factory honest and testable rather than being an instagram filter with a fancy name.

## studio role

a finisher, like weaverly: the studio's compositions leave through analogistry when the destination is print-flavored branding, packaging, stationery.

## status

parked. readme only, no build.
