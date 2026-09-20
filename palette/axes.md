# palette axes

four observable questions about what the color is doing. unseeded, research-derived.

---

```json
{
  "axes": [
    {
      "id": "value_structure",
      "question": "how is light and dark organized?",
      "values": [
        {
          "id": "notan_2",
          "description": "two values carry the design. pure black and white shapes. the strict notan of japanese design."
        },
        {
          "id": "notan_3",
          "description": "black, white, and one mid-tone. the liberal notan used for composition studies."
        },
        {
          "id": "full_range",
          "description": "many values, no enforced step structure. tonal organization is gradient-like."
        }
      ],
      "secondary_question": "where does the image sit on the key?",
      "key_values": ["high_key", "low_key", "full_key"]
    },
    {
      "id": "hue_scheme",
      "question": "what is the relationship between the hues present?",
      "values": [
        {
          "id": "mono",
          "description": "one hue family, value does the work."
        },
        {
          "id": "analogous",
          "description": "neighboring hues. harmonious by construction."
        },
        {
          "id": "complementary",
          "description": "opposing hue pairs. tension by construction."
        },
        {
          "id": "triadic",
          "description": "three hues spaced around the wheel. the classic saturated triad."
        },
        {
          "id": "earth",
          "description": "ochres, siennas, umbers, greens. the earth-palette family, recognized as a mood before it is a scheme."
        },
        {
          "id": "unrestricted",
          "description": "no legible scheme. color is local and observational."
        }
      ]
    },
    {
      "id": "saturation_mode",
      "question": "how loud is the color, and where is the loudness?",
      "values": [
        {
          "id": "muted",
          "description": "saturation low across the board. chalky, dusty, faded."
        },
        {
          "id": "natural",
          "description": "saturation where observation would put it. greens green, not neon."
        },
        {
          "id": "saturated",
          "description": "loud everywhere. poster, cartoon, candy energy."
        },
        {
          "id": "accent",
          "description": "one or two saturated pops over an otherwise muted field. the single red coat problem."
        }
      ]
    },
    {
      "id": "temperature_bias",
      "question": "does the image lean warm, cool, or split?",
      "values": [
        {
          "id": "warm",
          "description": "reds, yellows, ochres dominate."
        },
        {
          "id": "cool",
          "description": "blues, greens, violets dominate."
        },
        {
          "id": "split",
          "description": "warm light against cool shadow, or vice versa. temperature used as a depth or lighting tool."
        },
        {
          "id": "neutral",
          "description": "no temperature lean reads."
        }
      ]
    }
  ]
}
```

## notes on the axis choices

- `value_structure` imports notan (two- and three-value design) because it is the one piece of color vocabulary that survived from research as both observable and user-nameable. notan studies are exactly the value axis the engine can measure: count the tonal steps, check the step structure.
- the key (high/low) is a secondary value on value_structure rather than its own axis. it is one bit per image, and users rarely discuss it in isolation.
- `hue_scheme` includes `earth` even though it is a palette family rather than a geometric scheme, because users say "earthy" constantly and never say "analogous". vocabulary follows users, not the color wheel.
- `saturation_mode` keeps `accent` separate from `saturated` because the single-pop structure behaves differently in every downstream use (extraction, transfer strength, leakage risk).
