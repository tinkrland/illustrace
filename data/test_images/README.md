# test images

the reference illustrations liat sent (2026-09-08), kept as-is and used as
test/style targets throughout the benchmark. provenance and roles:

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

stimuli derived from these live in `data/generated/` (fidelity sweeps,
granularity/anchor pairs, texture gt renders). nothing in this folder is
ever modified: reads only, they are the ground-truth references.
