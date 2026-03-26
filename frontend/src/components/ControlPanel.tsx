import { useState, useEffect } from 'react'
import { Play, Square, RefreshCw, Map as MapIcon } from 'lucide-react'
import axios from 'axios'

interface ControlPanelProps {
  isRunning: boolean
  setIsRunning: (val: boolean) => void
  simulationId: string | null
  setSimulationId: (val: string | null) => void
  selectedTrack: string | null
  setSelectedTrack: (val: string | null) => void
}

const ControlPanel = ({ isRunning, setIsRunning, simulationId, setSimulationId, selectedTrack, setSelectedTrack }: ControlPanelProps) => {
  const [tracks, setTracks] = useState<any[]>([])

  useEffect(() => {
    // Fetch available tracks
    axios.get('/api/tracks/').then(res => {
      setTracks(res.data)
      if (res.data.length > 0 && selectedTrack === null) {
        setSelectedTrack(res.data[0].id)
      }
    })
  }, [])

  const handleRandomTrack = () => {
    if (tracks.length > 0) {
      const randomIdx = Math.floor(Math.random() * tracks.length)
      setSelectedTrack(tracks[randomIdx].id)
    }
  }

  const handleGenerateTrack = async () => {
    try {
      const res = await axios.post('/api/tracks/generate')
      setTracks([...tracks, res.data])
      setSelectedTrack(res.data.id)
    } catch (err) {
      console.error("Failed to generate track", err)
    }
  }

  const handleStart = async () => {
    if (!selectedTrack) return
    try {
      const res = await axios.post('/api/simulations/start', { track_id: String(selectedTrack), status: "running" })
      setSimulationId(res.data.id)
      setIsRunning(true)
    } catch (err) {
      console.error("Failed to start simulation", err)
    }
  }

  const handleStop = async () => {
    // ... same as before
    if (!simulationId) return
    try {
      await axios.post(`/api/simulations/${simulationId}/stop`)
      setIsRunning(false)
      setSimulationId(null)
    } catch (err) {
      console.error("Failed to stop simulation", err)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="text-xs font-bold uppercase tracking-wider text-gray-500">Simulation Controls</div>
      
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-gray-300">Active Track</label>
          <div className="flex flex-col gap-2">
            <select 
              value={selectedTrack || ''} 
              onChange={(e) => setSelectedTrack(e.target.value)}
              className="w-full rounded-lg bg-black px-3 py-2 border border-gray-700 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            >
              {tracks.map((t: any) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
            <button 
              onClick={handleRandomTrack}
              className="flex items-center justify-center gap-2 rounded-lg bg-gray-800 py-2 text-xs font-medium text-gray-300 hover:bg-gray-700 transition-colors border border-gray-700"
            >
              <RefreshCw size={14} />
              Pick Random Track
            </button>
            <button 
              onClick={handleGenerateTrack}
              className="flex items-center justify-center gap-2 rounded-lg bg-primary/10 py-2 text-xs font-medium text-primary hover:bg-primary/20 transition-colors border border-primary/30"
            >
              <MapIcon size={14} />
              Generate New Track
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-2">
          {!isRunning ? (
            <button 
              onClick={handleStart}
              className="flex items-center justify-center gap-2 rounded-lg bg-primary py-2.5 font-semibold text-white hover:bg-blue-600 transition-all"
            >
              <Play size={18} fill="white" />
              Initialize System
            </button>
          ) : (
            <button 
              onClick={handleStop}
              className="flex items-center justify-center gap-2 rounded-lg bg-red-500/10 py-2.5 font-semibold text-red-500 border border-red-500/20 hover:bg-red-500/20 transition-all"
            >
              <Square size={18} fill="currentColor" />
              Terminate Run
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default ControlPanel
