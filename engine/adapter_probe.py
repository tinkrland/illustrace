#!/usr/bin/env python3
"""adapter probe harness: does a trained adapter actually deliver the
component it claims, and only that?

the contract (research/STYLE_LORA_ENGINE.md): every adapter's inspo corpus
gets profiled BEFORE training (the target profile), and its generations get
profiled AFTER. the delta report measures:

  1. fidelity  - did the claimed component move toward the target?
  2. leakage   - did unclaimed components move too? (stylebench claim,
                 applied to our own adapters)

report shape: json (per-component deltas + fidelity/leakage verdicts) and
a markdown table for the run log.

    # target profile from a corpus (pre-training, no gpu needed)
    python3 engine/adapter_probe.py target --corpus data/monet --out data/generated/probes/monet_target.json

    # after the adapter generates, profile its outputs and compare
    python3 engine/adapter_probe.py delta --target data/generated/probes/monet_target.json \\
        --outputs data/generated/adapter_out/monet_demo --claim palette \\
        --out data/generated/probes/monet_delta.json
"""
import argparse
import glob
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# the measurable components (must match engine/analyzer.py take set)
COMPONENTS = {
    "palette": lambda c: c["palette"]["colors_hex"],
    "stroke": lambda c: [c["stroke"]["width_mean"], c["stroke"]["width_cv"],
                          c["stroke"]["axis_deg"], c["stroke"]["axis_concentration"]],
    "texture": lambda c: [c["texture"]["energy"]],
    "edges": lambda c: [c["edges"]["direction_entropy"]],
    "shape": lambda c: [c["shape"]["perim_area"], c["shape"]["boundary_entropy"],
                         c["shape"]["ink_coverage"]],
}


def profile_dir(path):
    from inspo_profile import profile_inspo
    files = sorted(glob.glob(os.path.join(path, "*")))
    imgs = [f for f in files if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
    if not imgs:
        sys.exit("no images in %s" % path)
    return [profile_inspo(f) for f in imgs]


def component_stats(profiles):
    """mean + spread per component, so deltas compare distributions not
    single images."""
    out = {}
    for comp, get in COMPONENTS.items():
        vals = [get(p["components"]) for p in profiles]
        means = [statistics.mean(col) if not isinstance(col[0], str) else None
                 for col in zip(*vals)]
        sds = [statistics.pstdev(col) if len(col) > 1 and not isinstance(col[0], str) else 0.0
               for col in zip(*vals)]
        if comp == "palette":
            out[comp] = {"colors": vals[0]}  # representative palette
            continue
        out[comp] = {"means": [round(m, 3) if m is not None else None for m in means],
                     "sds": [round(s, 3) for s in sds]}
    out["n"] = len(profiles)
    return out


def _hex_lab(h):
    """srgb hex -> cie lab (d65). v0 metric: euclidean distance in lab
    (cie76 deltae). just-noticeable difference is ~2.3; palette mismatch
    between different artists is typically 20-50."""
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = lin(r), lin(g), lin(b)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return f(x) * 116 - 16, f(y) * 500, f(z) * 200


def hex_distance(a, b):
    (l1, a1, b1), (l2, a2, b2) = _hex_lab(a), _hex_lab(b)
    return round(((l1 - l2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2) ** 0.5, 2)


PALETTE_TOL = 10.0  # mean deltaE under this = palette fidelity ok


def delta(target, outputs, claim):
    """per-component: did outputs move from baseline toward the target?

    baseline = the pre-training adapter base model outputs would be ideal;
    v0 compares output spread against target means (cohen's d style).
    """
    rep = {}
    for comp in COMPONENTS:
        t, o = target[comp], outputs[comp]
        if comp == "palette":
            dists = [hex_distance(a, b) for a, b in zip(t["colors"], o["colors"])]
            rep[comp] = {"mean_hex_dist": round(statistics.mean(dists), 4),
                         "claimed": comp == claim}
            continue
        ds = []
        labels = {"stroke": ["width_mean", "width_cv", "axis_deg", "axis_conc"],
                  "texture": ["energy"], "edges": ["dir_entropy"],
                  "shape": ["perim_area", "boundary_entropy", "ink_coverage"]}[comp]
        for i, lab in enumerate(labels):
            tm, ts = t["means"][i], t["sds"][i] or 1e-6
            om, os_ = o["means"][i], o["sds"][i] or 1e-6
            d = (om - tm) / ((ts + os_) / 2 + 1e-6)  # standardized shift
            ds.append(round(d, 3))
        rep[comp] = {"shifts": dict(zip(labels, ds)),
                     "max_shift": max(abs(x) for x in ds),
                     "claimed": comp == claim}
    # verdicts: fidelity = claimed component near target; leakage = big
    # unclaimed shifts. thresholds are preregistration candidates, not truth.
    claimed = rep[claim]
    fidelity = ((claimed.get("mean_hex_dist", 99) < PALETTE_TOL)
                if claim == "palette" else claimed.get("max_shift", 99) < 1.0)
    leakage = [c for c, r in rep.items() if not r["claimed"]
               and r.get("max_shift", 0) > 1.0]
    return {"components": rep, "claim": claim,
            "fidelity_ok": fidelity, "leaked": leakage}


def report_markdown(res, name):
    lines = ["# adapter probe: %s" % name, "",
             "claim: **%s** | fidelity: %s | leakage: %s"
             % (res["claim"], "ok" if res["fidelity_ok"] else "FAIL",
                ", ".join(res["leaked"]) or "none"), ""]
    for comp, r in res["components"].items():
        if "shifts" in r:
            for k, v in r["shifts"].items():
                lines.append("- %s.%s: %+0.3f %s" %
                             (comp, k, v, "(claimed)" if r["claimed"] else ""))
        else:
            lines.append("- palette mean hex dist: %s %s" %
                         (r["mean_hex_dist"], "(claimed)" if r["claimed"] else ""))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("target", help="profile a corpus as the adapter target")
    t.add_argument("--corpus", required=True)
    t.add_argument("--out", required=True)
    d = sub.add_parser("delta", help="compare adapter outputs against target")
    d.add_argument("--target", required=True)
    d.add_argument("--outputs", required=True)
    d.add_argument("--claim", required=True, choices=COMPONENTS)
    d.add_argument("--out", required=True)
    d.add_argument("--name", default="adapter")
    args = ap.parse_args()

    sys.path.insert(0, HERE)
    if args.cmd == "target":
        stats = component_stats(profile_dir(args.corpus))
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        json.dump(stats, open(args.out, "w"), indent=1)
        print("[probe] target profile (n=%d) -> %s" % (stats["n"], args.out))
        return

    target = json.load(open(args.target))
    outputs = component_stats(profile_dir(args.outputs))
    res = delta(target, outputs, args.claim)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(res, open(args.out, "w"), indent=1)
    md = args.out.replace(".json", ".md")
    open(md, "w").write(report_markdown(res, args.name))
    print("[probe] fidelity:", "ok" if res["fidelity_ok"] else "FAIL",
          "| leakage:", ", ".join(res["leaked"]) or "none")
    print("[probe] report -> %s + %s" % (args.out, md))


if __name__ == "__main__":
    main()
