# construction axes

four observable questions about where the camera is. every construction canonical will be a combination of answers. unseeded: these axes are research-derived and have not survived contact with real session images yet, so they are expected to move.

---

```json
{
  "axes": [
    {
      "id": "projective_system",
      "question": "what happens to parallel lines in the subject?",
      "values": [
        {
          "id": "none",
          "description": "parallel lines stay parallel. orthographic or axonometric. elevation view, isometric, storybook flatness."
        },
        {
          "id": "one_point",
          "description": "one set of parallel lines converges to a single vanishing point. frontal faces stay undistorted."
        },
        {
          "id": "two_point",
          "description": "two sets converge to two vanishing points on the horizon. the everyday street-corner view."
        },
        {
          "id": "three_point",
          "description": "verticals converge too. looking up or down hard. the dramatic view."
        },
        {
          "id": "curvilinear",
          "description": "straight lines render curved, like a fisheye lens. the outer-field-of-view effect."
        }
      ]
    },
    {
      "id": "eye_level",
      "question": "where does the horizon line sit relative to the main subject?",
      "values": [
        {
          "id": "above",
          "description": "viewer looks down at the subject. subject sits below the horizon. bird's eye territory."
        },
        {
          "id": "at",
          "description": "horizon cuts through or beside the subject. eye-level, the neutral conversational view."
        },
        {
          "id": "below",
          "description": "viewer looks up. subject sits above the horizon. worm's eye territory."
        }
      ]
    },
    {
      "id": "convergence_strength",
      "question": "how strict is the perspective construction?",
      "values": [
        {
          "id": "strict",
          "description": "vanishing lines visibly disciplined. architectural, technical, deliberate."
        },
        {
          "id": "loose",
          "description": "perspective exists but wobbles. naive, gestural, hand-drawn feel."
        },
        {
          "id": "none",
          "description": "no convergence discipline at all. flatness is the choice."
        }
      ]
    },
    {
      "id": "foreshortening",
      "question": "how compressed are the surfaces angled toward the camera?",
      "values": [
        {
          "id": "extreme",
          "description": "depth-facing surfaces strongly compressed. objects appear to lunge at or away from the viewer."
        },
        {
          "id": "moderate",
          "description": "visible compression on receding surfaces but nothing shouts."
        },
        {
          "id": "minimal",
          "description": "faces keep their true proportions. elevation-like calm."
        }
      ]
    }
  ]
}
```

## notes on the axis choices

- `eye_level` and horizon are the same thing in this system. the life-drawing tradition treats the horizon line as the viewer's eye level by definition, and the two research sources agree. one axis, not two.
- `convergence_strength` exists because the session's render seeds already showed the pattern it captures: the buildings sketch and the house sketch are the same canonical with different discipline. construction needs the same dial (systematic vs gestural) or it will invent a canonical per discipline, which is wrong.
- `projective_system` is the only axis here that names a system rather than a property. it stays because users and art education both name projections directly ("one point", "isometric") and the mapping is one-to-one, which is rare in this branch.
