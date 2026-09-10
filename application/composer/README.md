# composer

the node-based inspiration composer. two switchable views over the same state:

- **canvas** — inspiration nodes (with their measured probe profiles) wire
  into style components (palette / stroke / texture / edges / contour).
  each wire carries a strength slider: how much you take from that inspo
  for that component.
- **gravity** — a drag-to-reorder hierarchy of every assigned inspo.
  gravity is independent of strength: the top-ranked inspo wins a
  component's direction even at a lower percentage, and lower ranks blend
  in with decay (0.65 per rank step). strength is magnitude, gravity is
  who wins conflicts.

presets save the assignment set + gravity order (the recipe, not a render).
`queue (xano)` posts the preset json to the control plane's presets
endpoint.

## run it

no build needed — the profiles are baked in at generation time:

    python3 engine/inspo_profile.py              # refresh probe data
    python3 application/composer/build_composer.py
    open application/composer/index.html         # file:// works

images load from `data/test_images/` and `data/<painter>/` (monet,
van_gogh, hokusai — routed by filename prefix), so the repo folder must
stay intact. the library is 101 deduped inspos; refresh with
`engine/ingest_painter.py` for any wikidata painter.
