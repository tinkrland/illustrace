"""build batch-2 survey stimuli from the preregistered spec.

reads survey/specs/batch_2.json, renders any missing images via the svg
substrate, validates every referenced image exists, and writes
survey/stimuli.json (v2) that the survey app loads.

usage:  python3 survey/build_batch.py [--dry-run]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
ARCH = os.path.join(ROOT, "data", "generated", "arch_svg")
sys.path.insert(0, ROOT)


def render_missing():
    """render spec-declared new images that don't exist yet."""
    spec = json.load(open(os.path.join(HERE, "specs", "batch_2.json")))
    from benchmarks.svg_house import BRUSHES, build_svg, render, derive_roles
    from benchmarks.svg_fidelity2 import REF_WARM, WARM

    rw = derive_roles(REF_WARM)
    made = []
    for img in spec.get("images_new", []):
        png = os.path.join(ARCH, img["file"] + ".png")
        if os.path.exists(png):
            print("exists:", img["file"])
            continue
        if img["file"] == "grain_11":
            svg = build_svg(derive_roles(), BRUSHES["clean"], textured=True, seed=7)
            render(svg, png, grain_amp=11.0)
        elif img["file"] == "b2_jit2":
            svg = build_svg(rw, dict(BRUSHES["clean"], width=7, taper=0.15, jitter=2.0), seed=7)
            render(svg, png)
        else:
            raise SystemExit("no recipe for declared image: " + img["file"])
        print("rendered:", img["file"])
        made.append(img["file"])
    return made


def validate(spec):
    missing = []
    for q in spec["questions"]:
        for side in ("left", "right"):
            if not os.path.exists(os.path.join(ARCH, q[side])):
                missing.append((q["id"], q[side]))
    for c in spec["catches"]:
        if not os.path.exists(os.path.join(ARCH, c["image"])):
            missing.append((c["id"], c["image"]))
    return missing


def emit_stimuli(spec):
    """write survey/stimuli.json (v2). catches are declared separately;
    the app places them at their fixed display positions."""
    out = {
        "version": 2,
        "batch": spec["batch"],
        "about": (
            "illustrace stylebench human-judgment validation, batch 2. "
            "preregistered spec: survey/specs/batch_2.json. ground truth comes "
            "from parametric svg stimuli: the gt side is the one with the "
            "provably higher parameter (or the spec-declared hypothesis). "
            "anchor question is a warm-up and is not scored. catch pairs are "
            "identical images: 'no difference' is the correct answer."
        ),
        "questions": [
            {
                "id": q["id"],
                "kind": q["kind"],
                "dimension": q["dimension"],
                "prompt": q["prompt"],
                "left": "../data/generated/arch_svg/" + q["left"],
                "right": "../data/generated/arch_svg/" + q["right"],
                "gt": q["gt"],
                "scored": q.get("scored", q["kind"] == "pair"),
                "note": q.get("note"),
            }
            for q in spec["questions"]
        ],
        "catches": [
            {"id": c["id"], "image": "../data/generated/arch_svg/" + c["image"],
             "position": c["position"], "prompt": c["prompt"],
             "dimension": c["dimension"]}
            for c in spec["catches"]
        ],
    }
    path = os.path.join(HERE, "stimuli.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    return path


def main():
    dry = "--dry-run" in sys.argv
    spec = json.load(open(os.path.join(HERE, "specs", "batch_2.json")))

    n_q = len(spec["questions"])
    n_c = len(spec["catches"])
    print(f"spec: {spec['batch']}  questions={n_q}  catches={n_c}  total={n_q + n_c}")
    assert n_q + n_c == spec["session_shape"]["total_questions"], "question budget mismatch"

    if not dry:
        render_missing()

    missing = validate(spec)
    if missing:
        for qid, f in missing:
            print("MISSING:", qid, f)
        raise SystemExit("spec references images that don't exist")
    print("all images present")

    positions = sorted(c["position"] for c in spec["catches"])
    assert positions == spec["session_shape"]["catch_positions_display_order"], "catch positions mismatch"

    if not dry:
        path = emit_stimuli(spec)
        print("wrote", path)


if __name__ == "__main__":
    main()
