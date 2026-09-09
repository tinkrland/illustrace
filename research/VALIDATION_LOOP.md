---
status: proposal (research-first, nothing built from it yet)
---

# the validation loop (deeper, not broader)

inspiration taken as reference points only (same standing as nova3d and
openscad): adaptionlabs' **invent a dataset** changes dataset creation from
collection to specification, and **autoscietist** closes the research loop
(set outcome, co-optimize data and recipe until convergence). both map
cleanly onto what illustrace already half does, and each one goes deeper
into the validation and testing scope, not wider.

## 1. specification-first validation datasets

today: stimuli are code, the survey app serves pairs, and the connection
between "what a batch intends to prove" and "what got run" lives in
commit messages.

deeper: every validation batch is declared as an **experiment spec** that
generates both the stimuli and the pass criteria from the same document:

```json
{
  "factor": "texture_energy",
  "claim": "metric deltas track what humans call rougher texture",
  "pairs": [{"a": {"grain_amp": 0.0}, "b": {"grain_amp": 14.0},
             "seed": 7, "subject": "house_solo"}],
  "n_per_pair": 12,
  "pass": {"agreement_min": 0.70, "ci95_width_max": 0.20},
  "registry_consequence": {"on_pass": "validated -> controllable_track",
                            "on_fail": "demote with evidence"}
}
```

no batch exists that wasn't preregistered. survey, metrics, and registry
verdicts all read the same spec file.

## 2. closed-loop metric vs human co-optimization

the autoscietist move, shrunk to bench scale:

- **outcome**: metric agreement, the rank correlation between metric
  deltas and human forced-choice frequencies
- **loop**: survey batch -> agreement stats -> verdict per metric
  (keep / adjust / demote) -> regenerate stimuli -> repeat
- **convergence**: two consecutive batches with agreement within each
  other's confidence intervals, at the preregistered minimum n. the loop
  stops when the metric's agreement plateaus, and the plateau value is
  the honest ceiling of that metric.

the judge stays human judgment. the glm scientist session preregisters;
the loop only executes.

## 3. adaptive stimulus difficulty

the loop's data-side half, and the part that keeps validation honest:

- pairs humans split 50/50 are **stimulus failures**, not human noise:
  regenerate at higher contrast, log the failure as stimulus-quality data
- pairs humans agree on but the metric misses are **metric failures**:
  registry demotion with evidence, the same honesty ladder as texture_energy
- discriminating pairs where humans agree AND the metric tracks: the only
  pairs that count toward a validated -> controllable promotion

## scope discipline

this adds no new style dimensions, no operators, no breadth. everything
lands inside the existing validation thread: the survey app, the stimuli
substrate, the registry. the loop automates the boring part (batch
generation, stats, verdict application), never the judgment.

## implementation order

- experiment spec schema + a spec-to-stimuli generator binding (the
  survey app consumes specs, not ad-hoc pairs)
- agreement stats module: per-pair discrimination, rank correlation,
  bootstrap CIs
- first closed-loop batch on the two internally-validated metrics that
  humans can actually judge blind: texture_energy (rough vs clean) and
  stroke width (thin vs thick)
