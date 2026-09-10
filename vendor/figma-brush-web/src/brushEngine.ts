export type BrushName =
  | "Clean"
  | "Sketchy"
  | "Marker"
  | "Calligraphy"
  | "Tapered"
  | "Ink brush"
  | "Charcoal"
  | "Pencil"
  | "Felt tip"

export interface Point {
  x: number
  y: number
}

export interface BrushParams {
  brush: BrushName
  width: number
  color: string
  opacity: number
  seed: number
  jitterOverride: number
  taperOverride: number
}

export interface Stroke {
  centerline: Point[]
  params: BrushParams
  outlines: Point[][]
}

interface BrushPreset {
  width: number
  jitter: number
  passes: number
  taper: number
  taperDir: string
}

function seededRandom(seed: number): () => number {
  let s = seed
  return () => {
    s = (s * 16807 + 0) % 2147483647
    return (s - 1) / 2147483646
  }
}

function gaussRandom(rng: () => number): number {
  const u1 = rng()
  const u2 = rng()
  return Math.sqrt(-2 * Math.log(Math.max(u1, 0.0001))) * Math.cos(2 * Math.PI * u2)
}

export function resamplePolyline(pts: Point[], spacing: number): Point[] {
  if (pts.length < 2) return pts
  const out: Point[] = [pts[0]]
  let residual = 0
  for (let i = 1; i < pts.length; i++) {
    const dx = pts[i].x - pts[i - 1].x
    const dy = pts[i].y - pts[i - 1].y
    const segLen = Math.sqrt(dx * dx + dy * dy)
    if (segLen < 0.001) continue
    const ux = dx / segLen
    const uy = dy / segLen
    let traveled = residual
    while (traveled + spacing <= segLen) {
      traveled += spacing
      out.push({ x: pts[i - 1].x + ux * traveled, y: pts[i - 1].y + uy * traveled })
    }
    residual = segLen - traveled
  }
  const last = pts[pts.length - 1]
  const prev = out[out.length - 1]
  if (Math.abs(last.x - prev.x) > 0.1 || Math.abs(last.y - prev.y) > 0.1) out.push(last)
  return out
}

function jitterPolyline(pts: Point[], sigma: number, seed: number): Point[] {
  if (sigma <= 0) return pts
  const rng = seededRandom(seed)
  const out: Point[] = [pts[0]]
  for (let i = 1; i < pts.length - 1; i++) {
    out.push({
      x: pts[i].x + gaussRandom(rng) * sigma,
      y: pts[i].y + gaussRandom(rng) * sigma,
    })
  }
  out.push(pts[pts.length - 1])
  return out
}

function bakeOutline(
  pts: Point[],
  baseWidth: number,
  taperFraction: number,
  taperDir: string,
): Point[] {
  if (pts.length < 2) return pts
  const resampled = resamplePolyline(pts, 4)
  const n = resampled.length
  const left: Point[] = []
  const right: Point[] = []
  for (let i = 0; i < n; i++) {
    let nx: number, ny: number
    if (i === 0) {
      nx = -(resampled[1].y - resampled[0].y)
      ny = resampled[1].x - resampled[0].x
    } else if (i === n - 1) {
      nx = -(resampled[i].y - resampled[i - 1].y)
      ny = resampled[i].x - resampled[i - 1].x
    } else {
      nx = -(resampled[i + 1].y - resampled[i - 1].y)
      ny = resampled[i + 1].x - resampled[i - 1].x
    }
    const mag = Math.sqrt(nx * nx + ny * ny)
    if (mag < 0.001) {
      nx = 0
      ny = 1
    } else {
      nx /= mag
      ny /= mag
    }
    const t = i / Math.max(1, n - 1)
    let widthFactor = 1.0
    if (taperFraction > 0) {
      if (taperDir === "symmetric") {
        if (t < taperFraction) widthFactor = t / taperFraction
        else if (t > 1 - taperFraction) widthFactor = (1 - t) / taperFraction
      } else if (taperDir === "toward") {
        if (t > 1 - taperFraction) widthFactor = (1 - t) / taperFraction
      } else if (taperDir === "away") {
        if (t < taperFraction) widthFactor = t / taperFraction
      }
    }
    widthFactor = Math.max(0.05, widthFactor)
    const halfW = (baseWidth / 2) * widthFactor
    left.push({ x: resampled[i].x + nx * halfW, y: resampled[i].y + ny * halfW })
    right.push({ x: resampled[i].x - nx * halfW, y: resampled[i].y - ny * halfW })
  }
  return [...left, ...right.reverse()]
}

