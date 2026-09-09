"""the parameter registry — the research matrix as code.

single source of truth for every candidate style parameter: its operational
definition, measurement family, scale dependence, granularity, and evidence
status. results/PARAMETER_MATRIX.md renders from this file.

the status ladder (see research/STYLE_ONTOLOGY.md):
    candidate -> measurable -> transferable -> independently_transferable
              -> controllable

a parameter only climbs when its tests pass on the parametric substrate:
test 1 machine fidelity, test 2 human agreement, test 3 independence.
honesty rule: statuses reflect recorded evidence, never optimism — see the
failed entries (lighting contrast, grain independence) for the pattern.
"""
import json

FAMILIES = ["geometry", "mark", "color", "surface", "illumination", "presentation"]

# status shorthand:
#   candidate    — proposed, no test run yet
#   measurable   — test 1 passed (machine tracks ground truth)
#   detector     — measurable but nonlinear; detects change, no slider
#   validated    — test 1 + at least monotone linearity evidence

P = []


def _p(name, family, definition, status="candidate", scale_dep=True,
       granularity="both", evidence="", metric=None):
    P.append({
        "name": name, "family": family, "definition": definition,
        "status": status, "scale_dependent": scale_dep,
        "granularity": granularity, "evidence": evidence, "metric": metric,
    })


# --- family 1: geometry ----------------------------------------------------
_p("shape_complexity", "geometry",
   "contour information density: number of direction changes per unit contour length")
_p("angularity", "geometry",
   "corner angle distribution: acute/obtuse frequency + polygonality index")
_p("curvature_mean", "geometry",
   "mean signed curvature along dominant contours")
_p("curvature_variance", "geometry",
   "curvature variance + frequency of abrupt direction changes")
_p("silhouette_complexity", "geometry",
   "perimeter^2/area + fractal dimension of the subject mask")
_p("silhouette_convexity", "geometry",
   "subject area / convex hull area (concavity and pocket structure)")
_p("simplification", "geometry",
   "detail-to-area ratio: feature count vs minimum feature size")
_p("exaggeration", "geometry",
   "proportion deviation from a canonical object model (needs canonical baselines)",
   granularity="asset")
_p("symmetry", "geometry", "bilateral symmetry score of the subject mask")

# --- family 2: mark ----------------------------------------------------------
_p("stroke_width", "mark",
   "mean stroke width, normalized by subject height (px never transfers alone)",
   status="validated", granularity="both, scale-normalizable",
   evidence="fidelity run 2: monotone + linear, 0.78x bias; granularity run 1: normalized w/subject_height stable to 1-3% across staging (0.01691 vs 0.01735)",
   metric="profile.stroke_width_mean")
_p("stroke_width_variation", "mark",
   "width coefficient of variation along strokes",
   status="validated",
   evidence="fidelity runs 1-2: tracks jitter sigma (saturating), detects taper; granularity run 1: contaminated crops inflate cv to 0.786 (context features mixing into the width population) — asset measurement requires context exclusion",
   metric="profile.stroke_width_cv")
_p("jitter_position", "mark",
   "contour deviation amplitude: high-frequency normal displacement of the ideal line",
   status="detector",
   evidence="svg sweep: monotone via cv/edge entropy but saturating after sigma~1.25 — ordinal, calibration curve pending",
   metric="profile.stroke_width_cv")
_p("jitter_width", "mark",
   "width modulation amplitude along the stroke (separate from position jitter)",
   evidence="split proposed in the ontology; untested as a separate axis")
_p("taper", "mark",
   "width change along stroke: ease fraction + taper rate/symmetry",
   status="validated",
   evidence="fidelity run 2: mean width rises monotonically as taper eases; cv confirms profile detection",
   metric="profile.stroke_width_mean")
_p("stroke_directionality", "mark",
   "orientation distribution entropy + local directional coherence",
   status="measurable",
   evidence="edge_direction_entropy monotone on the jitter sweep; granularity run 1: stable across solo/set/staging (0.991-0.992) — first uncaveated 'both, stable'",
   metric="profile.edge_direction_entropy")
_p("stroke_density", "mark",
   "stroke_mask coverage: marks per area",
   status="detector",
   evidence="double-pass ratio 1.34 (not ~2 — spatial overlap); detects, does not scale",
   metric="stroke_mask.mean")
_p("stroke_continuity", "mark",
   "average uninterrupted run length + gap frequency")
_p("contour_hierarchy", "mark",
   "outer/inner contour width ratio")
_p("contour_completeness", "mark",
   "fraction of implied region boundaries that carry a drawn contour")

# --- family 3: color ----------------------------------------------------------
_p("palette_size", "color", "distinct perceptual color clusters",
   scale_dep=False, evidence="k currently fixed at 6 — perceptual-count estimator pending")
_p("palette_entropy", "color", "color cluster distribution entropy",
   scale_dep=False)
_p("value_range", "color", "luminance percentile spread (p5-p95)", scale_dep=False)
_p("value_bands", "color", "quantized tonal band count in interiors",
   scale_dep=False)
_p("saturation_mean", "color", "mean saturation over subject regions", scale_dep=False)
_p("temperature_balance", "color", "warm/cool luminance-weighted hue balance",
   scale_dep=False)
