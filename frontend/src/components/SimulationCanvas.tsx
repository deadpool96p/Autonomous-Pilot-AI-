import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

interface SimulationCanvasProps {
  simulationId: string | null
  isRunning: boolean
  selectedTrack: string | null
  setStats: (stats: any) => void
}

const SimulationCanvas = ({ simulationId, isRunning, selectedTrack, setStats }: SimulationCanvasProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!isRunning || !simulationId) {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host;
    const ws = new WebSocket(`${protocol}//${wsHost}/ws/${simulationId}`)
    ws.onopen = () => console.log(`WebSocket Connected to ${simulationId}`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      renderFrame(data)
      const cars = data.cars || []
      const peakProgress = cars.length > 0 ? Math.max(...cars.map((c: any) => c.progress || 0)) : 0
      setStats({
        generation: data.generation,
        alive: cars.filter((c: any) => c.alive).length,
        bestFitness: peakProgress * 100,
        progress: peakProgress
      })
    }
    ws.onerror = (err) => console.error("WebSocket Error:", err);
    ws.onclose = () => console.log("WebSocket Disconnected");
    wsRef.current = ws

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [isRunning, simulationId])

  const [trackData, setTrackData] = useState<any>(null)

  const carImage = useRef<HTMLImageElement | null>(null);

  useEffect(() => {
    const img = new Image();
    img.src = '/car.png';
    img.onload = () => { carImage.current = img; };
  }, []);

  useEffect(() => {
    if (selectedTrack) {
      console.log(`Fetching track data for: ${selectedTrack}`);
      axios.get(`/api/tracks/`).then(res => {
        console.log("Available tracks:", res.data.map((t: any) => t.id));
        const track = res.data.find((t: any) => t.id === selectedTrack) || res.data[0];
        if (track) {
            console.log("Selected track data loaded:", track.id);
            setTrackData(track.json_data);
            setTimeout(() => renderFrame({ cars: [] }), 100);
        } else {
            console.error("No tracks found on backend!");
        }
      }).catch(err => console.error("Error fetching tracks:", err));
    }
  }, [selectedTrack])

  const renderFrame = (data: any) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear background
    ctx.fillStyle = '#020617'; // Even deeper background
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (!trackData) {
        ctx.fillStyle = 'white';
        ctx.font = '20px Arial';
        ctx.fillText("Loading Track...", 400, 400);
        return;
    }

    // Draw Track
    if (trackData) {
      if (trackData.road_boundaries) {
        trackData.road_boundaries.forEach((points: any[], index: number) => {
          ctx.fillStyle = index === 0 ? '#1e293b' : '#020617'; 
          ctx.beginPath();
          ctx.moveTo(points[0][0], points[0][1]);
          points.forEach((p: any) => ctx.lineTo(p[0], p[1]));
          ctx.closePath();
          ctx.fill();
          
          ctx.strokeStyle = '#334155';
          ctx.lineWidth = 3;
          ctx.stroke();
        });
      }

      // Draw Checkpoints
      if (trackData.checkpoints) {
        trackData.checkpoints.forEach((cp: any) => {
          ctx.strokeStyle = 'rgba(234, 179, 8, 0.1)';
          ctx.beginPath();
          ctx.moveTo(cp.start[0], cp.start[1]);
          ctx.lineTo(cp.end[0], cp.end[1]);
          ctx.stroke();
        });
      }

      // Draw Obstacles
      if (trackData.obstacles) {
        ctx.fillStyle = '#ef4444';
        trackData.obstacles.forEach((obs: any) => {
            ctx.beginPath();
            ctx.moveTo(obs.points[0][0], obs.points[0][1]);
            obs.points.forEach((p: any) => ctx.lineTo(p[0], p[1]));
            ctx.closePath();
            ctx.fill();
        });
      }
    }

    // Draw Cars
    if (data.cars) {
      data.cars.forEach((car: any) => {
        ctx.save();
        ctx.translate(car.pos.x, car.pos.y);
        ctx.rotate(-car.angle * Math.PI / 180 + Math.PI/2); // Sprite is vertical
        
        if (carImage.current) {
            ctx.drawImage(carImage.current, -10, -20, 20, 40);
        } else {
            ctx.fillStyle = car.alive ? '#10b981' : '#dc2626';
            ctx.fillRect(-10, -20, 20, 40);
        }
        ctx.restore();
        
        // Sensors
        if (car.alive && car.sensors) {
          const start_angle = (car.angle - 45) * (Math.PI / 180);
          const step = (90 / (car.sensors.length - 1)) * (Math.PI / 180);
          
          car.sensors.forEach((dist: number, i: number) => {
            const angle = start_angle + (i * step);
            const end_x = car.pos.x + Math.cos(angle) * dist;
            const end_y = car.pos.y - Math.sin(angle) * dist;
            
            ctx.strokeStyle = `rgba(34, 211, 238, ${0.1 + (1 - dist/150) * 0.4})`;
            ctx.beginPath();
            ctx.moveTo(car.pos.x, car.pos.y);
            ctx.lineTo(end_x, end_y);
            ctx.stroke();
            
            if (dist < 150) {
              ctx.fillStyle = '#22d3ee';
              ctx.beginPath();
              ctx.arc(end_x, end_y, 2, 0, Math.PI * 2);
              ctx.fill();
            }
          });
        }
      });

      // Overlay Telemetry
      ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
      ctx.fillRect(10, 10, 220, 80);
      ctx.fillStyle = '#f8fafc';
      ctx.font = 'bold 14px Inter';
      ctx.fillText(`Generation: ${data.generation}`, 20, 35);
      const aliveCount = data.cars.filter((c: any) => c.alive).length;
      ctx.fillText(`Alive: ${aliveCount} / ${data.cars.length}`, 20, 55);
      const bestProgress = Math.max(...data.cars.map((c: any) => c.progress || 0));
      ctx.fillText(`Best Progress: ${(bestProgress * 100).toFixed(1)}%`, 20, 75);
    }
  }

  return (
    <canvas 
      ref={canvasRef} 
      width={1000} 
      height={800} 
      className="h-full w-full object-contain"
    />
  )
}

export default SimulationCanvas
