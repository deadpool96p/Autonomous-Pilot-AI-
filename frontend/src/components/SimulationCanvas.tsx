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

  // 1. Smooth Animation Loop
  const animate = () => {
    if (latestState.current && canvasRef.current && trackData) {
      renderSimulation(canvasRef.current, latestState.current, trackData)
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

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.cars) {
          latestState.current = data;
          
          // Update parent stats periodically or every frame
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
        } else {
          console.warn("[API] Selected track not found in list:", selectedTrack);
        }
      }).catch(err => console.error("[API] Error fetching tracks:", err));
    }
  }, [selectedTrack])

  // 4. Dedicated Render Function
  const renderSimulation = (canvas: HTMLCanvasElement, state: any, track: any) => {
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // Draw Roads
    track.roads?.forEach((road: any) => {
      ctx.beginPath()
      ctx.moveTo(road.points[0][0], road.points[0][1])
      road.points.slice(1).forEach((p: any) => ctx.lineTo(p[0], p[1]))
      // If road is specified as a polygon-like shape
      ctx.strokeStyle = "#475569"
      ctx.lineWidth = road.width || 15
      ctx.lineCap = "round"
      ctx.lineJoin = "round"
      ctx.stroke()
      
      // Paint the surface
      ctx.strokeStyle = "#1e293b"
      ctx.lineWidth = (road.width || 15) * 0.95
      ctx.stroke()
    })

    // Draw Buildings
    track.buildings?.forEach((building: any) => {
      if (!building.points || building.points.length < 3) return
      ctx.beginPath()
      ctx.moveTo(building.points[0][0], building.points[0][1])
      building.points.slice(1).forEach((p: any) => ctx.lineTo(p[0], p[1]))
      ctx.closePath()
      ctx.fillStyle = "rgba(71, 85, 105, 0.4)"
      ctx.fill()
      ctx.strokeStyle = "rgba(148, 163, 184, 0.5)"
      ctx.lineWidth = 1
      ctx.stroke()
    })

    // Draw HD Lanes
    track.lanes?.forEach((lane: any) => {
      // Draw left boundary
      if (lane.left_boundary && lane.left_boundary.length > 0) {
        ctx.beginPath()
        ctx.moveTo(lane.left_boundary[0][0], lane.left_boundary[0][1])
        lane.left_boundary.slice(1).forEach((p: any) => ctx.lineTo(p[0], p[1]))
        ctx.strokeStyle = lane.markings?.includes("solid_white") ? "#ffffff" : "#cbd5e1"
        ctx.setLineDash(lane.markings?.includes("dashed") ? [10, 10] : [])
        ctx.lineWidth = 1.5
        ctx.stroke()
        ctx.setLineDash([])
      }
      // Draw right boundary
      if (lane.right_boundary && lane.right_boundary.length > 0) {
        ctx.beginPath()
        ctx.moveTo(lane.right_boundary[0][0], lane.right_boundary[0][1])
        lane.right_boundary.slice(1).forEach((p: any) => ctx.lineTo(p[0], p[1]))
        ctx.strokeStyle = "#ffffff"
        ctx.lineWidth = 1.5
        ctx.stroke()
      }
      // Draw center line
      if (lane.center_line && lane.center_line.length > 0) {
        ctx.beginPath()
        ctx.moveTo(lane.center_line[0][0], lane.center_line[0][1])
        lane.center_line.slice(1).forEach((p: any) => ctx.lineTo(p[0], p[1]))
        ctx.strokeStyle = "#eab308" // yellow
        ctx.setLineDash([8, 12])
        ctx.lineWidth = 1.5
        ctx.stroke()
        ctx.setLineDash([])
      }
    })

    // Draw Traffic Signs
    track.traffic_signs?.forEach((sign: any) => {
      ctx.save()
      ctx.translate(sign.position[0], sign.position[1])
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

    // Draw Dynamic Objects (NPCs, Pedestrians)
    if (showDynamicObjects) {
      state.dynamic_objects?.forEach((obj: any) => {
        ctx.save()
        ctx.translate(obj.x, obj.y)
        ctx.rotate(obj.angle)
        
        if (obj.type === "pedestrian") {
          ctx.fillStyle = "#ff9f43" // Orange for pedestrians
          ctx.beginPath()
          ctx.arc(0, 0, 4, 0, Math.PI * 2)
          ctx.fill()
        } else {
          ctx.fillStyle = "#54a0ff" // Light blue for NPC cars
          ctx.fillRect(-18, -9, 36, 18)
          ctx.fillStyle = "#2e86de" // Darker blue cap
          ctx.fillRect(8, -7, 4, 14)
        }
        ctx.restore()
      })
    }

    // Draw Main Cars
    state.cars?.forEach((car: any) => {
      if (!car.alive) return
      
      ctx.save()
      ctx.translate(car.x, car.y)
      ctx.rotate(car.angle)
      
      // Body
      ctx.fillStyle = state.mode === "ga" ? "#ee5253" : "#10ac84"
      ctx.fillRect(-20, -10, 40, 20)
      
      // Front marker
      ctx.fillStyle = "#fff"
      ctx.fillRect(15, -8, 5, 16)
      
      // Sensor Rays
      if (car.sensors) {
        ctx.strokeStyle = "rgba(46, 213, 115, 0.4)"
        ctx.lineWidth = 1
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
      }
      
      ctx.restore()
    })
  }

  return (
    <div ref={containerRef} className="relative w-full h-full bg-slate-900 rounded-2xl overflow-hidden border border-slate-700 shadow-2xl">
      <canvas
        ref={canvasRef}
        width={canvasSize.w}
        height={canvasSize.h}
        className="w-full h-full"
      />
      {!isRunning && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
          <p className="text-slate-400 font-bold text-lg">Select a track and press Start Simulation</p>
        </div>
      )}
    </div>
  )
}

export default SimulationCanvas