_p("color_relationships", "color",
   "relationship tendency scores (complementary/analogous/triadic) + relative structure, not raw rgb",
   scale_dep=False)
_p("local_contrast", "color", "adjacent-region color distance distribution",
   scale_dep=False)
_p("palette_distance", "color",
   "distance between measured palettes (mean nearest-color)",
   status="measurable", scale_dep=False,
   evidence="lerp sweep: monotone but compressive at long range; granularity run 1: asset-anchored palette stable (d=0.7), set-anchored differs (d=7.0, zero new colors) — the set is a real different profile",
   metric="metrics.palette_distance")

# --- family 4: surface ----------------------------------------------------------
_p("texture_energy", "surface",
   "high-frequency luminance energy over interior fills",
   status="validated",
   evidence="grain amplitude 0->14 doubles energy, monotone; run-1 leak was a mask problem (fixed); granularity run 1: canvas-anchored — px-stable across staging but +41% subject-relative at 0.55 scale (declared anchor)",
   metric="profile.texture_energy")
_p("texture_scale", "surface",
   "micro/meso/macro band split of spatial frequency energy (paper grain vs brush patches vs blooms)")
_p("texture_directionality", "surface", "dominant texture orientation distribution")
_p("texture_regularity", "surface", "periodicity/regularity of texture pattern")
_p("grain_strength", "surface",
   "grain amplitude at the micro band",
   evidence="independence from texture_energy untested — likely confounded by construction")
_p("fill_boundary_precision", "surface",
   "fill boundary sharpness + color bleed at region edges")

# --- family 5: illumination -----------------------------------------------------
_p("shading_band_count", "illumination",
   "quantized luminance transition count in interior regions")
_p("shadow_softness", "illumination", "shadow transition width profiles")
_p("shadow_darkness", "illumination",
   "shadow value relative to local fill value (relational reading)")
_p("highlight_intensity", "illumination", "highlight luminance + size distribution")
_p("lighting_strength", "illumination",
   "mean luminance delta over fixed-support interiors (w3c soft-light model)",
   status="validated", granularity="both",
   evidence="run 2b: monotone 94.3->100.8 under true soft-light + fixed support; granularity run 1: canvas-anchored recipe — identical house reads 133.8/134.2/129.6 by staging position (set-context contaminates unless subject-anchored)",
   metric="shading mean luminance on fixed supports")
_p("lighting_directionality", "illumination",
   "luminance gradient field directionality across the subject")
_p("shading_contrast", "illumination",
   "interior luminance std on fixed supports",
   status="candidate",
   evidence="FAILED as a lighting-strength metric (flat response by design of the recipe) — kept as candidate for directional-lighting recipes")

# --- family 6: presentation -----------------------------------------------------
_p("edge_hardness", "presentation", "edge transition width profile (hard/soft/lost)")
_p("edge_irregularity", "presentation", "edge deviation + broken-edge frequency")
_p("negative_space_ratio", "presentation",
   "empty-area proportion + empty-region distribution", scale_dep=False)
_p("visual_density", "presentation",
   "marks + details per area vs negative space (minimalist vs ornate)",
   evidence="overlaps stroke_density at the line level — independence test pending")
_p("medium_bleed", "presentation",
   "pigment/substrate interaction: bleed, pooling, dry-brush gaps (medium simulation, not overlay texture)")

PARAMETERS = P


def by_family():
    out = {f: [] for f in FAMILIES}
    for p in P:
        out[p["family"]].append(p)
    return out


def status_counts():
    c = {}
    for p in P:
        c[p["status"]] = c.get(p["status"], 0) + 1
    return c


def render_markdown(path=None):
    """render the research matrix doc from the registry."""
    lines = [
        "# parameter matrix (renders from engine/registry.py — edit there)",
        "",
        "status ladder: candidate -> measurable -> detector -> validated ->",
        "(transferable -> independently transferable -> controllable, tested next).",
        "",
        f"**{len(P)} candidates** across {len(FAMILIES)} families —",
        " ".join(f"{k}: {v}" for k, v in sorted(status_counts().items())),
        "",
    ]
    for fam in FAMILIES:
        rows = by_family()[fam]
        lines += [f"## {fam} ({len(rows)})", "",
                  "| parameter | status | granularity | operational definition | evidence |",
                  "|---|---|---|---|---|"]
        for p in rows:
            ev = p["evidence"] or "untested"
            lines.append(f"| {p['name']} | {p['status']} | {p['granularity']} |"
                         f" {p['definition']} | {ev} |")
        lines.append("")
    lines += ["## evidence legend", "",
              "- validated — machine fidelity passed (monotone at minimum)",
              "- measurable — tracks ground truth; linearity unproven",
              "- detector — detects change, nonlinear response",
              "- candidate — proposed, awaiting test 1", ""]
    doc = "\n".join(lines)
    if path:
        with open(path, "w") as f:
            f.write(doc)
    return doc


if __name__ == "__main__":
    import os
    out = os.path.normpath(os.path.join(os.path.dirname(__file__), "..",
                                         "results", "PARAMETER_MATRIX.md"))
    render_markdown(out)
    print("rendered", out, "-", json.dumps(status_counts()))
