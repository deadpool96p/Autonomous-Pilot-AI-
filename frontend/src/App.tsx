import { useState } from 'react'
import { Activity, Play, Square, Database, Settings } from 'lucide-react'
import axios from 'axios'
import SimulationCanvas from './components/SimulationCanvas'
import ControlPanel from './components/ControlPanel'
import StatsPanel from './components/StatsPanel'
import LaneVisualization from './components/LaneVisualization'

function App() {
  const [simulationId, setSimulationId] = useState<string | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [selectedTrack, setSelectedTrack] = useState<string | null>(null)
  const [showDynamicObjects, setShowDynamicObjects] = useState<boolean>(true)
  const [showLanes, setShowLanes] = useState<boolean>(true)
  const [showLookahead, setShowLookahead] = useState<boolean>(true)
  const [stats, setStats] = useState<any>({ generation: 1, alive: 0, bestFitness: 0 })

  const handleReset = async () => {
    if (window.confirm("Are you sure? This will stop all running simulations and clear state.")) {
      try {
        await axios.post('/api/simulations/reset')
        setIsRunning(false)
        setSimulationId(null)
      } catch (err) {
        console.error("Reset failed:", err)
      }
    }
  }

  return (
    <div className="flex h-screen w-screen flex-col bg-background text-white">
      {/* Header */}
      <header className="flex h-14 items-center justify-between border-b border-gray-800/80 px-6 bg-gray-950/50 backdrop-blur-sm" id="app-header">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary/15 p-2 text-primary">
            <Activity size={22} />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight leading-none">AI Autonomous Pilot</h1>
            <p className="text-[10px] text-gray-600 tracking-wider uppercase">Neural Vehicle Simulation Platform</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={handleReset}
            className="flex items-center gap-2 rounded-md bg-red-900/15 px-3 py-1.5 hover:bg-red-900/30 text-red-400 text-xs transition-colors border border-red-900/30"
            id="reset-btn"
          >
            Reset
          </button>
          <div className="h-5 w-px bg-gray-800" />
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <div className={`h-2 w-2 rounded-full ${isRunning ? 'bg-green-500 shadow-lg shadow-green-500/50' : 'bg-gray-600'} ${isRunning ? 'animate-pulse' : ''}`} />
            {isRunning ? 'Live' : 'Idle'}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-80 border-r border-gray-800/80 p-4 flex flex-col gap-4 overflow-y-auto custom-scrollbar bg-gray-950/30" id="sidebar">
          <ControlPanel 
            isRunning={isRunning} 
            setIsRunning={setIsRunning} 
            simulationId={simulationId}
            setSimulationId={setSimulationId}
            selectedTrack={selectedTrack}
            setSelectedTrack={setSelectedTrack}
            showDynamicObjects={showDynamicObjects}
            setShowDynamicObjects={setShowDynamicObjects}
          />
          <LaneVisualization 
            showLanes={showLanes} setShowLanes={setShowLanes}
            showLookahead={showLookahead} setShowLookahead={setShowLookahead}
          />
          <StatsPanel stats={stats} />
          
          <div className="mt-auto rounded-xl bg-gray-900/50 p-4 border border-gray-800">
            <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
              <Database size={16} />
              <span>Genome Library</span>
            </div>
            <p className="text-xs text-gray-500">
              Load previously trained champion genomes to resume simulation.
            </p>
          </div>
        </div>

        {/* Viewport */}
        <div className="relative flex-1 bg-black" id="main-viewport">
          <SimulationCanvas 
            simulationId={simulationId} 
            isRunning={isRunning} 
            selectedTrack={selectedTrack}
            setStats={setStats} 
            showDynamicObjects={showDynamicObjects}
            showLanes={showLanes}
            showLookahead={showLookahead}
          />
          
          {/* Bottom Overlay Controls */}
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 rounded-full bg-black/60 backdrop-blur-md border border-white/10 p-1.5 shadow-2xl">
            <button 
              className="p-2.5 rounded-full hover:bg-white/10 transition-colors text-white/50 hover:text-white/80"
              id="settings-btn"
            >
              <Settings size={18} />
            </button>
            <div className="h-4 w-px bg-white/10" />
            <button 
              onClick={() => {
                if (isRunning) {
                  // Stop via the same flow
                  if (simulationId) {
                    axios.post(`/api/simulations/${simulationId}/stop`).catch(() => {})
                  }
                  setIsRunning(false)
                  setSimulationId(null)
                } else {
                  // This will be handled by ControlPanel's start
                  // Just toggle for the overlay button
                }
              }}
              className={`flex items-center gap-2 rounded-full px-5 py-2 font-semibold text-sm transition-all shadow-lg ${
                isRunning 
                  ? 'bg-red-500/80 text-white hover:bg-red-500 shadow-red-500/20' 
                  : 'bg-primary/80 text-white hover:bg-primary shadow-primary/20 opacity-60 cursor-default'
              }`}
              disabled={!isRunning}
              id="overlay-stop-btn"
            >
              {isRunning ? <Square size={16} fill="white" /> : <Play size={16} fill="white" />}
              {isRunning ? 'Stop' : 'Start'}
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
