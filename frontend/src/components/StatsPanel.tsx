import { TrendingUp, Users, Target } from 'lucide-react'

interface StatsPanelProps {
  stats: {
    generation: number | string
    alive: number
    bestFitness: number
  }
}

const StatsPanel = ({ stats }: StatsPanelProps) => {
  return (
    <div className="flex flex-col gap-4">
      <div className="text-xs font-bold uppercase tracking-wider text-gray-500">Real-time Metrics</div>
      
      <div className="grid grid-cols-1 gap-3">
        <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
          <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
            < TrendingUp size={14} />
            <span>Generation Cycle</span>
          </div>
          <div className="text-2xl font-bold text-white">{stats.generation}</div>
        </div>

        <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
          <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
            <Users size={14} />
            <span>Active Agents</span>
          </div>
          <div className="text-2xl font-bold text-green-500">{stats.alive}</div>
        </div>

        <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
          <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
            <Target size={14} />
            <span>Peak Fitness</span>
          </div>
          <div className="text-2xl font-bold text-accent">{stats.bestFitness.toFixed(1)}</div>
        </div>
      </div>
    </div>
  )
}

export default StatsPanel
