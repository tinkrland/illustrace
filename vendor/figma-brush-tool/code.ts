type ToolColor = { r: number; g: number; b: number; a: number }
type State = { outputId: string; centerline: { x: number; y: number }[] }
type Params = { brush: "Clean" | "Sketchy" | "Marker" | "Calligraphy" | "Tapered" | "Ink brush" | "Charcoal" | "Pencil" | "Felt tip"; width: number; color: ToolColor; seed: number; jitterOverride: number; taperOverride: number }
type Attachment = { version: 1; params: Params; state: State | null }
type RunMsg =
  | { type: 'action'; id: string; params: Partial<Params> }
  | { type: 'params-change'; params: Partial<Params>; changed: string }
  | { type: 'resize'; height: number }
const TOOL_ID = "4b4bc9f4-6fda-4d68-bd35-49d3940e47ce"
const DISPLAY_NAME = "Brush strokes"
const ATTACH_KEY = TOOL_ID + ':state'
const DEFAULTS: Params = { brush: "Sketchy", width: 5, color: {"r":0.15,"g":0.15,"b":0.15,"a":1}, seed: 42, jitterOverride: -1, taperOverride: -1 }
let latestParams: Params = DEFAULTS
let isExecuting = false

function finiteNumber(value: unknown, fallback: number): number {
  const num = Number(value)
  return Number.isFinite(num) ? num : fallback
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

function normalizeColor(value: unknown, fallback: ToolColor): ToolColor {
  if (typeof value !== 'object' || value === null) return fallback
  const obj = value as Partial<ToolColor>
  return {
    r: clamp(finiteNumber(obj.r, fallback.r), 0, 1),
    g: clamp(finiteNumber(obj.g, fallback.g), 0, 1),
    b: clamp(finiteNumber(obj.b, fallback.b), 0, 1),
    a: clamp(finiteNumber(obj.a, fallback.a), 0, 1),
  }
}

function normalizeParams(input: Partial<Params> | null | undefined): Params {
  const value = input ?? {}
  return {
    brush: ["Clean","Sketchy","Marker","Calligraphy","Tapered","Ink brush","Charcoal","Pencil","Felt tip"].includes(String(value.brush)) ? (String(value.brush) as Params['brush']) : DEFAULTS.brush,
    width: clamp(finiteNumber(value.width, DEFAULTS.width), 1, 40),
    color: normalizeColor(value.color, DEFAULTS.color),
    seed: clamp(finiteNumber(value.seed, DEFAULTS.seed), 1, 9999),
    jitterOverride: clamp(finiteNumber(value.jitterOverride, DEFAULTS.jitterOverride), -1, 10),
    taperOverride: clamp(finiteNumber(value.taperOverride, DEFAULTS.taperOverride), -1, 1),
  }
}

function solidPaint(color: ToolColor): SolidPaint {
  return {
    type: 'SOLID',
    color: { r: color.r, g: color.g, b: color.b },
    opacity: color.a,
  }
}

class VectorPathBuilder {
  private commands: string[] = []
  // Guard against NaN/Infinity (a non-finite token crashes the path parser),
  // then 2-decimal round at emit time so control-point math stays full precision.
  private coord(value: number): string {
    const safe = Number.isFinite(value) ? value : 0
    return Number.isInteger(safe) ? String(safe) : Number(safe.toFixed(2)).toString()
  }
  moveTo(x: number, y: number): this {
    this.commands.push('M', this.coord(x), this.coord(y))
    return this
  }
  lineTo(x: number, y: number): this {
    this.commands.push('L', this.coord(x), this.coord(y))
    return this
  }
  curveTo(c1x: number, c1y: number, c2x: number, c2y: number, x: number, y: number): this {
    this.commands.push(
      'C',
      this.coord(c1x), this.coord(c1y),
      this.coord(c2x), this.coord(c2y),
      this.coord(x), this.coord(y),
    )
    return this
  }
  quadraticCurveTo(cx: number, cy: number, x: number, y: number): this {
    this.commands.push('Q', this.coord(cx), this.coord(cy), this.coord(x), this.coord(y))
    return this
  }
  close(): this {
    this.commands.push('Z')
    return this
  }
  toPathData(): string {
    return this.commands.join(' ')
  }
  toVectorPath(
    windingRule: 'NONZERO' | 'EVENODD' | 'NONE' = 'NONZERO',
  ): { windingRule: 'NONZERO' | 'EVENODD' | 'NONE'; data: string } {
    return { windingRule, data: this.toPathData() }
  }
}

function htmlEscapeAttribute(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
}

function colorToHex(color: ToolColor): string {
  const channel = (value: number) =>
    Math.round(clamp(value, 0, 1) * 255)
      .toString(16)
      .padStart(2, '0')
      .toUpperCase()
  return '#' + channel(color.r) + channel(color.g) + channel(color.b) + channel(color.a)
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
function extractCenterline(node: VectorNode): { x: number; y: number }[] {
  const pts: { x: number; y: number }[] = []
  const network = node.vectorNetwork
  for (const seg of network.segments) {
    const v0 = network.vertices[seg.start]
    const v1 = network.vertices[seg.end]
    if (pts.length === 0 || (pts[pts.length - 1].x !== v0.x || pts[pts.length - 1].y !== v0.y)) {
      pts.push({ x: v0.x, y: v0.y })
    }
    const ts = seg.tangentStart ?? { x: 0, y: 0 }
    const te = seg.tangentEnd ?? { x: 0, y: 0 }
    if (ts.x !== 0 || ts.y !== 0 || te.x !== 0 || te.y !== 0) {
      const cx1 = v0.x + ts.x
      const cy1 = v0.y + ts.y
      const cx2 = v1.x + te.x
      const cy2 = v1.y + te.y
      for (let t = 0.1; t <= 0.9; t += 0.1) {
        const mt = 1 - t
        const bx = mt * mt * mt * v0.x + 3 * mt * mt * t * cx1 + 3 * mt * t * t * cx2 + t * t * t * v1.x
        const by = mt * mt * mt * v0.y + 3 * mt * mt * t * cy1 + 3 * mt * t * t * cy2 + t * t * t * v1.y
        pts.push({ x: bx, y: by })
      }
    }
    pts.push({ x: v1.x, y: v1.y })
  }
  return pts
}
function resamplePolyline(pts: { x: number; y: number }[], spacing: number): { x: number; y: number }[] {
  if (pts.length < 2) return pts
  const out: { x: number; y: number }[] = [pts[0]]
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
      out.push({
        x: pts[i - 1].x + ux * traveled,
        y: pts[i - 1].y + uy * traveled
      })
    }
    residual = segLen - traveled
  }
  const last = pts[pts.length - 1]
  const prev = out[out.length - 1]
  if (Math.abs(last.x - prev.x) > 0.1 || Math.abs(last.y - prev.y) > 0.1) {
    out.push(last)
  }
  return out
}
function jitterPolyline(pts: { x: number; y: number }[], sigma: number, seed: number): { x: number; y: number }[] {
  if (sigma <= 0) return pts
  const rng = seededRandom(seed)
  const out: { x: number; y: number }[] = [pts[0]]
  for (let i = 1; i < pts.length - 1; i++) {
    out.push({
      x: pts[i].x + gaussRandom(rng) * sigma,
      y: pts[i].y + gaussRandom(rng) * sigma
    })
  }
  out.push(pts[pts.length - 1])
  return out
}
function bakeOutline(
  pts: { x: number; y: number }[],
  baseWidth: number,
  taperFraction: number,
  taperDir: string
): { x: number; y: number }[] {
  if (pts.length < 2) return pts
  const resampled = resamplePolyline(pts, 4)
  const n = resampled.length
  const left: { x: number; y: number }[] = []
  const right: { x: number; y: number }[] = []
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
    if (mag < 0.001) { nx = 0; ny = 1 } else { nx /= mag; ny /= mag }
    const t = i / Math.max(1, n - 1)
    let widthFactor = 1.0
    if (taperFraction > 0) {
      if (taperDir === 'symmetric') {
        if (t < taperFraction) widthFactor = t / taperFraction
        else if (t > 1 - taperFraction) widthFactor = (1 - t) / taperFraction
      } else if (taperDir === 'toward') {
        if (t > 1 - taperFraction) widthFactor = (1 - t) / taperFraction
      } else if (taperDir === 'away') {
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
interface BrushPreset {
  width: number
  jitter: number
  passes: number
  taper: number
  taperDir: string
  cap: string
}
function getBrushPreset(name: string, width: number): BrushPreset {
  switch (name) {
    case 'Sketchy':
      return { width, jitter: 2.5, passes: 2, taper: 0, taperDir: 'symmetric', cap: 'round' }
    case 'Marker':
      return { width: width * 1.8, jitter: 0, passes: 1, taper: 0, taperDir: 'symmetric', cap: 'round' }
    case 'Calligraphy':
      return { width, jitter: 0, passes: 1, taper: 0.3, taperDir: 'symmetric', cap: 'round' }
    case 'Tapered':
      return { width, jitter: 0, passes: 1, taper: 0.4, taperDir: 'toward', cap: 'round' }
    case 'Ink brush':
      return { width: width * 1.2, jitter: 1.0, passes: 1, taper: 0.25, taperDir: 'away', cap: 'round' }
    case 'Charcoal':
      return { width: width * 1.5, jitter: 3.5, passes: 3, taper: 0.1, taperDir: 'symmetric', cap: 'round' }
    case 'Pencil':
      return { width: width * 0.6, jitter: 1.2, passes: 2, taper: 0.05, taperDir: 'symmetric', cap: 'round' }
    case 'Felt tip':
      return { width: width * 1.3, jitter: 0.3, passes: 1, taper: 0.15, taperDir: 'toward', cap: 'round' }
    default:
      return { width, jitter: 0, passes: 1, taper: 0, taperDir: 'symmetric', cap: 'square' }
  }
}

function uniqueSceneNodes(nodes: readonly SceneNode[]): SceneNode[] {
  return [...new Set(nodes)].filter((node) => !node.removed)
}

function attachRelaunch(nodes: readonly SceneNode[]): void {
  const unique = uniqueSceneNodes(nodes)
  if (unique.length > 0) {
    for (const node of unique) node.setRelaunchData({ [TOOL_ID]: DISPLAY_NAME })
  } else {
    figma.root.setRelaunchData({ [TOOL_ID]: DISPLAY_NAME })
  }
}

function singleSelectedTarget(): SceneNode | null {
  const selection = figma.currentPage.selection
  return selection.length === 1 ? (selection[0] ?? null) : null
}

function readAttachment(node: SceneNode): Attachment | null {
  try {
    const parsed = JSON.parse(node.getPluginData(ATTACH_KEY)) as Partial<Attachment>
    if (parsed?.version !== 1) return null
    return {
      version: 1,
      params: normalizeParams(parsed.params),
      state: (parsed.state ?? null) as State | null,
    }
  } catch {
    return null
  }
}

function writeAttachment(node: SceneNode, params: Params, state: State | null): void {
  node.setPluginData(ATTACH_KEY, JSON.stringify({ version: 1, params, state }))
}

function clearAttachment(node: SceneNode): void {
  node.setPluginData(ATTACH_KEY, '')
}

function bindStatus_apply(hasTarget: boolean, isBound: boolean): string {
  if (!hasTarget) return "Select a vector path"
  return isBound ? "Reapply brush" : "Apply brush style"
}
function evaluateEnabled_apply(selection: readonly SceneNode[]): boolean {
  return (selection.length === 1 && selection[0].type === 'VECTOR')
}
function actionTarget_apply(): SceneNode | null {
  const target = singleSelectedTarget()
  if (target == null) return null
  return evaluateEnabled_apply([target]) ? target : null
}
async function action_apply(params: Params, target: SceneNode, previousState: State | null): Promise<{ affectedNodes: SceneNode[]; state: State | null }> {
  const affectedNodes: SceneNode[] = [target]
  let state: State | null = previousState
  await (async () => {
    if (target.type !== 'VECTOR') return
    const centerline = extractCenterline(target)
    if (centerline.length < 2) return
    const preset = getBrushPreset(params.brush, params.width)
    const jitter = params.jitterOverride >= 0 ? params.jitterOverride : preset.jitter
    const taper = params.taperOverride >= 0 ? params.taperOverride : preset.taper
    const allOutlines: { x: number; y: number }[][] = []
    for (let pass = 0; pass < preset.passes; pass++) {
      const jittered = jitterPolyline(centerline, jitter, params.seed + pass * 1000)
      const outline = bakeOutline(jittered, preset.width, taper, preset.taperDir)
      allOutlines.push(outline)
    }
    const builder = new VectorPathBuilder()
    for (const outline of allOutlines) {
      if (outline.length < 3) continue
      builder.moveTo(outline[0].x, outline[0].y)
      for (let i = 1; i < outline.length; i++) {
        builder.lineTo(outline[i].x, outline[i].y)
      }
      builder.close()
    }
    const pathData = builder.toPathData()
    const vec = figma.createVector()
    vec.name = target.name + ' — ' + params.brush
    vec.vectorPaths = [{ windingRule: 'NONZERO', data: pathData }]
    vec.fills = [solidPaint(params.color)]
    vec.strokes = []
    vec.x = target.x
    vec.y = target.y
    if (target.parent != null && 'appendChild' in target.parent) {
      const parentNode = target.parent
      const idx = parentNode.children.indexOf(target)
      parentNode.insertChild(idx, vec)
    }
    target.visible = false
    const prevId = previousState?.outputId
    if (prevId) {
      const prevNode = await figma.getNodeByIdAsync(prevId)
      if (prevNode != null && !prevNode.removed) prevNode.remove()
    }
    state = { outputId: vec.id, centerline }
    affectedNodes.push(vec)
  })()
  return { affectedNodes, state: state }
}
async function runAction_apply(target: SceneNode, notify: boolean): Promise<void> {
  isExecuting = true
  try {
    const result = await action_apply(latestParams, target, readAttachment(target)?.state ?? null)
    writeAttachment(target, latestParams, result.state)
    attachRelaunch(result.affectedNodes)
    pushActionStates()
    if (notify) {
      const created = result.affectedNodes.filter((node) => node !== target)
      if (created.length > 0) {
        figma.viewport.scrollAndZoomIntoView(created)
      }
      figma.notify(DISPLAY_NAME + " applied")
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    figma.notify(message, { error: true })
    throw error
  } finally {
    isExecuting = false
  }
}
async function removeAction_apply(target: SceneNode): Promise<void> {
  const attachment = readAttachment(target)
  if (attachment == null) return
  target.visible = true
  const outId = attachment?.state?.outputId
  if (outId) {
    const outNode = await figma.getNodeByIdAsync(outId)
    if (outNode != null && !outNode.removed) outNode.remove()
  }
  clearAttachment(target)
  target.setRelaunchData({})
  pushActionStates()
  figma.notify(DISPLAY_NAME + ' removed')
}
async function onParameterChange(params: Params, target: SceneNode, previousState: State | null): Promise<{ affectedNodes: SceneNode[]; state: State | null }> {
  const affectedNodes: SceneNode[] = [target]
  let state: State | null = previousState
  await (async () => {
    if (target.type !== 'VECTOR') return
    const centerline = previousState?.centerline ?? extractCenterline(target)
    if (centerline.length < 2) return
    const preset = getBrushPreset(params.brush, params.width)
    const jitter = params.jitterOverride >= 0 ? params.jitterOverride : preset.jitter
    const taper = params.taperOverride >= 0 ? params.taperOverride : preset.taper
    const allOutlines: { x: number; y: number }[][] = []
    for (let pass = 0; pass < preset.passes; pass++) {
      const jittered = jitterPolyline(centerline, jitter, params.seed + pass * 1000)
      const outline = bakeOutline(jittered, preset.width, taper, preset.taperDir)
      allOutlines.push(outline)
    }
    const builder = new VectorPathBuilder()
    for (const outline of allOutlines) {
      if (outline.length < 3) continue
      builder.moveTo(outline[0].x, outline[0].y)
      for (let i = 1; i < outline.length; i++) {
        builder.lineTo(outline[i].x, outline[i].y)
      }
      builder.close()
    }
    const pathData = builder.toPathData()
    const prevId = previousState?.outputId
    let vec: VectorNode | null = null
    if (prevId) {
      const existing = await figma.getNodeByIdAsync(prevId)
      if (existing != null && !existing.removed && existing.type === 'VECTOR') {
        vec = existing
      }
    }
    if (vec == null) {
      vec = figma.createVector()
      vec.x = target.x
      vec.y = target.y
      if (target.parent != null && 'appendChild' in target.parent) {
        const parentNode = target.parent
        const idx = parentNode.children.indexOf(target)
        parentNode.insertChild(idx, vec)
      }
    }
    vec.name = target.name + ' — ' + params.brush
    vec.vectorPaths = [{ windingRule: 'NONZERO', data: pathData }]
    vec.fills = [solidPaint(params.color)]
    vec.strokes = []
    state = { outputId: vec.id, centerline }
    affectedNodes.push(vec)
  })()
  return { affectedNodes, state: state }
}

async function runOnParameterChange(params: Params, changed: string): Promise<void> {
  latestParams = params
  if (!["brush","width","color","seed","jitterOverride","taperOverride"].includes(changed)) return
  const target = singleSelectedTarget()
  if (target == null) return
  const attachment = readAttachment(target)
  if (attachment == null) return
  isExecuting = true
  try {
    const result = await onParameterChange(latestParams, target, attachment.state)
    writeAttachment(target, latestParams, result.state)
    attachRelaunch(result.affectedNodes)
    pushActionStates()
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    figma.notify(message, { error: true })
    throw error
  } finally {
    isExecuting = false
  }
}
function pushActionStates(): void {
  const t_apply = actionTarget_apply()
  const bound_apply = t_apply != null && readAttachment(t_apply!) != null
  const enabled_apply = t_apply != null
  figma.ui.postMessage({
    type: 'action-state',
    actions: {
      "apply": { enabled: enabled_apply, label: bound_apply ? "Remove brush" : "Apply brush", status: bindStatus_apply(enabled_apply, bound_apply) },
    },
  })
}
function refreshSelection(): void {
  if (isExecuting) return
  const target = singleSelectedTarget()
  const attachment = target != null ? readAttachment(target) : null
  latestParams = attachment?.params ?? DEFAULTS
  figma.ui.postMessage({ type: 'params-change', params: latestParams })
  pushActionStates()
}

const initialTarget = singleSelectedTarget()
const initialAttachment = initialTarget != null ? readAttachment(initialTarget) : null
const initialParams: Params = initialAttachment?.params ?? DEFAULTS
latestParams = initialParams
let html = __html__
html = html.replace(/(id="brush"[^>]*\bvalue=")[^"]*(")/g, '$1' + htmlEscapeAttribute(String(initialParams.brush)) + '$2')
html = html.replace(/(id="width"[^>]*\bvalue=")[^"]*(")/g, '$1' + htmlEscapeAttribute(String(initialParams.width)) + '$2')
html = html.replace(/(id="color"[^>]*\bvalue=")[^"]*(")/g, '$1' + htmlEscapeAttribute(colorToHex(initialParams.color)) + '$2')
html = html.replace(/(id="seed"[^>]*\bvalue=")[^"]*(")/g, '$1' + htmlEscapeAttribute(String(initialParams.seed)) + '$2')
html = html.replace(/(id="jitterOverride"[^>]*\bvalue=")[^"]*(")/g, '$1' + htmlEscapeAttribute(String(initialParams.jitterOverride)) + '$2')
html = html.replace(/(id="taperOverride"[^>]*\bvalue=")[^"]*(")/g, '$1' + htmlEscapeAttribute(String(initialParams.taperOverride)) + '$2')
figma.root.setRelaunchData({ [TOOL_ID]: DISPLAY_NAME })
figma.showUI(html, { width: 280, height: 320 })
pushActionStates()
figma.on('selectionchange', refreshSelection)

figma.ui.onmessage = (msg: RunMsg) => {
  if (msg.type === 'resize') {
    figma.ui.resize(280, Math.max(48, Math.min(900, Math.round(msg.height))))
    return
  }
  if (msg.type === 'action') {
    if (msg.id === "apply") {
      const target = actionTarget_apply()
      if (target == null) return
      if (readAttachment(target) != null) {
        void removeAction_apply(target)
      } else {
        latestParams = normalizeParams(msg.params)
        void runAction_apply(target, true)
      }
      return
    }
    return
  }
  if (msg.type === 'params-change') {
    void runOnParameterChange(normalizeParams(msg.params), msg.changed)
    return
  }
}