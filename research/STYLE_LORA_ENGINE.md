---
title: style lora engine
summary: the training engine, the inspo contract (what gets taken from each reference), composition rules, and the demo corpus plan (monet + sent styles)
---

# style lora engine

status: architecture defined 2026-09-10; training blocked on amd access,
everything upstream of the gpu (ingestion, probing, queue, ui) is buildable now.

---

## what this engine is

a robust pipeline that turns inspiration images into **composable style
adapters** with a node-based ui for assigning them. it is not a "clone my
style" generator: each trained lora is an *inspiration source in the
library*, and the node ui composes several (monet for color, a sent ref for
stroke, another for texture) with per-assignment strength sliders. a
preset is the saved adapter-weight recipe, not a rendered image.

two layers, same thesis as the editable brush engine:

1. **recipe layer (deterministic, today):** measurable components —
   palette, stroke width/cv, hatching axis, texture energy, edge entropy —
   are *extracted*, not learned. `engine/inspo_profile.py` already does this.
2. **adapter layer (learned, gpu):** components that resist
   parameterization — wash rendering, brush feel, light treatment — get a
   lora trained per inspiration corpus. the adapter's *contract* is still
   bounded by probe deltas: what it changes and what it leaves alone is
   measured, not vibes.

## the inspo contract: what "take" means per component

this is the answer to "how do we define what to take from each inspo
image?" — each assignment in the node ui is a triple:

**(component, extraction, strength)**

- the **component** is one of the ontology buckets (palette / stroke /
  texture / edges / shading / rendering).
- the **extraction** is the measured parameters (recipe components) or the
  trained adapter + its probe profile (hard components).
- the **strength** is the slider: for recipe components it interpolates the
  measured parameters toward the target; for adapters it is the
  `adapter_weight` at inference.

every inspo image that enters the library gets profiled first
(`engine/inspo_profile.py`, output `data/generated/inspo/profiles.json`):

| component | measured today | take |
|---|---|---|
| palette | dominant-k hex + value range | exact colors + weights |
| stroke | width mean/cv, axis + concentration | width profile, wobble, hatching angle |
| texture | texture_energy | grain recipe target |
| edges | direction entropy | orientation histogram |
| shape | perim/area, boundary entropy, ink coverage | contour density proxies |

the same profile doubles as the **probe spec for adapters**: after training,
we re-measure the adapter's outputs against the source profile. an adapter
that claims "monet palette" but shifts stroke entropy wildly is caught by
the probe, not by eyeballing. this is stylebench applied to our own
adapters.

## probe results on the sent styles (2026-09-10)

all 24 sent refs profiled. immediate findings:

- **four exact duplicate pairs** in the sent set: 03≡18, 04≡17, 05≡15,
  08≡19 (identical stats). the library should dedupe on ingest — duplicates
  silently double an inspo's weight.
- stroke width ranges 2.0–20.3px with cv 0.0–2.20: the sent set spans thin
  uniform technical linework to thick wobbling marker strokes — genuinely
  wide coverage for stroke-node assignments.
- texture energy 13–43 separates flat-color refs (13–16) from grungy ones
  (34–43): good axis for texture assignments.
- the redundancy matrix (in profiles.json) tells the node ui when two inspos
  buy nothing over one (near-identical vectors) — that's the "assign
  differently" guardrail.

## the training stack (research pass, mi300x)

recommended path for the amd box (when access lands):

- **trainer:** kohya-ss/sd-scripts (or diffusers' official lora scripts)
  inside amd's `rocm/pytorch` docker (rocm 6.3+). pytorch native sdpa, no
  xformers/flash-attn compile needed. bitsandbytes 0.44+ has native rocm.
- **base model:** flux.1 [dev] — higher style fidelity per gpu-hour on
  mi300x (192gb hbm allows batch 16–32 in bf16). non-commercial research
  license is fine for the demo; commercial would need a license swap.
- **cost per style lora (one mi300x):** 15–30 min, ~$0.50–1.50 for flux;
  sdxl 5–15 min, ~$0.20–0.50. cheap enough to train a whole library.

### composition primitive (what makes the node ui real)

diffusers `set_adapters` + `adapter_weights` — weights update in memory,
sub-millisecond, so sliders are live. known limit: **adapter interference**
grows past 2–3 simultaneous style loras (weight bleeding, over-saturation).
house rules: keep individual weights in 0.3–0.7, sum of active weights near
1.0–1.2, and prefer spatial/attention masking nodes over raw stacking.
this is exactly the kind of claim stylebench should preregister as a
separability batch once we can generate with adapters: *do palette
adapters actually stay palette-scoped at 0.7 + 0.5 stacking?*

## how many inspo images it takes

- **recipe-layer inspos:** one image is enough — extraction is
  deterministic. more images just stabilize the k-means palette and stroke
  stats (3–5 images is plenty for a stable average).
- **adapter-layer inspos:** the 2026-era guidance for a *consistent* style
  lora is ~20–50 curated images at 1024px (1–2k steps). a painter corpus
  (monet's late period) easily supplies 50+. consistency matters more than
  count: style-pure curation beats volume (see the ingestion notes once the
  corpus research lands — sources: met open access, art institute of
  chicago, wikimedia commons).
- **hybrid:** an inspo can enter the library with one image (recipe
  components live immediately) and get its adapter trained later when
  enough corpus accumulates. the node assignment doesn't change — only the
  extraction layer under it upgrades.

## pipeline shape

```
ingest (dedupe, curate, caption)      <- painter corpus + sent styles
  -> profile (engine/inspo_profile.py, always, pre-training)
  -> dataset prep (resize 1024, style-pure filter)
  -> train (xano training_jobs, job_type lora; kohya on mi300x)
  -> adapter registry (adapter + probe profile side by side)
  -> node composer (image nodes -> component nodes with sliders -> preset)
  -> preset library (saved adapter-weight recipes, figma-style)
```

xano queue: `training_jobs` (table 33) already takes job_type="lora". the
amd runner pulls jobs, trains from the dataset path, posts metrics +
adapter uri back.

## demo plan (first library)

1. monet (late period, public domain, style-pure) — palette + wash
   rendering adapter.
2. the sent styles — the 20 deduped refs become library inspos; the ones
   with distinctive stroke (05/15, 12) and texture (20–24) are the first
   adapter candidates.
3. 2–3 more painters for breadth (van gogh, hokusai) once ingestion is
   proven on monet.

status update (2026-09-10): ingestion is live. `engine/ingest_monet.py`
pulled 39 late-period monet works (1890-1923, wikidata Q296 -> commons,
1024px, public domain, metadata in `data/monet/metadata.json`) — inside
the 20-50 guidance band. all 39 are profiled and merged into the composer
library (`data/generated/inspo/monet_profiles.json`), so monet is already
assignable to components with gravity + strength, pre-training.

next: adapter probe harness (profile-before, profile-after, delta report)
before the first lora trains, so the demo comes with numbers attached;
dataset packaging for kohya (resize/crop policy, captioning strategy) when
the amd box arrives.
