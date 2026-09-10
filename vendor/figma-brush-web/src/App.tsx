import { useRef, useState, useCallback, useEffect } from "react"
import {
  generateOutlines,
  renderOutlines,
  strokesToSVG,
  resamplePolyline,
} from "./brushEngine"
import type { BrushName, BrushParams, Stroke, Point } from "./brushEngine"

const BRUSH_NAMES: BrushName[] = [
  "Clean",
  "Sketchy",
  "Marker",
  "Calligraphy",
  "Tapered",
  "Ink brush",
  "Charcoal",
  "Pencil",
  "Felt tip",
]

const CANVAS_W = 1200
const CANVAS_H = 900

const DEFAULT_PARAMS: BrushParams = {
  brush: "Sketchy",
  width: 8,
  color: "#1a1814",
  opacity: 0.85,
  seed: 42,
  jitterOverride: -1,
  taperOverride: -1,
}

interface FigmaUser {
  handle: string
  email: string
}

export default function App() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const offscreenRef = useRef<HTMLCanvasElement | null>(null)
  const currentPointsRef = useRef<Point[]>([])

  const [strokes, setStrokes] = useState<Stroke[]>([])
  const [params, setParams] = useState<BrushParams>(DEFAULT_PARAMS)
  const [isDrawing, setIsDrawing] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [selected, setSelected] = useState<number | null>(null)

  const [showFigmaPanel, setShowFigmaPanel] = useState(false)
  const [figmaTokenInput, setFigmaTokenInput] = useState("")
  const [figmaUser, setFigmaUser] = useState<FigmaUser | null>(null)
  const [figmaConnecting, setFigmaConnecting] = useState(false)
  const [figmaError, setFigmaError] = useState("")

  const [copied, setCopied] = useState(false)

  // Initialize offscreen canvas
  useEffect(() => {
    const off = document.createElement("canvas")
    off.width = CANVAS_W
    off.height = CANVAS_H
    const ctx = off.getContext("2d")!
    ctx.fillStyle = "#f4eed8"
    ctx.fillRect(0, 0, CANVAS_W, CANVAS_H)
    offscreenRef.current = off
    blitToDisplay(off)
  }, [])

  const blitToDisplay = useCallback((off: HTMLCanvasElement) => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")!
    ctx.drawImage(off, 0, 0)
  }, [])

  const redrawAll = useCallback(
    (strokeList: Stroke[], highlightIdx: number | null = null) => {
      const off = offscreenRef.current
      if (!off) return
      const ctx = off.getContext("2d")!
      ctx.fillStyle = "#f4eed8"
      ctx.fillRect(0, 0, CANVAS_W, CANVAS_H)
      for (const s of strokeList) {
        renderOutlines(ctx, s.outlines, s.params.color, s.params.opacity)
      }
      const hi = highlightIdx != null ? strokeList[highlightIdx] : null
      if (hi) {
        ctx.save()
        ctx.strokeStyle = "#e8a34a"
        ctx.lineWidth = 1.5
        ctx.setLineDash([5, 4])
        ctx.beginPath()
        ctx.moveTo(hi.centerline[0].x, hi.centerline[0].y)
        for (let i = 1; i < hi.centerline.length; i++) ctx.lineTo(hi.centerline[i].x, hi.centerline[i].y)
        ctx.stroke()
        ctx.restore()
      }
      blitToDisplay(off)
    },
    [blitToDisplay],
  )

  const appendStroke = useCallback(
    (stroke: Stroke) => {
      const off = offscreenRef.current
      if (!off) return
      const ctx = off.getContext("2d")!
      renderOutlines(ctx, stroke.outlines, stroke.params.color, stroke.params.opacity)
      blitToDisplay(off)
    },
    [blitToDisplay],
  )

  function canvasPoint(e: React.PointerEvent<HTMLCanvasElement>): Point {
    const canvas = canvasRef.current!
    const rect = canvas.getBoundingClientRect()
    return {
      x: ((e.clientX - rect.left) / rect.width) * CANVAS_W,
      y: ((e.clientY - rect.top) / rect.height) * CANVAS_H,
    }
  }

  function nearestStroke(pt: Point): number | null {
    let best: number | null = null
    let bestDist = 18
    strokes.forEach((s, idx) => {
      for (const c of s.centerline) {
        const d = Math.hypot(c.x - pt.x, c.y - pt.y)
        if (d < bestDist) {
          bestDist = d
          best = idx
        }
      }
    })
    return best
  }

  function handlePointerDown(e: React.PointerEvent<HTMLCanvasElement>) {
    const pt = canvasPoint(e)
    if (editMode) {
      const hit = nearestStroke(pt)
      setSelected(hit)
      redrawAll(strokes, hit)
      return
    }
    e.currentTarget.setPointerCapture(e.pointerId)
    setIsDrawing(true)
    currentPointsRef.current = [pt]
  }

  function handlePointerMove(e: React.PointerEvent<HTMLCanvasElement>) {
    if (!isDrawing) return
    const pt = canvasPoint(e)
    const pts = currentPointsRef.current
    const last = pts[pts.length - 1]
    if (Math.abs(pt.x - last.x) < 1.5 && Math.abs(pt.y - last.y) < 1.5) return
    pts.push(pt)

    // Show lightweight preview on display canvas (offscreen stays clean)
    const canvas = canvasRef.current
    const off = offscreenRef.current
    if (!canvas || !off) return
    const ctx = canvas.getContext("2d")!
    ctx.clearRect(0, 0, CANVAS_W, CANVAS_H)
    ctx.drawImage(off, 0, 0)
    ctx.save()
    ctx.globalAlpha = params.opacity * 0.55
    ctx.strokeStyle = params.color
    ctx.lineWidth = params.width * 0.55
    ctx.lineCap = "round"
    ctx.lineJoin = "round"
    ctx.beginPath()
    ctx.moveTo(pts[0].x, pts[0].y)
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y)
    ctx.stroke()
    ctx.restore()
  }

  function handlePointerUp() {
    if (!isDrawing) return
    setIsDrawing(false)
    const pts = currentPointsRef.current
    currentPointsRef.current = []
    if (pts.length < 2) {
      // single tap — draw a dot
      const off = offscreenRef.current
      if (!off) return
      const ctx = off.getContext("2d")!
      ctx.save()
      ctx.globalAlpha = params.opacity
      ctx.fillStyle = params.color
      ctx.beginPath()
      ctx.arc(pts[0]?.x ?? 0, pts[0]?.y ?? 0, params.width / 4, 0, Math.PI * 2)
      ctx.fill()
      ctx.restore()
      blitToDisplay(off)
      return
    }
    const centerline = resamplePolyline(pts, 2)
    const outlines = generateOutlines(centerline, params)
    const stroke: Stroke = { centerline, params: { ...params }, outlines }
    setStrokes((prev) => {
      const next = [...prev, stroke]
      appendStroke(stroke)
      return next
    })
  }

  function handleUndo() {
    if (selected != null && selected >= strokes.length - 1) setSelected(null)
    setStrokes((prev) => {
      const next = prev.slice(0, -1)
      redrawAll(next, selected != null && selected < next.length ? selected : null)
      return next
    })
  }

  function handleClear() {
    setStrokes([])
    setSelected(null)
    redrawAll([])
  }

  function handleExportSVG() {
    const svg = strokesToSVG(strokes, CANVAS_W, CANVAS_H)
    const blob = new Blob([svg], { type: "image/svg+xml" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "brush-strokes.svg"
    a.click()
    URL.revokeObjectURL(url)
  }

  function handleExportPNG() {
    const off = offscreenRef.current
    if (!off) return
    off.toBlob((blob) => {
      if (!blob) return
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = "brush-strokes.png"
      a.click()
      URL.revokeObjectURL(url)
    }, "image/png")
  }

  async function handleCopySVG() {
    const svg = strokesToSVG(strokes, CANVAS_W, CANVAS_H)
    try {
      await navigator.clipboard.writeText(svg)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    } catch {
      /* clipboard unavailable */
    }
  }

  async function handleConnectFigma() {
    if (!figmaTokenInput.trim()) return
    setFigmaConnecting(true)
    setFigmaError("")
    try {
      const res = await fetch("https://api.figma.com/v1/me", {
        headers: { "X-Figma-Token": figmaTokenInput.trim() },
      })
      if (!res.ok) throw new Error("bad token")
      const data = await res.json()
      setFigmaUser({ handle: data.handle, email: data.email })
      setShowFigmaPanel(false)
    } catch {
      setFigmaError("Token not recognised. Check it and try again.")
    }
    setFigmaConnecting(false)
  }

  const update = <K extends keyof BrushParams>(key: K, value: BrushParams[K]) => {
    setParams((p) => ({ ...p, [key]: value }))
    if (editMode && selected != null) {
      setStrokes((prev) => {
        const next = prev.map((s, i) => {
          if (i !== selected) return s
          const nextParams = { ...s.params, [key]: value }
          return { ...s, params: nextParams, outlines: generateOutlines(s.centerline, nextParams) }
        })
        redrawAll(next, selected)
        return next
      })
    }
  }

  return (
    <div className="flex flex-col h-full bg-[#141210] text-[#c8c4bc] select-none overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-5 py-2.5 border-b border-[#252220] shrink-0">
        <h1 className="font-display text-lg font-light text-[#f0e8d5] tracking-wide italic">
          Brush Strokes
        </h1>
        <div className="flex items-center gap-3">
          {figmaUser ? (
            <div className="flex items-center gap-3 text-xs">
              <span className="text-[#6a6560]">Figma</span>
              <span className="text-[#c8864a] font-medium">{figmaUser.handle}</span>
              <button
                onClick={() => setFigmaUser(null)}
                className="text-[#6a6560] hover:text-[#c8c4bc] transition-colors"
              >
                Disconnect
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowFigmaPanel((x) => !x)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs border transition-colors ${
                showFigmaPanel
                  ? "border-[#c8864a]/50 text-[#c8864a] bg-[#c8864a]/8"
                  : "border-[#252220] text-[#6a6560] hover:border-[#c8864a]/40 hover:text-[#c8864a]"
              }`}
            >
              <FigmaIcon />
              Connect Figma
            </button>
          )}
        </div>
      </header>

      {/* Figma auth drawer */}
      {showFigmaPanel && !figmaUser && (
        <div className="bg-[#1c1a17] border-b border-[#252220] px-5 py-4 shrink-0">
          <div className="max-w-md">
            <p className="text-[11px] text-[#6a6560] mb-3 leading-relaxed">
              Paste a Personal Access Token from{" "}
              <a
                href="https://www.figma.com/settings"
                target="_blank"
                rel="noopener"
                className="text-[#c8864a] hover:underline"
              >
                Figma Settings → Security
              </a>
              . Once connected, export SVG and paste it directly into any Figma file.
            </p>
            <div className="flex gap-2">
              <input
                type="password"
                value={figmaTokenInput}
                onChange={(e) => setFigmaTokenInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleConnectFigma()}
                placeholder="figd_••••••••"
                className="flex-1 bg-[#211f1c] border border-[#302e29] focus:border-[#c8864a]/60 rounded px-3 py-1.5 text-xs text-[#c8c4bc] placeholder-[#3e3b36] font-mono outline-none transition-colors"
              />
              <button
                onClick={handleConnectFigma}
                disabled={figmaConnecting || !figmaTokenInput.trim()}
                className="px-4 py-1.5 bg-[#c8864a] hover:bg-[#d99b62] text-[#141210] text-xs font-semibold rounded transition-colors disabled:opacity-40"
              >
                {figmaConnecting ? "Checking…" : "Connect"}
              </button>
            </div>
            {figmaError && (
              <p className="text-red-400/80 text-[11px] mt-2">{figmaError}</p>
            )}
          </div>
        </div>
      )}

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <aside className="w-52 shrink-0 flex flex-col border-r border-[#252220] bg-[#1a1814] overflow-y-auto">
          <div className="p-4 space-y-5 flex-1">
            {/* Brush list */}
            <section>
              <SectionLabel>Brush</SectionLabel>
              <div className="space-y-0.5 mt-2">
                {BRUSH_NAMES.map((name) => (
                  <button
                    key={name}
                    onClick={() => update("brush", name)}
                    className={`w-full text-left px-3 py-1.5 rounded text-xs transition-colors ${
                      params.brush === name
                        ? "bg-[#c8864a]/12 text-[#c8864a] ring-1 ring-inset ring-[#c8864a]/25"
                        : "text-[#6a6560] hover:text-[#c8c4bc] hover:bg-[#211f1c]"
                    }`}
                  >
                    {name}
                  </button>
                ))}
              </div>
            </section>

            {/* Width */}
            <section>
              <div className="flex justify-between items-baseline">
                <SectionLabel>Width</SectionLabel>
                <MonoValue>{params.width}px</MonoValue>
              </div>
              <input
                type="range"
                min="1"
                max="40"
                step="0.5"
                value={params.width}
                onChange={(e) => update("width", Number(e.target.value))}
                className="slider mt-2"
              />
            </section>

            {/* Color */}
            <section>
              <SectionLabel>Color</SectionLabel>
              <div className="flex items-center gap-2.5 mt-2">
                <div className="relative">
                  <div
                    className="w-7 h-7 rounded border border-[#302e29] cursor-pointer"
                    style={{ background: params.color }}
                  />
                  <input
                    type="color"
                    value={params.color}
                    onChange={(e) => update("color", e.target.value)}
                    className="absolute inset-0 opacity-0 w-full h-full cursor-pointer"
                  />
                </div>
                <MonoValue>{params.color.toUpperCase()}</MonoValue>
              </div>
            </section>

            {/* Opacity */}
            <section>
              <div className="flex justify-between items-baseline">
                <SectionLabel>Opacity</SectionLabel>
                <MonoValue>{Math.round(params.opacity * 100)}%</MonoValue>
              </div>
              <input
                type="range"
                min="0.05"
                max="1"
                step="0.05"
                value={params.opacity}
                onChange={(e) => update("opacity", Number(e.target.value))}
                className="slider mt-2"
              />
            </section>

            {/* Advanced */}
            <button
              onClick={() => setShowAdvanced((x) => !x)}
              className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-[#3e3b36] hover:text-[#6a6560] transition-colors"
            >
              <span className="text-[8px]">{showAdvanced ? "▾" : "▸"}</span>
              Advanced
            </button>

            {showAdvanced && (
              <div className="space-y-4">
                <section>
                  <div className="flex justify-between items-baseline">
                    <SectionLabel>Seed</SectionLabel>
                    <MonoValue>{params.seed}</MonoValue>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="9999"
                    step="1"
                    value={params.seed}
                    onChange={(e) => update("seed", Number(e.target.value))}
                    className="slider mt-2"
                  />
                </section>

                <section>
                  <div className="flex justify-between items-baseline">
                    <SectionLabel>Jitter</SectionLabel>
                    <MonoValue>
                      {params.jitterOverride < 0 ? "auto" : params.jitterOverride}
                    </MonoValue>
                  </div>
                  <input
                    type="range"
                    min="-1"
                    max="10"
                    step="0.5"
                    value={params.jitterOverride}
                    onChange={(e) => update("jitterOverride", Number(e.target.value))}
                    className="slider mt-2"
                  />
                </section>

                <section>
                  <div className="flex justify-between items-baseline">
                    <SectionLabel>Taper</SectionLabel>
                    <MonoValue>
                      {params.taperOverride < 0 ? "auto" : params.taperOverride}
                    </MonoValue>
                  </div>
                  <input
                    type="range"
                    min="-1"
                    max="1"
                    step="0.05"
                    value={params.taperOverride}
                    onChange={(e) => update("taperOverride", Number(e.target.value))}
                    className="slider mt-2"
                  />
                </section>
              </div>
            )}
          </div>

          {/* Action footer */}
          <div className="p-4 border-t border-[#252220] space-y-2 shrink-0">
            <button
              onClick={() => {
                const next = !editMode
                setEditMode(next)
                if (!next) {
                  setSelected(null)
                  redrawAll(strokes, null)
                }
              }}
              className={`w-full py-1.5 text-xs rounded border transition-colors ${
                editMode
                  ? "border-[#c8864a]/60 text-[#e8a34a] bg-[#c8864a]/10"
                  : "border-[#c8864a]/35 text-[#c8864a] hover:bg-[#c8864a]/8"
              }`}
            >
              {editMode ? (selected != null ? "Editing stroke " + (selected + 1) + " — sliders re-render it" : "Edit strokes: click one") : "Edit strokes"}
            </button>

            <div className="flex gap-2">
              <GhostButton onClick={handleUndo} disabled={strokes.length === 0}>
                Undo
              </GhostButton>
              <GhostButton
                onClick={handleClear}
                disabled={strokes.length === 0}
                danger
              >
                Clear
              </GhostButton>
            </div>

            <button
              onClick={handleExportSVG}
              disabled={strokes.length === 0}
              className="w-full py-1.5 text-xs rounded border border-[#c8864a]/35 text-[#c8864a] hover:bg-[#c8864a]/8 disabled:opacity-30 transition-colors"
            >
              Download SVG
            </button>

            <button
              onClick={handleExportPNG}
              disabled={strokes.length === 0}
              className="w-full py-1.5 text-xs rounded border border-[#252220] text-[#6a6560] hover:border-[#3e3b36] hover:text-[#c8c4bc] disabled:opacity-30 transition-colors"
            >
              Download PNG
            </button>

            <button
              onClick={handleCopySVG}
              disabled={strokes.length === 0}
              className={`w-full py-1.5 text-xs rounded border transition-colors disabled:opacity-30 ${
                copied
                  ? "border-emerald-800/60 text-emerald-400 bg-emerald-900/10"
                  : "border-[#252220] text-[#6a6560] hover:border-[#3e3b36] hover:text-[#c8c4bc]"
              }`}
            >
              {copied ? "Copied — paste into Figma" : "Copy SVG for Figma"}
            </button>

            {figmaUser && strokes.length > 0 && (
              <p className="text-[10px] text-[#6a6560] leading-relaxed pt-1">
                In Figma: Edit → Paste (⌘V) to import as vectors.
              </p>
            )}
          </div>
        </aside>

        {/* Canvas */}
        <main className="flex-1 flex items-center justify-center bg-[#0e0d0b] min-w-0">
          <div
            className="relative shadow-2xl"
            style={{
              maxHeight: "calc(100vh - 120px)",
              aspectRatio: `${CANVAS_W} / ${CANVAS_H}`,
              height: "100%",
            }}
          >
            <canvas
              ref={canvasRef}
              width={CANVAS_W}
              height={CANVAS_H}
              style={{
                width: "100%",
                height: "100%",
                display: "block",
                cursor: "crosshair",
                touchAction: "none",
              }}
              onPointerDown={handlePointerDown}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUp}
              onPointerLeave={handlePointerUp}
            />
            {strokes.length === 0 && (
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none gap-2">
                <p className="font-display text-3xl font-light italic text-[#b8aa8a]/25">
                  Draw here
                </p>
                <p className="text-[11px] text-[#b8aa8a]/18 font-sans tracking-wide">
                  mouse or touch · {CANVAS_W} × {CANVAS_H}
                </p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-[10px] uppercase tracking-widest text-[#3e3b36]">
      {children}
    </span>
  )
}

function MonoValue({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-[10px] font-mono text-[#6a6560]">{children}</span>
  )
}

function GhostButton({
  children,
  onClick,
  disabled,
  danger,
}: {
  children: React.ReactNode
  onClick: () => void
  disabled?: boolean
  danger?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex-1 py-1.5 text-xs rounded border transition-colors disabled:opacity-30 ${
        danger
          ? "border-[#252220] text-[#6a6560] hover:border-red-900/60 hover:text-red-400/80"
          : "border-[#252220] text-[#6a6560] hover:border-[#3e3b36] hover:text-[#c8c4bc]"
      }`}
    >
      {children}
    </button>
  )
}

function FigmaIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 38 57" fill="currentColor" aria-hidden="true">
      <path d="M19 28.5a9.5 9.5 0 1 1 19 0 9.5 9.5 0 0 1-19 0z" />
      <path d="M0 47.5A9.5 9.5 0 0 1 9.5 38H19v9.5a9.5 9.5 0 0 1-19 0z" />
      <path d="M19 0v19h9.5a9.5 9.5 0 0 0 0-19H19z" />
      <path d="M0 9.5A9.5 9.5 0 0 0 9.5 19H19V0H9.5A9.5 9.5 0 0 0 0 9.5z" />
      <path d="M0 28.5A9.5 9.5 0 0 0 9.5 38H19V19H9.5A9.5 9.5 0 0 0 0 28.5z" />
    </svg>
  )
}
