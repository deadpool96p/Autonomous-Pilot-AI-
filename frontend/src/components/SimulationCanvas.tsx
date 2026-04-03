import { useState, useEffect, useRef, useCallback } from 'react'
import axios from 'axios'

interface SimulationCanvasProps {
  simulationId: string | null
  isRunning: boolean
  selectedTrack: string | null
  setStats: (stats: any) => void
  showDynamicObjects: boolean
  showLanes?: boolean
  showLookahead?: boolean
  onCameraReset?: () => void
}

interface Camera {
  x: number
  y: number
  zoom: number
}

const SimulationCanvas = ({ 
  simulationId, isRunning, selectedTrack, 
  setStats, showDynamicObjects, showLanes, showLookahead 
}: SimulationCanvasProps) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const latestState = useRef<any>(null)
  const requestRef = useRef<number>()
  const [trackData, setTrackData] = useState<any>(null)
  const [canvasSize, setCanvasSize] = useState({ w: 1600, h: 900 })
  
  // Camera system
  const cameraRef = useRef<Camera>({ x: 0, y: 0, zoom: 1 })
  const isPanning = useRef(false)
  const panStart = useRef({ x: 0, y: 0 })
  const [zoomLevel, setZoomLevel] = useState(1)

  // 0. Responsive resize
  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        if (width > 0 && height > 0) {
          setCanvasSize({ w: Math.floor(width), h: Math.floor(height) })
        }
      }
    })
    ro.observe(container)
    return () => ro.disconnect()
  }, [])

  // Auto-fit camera when track data changes
  const fitCameraToTrack = useCallback((track: any) => {
    if (!track || !canvasRef.current) return
    
    // Calculate track bounds from road data
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
    
    const processPoints = (points: number[][]) => {
      points.forEach(([x, y]) => {
        minX = Math.min(minX, x)
        minY = Math.min(minY, y)
        maxX = Math.max(maxX, x)
        maxY = Math.max(maxY, y)
      })
    }
    
    track.roads?.forEach((road: any) => {
      if (road.points) processPoints(road.points)
    })
    track.buildings?.forEach((b: any) => {
      if (b.points) processPoints(b.points)
    })
    track.lanes?.forEach((lane: any) => {
      if (lane.left_boundary) processPoints(lane.left_boundary)
      if (lane.right_boundary) processPoints(lane.right_boundary)
      if (lane.center_line) processPoints(lane.center_line)
    })
    
    if (minX === Infinity) {
      // Fallback
      minX = 0; minY = 0; maxX = 1000; maxY = 800
    }

    const trackW = maxX - minX
    const trackH = maxY - minY
    const padding = 60
    const { w, h } = canvasSize
    
    const scaleX = (w - padding * 2) / trackW
    const scaleY = (h - padding * 2) / trackH
    const zoom = Math.min(scaleX, scaleY, 3) // Cap at 3x zoom
    
    const centerX = (minX + maxX) / 2
    const centerY = (minY + maxY) / 2
    
    cameraRef.current = {
      x: w / 2 - centerX * zoom,
      y: h / 2 - centerY * zoom,
      zoom: zoom
    }
    setZoomLevel(zoom)
  }, [canvasSize])

  // Mouse interaction for pan/zoom
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    
    const handleWheel = (e: WheelEvent) => {
      e.preventDefault()
      const rect = canvas.getBoundingClientRect()
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top
      
      const cam = cameraRef.current
      const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9
      const newZoom = Math.max(0.05, Math.min(10, cam.zoom * zoomFactor))
      
      // Zoom toward mouse position
      cam.x = mouseX - (mouseX - cam.x) * (newZoom / cam.zoom)
      cam.y = mouseY - (mouseY - cam.y) * (newZoom / cam.zoom)
      cam.zoom = newZoom
      setZoomLevel(newZoom)
    }
    
    const handleMouseDown = (e: MouseEvent) => {
      if (e.button === 0 || e.button === 1) { // Left or middle click
        isPanning.current = true
        panStart.current = { x: e.clientX - cameraRef.current.x, y: e.clientY - cameraRef.current.y }
        canvas.style.cursor = 'grabbing'
      }
    }
    
    const handleMouseMove = (e: MouseEvent) => {
      if (isPanning.current) {
        cameraRef.current.x = e.clientX - panStart.current.x
        cameraRef.current.y = e.clientY - panStart.current.y
      }
    }
    
    const handleMouseUp = () => {
      isPanning.current = false
      canvas.style.cursor = 'grab'
    }
    
    canvas.addEventListener('wheel', handleWheel, { passive: false })
    canvas.addEventListener('mousedown', handleMouseDown)
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
    canvas.style.cursor = 'grab'
    
    return () => {
      canvas.removeEventListener('wheel', handleWheel)
      canvas.removeEventListener('mousedown', handleMouseDown)
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [])

  // 1. Smooth Animation Loop
  const animate = () => {
    const canvas = canvasRef.current
    if (canvas) {
      if (trackData) {
        renderSimulation(canvas, latestState.current, trackData)
      } else {
        // Draw empty state with grid
        const ctx = canvas.getContext('2d')
        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height)
          drawGrid(ctx, canvas.width, canvas.height)
        }
      }
    }
    requestRef.current = requestAnimationFrame(animate)
  }

  useEffect(() => {
    requestRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(requestRef.current!)
  }, [trackData])

  // 2. WebSocket Connection
  useEffect(() => {
    if (!isRunning || !simulationId) {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${simulationId}`;
    console.log("[WS] Connecting to:", wsUrl);
    
    const socket = new WebSocket(wsUrl);
    wsRef.current = socket

    socket.onopen = () => {
      console.log("[WS] Connected");
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "heartbeat" || data.type === "pong") return;
        
        if (data.cars) {
          latestState.current = data;
          
          const aliveCount = data.cars.filter((c: any) => c.alive).length;
          const bestFitness = data.cars.length > 0 ? Math.max(...data.cars.map((c: any) => c.fitness || 0)) : 0;
          
          setStats({
            generation: data.generation,
            alive: aliveCount,
            bestFitness: bestFitness,
            pedestrianHits: data.stats?.pedestrian_hits || 0,
            npcHits: data.stats?.npc_hits || 0,
            boundary_hits: data.stats?.boundary_hits || 0,
            clean_laps: data.stats?.clean_laps || 0,
            autoLearning: data.auto_learning
          });
        }
      } catch (err) {
        console.error("[WS] Error parsing message:", err);
      }
    }

    socket.onerror = (err) => console.error("[WS] Socket error:", err);
    socket.onclose = () => console.log("[WS] Socket closed");

    return () => {
      console.log("[WS] Cleaning up socket");
      if (socket.readyState === 1) socket.close();
      wsRef.current = null;
    }
  }, [isRunning, simulationId, setStats])

  // 3. Track Loading
  useEffect(() => {
    if (selectedTrack) {
      console.log("[API] Fetching track:", selectedTrack);
      axios.get(`/api/tracks/`).then(res => {
        const track = res.data.find((t: any) => String(t.id) === String(selectedTrack));
        if (track) {
          console.log("[API] Track data loaded for:", track.name);
          setTrackData(track.json_data);
          // Auto-fit camera to new track
          setTimeout(() => fitCameraToTrack(track.json_data), 50)
        } else {
          console.warn("[API] Selected track not found in list:", selectedTrack);
        }
      }).catch(err => console.error("[API] Error fetching tracks:", err));
    }
  }, [selectedTrack, fitCameraToTrack])
  
  // Re-fit when canvas resizes
  useEffect(() => {
    if (trackData) {
      fitCameraToTrack(trackData)
    }
  }, [canvasSize, trackData, fitCameraToTrack])

  // Drawing helpers
  const drawGrid = (ctx: CanvasRenderingContext2D, w: number, h: number) => {
    const cam = cameraRef.current
    const gridSize = 100
    
    ctx.save()
    ctx.strokeStyle = "rgba(30, 41, 59, 0.5)"
    ctx.lineWidth = 0.5
    
    const startX = Math.floor(-cam.x / cam.zoom / gridSize) * gridSize
    const startY = Math.floor(-cam.y / cam.zoom / gridSize) * gridSize
    const endX = startX + w / cam.zoom + gridSize * 2
    const endY = startY + h / cam.zoom + gridSize * 2
    
    for (let x = startX; x < endX; x += gridSize) {
      const sx = x * cam.zoom + cam.x
      ctx.beginPath()
      ctx.moveTo(sx, 0)
      ctx.lineTo(sx, h)
      ctx.stroke()
    }
    for (let y = startY; y < endY; y += gridSize) {
      const sy = y * cam.zoom + cam.y
      ctx.beginPath()
      ctx.moveTo(0, sy)
      ctx.lineTo(w, sy)
      ctx.stroke()
    }
    ctx.restore()
  }

  // 4. Dedicated Render Function  
  const renderSimulation = (canvas: HTMLCanvasElement, state: any, track: any) => {
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const cam = cameraRef.current

    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // Draw grid
    drawGrid(ctx, canvas.width, canvas.height)
    
    // Apply camera transform
    ctx.save()
    ctx.translate(cam.x, cam.y)
    ctx.scale(cam.zoom, cam.zoom)
    
    // ═══ Draw Roads (visible road surface) ═══
    track.roads?.forEach((road: any) => {
      if (!road.points || road.points.length < 2) return
      
      // Road outline (edge/curb)
      ctx.beginPath()
      ctx.moveTo(road.points[0][0], road.points[0][1])
      road.points.slice(1).forEach((p: any) => ctx.lineTo(p[0], p[1]))
      ctx.strokeStyle = "#475569"
      ctx.lineWidth = (road.width || 15) + 4
      ctx.lineCap = "round"
      ctx.lineJoin = "round"
      ctx.stroke()
      
      // Road surface (dark asphalt)
      ctx.beginPath()
      ctx.moveTo(road.points[0][0], road.points[0][1])
      road.points.slice(1).forEach((p: any) => ctx.lineTo(p[0], p[1]))
      ctx.strokeStyle = "#1e293b"
      ctx.lineWidth = road.width || 15
      ctx.lineCap = "round"
      ctx.lineJoin = "round"
      ctx.stroke()
      
      // Center dashed line
      ctx.beginPath()
      ctx.moveTo(road.points[0][0], road.points[0][1])
      road.points.slice(1).forEach((p: any) => ctx.lineTo(p[0], p[1]))
      ctx.strokeStyle = "rgba(250, 204, 21, 0.4)"
      ctx.lineWidth = 1.5
      ctx.setLineDash([8, 12])
      ctx.stroke()
      ctx.setLineDash([])
    })

    // ═══ Draw Buildings ═══
    track.buildings?.forEach((building: any) => {
      if (!building.points || building.points.length < 3) return
      ctx.beginPath()
      ctx.moveTo(building.points[0][0], building.points[0][1])
      building.points.slice(1).forEach((p: any) => ctx.lineTo(p[0], p[1]))
      ctx.closePath()
      
      // Building fill with gradient effect
      ctx.fillStyle = "rgba(51, 65, 85, 0.6)"
      ctx.fill()
      ctx.strokeStyle = "rgba(148, 163, 184, 0.4)"
      ctx.lineWidth = 1
      ctx.stroke()
      
      // Building "roof" highlight
      ctx.fillStyle = "rgba(71, 85, 105, 0.3)"
      ctx.fill()
    })

    // ═══ Draw HD Lanes ═══
    if (showLanes !== false) {
      track.lanes?.forEach((lane: any) => {
        // Left boundary
        if (lane.left_boundary && lane.left_boundary.length > 0) {
          ctx.beginPath()
          ctx.moveTo(lane.left_boundary[0][0], lane.left_boundary[0][1])
          lane.left_boundary.slice(1).forEach((p: any) => ctx.lineTo(p[0], p[1]))
          ctx.strokeStyle = lane.markings?.includes("solid_white") ? "#ffffff" : "rgba(203, 213, 225, 0.7)"
          ctx.setLineDash(lane.markings?.includes("dashed") ? [10, 10] : [])
          ctx.lineWidth = 1.5
          ctx.stroke()
          ctx.setLineDash([])
        }
        // Right boundary
        if (lane.right_boundary && lane.right_boundary.length > 0) {
          ctx.beginPath()
          ctx.moveTo(lane.right_boundary[0][0], lane.right_boundary[0][1])
          lane.right_boundary.slice(1).forEach((p: any) => ctx.lineTo(p[0], p[1]))
          ctx.strokeStyle = "rgba(255, 255, 255, 0.7)"
          ctx.lineWidth = 1.5
          ctx.stroke()
        }
        // Center line
        if (lane.center_line && lane.center_line.length > 0) {
          ctx.beginPath()
          ctx.moveTo(lane.center_line[0][0], lane.center_line[0][1])
          lane.center_line.slice(1).forEach((p: any) => ctx.lineTo(p[0], p[1]))
          ctx.strokeStyle = "#eab308"
          ctx.setLineDash([8, 12])
          ctx.lineWidth = 1.5
          ctx.stroke()
          ctx.setLineDash([])
        }
      })
    }

    // ═══ Draw Checkpoints ═══
    track.checkpoints?.forEach((cp: any) => {
      if (cp.points && cp.points.length === 2) {
        ctx.beginPath()
        ctx.moveTo(cp.points[0][0], cp.points[0][1])
        ctx.lineTo(cp.points[1][0], cp.points[1][1])
        ctx.strokeStyle = "rgba(16, 185, 129, 0.3)"
        ctx.lineWidth = 2
        ctx.setLineDash([4, 6])
        ctx.stroke()
        ctx.setLineDash([])
      }
    })

    // ═══ Draw Traffic Signs ═══
    track.traffic_signs?.forEach((sign: any) => {
      ctx.save()
      ctx.translate(sign.position[0], sign.position[1])
      const signScale = 1 / Math.max(cam.zoom * 0.5, 0.3) // Keep signs readable
      ctx.scale(Math.min(signScale, 2), Math.min(signScale, 2))
      
      if (sign.type === "stop") {
        ctx.fillStyle = "#ef4444"
        ctx.beginPath()
        ctx.arc(0, 0, 6, 0, Math.PI * 2)
        ctx.fill()
        ctx.fillStyle = "white"
        ctx.font = "bold 4px Arial"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.fillText("STOP", 0, 0)
      } else if (sign.type?.includes("speed_limit")) {
        ctx.fillStyle = "white"
        ctx.beginPath()
        ctx.arc(0, 0, 6, 0, Math.PI * 2)
        ctx.fill()
        ctx.strokeStyle = "#ef4444"
        ctx.lineWidth = 1.5
        ctx.stroke()
        ctx.fillStyle = "black"
        ctx.font = "bold 5px Arial"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.fillText(sign.value?.toString() || "30", 0, 0)
      } else {
        ctx.fillStyle = "#eab308"
        ctx.beginPath()
        ctx.moveTo(0, -6)
        ctx.lineTo(6, 6)
        ctx.lineTo(-6, 6)
        ctx.closePath()
        ctx.fill()
      }
      ctx.restore()
    })

    // ═══ Draw Start Position Marker ═══
    if (track.start_pos) {
      ctx.save()
      ctx.translate(track.start_pos[0], track.start_pos[1])
      
      // Pulsing ring
      const pulse = (Math.sin(Date.now() / 400) + 1) * 0.5
      ctx.strokeStyle = `rgba(59, 130, 246, ${0.3 + pulse * 0.4})`
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.arc(0, 0, 10 + pulse * 4, 0, Math.PI * 2)
      ctx.stroke()
      
      // Center dot
      ctx.fillStyle = "#3b82f6"
      ctx.beginPath()
      ctx.arc(0, 0, 4, 0, Math.PI * 2)
      ctx.fill()
      
      // "S" label
      ctx.fillStyle = "white"
      ctx.font = "bold 6px Arial"
      ctx.textAlign = "center"
      ctx.textBaseline = "middle"
      ctx.fillText("S", 0, 0)
      ctx.restore()
    }

    // ═══ Draw Dynamic Objects (NPCs, Pedestrians) ═══
    if (showDynamicObjects && state) {
      state.dynamic_objects?.forEach((obj: any) => {
        ctx.save()
        ctx.translate(obj.x, obj.y)
        ctx.rotate(obj.angle)
        
        if (obj.type === "pedestrian") {
          // Glow effect
          ctx.shadowColor = "#ff9f43"
          ctx.shadowBlur = 6
          ctx.fillStyle = "#ff9f43"
          ctx.beginPath()
          ctx.arc(0, 0, 4, 0, Math.PI * 2)
          ctx.fill()
          ctx.shadowBlur = 0
        } else {
          ctx.fillStyle = "#54a0ff"
          ctx.fillRect(-18, -9, 36, 18)
          ctx.fillStyle = "#2e86de"
          ctx.fillRect(8, -7, 4, 14)
          // Headlights
          ctx.fillStyle = "#fcd34d"
          ctx.fillRect(17, -6, 2, 4)
          ctx.fillRect(17, 2, 2, 4)
        }
        ctx.restore()
      })
    }

    // ═══ Draw Main Cars ═══
    if (state) {
      state.cars?.forEach((car: any) => {
        if (!car.alive) return
        
        ctx.save()
        ctx.translate(car.x, car.y)
        ctx.rotate(car.angle)
        
        // Car shadow
        ctx.fillStyle = "rgba(0, 0, 0, 0.3)"
        ctx.fillRect(-19, -9, 40, 20)
        
        // Body
        const carColor = state.mode === "ga" ? "#ef4444" : state.mode === "pid" ? "#8b5cf6" : "#10ac84"
        ctx.fillStyle = carColor
        ctx.fillRect(-20, -10, 40, 20)
        
        // Roof
        ctx.fillStyle = "rgba(0, 0, 0, 0.2)"
        ctx.fillRect(-8, -7, 16, 14)
        
        // Front marker (headlights)
        ctx.fillStyle = "#fcd34d"
        ctx.fillRect(17, -8, 3, 6)
        ctx.fillRect(17, 2, 3, 6)
        
        // Tail lights
        ctx.fillStyle = "#ef4444"
        ctx.fillRect(-20, -8, 2, 5)
        ctx.fillRect(-20, 3, 2, 5)
        
        // Sensor Rays
        if (car.sensors) {
          ctx.strokeStyle = "rgba(46, 213, 115, 0.35)"
          ctx.lineWidth = 0.8
          car.sensors.forEach((dist: number, i: number) => {
            const spread = (160 * Math.PI) / 180
            const startAngle = -spread / 2
            const step = spread / (car.sensors.length - 1)
            const angle = startAngle + i * step
            
            ctx.beginPath()
            ctx.moveTo(0, 0)
            ctx.lineTo(Math.cos(angle) * dist, Math.sin(angle) * dist)
            ctx.stroke()
          })
          
          // Sensor endpoints
          ctx.fillStyle = "rgba(46, 213, 115, 0.6)"
          car.sensors.forEach((dist: number, i: number) => {
            const spread = (160 * Math.PI) / 180
            const startAngle = -spread / 2
            const step = spread / (car.sensors.length - 1)
            const angle = startAngle + i * step
            ctx.beginPath()
            ctx.arc(Math.cos(angle) * dist, Math.sin(angle) * dist, 1.5, 0, Math.PI * 2)
            ctx.fill()
          })
        }
        
        ctx.restore()
      })
    }
    
    // Restore from camera transform
    ctx.restore()
    
    // ═══ HUD Overlay (not affected by camera) ═══
    drawHUD(ctx, canvas.width, canvas.height, state)
  }

  const roundedRect = (ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) => {
    ctx.beginPath()
    ctx.moveTo(x + r, y)
    ctx.lineTo(x + w - r, y)
    ctx.quadraticCurveTo(x + w, y, x + w, y + r)
    ctx.lineTo(x + w, y + h - r)
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
    ctx.lineTo(x + r, y + h)
    ctx.quadraticCurveTo(x, y + h, x, y + h - r)
    ctx.lineTo(x, y + r)
    ctx.quadraticCurveTo(x, y, x + r, y)
    ctx.closePath()
  }

  const drawHUD = (ctx: CanvasRenderingContext2D, w: number, h: number, state: any) => {
    const cam = cameraRef.current
    
    // Zoom indicator (top-right)
    ctx.save()
    ctx.fillStyle = "rgba(0, 0, 0, 0.5)"
    roundedRect(ctx, w - 120, 12, 108, 28, 6)
    ctx.fill()
    ctx.fillStyle = "#94a3b8"
    ctx.font = "11px 'Inter', monospace"
    ctx.textAlign = "right"
    ctx.textBaseline = "middle"
    ctx.fillText(`Zoom: ${(cam.zoom * 100).toFixed(0)}%`, w - 18, 26)
    
    // Alive cars count (top-left in viewport)
    if (state?.cars) {
      const alive = state.cars.filter((c: any) => c.alive).length
      const total = state.cars.length
      
      ctx.fillStyle = "rgba(0, 0, 0, 0.5)"
      roundedRect(ctx, 12, 12, 130, 28, 6)
      ctx.fill()
      
      // Active indicator
      ctx.fillStyle = alive > 0 ? "#22c55e" : "#ef4444"
      ctx.beginPath()
      ctx.arc(26, 26, 4, 0, Math.PI * 2)
      ctx.fill()
      
      ctx.fillStyle = "#e2e8f0"
      ctx.font = "11px 'Inter', sans-serif"
      ctx.textAlign = "left"
      ctx.fillText(`${alive}/${total} agents active`, 36, 27)
    }
    
    // Mode badge (top-center)
    if (state?.mode) {
      const modeLabel = state.mode === "ga" ? "EVOLUTION (GA)" : state.mode === "dl" ? "DEEP LEARNING" : "PID CONTROL"
      const modeColor = state.mode === "ga" ? "#ef4444" : state.mode === "dl" ? "#10b981" : "#8b5cf6"
      const labelW = ctx.measureText(modeLabel).width + 24
      
      ctx.fillStyle = "rgba(0, 0, 0, 0.5)"
      roundedRect(ctx, w / 2 - labelW / 2, 12, labelW, 24, 6)
      ctx.fill()
      
      ctx.strokeStyle = modeColor
      ctx.lineWidth = 1
      roundedRect(ctx, w / 2 - labelW / 2, 12, labelW, 24, 6)
      ctx.stroke()
      
      ctx.fillStyle = modeColor
      ctx.font = "bold 10px 'Inter', monospace"
      ctx.textAlign = "center"
      ctx.textBaseline = "middle"
      ctx.fillText(modeLabel, w / 2, 24)
    }
    
    ctx.restore()
  }

  // Expose fit function for external use
  const handleDoubleClick = () => {
    if (trackData) {
      fitCameraToTrack(trackData)
    }
  }

  return (
    <div 
      ref={containerRef} 
      className="relative w-full h-full bg-slate-950 overflow-hidden"
      id="simulation-viewport"
    >
      <canvas
        ref={canvasRef}
        width={canvasSize.w}
        height={canvasSize.h}
        className="w-full h-full"
        onDoubleClick={handleDoubleClick}
      />
      {!isRunning && !trackData && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-sm gap-4">
          <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-blue-400">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <p className="text-slate-400 font-semibold text-base">Select a track to begin</p>
          <p className="text-slate-600 text-sm">Choose from the available tracks in the sidebar</p>
        </div>
      )}
      {trackData && !isRunning && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="bg-slate-900/70 backdrop-blur-sm rounded-xl px-6 py-3 border border-slate-700/50">
            <p className="text-slate-300 font-medium text-sm">Track loaded — Press <span className="text-blue-400">Start</span> to begin simulation</p>
          </div>
        </div>
      )}
      
      {/* Camera control hint */}
      <div className="absolute bottom-2 right-3 text-[10px] text-slate-600 space-x-3 pointer-events-none select-none">
        <span>Scroll: Zoom</span>
        <span>Drag: Pan</span>
        <span>DblClick: Fit</span>
      </div>
    </div>
  )
}

export default SimulationCanvas
