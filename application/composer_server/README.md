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

each operator owns a wire color (palette green, stroke pink, texture
orange, edges cyan, value blue, color_zones yellow, shading purple — the
sidebar operator list doubles as the legend). only `ref` wires are colored
by their operator; `base`/`in` wires stay neutral grey, since the image
being made isn't a style factor. a source node that feeds one or more
`ref` ports grows a matching dot per connection — click a dot to open an
inline slider that's the same strength value as the operator node's own
slider (two views of one number, so you can dial a factor without hunting
down which op node it's wired to). a source node also carries its own
crit-tag: a free-text note ("just the linework, not the palette") scoped
to that specific reference image, saved into the recipe as `tag` — display
only for now, no operator reads it yet.

one deliberate omission: there's no "object/subject" reference type or
color here, even though it's an obvious fourth bucket alongside style
factors. subject/composition transfer stays a disabled-by-default bucket
in illustrace (surprise is a bug, and identity/subject transfer is the
part most likely to produce it) — so there's nothing honest to wire that
color to yet.

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
