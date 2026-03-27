import { Eye, EyeOff } from 'lucide-react'

interface LaneVisualizationProps {
  showLanes: boolean
  setShowLanes: (val: boolean) => void
  showLookahead: boolean
  setShowLookahead: (val: boolean) => void
}

const LaneVisualization = ({ 
  showLanes, setShowLanes, 
  showLookahead, setShowLookahead 
}: LaneVisualizationProps) => {
  return (
    <div className="rounded-xl bg-gray-900 border border-blue-500/20 p-4">
      <div className="flex items-center gap-2 text-xs text-blue-400 mb-3">
        <Eye size={14} />
        <span className="font-bold uppercase tracking-wider">Perception Overlays</span>
      </div>
      
      <div className="flex flex-col gap-2">
        <button
          onClick={() => setShowLanes(!showLanes)}
          className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors border ${
            showLanes 
            ? 'bg-blue-900/30 border-blue-800 text-blue-300' 
            : 'bg-black border-gray-800 text-gray-500 hover:border-gray-600'
          }`}
        >
          <span>HD Lane Boundaries & Signs</span>
          {showLanes ? <Eye size={14} /> : <EyeOff size={14} />}
        </button>
        
        <button
          onClick={() => setShowLookahead(!showLookahead)}
          className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors border ${
            showLookahead 
            ? 'bg-purple-900/30 border-purple-800 text-purple-300' 
            : 'bg-black border-gray-800 text-gray-500 hover:border-gray-600'
          }`}
        >
          <span>PID Lookahead / Trajectory</span>
          {showLookahead ? <Eye size={14} /> : <EyeOff size={14} />}
        </button>
      </div>
    </div>
  )
}

export default LaneVisualization