function getBrushPreset(name: string, width: number): BrushPreset {
  switch (name) {
    case "Sketchy":
      return { width, jitter: 2.5, passes: 2, taper: 0, taperDir: "symmetric" }
    case "Marker":
      return { width: width * 1.8, jitter: 0, passes: 1, taper: 0, taperDir: "symmetric" }
    case "Calligraphy":
      return { width, jitter: 0, passes: 1, taper: 0.3, taperDir: "symmetric" }
    case "Tapered":
      return { width, jitter: 0, passes: 1, taper: 0.4, taperDir: "toward" }
    case "Ink brush":
      return { width: width * 1.2, jitter: 1.0, passes: 1, taper: 0.25, taperDir: "away" }
    case "Charcoal":
      return { width: width * 1.5, jitter: 3.5, passes: 3, taper: 0.1, taperDir: "symmetric" }
    case "Pencil":
      return { width: width * 0.6, jitter: 1.2, passes: 2, taper: 0.05, taperDir: "symmetric" }
    case "Felt tip":
      return { width: width * 1.3, jitter: 0.3, passes: 1, taper: 0.15, taperDir: "toward" }
    default:
      return { width, jitter: 0, passes: 1, taper: 0, taperDir: "symmetric" }
  }
}

export function generateOutlines(centerline: Point[], params: BrushParams): Point[][] {
  if (centerline.length < 2) return []
  const preset = getBrushPreset(params.brush, params.width)
  const jitter = params.jitterOverride >= 0 ? params.jitterOverride : preset.jitter
  const taper = params.taperOverride >= 0 ? params.taperOverride : preset.taper
  const outlines: Point[][] = []
  for (let pass = 0; pass < preset.passes; pass++) {
    const jittered = jitterPolyline(centerline, jitter, params.seed + pass * 1000)
    const outline = bakeOutline(jittered, preset.width, taper, preset.taperDir)
    outlines.push(outline)
  }
  return outlines
}

export function renderOutlines(
  ctx: CanvasRenderingContext2D,
  outlines: Point[][],
  color: string,
  opacity: number,
): void {
  ctx.save()
  ctx.globalAlpha = opacity
  ctx.fillStyle = color
  for (const outline of outlines) {
    if (outline.length < 3) continue
    ctx.beginPath()
    ctx.moveTo(outline[0].x, outline[0].y)
    for (let i = 1; i < outline.length; i++) ctx.lineTo(outline[i].x, outline[i].y)
    ctx.closePath()
    ctx.fill()
  }
  ctx.restore()
}

function outlineToSVGPath(outline: Point[]): string {
  if (outline.length < 2) return ""
  const d = [`M ${outline[0].x.toFixed(1)} ${outline[0].y.toFixed(1)}`]
  for (let i = 1; i < outline.length; i++) {
    d.push(`L ${outline[i].x.toFixed(1)} ${outline[i].y.toFixed(1)}`)
  }
  d.push("Z")
  return d.join(" ")
}

export function strokesToSVG(strokes: Stroke[], width: number, height: number): string {
  const paths = strokes.flatMap((s) =>
    s.outlines.map(
      (outline) =>
        `  <path d="${outlineToSVGPath(outline)}" fill="${s.params.color}" fill-opacity="${s.params.opacity.toFixed(3)}" fill-rule="nonzero"/>`,
    ),
  )
  return [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`,
    ...paths,
    `</svg>`,
  ].join("\n")
}
