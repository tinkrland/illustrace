# editable presets: the 3d thread

the parallel research thread to the 2d stylebench work: what "preset styles" means when the asset is a 3d model instead of an illustration. same thesis, different geometry. a style is not a baked render, it is a parametric program you can take apart, which is where the name of this whole thread came from.

## the data model sketch

from the original research pass, the hybrid three-layer shape:

- a **parametric program**: the actual editable geometry, nodes and sliders and joints, the thing you bend
- **preset layers** on top, usd-style: a preset is a named stack of parameter overrides + material + texture decisions. movable, reorderable, combinable, disposable. a style is one of these, never the geometry itself and never a render
- a **disposable glb**: the export is cache. if losing it hurts, the model was wrong

mvp shape: one preset family (a chair, a lamp, whatever has honest parameter space), sliders + joint drags, save-as-style, blender round-trip. one family is enough to prove a preset composes like a preset.

## reference points (kept here, not in the main readme)

| reference | why it's here |
|---|---|
| *nova3d* | where parametric preset styles could eventually go |
| *openscad* | programmatic geometry done right |

nothing here is an affiliation or a flagship relationship; they are reference points the thread thinks around, the same way the 2d thread keeps stylometry and metrology.

## status

parked behind the 2d work, deliberately. when the 2d metrology methodology stabilizes, the same pattern replays here: decompose the style of a model into factors, validate the measurements against human judgment, and only then build transfer operators. the 2d thread had to come first because its ground truth is cheap: a vector render beats a geometry bake for asking "did this factor move."
