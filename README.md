# engine v0: one paragraph

stylebench says a style is measurable. this repo makes that falsifiable instead of rhetorical:
a tiny analyzer that turns an image into numbers (palette, stroke width, stroke roughness,
texture energy), one deterministic operator (palette transfer with strength), and controlled
benchmark pairs where exactly one style factor changes. if the analyzer can tell the pairs
apart, track b (parameter discovery) is real. if the operator transfers one factor without
moving the others, "requested fidelity / non-target preservation" is a measurable engineering
target instead of vibes.

**read `research/STYLEBENCH_THESIS.md` first.** it's the formalized scope + roadmap (2026-09-08):
explicitly stylized/illustrated 2d+3d only (no human/realism/anatomy for now), a hierarchical
style representation (mark-making, shape, color, texture, rendering, edge language for 2d;
geometry/construction/surface/color/shading/rendering for 3d), and a reordered pipeline —
*validate candidate measurements against human judgment before building more transfer
operators*, not the other way around. everything below is what exists; the thesis doc is
what's next.

run:
    python3 benchmarks/make_stimuli.py     # generates controlled pairs into data/generated/
    python3 benchmarks/run_bench.py       # runs experiments, writes results/

layout:
    engine/analyzer.py       measurable style parameters
    engine/operators.py      deterministic style operators (v0.1: soft palette transfer)
    engine/metrics.py        benchmark numbers
    benchmarks/              controlled stimulus generation + bench runner
    research/                thesis, scope, roadmap docs
    data/references/         reference illustrations for the next (architecture) stimulus set
    xano/                    provisioning spec + client (mirrors every run to xano)
    results/                 run records (json) + report

the engine starts embarrassingly small on purpose. research decides what deserves to become
a learned operator later; nothing here is neural.
