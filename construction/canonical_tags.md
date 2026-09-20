# construction canonical tags

> status: research-derived candidates. none of these is a canonical yet. no real image has been tagged against any of them.

each candidate is a combination of axis values plus what it would imply for engine parameters. the `_candidates` block is the wrangler's expectation of what real images will force into existence. when a seed image arrives, a candidate moves into `canonicals` with real registry hints. until then, the engine never sees these.

---

```json
{
  "canonicals": [],

  "_candidates": [
    {
      "id": "flat_parallel",
      "label": "flat parallel",
      "axes": { "projective_system": "none", "eye_level": "at", "convergence_strength": "none", "foreshortening": "minimal" },
      "description": "no convergence at all. subjects face the viewer squarely. storybook, naive drawing, isometric game art, children's-book elevation.",
      "would_touch": { "camera_mode": "orthographic", "vanishing_points": 0, "tilt": 0 }
    },
    {
      "id": "one_point_deep",
      "label": "one point deep",
      "axes": { "projective_system": "one_point", "eye_level": "at", "convergence_strength": "strict", "foreshortening": "moderate" },
      "description": "a single vanishing point pulls the eye into the picture. corridor, road, railway. the most legible perspective there is.",
      "would_touch": { "camera_mode": "perspective", "vanishing_points": 1, "convergence_visibility": "high" }
    },
    {
      "id": "eye_level_natural",
      "label": "eye level natural",
      "axes": { "projective_system": "two_point", "eye_level": "at", "convergence_strength": "loose", "foreshortening": "moderate" },
      "description": "two vanishing points, undisciplined lines, everyday standing view. the default human scene. most plein air sketches live here.",
      "would_touch": { "camera_mode": "perspective", "vanishing_points": 2, "horizon_ratio": "mid-frame" }
    },
    {
      "id": "worms_eye",
      "label": "worm's eye",
      "axes": { "projective_system": "three_point", "eye_level": "below", "convergence_strength": "strict", "foreshortening": "extreme" },
      "description": "viewer at the ground looking up. verticals converge. subject towers. hero shot, cathedral interior, dramatic upview.",
      "would_touch": { "camera_mode": "perspective", "vanishing_points": 3, "pitch": "up" }
    },
    {
      "id": "birds_eye",
      "label": "bird's eye",
      "axes": { "projective_system": "three_point", "eye_level": "above", "convergence_strength": "loose", "foreshortening": "extreme" },
      "description": "viewer above the subject looking down. map-like or god view. cityscapes from a rooftop, diorama feeling.",
      "would_touch": { "camera_mode": "perspective", "vanishing_points": 3, "pitch": "down" }
    },
    {
      "id": "fisheye_curved",
      "label": "fisheye curved",
      "axes": { "projective_system": "curvilinear", "eye_level": "at", "convergence_strength": "strict", "foreshortening": "extreme" },
      "description": "straight lines bend. the frame edges curve away. skate videos, extreme wide-angle, distorted poster energy.",
      "would_touch": { "camera_mode": "curvilinear", "distortion": "high" }
    }
  ]
}
```

## requirements before promotion

same as render, plus one: a promoted construction canonical needs to be distinguishable from a render canonical's effects. if an image's "worm's eye" feeling is actually produced by its marks rather than its camera, it belongs in render, not here. the domains share custody of drama.
