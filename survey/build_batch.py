"""build batch survey stimuli from a preregistered spec.

usage:  python3 survey/build_batch.py batch_2|batch_3|batch_4 [--dry-run]

reads survey/specs/<batch>.json, renders any missing images (params-driven:
brush params go through build_svg on the warm-reference roles, grain_amp goes
through the textured clean render), validates every referenced image exists,
and writes survey/stimuli_<batch>.json plus survey/stimuli.json (the served
app fetches the latter; the copy made is whatever batch was last built).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
ARCH = os.path.join(ROOT, "data", "generated", "arch_svg")
sys.path.insert(0, ROOT)

BRUSH_KEYS = {"width", "taper", "jitter", "taper_dir", "opacity", "jitter_lat"}


def image_dir(spec):
    """arch_svg by default; specs may declare a stimuli_source dir.
    stimuli_source is often prose, so pull the first data/... path token."""
    import re
    m = re.search(r"(data/[\w/]+)", spec.get("stimuli_source", ""))
    if m:
        return os.path.join(ROOT, m.group(1).rstrip("/"))
    return ARCH


def render_missing(spec, imgdir):
    """render spec-declared new images that don't exist yet."""
    from benchmarks.svg_house import BRUSHES, build_svg, render, derive_roles
    from benchmarks.svg_fidelity2 import REF_WARM

    rw = derive_roles(REF_WARM)
    made = []
    for img in spec.get("images_new", []):
        png = os.path.join(imgdir, img["file"] + ".png")
        if os.path.exists(png):
            continue
        params = img.get("params", {})
        if "grain_amp" in params:
            svg = build_svg(derive_roles(), BRUSHES["clean"], textured=True, seed=7)
            render(svg, png, grain_amp=float(params["grain_amp"]))
        elif params and set(params) <= BRUSH_KEYS:
            brush = dict(BRUSHES["clean"], **params)
            svg = build_svg(rw, brush, seed=7)
            render(svg, png)
        else:
            raise SystemExit("no recipe for declared image %r (params %r)"
                             % (img["file"], sorted(params)))
        print("rendered:", img["file"])
        made.append(img["file"])
    return made


def validate(spec, imgdir):
    missing = []
    for q in spec["questions"]:
        for side in ("left", "right"):
            if not os.path.exists(os.path.join(imgdir, q[side])):
                missing.append((q["id"], q[side]))
    for c in spec["catches"]:
        if not os.path.exists(os.path.join(imgdir, c["image"])):
            missing.append((c["id"], c["image"]))
    return missing


def emit_stimuli(spec, imgdir):
    """write survey/stimuli_<batch>.json + stimuli.json. catches are declared
    separately; the app places them at their fixed display positions."""
    batch = spec["batch"]
    out = {
        "version": spec["version"],
        "batch": batch,
        "about": (
            "illustrace stylebench human-judgment validation, %s. "
            "preregistered spec: survey/specs/%s.json. ground truth comes "
            "from parametric svg stimuli: the gt side is the one with the "
            "provably higher parameter (or the spec-declared hypothesis). "
            "anchor question is a warm-up and is not scored. catch pairs are "
            "identical images: 'no difference' is the correct answer."
            % (batch, batch)
        ),
        "questions": [
            {
                "id": q["id"],
                "kind": q["kind"],
                "dimension": q["dimension"],
                "prompt": q["prompt"],
                "left": "../" + os.path.relpath(os.path.join(imgdir, q["left"]), ROOT),
                "right": "../" + os.path.relpath(os.path.join(imgdir, q["right"]), ROOT),
                "gt": q["gt"],
                "scored": q.get("scored", q["kind"] == "pair"),
                "note": q.get("note"),
            }
            for q in spec["questions"]
        ],
        "catches": [
            {"id": c["id"], "image": "../" + os.path.relpath(os.path.join(imgdir, c["image"]), ROOT),
             "position": c["position"], "prompt": c["prompt"],
             "dimension": c["dimension"]}
            for c in spec["catches"]
        ],
    }
    for path in (os.path.join(HERE, "stimuli_%s.json" % batch),
                 os.path.join(HERE, "stimuli.json")):
        with open(path, "w") as f:
            json.dump(out, f, indent=2)
    return batch


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry = "--dry-run" in sys.argv
    if not args:
        raise SystemExit("usage: build_batch.py batch_2|batch_3|batch_4 [--dry-run]")
    batch = args[0]
    spec = json.load(open(os.path.join(HERE, "specs", "%s.json" % batch)))

    n_q = len(spec["questions"])
    n_c = len(spec["catches"])
    print(f"spec: {spec['batch']}  questions={n_q}  catches={n_c}  total={n_q + n_c}")
    assert n_q + n_c == spec["session_shape"]["total_questions"], "question budget mismatch"

    imgdir = image_dir(spec)
    if not dry:
        render_missing(spec, imgdir)

    missing = validate(spec, imgdir)
    if missing:
        for qid, f in missing:
            print("MISSING:", qid, f)
        raise SystemExit("spec references images that don't exist")
    print("all images present (%s)" % os.path.relpath(imgdir, ROOT))

    positions = sorted(c["position"] for c in spec["catches"])
    assert positions == spec["session_shape"]["catch_positions_display_order"], "catch positions mismatch"

    if not dry:
        emit_stimuli(spec, imgdir)
        print("wrote stimuli_%s.json (+ stimuli.json for the served app)" % batch)
    else:
        print("dry-run: nothing written")


if __name__ == "__main__":
    main()
