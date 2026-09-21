# composer server

the node graph that *executes*: an infinite-canvas ui (pan with the empty
space, zoom with the wheel) where inspo sources, the 7 transfer operators,
and previews wire into a runnable graph. run renders actual assets through
the real operators; save writes the recipe (the graph json) plus its
renders to `results/composer/`. this is the execution counterpart to the
static profile view in [../composer](../composer) — same preset principle
(a preset stores the recipe, not a render), now with pixels.

## run

no dependencies beyond the repo's (stdlib server, the operators as-is):

    python3 application/composer_server/server.py
    # http://localhost:8642  (COMPOSER_PORT to change)

## the graph

- **source** — an inspo image (library in the sidebar: subjects + the
  painter corpora). the whole point of multiple sources: one is the base,
  others are per-factor references.
- **op** — one of the 7 operators (palette, stroke, texture, edges, value,
  color_zones, shading). two inputs: `base` (the image being made) and
  `ref` (the image the factor is taken from). a strength slider per node.
- **preview** — shows the rendered result of whatever is wired into it.

wires: drag from an output dot to an input dot; click a wire to delete it;
click an input to unplug it. one input port accepts one wire (a factor has
one reference — that constraint is the design).

## endpoints

| route | what |
|-------|------|
| `GET /` | the canvas page |
| `GET /api/inspos` | the inspo library (paths + painter) |
| `GET /api/thumb?path=…` | an image under `data/` (path-guarded) |
| `POST /api/run` | `{graph}` → `{images: {preview_id: data_url}, errors}` |
| `POST /api/save` | `{name, graph}` → recipe json + renders in `results/composer/` |

## determinism

execution is deterministic: seedful operators run at fixed seed, so the
same recipe renders the same pixels every run. saving a preset means saving
the graph — renders are reproducible from it, and diffs between two presets
are attributable to their recipe diff, not sampler mood.
