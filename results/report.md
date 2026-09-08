# stylebench v0 run 20260908_123056

## experiment 1: measurability

| measurement | value | expectation |
|---|---|---|
| palette distance A-B (palette-only change) | 0.095 | want large |
| palette distance A-C (stroke-only change) | 0.0 | want ~0 |
| stroke width cv  A (clean) | 0.316 | baseline |
| stroke width cv  C (rough) | 0.385 | want >> A |
| edge dir entropy A (clean) | 0.995 | baseline |
| edge dir entropy C (rough) | 0.998 | want > A |
| texture energy A | 46.69 | baseline |
| texture energy C | 47.95 | want ~ A |

**verdict: parameters separate the pairs**

## experiment 2: palette transfer (A -> B palette)

| strength | palette dist to ref | fraction closed | content pres | non-target pres |
|---|---|---|---|---|
| 0.25 | 0.0712 | 0.250 | 0.951 | 0.665 |
| 0.50 | 0.0475 | 0.500 | 0.951 | 0.666 |
| 0.75 | 0.0237 | 0.750 | 0.951 | 0.665 |
| 1.00 | 0.0000 | 1.000 | 0.948 | 0.666 |

**verdict: monotonic interpolation, geometry untouched**

