---
title: node-canvas ui for reference assignment (oss candidates)
summary: the multi-reference assignment workflow is a graph, so the ui should be a node canvas — verified oss candidates, licenses, and how they map to the recipe model
status: research pass complete (2026-09-10, github api verified)
---

the canonical request is already a graph:

```
[image 1..5 refs] ──> style component (strength)
[image 2 refs]     ──> palette component (ignore drawing style)
[image 3 refs]     ──> shading component
[image 4..5 views] ──> content component (what to draw)
        all         ──> composite recipe ──> preset (saved, reusable)
```

liat's clarification (2026-09-10): slots aren't single-image. five images can
feed the style/shading slot, two images can describe the object to replicate
(multiple views / front + back). fan-in per component, fan-out per image, a
content slot that carries no style. a form with dropdowns cannot express
that honestly; a node canvas is the native shape.

## candidates (github api, verified 2026-09-10)

| repo | stars | license | last push | stack | read |
|---|---|---|---|---|---|
| xyflow/xyflow (react flow) | 38.3k | MIT | active (sep 2026) | react | the default. ui-only node/edge canvas; graph semantics are ours to define. battle-tested (langflow, flowise lineage of apps) |
| retejs/rete | 12.2k | MIT | active (jul 2026) | core + react/vue/angular render plugins | the interesting one: ships an actual dataflow engine, so the graph can *compute* (recipe merge as graph evaluation) |
| bcakmakoglu/vue-flow | 6.8k | MIT | active (jul 2026) | vue | react flow's vue sibling; pick only if the app is vue |
| jerosoler/Drawflow | 6.1k | MIT | stale (oct 2024) | vanilla js | dead simple, tiny, comfy-flavored; fine for prototypes, risky as a long-term base |
| jagenjo/litegraph.js | 8.1k | MIT | stale (aug 2024) | vanilla canvas | the comfyui original: widgets-in-nodes (sliders live on the node), but aging api |
| Comfy-Org/litegraph.js | 253 | MIT | active (jan 2026) | canvas | comfy's fork — maintained but comfy-specific; extraction cost not worth it |
| baklava.js | — | — | **gone** (repo 404) | vue | excluded: project vanished |

all MIT, so repurposing is unproblematic.

## fit against our criteria

what the canvas must do that generic node editors don't out of the box:

1. **image nodes with role tags** — a thumbnail port whose only semantic is
   "i contribute X to component Y". no node in the oss list does this natively;
   it's a custom node type in any of them.
2. **strength slider on the node** — litegraph does widgets-in-nodes
   natively; react flow needs a custom node with an html slider (trivial);
   rete has control widgets via plugins.
3. **fan-in merge semantics** — the real research question, not a ui
   question: when five references feed the style slot, what is the merged
   recipe? mean of measured factors? per-ref weights? per-zone attribution
   (ref a owns hatching, ref b owns edge weight)? this is a stylebench
   experiment (combinability was already a preregistered claim), the node ui
   just exposes whatever we validate.
4. **preset save = graph serialization** — presets already store recipes
   (components, strengths, assigned references, extraction settings); the
   graph *is* the preset. export/import is graph json, same as the .swatches /
   qr-shortcode precedents (see BRUSH_CATALOGS.md).

## verdict

react flow (xyflow) as the base: most active, MIT, ui-only keeps execution
deterministic and in our bake (nodes produce recipe json; nothing "runs" on
the canvas). rete.js is the runner-up if we later want the graph itself to
evaluate recipe merges — its dataflow engine fits the merge-semantics
research above, but that's a later decision, not a ui one.

prototype scope when it happens: three node types (image, component,
preset), one demo graph reproducing the canonical four-image example, recipe
json export identical to what the substrate already consumes. no execution
on the canvas, ever — the bake stays a deterministic build step.
