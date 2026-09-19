# micro-lora probes: colab before the a100

why train 10-20 image corpora on a free colab gpu when a $100 a100
budget exists? because the micro-run is not about the adapter, it is
about the pipeline. the first a100 session should be a known-good
rerun, not a first debug session.

## the regime is right, the sample is the question

the llm steering plan already assumes micro-datasets (6-10 references)
for zero-shot conditioning. style loras behave the same way: community
range for a coherent style is 10-30 images. so a 10-20 image corpus
trains a real (small) adapter and exercises every stage: packaging,
captions, kohya config, adapter save, probe scoring, promotion rules.

## what to train on

the reference pool is 24 images, and per the redundancy matrix they are
24 *different* styles: one image each, no exploitable family except
ref_20-23 (ink + watercolor storefronts, one hand, pairwise similarity
0.34-0.62 while everything else sits near zero). so "10-20 refs" means
one thing: the storefront family plus more images from the same series,
which liat has (they arrived as whatsapp images; there are more where
those came from).

alternatives considered:

- **the painter corpora** (monet et al): 39-60 images each, ready to
  go, but they are fine-art scans with provenance confounds and they
  are *not* the target domain. liat's call was right: stylized
  illustration is.
- **the parametric substrate**: unlimited in-domain samples with known
  ground-truth parameters, zero licensing questions. the catch is that
  training flux on svg renders teaches substrate-style, which is fine
  for pipeline validation but says nothing about reference-style
  fidelity. keep it in reserve for the fitter lane, where it belongs.

## the living-artist line

the storefront refs are a named (signed) contemporary illustrator's
work. the standing rule from the stylebench side applies doubled here:
these images and any adapter trained on them are internal research
probes, never published. adapters and probe outputs stay uncommitted
(adapters/ is gitignored); the repo ships the method, not the
imitation. public-domain painters remain the demo lane; the storefront
probe stays in the workspace.

## feasibility (colab)

- free tier: t4 16gb. flux.1-dev trains with kohya `--fp8_base` +
  `--mixed_precision fp16` (t4 has no bf16) + cached latents, ~10-20
  s/step. 15 images x repeats 3 x 10 epochs = 450 steps = a 1.5-2.5 hr
  session. fits inside a free session with checkpoints saved to drive
  every 2 epochs in case colab kills it.
- colab pro: l4 22gb (same session shape, ~2x faster) or the a100 40gb.
  nice, not required for this probe.
- weights: flux.1-dev is license-gated on hf; needs a token from an
  account that accepted the license (liat's). ~12gb download on
  colab's network is minutes.

## what success looks like

the probe (engine/adapter_probe.py, cie76 deltae in lab space) scores
the micro-adapter's generations against the storefront family profile:
fidelity within dE < 10 on palette (with the measurement-noise caveat
from the packaging spec), unclaimed components no higher than the
untrained-flux floor + 1sd. if the whole chain passes on a t4, the a100
session for the painter library becomes a config change, not a
debugging project.
