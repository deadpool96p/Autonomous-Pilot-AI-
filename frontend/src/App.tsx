import { useState, useEffect, useRef } from 'react'
import { Activity, Play, Square, Upload, Database, Settings } from 'lucide-react'
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
    if (window.confirm("Are you sure? This will clear all training data.")) {
      await axios.post('/api/simulations/reset')
      window.location.reload()
    }
  }

  return (
    <div className="flex h-screen w-screen flex-col bg-background text-white">
      {/* Header */}
      <header className="flex h-16 items-center justify-between border-b border-gray-800 px-6">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary/20 p-2 text-primary">
            <Activity size={24} />
          </div>
          <h1 className="text-xl font-bold tracking-tight">AI Autonomous Pilot</h1>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={handleReset}
            className="flex items-center gap-2 rounded-md bg-red-900/20 px-4 py-2 hover:bg-red-900/40 text-red-400 text-sm transition-colors border border-red-900/50"
          >
            Reset Simulation
          </button>
          <button className="flex items-center gap-2 rounded-md bg-gray-800 px-4 py-2 hover:bg-gray-700 transition-colors">
            <Upload size={18} />
            <span>Import Track</span>
          </button>
          <div className="h-6 w-px bg-gray-700" />
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <div className={`h-2 w-2 rounded-full ${isRunning ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
            {isRunning ? 'Connected' : 'Disconnected'}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-80 border-r border-gray-800 p-6 flex flex-col gap-6 overflow-y-auto">
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
        <div className="relative flex-1 bg-black">
          <SimulationCanvas 
            simulationId={simulationId} 
            isRunning={isRunning} 
            selectedTrack={selectedTrack}
            setStats={setStats} 
            showDynamicObjects={showDynamicObjects}
            showLanes={showLanes}
            showLookahead={showLookahead}
          />
          
          {/* Overlay Controls */}
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 rounded-full bg-black/50 backdrop-blur-md border border-white/10 p-2">
            <button className="p-3 rounded-full hover:bg-white/10 transition-colors text-white/70">
              <Settings size={20} />
            </button>
            <div className="h-4 w-px bg-white/10 mx-2" />
            <button 
              onClick={() => setIsRunning(!isRunning)}
              className="flex items-center gap-2 rounded-full bg-primary px-6 py-2.5 font-semibold text-white hover:bg-blue-600 transition-all shadow-lg shadow-primary/20"
            >
              {isRunning ? <Square size={18} fill="white" /> : <Play size={18} fill="white" />}
              {isRunning ? 'Stop' : 'Start'}
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
