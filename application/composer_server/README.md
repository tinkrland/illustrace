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

## the canvas

flat, not chained: every inspo image wires straight to the **generation
node** in the middle. the canvas is informally divided into labeled
sections — subject, palette, stroke, texture, edges, value, color
zones, shading — and dropping an image into a section is how you say
what it contributes ("take the palette from this corner"). sections are
informal by design: passing a node through a section re-assigns it live,
but any image can be overridden per-image from its menu.

- **subject** — the image being made. one image, the base of the chain.
- **factor sections** — one inspo image per contribution, each with its
  own strength and crit tag.
- **generation** — the preset hub; every wire ends here. it renders the
  deterministic factor chain derived from the sections (subject as base,
  then one operator per image in a fixed order: palette, value,
  color_zones, shading, texture, stroke, edges), so the same arrangement
  of sections renders the same pixels every time.

interactions: drag an image from the library into a section; drag a node
between sections to re-assign it; **right-click any image** for its menu —
which section it feeds, its strength, its crit tag (a free-text note
scoped to that image, saved into the recipe), or remove it. clicking a
wire opens the same menu. `generate` renders the graph; `save preset`
writes the recipe json plus renders to `results/composer/`.

**the sections vs the old op-chain:** the op-chain view (explicit
operator nodes wired base→ref) still exists in the executor — the section
canvas compiles to it at run time. the ui is what the user thinks in
("this corner is my palette inspo"), the executor is what actually runs.

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
