# test images

the reference illustrations liat sent, kept as-is and used as test/style
targets throughout the benchmark. provenance and roles:

| file | upload | used as |
|---|---|---|
| ref_01.webp | 7424a5fd6_*.webp | warm palette target (REF_WARM, stimuli set) |
| ref_02.png | 3abaa1d1a_image.png | cool palette target (REF_COOL, stimuli set) |
| ref_03.png | c9a280efb_image.png | style target (texture/stroke studies) |
| ref_04.png | 0ef3af796_image.png | style target (texture/stroke studies) |
| ref_05.png | db2f8e3c0_image.png | style target (texture/stroke studies) |
| ref_06.png | 4fbdbc3fc_image.png | style target (texture/stroke studies) |
| ref_07.png | f39cbd5e9_image.png | style target (texture/stroke studies) |
| ref_08.png | 15905e3da_image.png | style target (texture/stroke studies) |
| ref_09.jpeg | 771a06008_WhatsAppImage...12817.jpeg | style target: soft airbrush/digital painting, muted cloudy palette, ivy-covered cottage, front view |
| ref_10.jpeg | 54add2a7c_WhatsAppImage...12827.jpeg | style target: flat gouache/vector, saturated folk-art palette, decorative pattern fills, night village front view |
| ref_11.jpeg | 21d1186b8_WhatsAppImage...12825.jpeg | style target: loose painterly gouache, limited flat-wash palette, parisian park (non-house subject, kept for mark-making/color) |
| ref_12.jpeg | 78af0a899_WhatsAppImage...12813.jpeg | style target: naturalistic digital painting, dappled light, detailed garden path (non-house subject) |
| ref_13.jpeg | a81476efa_WhatsAppImage...12807.jpeg | style target: mixed-media/textured (heavy impasto brushwork), high-contrast coastal cottage, front view |
| ref_14.jpg | 988b4f0f0_WhatsAppImage...12805.jpg | style target: flat pastel digital illustration, children's-book decorative linework, cottage front view |
| ref_15.png | e90c7acac_image.png | style target: dark storybook/whimsical digital painting, moody teal-green palette, decorative flat vine motif overlay |
| ref_16.png | 44ffc1ba1_image.png | style target: storybook flat-vector/gouache hybrid, heavy grain texture, whimsical proportions (signed illustration) |
| ref_17.png | d8f3431b6_image.png | style target: painterly gouache, dense brick pattern texture, amsterdam row houses (signed illustration) |
| ref_18.png | 3593360d1_image.png | style target: storybook/children's-book, exaggerated curved architecture, muted lavender palette, cream ground |
| ref_19.png | 175016f46_image.png | style target: flat vector poster illustration, saturated palette, gothic architecture |
| ref_20.png | 542b4beed_image.png | style target: loose ink + light watercolor wash, urban sketch, minimal flat color blocks |
| ref_21.png | f53a5eedf_image.png | style target: watercolor + ink line, traditional urban-sketch storefront |
| ref_22.png | d15264beb_image.png | style target: watercolor + ink line, urban-sketch storefront |
| ref_23.png | 1b6ebf146_image.png | style target: watercolor + ink line, urban-sketch storefront, denser color |
| ref_24.png | 4446cc627_image.png | style target: watercolor wash + expressive scribble ink trees, loose park sketch |

## ref_15-24 batch (2026-09-09): storybook/whimsical + watercolor styles

same front-view, style-first framing as ref_09-14. this batch adds two new
style families to the reference set: storybook/whimsical digital painting
(ref_15, 16, 18 — exaggerated proportions, decorative motifs, heavier grain)
and watercolor + ink urban sketching (ref_20-24 — traditional media, loose
linework, wash-based color). ref_17 and ref_19 round out painterly-detailed
and flat-vector-poster respectively. all kept front-view for the same reason:
isolate style from spatial construction (see the 2d-depth vs 3d-positioning
split noted in `research/STYLE_ONTOLOGY.md`, bucket 02).

## ref_09-14 batch (2026-09-09): front-view-only, style-first

liat's framing: these are given intentionally from a **front view**, same as
the earlier batch, so the benchmark isolates *style* (mark-making, color,
texture, rendering, edges) without also having to solve spatial construction,
placement, or perspective at the same time. that harder problem — scaling, positioning multiple objects/subjects
correctly, perspective-consistent placement — is dimension **02 spatial
construction** in `research/STYLE_ONTOLOGY.md` (already scoped out of the
default transfer, `content/composition preserved by default`). it's deferred
here on purpose and will likely need its own adaptionlabs research pass later,
separate from the current mark-making/color/texture/rendering work these refs
are for. ref_09-14 are for the *style* half of the ontology only.

stimuli derived from these live in `data/generated/` (fidelity sweeps,
granularity/anchor pairs, texture gt renders). nothing in this folder is
ever modified: reads only, they are the ground-truth references.
