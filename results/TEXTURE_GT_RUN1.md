# texture gt run 1: the metric rebuilt on vector ground truth

the rebuild prescription from anchor run 1: per-region statistics computed
directly from the substrate's known fill regions, never over a raster mask
whose size is scale-coupled. engine/texture_gt.py declares the fill
interiors in solo coordinates, maps them through the staging transform, and
reports per-region luminance sigma + gradient magnitude.

## fidelity (solo, grain amplitude)

| amp | sigma | grad |
|---|---|---|
| 0 | 1.94 | 0.72 |
| 8 | 4.85 | 7.11 |
| 14 | 7.16 | 11.87 |

monotone, near-linear in amplitude. the amp-0 baseline (1.94) is residual
aa edge energy, one tight inset away from zero.

## anchor laws (house regions, same renders as anchor run 1)

| condition | sigma | law | predicted |
|---|---|---|---|
| solo | 5.61 | — | — |
| set canvas-anchored | 5.21 | flat | ~5.61 |
| set subject-anchored | 3.22 | linear in s | 0.55 x 5.61 = 3.09 |

per-region the subject law is tight: wall_bottom 0.51x, wall_right 0.51x,
roof 0.54x of solo (wall_left and door still carry edge residue). the
anchor is a declared recipe property and each anchor's scale law predicts
the reading within ~4-7%. texture_energy is restored to validated, now as
a scale-invariant construction.

## the substrate bug the rebuild caught

the gt regions refused to read flat, and the forensics found a real bug:
**jitter_polyline was dropping every vertex except the last**, so each
corner of every stimulus got cut by a diagonal chord (the walls path drew
a 52px slash across the lower wall instead of its corner). every render
since the substrate commit had subtly clipped corners. fixed by keeping
the vertices; all runs rerun, all headline claims hold (normalized width
drift 1.6%, subject-anchored lighting exact at 133.6 vs 133.7). runs
granularity/anchor predate the fix; this record postdates it.

lesson: ground truth regions are not only a measurement tool — they audit
the substrate itself.
