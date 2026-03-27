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
  showDynamicObjects: boolean
  setShowDynamicObjects: (val: boolean) => void
}

const ControlPanel = ({ 
  isRunning, setIsRunning, simulationId, setSimulationId, 
  selectedTrack, setSelectedTrack, showDynamicObjects, setShowDynamicObjects 
}: ControlPanelProps) => {
  const [tracks, setTracks] = useState<any[]>([])
  const [mode, setMode] = useState<string>('ga')
  const [isRecording, setIsRecording] = useState<boolean>(false)
  const [trainingStatus, setTrainingStatus] = useState<string>('')

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
      const res = await axios.post('/api/simulations/start', { 
        track_id: String(selectedTrack), 
        status: "running",
        mode: mode 
      })
      setSimulationId(res.data.id)
      setIsRunning(true)
    } catch (err) {
      console.error("Failed to start simulation", err)
    }
  }

  const handleStop = async () => {
    if (!simulationId) return
    try {
      await axios.post(`/api/simulations/${simulationId}/stop`)
      setIsRunning(false)
      setSimulationId(null)
      setIsRecording(false)
    } catch (err) {
      console.error("Failed to stop simulation", err)
    }
  }

  const handleConfigUpdate = async (newMode: string, newRecording: boolean) => {
    try {
      await axios.post('/api/simulations/config', { mode: newMode, recording: newRecording })
      setMode(newMode)
      setIsRecording(newRecording)
    } catch (err) {
      console.error("Failed to update config", err)
    }
  }

  const handleTrain = async () => {
    setTrainingStatus('Training...')
    try {
      const res = await axios.post('/api/dl/train')
      setTrainingStatus(`Done: ${res.data.status}`)
      setTimeout(() => setTrainingStatus(''), 3000)
    } catch (err: any) {
      setTrainingStatus(`Error: ${err.response?.data?.detail || 'Failed'}`)
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
              className="flex items-center justify-center gap-2 rounded-lg bg-primary py-2.5 font-semibold text-white hover:bg-blue-600 transition-all shadow-lg shadow-primary/20"
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

          <div className="mt-4 border-t border-gray-800 pt-4">
            <label className="mb-2 block text-xs font-bold uppercase text-gray-500">Intelligence Mode</label>
            <div className="grid grid-cols-3 gap-2">
              {['ga', 'dl', 'pid'].map((m) => (
                <button
                  key={m}
                  onClick={() => handleConfigUpdate(m, isRecording)}
                  className={`rounded-lg py-1.5 text-xs font-bold uppercase transition-all border ${
                    mode === m 
                    ? 'bg-primary text-white border-primary' 
                    : 'bg-black text-gray-500 border-gray-800 hover:border-gray-600'
                  }`}
                >
                  {m === 'ga' ? 'Evolution (GA)' : m === 'dl' ? 'Deep Learning (DL)' : 'Lane Follow (PID)'}
                </button>
              ))}
            </div>
            
            <div className="mt-3 flex flex-col gap-2">
              <button
                onClick={() => handleConfigUpdate(mode, !isRecording)}
                disabled={!isRunning}
                className={`flex items-center justify-center gap-2 rounded-lg py-2 text-xs font-bold uppercase transition-all border ${
                  isRecording 
                  ? 'bg-red-500 text-white border-red-500 animate-pulse' 
                  : 'bg-gray-800 text-gray-300 border-gray-700 hover:bg-gray-700'
                } disabled:opacity-30 disabled:cursor-not-allowed`}
              >
                {isRecording ? 'Stop Recording' : 'Start Recording Data'}
              </button>
              
              <button
                onClick={handleTrain}
                disabled={isRecording}
                className="flex items-center justify-center gap-2 rounded-lg bg-indigo-900/20 py-2 text-xs font-bold uppercase text-indigo-400 border border-indigo-900/30 hover:bg-indigo-900/40 disabled:opacity-50 transition-colors"
              >
                 <RefreshCw size={12} className={trainingStatus.includes('...') ? 'animate-spin' : ''} />
                {trainingStatus || 'Train PilotNet Model'}
              </button>
              
              <button
                onClick={() => handleConfigUpdate(mode, isRecording)}
                className="flex items-center justify-center gap-2 rounded-lg bg-emerald-900/20 py-2 text-xs font-bold uppercase text-emerald-400 border border-emerald-900/30 hover:bg-emerald-900/40 transition-colors"
                title="Refresh model from disk"
              >
                Reload / Load Model
              </button>

              <button
                onClick={() => setShowDynamicObjects(!showDynamicObjects)}
                className={`flex items-center justify-center gap-2 rounded-lg py-2 text-xs font-bold uppercase transition-all border ${
                  showDynamicObjects 
                  ? 'bg-blue-900/20 text-blue-400 border-blue-900/30 hover:bg-blue-900/40' 
                  : 'bg-gray-800 text-gray-500 border-gray-700 hover:bg-gray-700'
                }`}
              >
                {showDynamicObjects ? 'Hide Dynamic Objects' : 'Show Dynamic Objects'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ControlPanel
