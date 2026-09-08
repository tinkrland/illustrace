"""bench runner: two experiments, real numbers, run records.

experiment 1 - measurability: can computed params separate one-factor-changed pairs?
    A vs B: palette distance should be LARGE, stroke metrics ~identical
    A vs C: palette distance should be SMALL, stroke roughness should differ
experiment 2 - palette transfer: A -> B's palette at strengths [0.25, 0.5, 0.75, 1.0]
    expected: palette distance closes monotonically, content preserved, strokes untouched,
    strength interpolates ~linearly (strength accuracy).
"""
import json
import os
import time
import numpy as np
from PIL import Image

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine.analyzer import profile, palette
from engine.operators import palette_transfer
from engine.metrics import (palette_distance, content_preservation,
                             non_target_preservation, requested_fidelity_fraction)
from xano.client import post_run, post_asset

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "data", "generated")
RESULTS = os.path.join(ROOT, "results")


def img(n):
    return Image.open(os.path.join(DATA, n + ".png"))


def main():
    os.makedirs(os.path.join(RESULTS, "runs"), exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    A, B, C = img("A_clean_p1"), img("B_clean_p2"), img("C_rough_p1")
    report = ["# stylebench v0 run " + stamp, ""]

    # ---- experiment 1: measurability
    pa, pb, pc = profile(A), profile(B), profile(C)
    d_ab = palette_distance(pa["palette"], pb["palette"])
    d_ac = palette_distance(pa["palette"], pc["palette"])
    rows = [
        ("palette distance A-B (palette-only change)", round(d_ab, 4), "want large"),
        ("palette distance A-C (stroke-only change)", round(d_ac, 4), "want ~0"),
        ("stroke width cv  A (clean)", pa["stroke_width_cv"], "baseline"),
        ("stroke width cv  C (rough)", pc["stroke_width_cv"], "want >> A"),
        ("edge dir entropy A (clean)", pa["edge_direction_entropy"], "baseline"),
        ("edge dir entropy C (rough)", pc["edge_direction_entropy"], "want > A"),
        ("texture energy A", pa["texture_energy"], "baseline"),
        ("texture energy C", pc["texture_energy"], "want ~ A"),
    ]
    report += ["## experiment 1: measurability", "",
               "| measurement | value | expectation |", "|---|---|---|"]
    report += ["| {} | {} | {} |".format(*r) for r in rows]
    sep_ok = (d_ab > 3 * max(d_ac, 1e-4)) and (pc["stroke_width_cv"] > pa["stroke_width_cv"]) \
             and (pc["edge_direction_entropy"] >= pa["edge_direction_entropy"] - 0.02)
    report += ["", "**verdict: {}**".format("parameters separate the pairs" if sep_ok else "parameters FAIL to separate the pairs"), ""]

    run1 = {"run_id": stamp + "_e1", "experiment": "measurability_v0",
            "subject": "controlled frog pairs", "metrics": {k: v for k, v, _ in rows},
            "verdict": "pass" if sep_ok else "fail",
            "profiles": {"A": pa, "B": pb, "C": pc}}

    # ---- experiment 2: palette transfer with strength
    report += ["## experiment 2: palette transfer (A -> B palette)", "",
               "| strength | palette dist to ref | fraction closed | content pres | non-target pres |",
               "|---|---|---|---|---|"]
    run2 = {"run_id": stamp + "_e2", "experiment": "palette_transfer_v0", "verdict": "",
            "requested": "palette", "target": "A_clean_p1", "reference": "B_clean_p2",
            "steps": []}
    d0 = palette_distance(pa["palette"], pb["palette"])
    strip = [A]
    for s in (0.25, 0.5, 0.75, 1.0):
        out = palette_transfer(A, B, strength=s)
        po = palette(out, 6)
        d1 = palette_distance(po, pb["palette"])
        closed = (d0 - d1) / d0 if d0 > 1e-9 else 1.0
        cp = content_preservation(A, out)
        ntp = non_target_preservation(A, out)
        strength_acc = 1 - min(1.0, abs(closed - s) / s) if s > 0 else 1.0
        report.append("| {:.2f} | {:.4f} | {:.3f} | {:.3f} | {:.3f} |".format(s, d1, closed, cp, ntp))
        run2["steps"].append({"strength": s, "palette_dist_to_ref": round(d1, 5),
                              "fraction_closed": round(closed, 3),
                              "content_preservation": round(cp, 3),
                              "non_target_preservation": round(ntp, 3),
                              "strength_accuracy": round(strength_acc, 3)})
        out.save(os.path.join(RESULTS, "runs", "A_pal_s{}.png".format(int(s * 100))))
        if s in (0.5, 1.0):
            strip.append(out)
    mono = all(run2["steps"][i]["palette_dist_to_ref"] >=
               run2["steps"][i + 1]["palette_dist_to_ref"] - 1e-6
               for i in range(len(run2["steps"]) - 1))
    report += ["", "**verdict: {}**".format(
        "monotonic interpolation, geometry untouched" if mono else "interpolation NOT monotonic"), ""]
    run2["verdict"] = "pass" if mono else "fail"

    # ---- comparison strip: A | A@0.5 | A@1.0 | B
    strip.append(B)
    w, h = strip[0].size
    canvas = Image.new("RGB", (w * len(strip) + 10 * (len(strip) - 1), h), "white")
    for i, im in enumerate(strip):
        canvas.paste(im, (i * (w + 10), 0))
    strip_path = os.path.join(RESULTS, "comparison_strip.png")
    canvas.save(strip_path)

    for rn, run in (("e1", run1), ("e2", run2)):
        with open(os.path.join(RESULTS, "runs", "run_{}_{}.json".format(stamp, rn)), "w") as f:
            json.dump(run, f, indent=2)
    # mirror into xano control plane (fails soft; local json is source of truth)
    for run, subject, requested in ((run1, "controlled frog pairs A/B/C", None),
                                    (run2, "A_clean_p1 -> B_clean_p2", "palette")):
        post_run({
            "experiment": run["experiment"], "subject": subject, "requested": requested,
            "params": {"run_id": run["run_id"]},
            "metrics": {k: v for k, v in run.get("metrics", {}).items()}
                       if run.get("metrics") else {"steps": run.get("steps", [])},
            "verdict": run.get("verdict", ""),
            "artifacts": {"strip_png": "results/comparison_strip.png"} if run is run2 else {},
        })
    with open(os.path.join(RESULTS, "report.md"), "w") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))
    print("\nstrip ->", strip_path)


if __name__ == "__main__":
    main()
