import { TrendingUp, Users, Target, Zap, AlertTriangle, ShieldCheck } from 'lucide-react'
import CollisionStats from './CollisionStats'

interface StatsPanelProps {
  stats: {
    generation: number | string
    alive: number
    bestFitness: number
    pedestrianHits?: number
    npcHits?: number
    boundary_hits?: number
    clean_laps?: number
    autoLearning?: {
      is_training: boolean
      data_count: number
      last_train: string | null
    }
  }
}

const StatsPanel = ({ stats }: StatsPanelProps) => {
  return (
    <div className="flex flex-col gap-4">
      <div className="text-xs font-bold uppercase tracking-wider text-gray-500">Real-time Metrics</div>
      
      <div className="grid grid-cols-1 gap-3">
        {/* Basic Stats */}
        <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
          <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
            <TrendingUp size={14} />
            <span>Generation Cycle</span>
          </div>
          <div className="text-2xl font-bold text-white">{stats.generation || 1}</div>
        </div>

        <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
          <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
            <Users size={14} />
            <span>Active Agents</span>
          </div>
          <div className="text-2xl font-bold text-green-500">{stats.alive || 0}</div>
        </div>

        {/* Training Status */}
        <div className="rounded-xl bg-slate-900 border border-indigo-500/30 p-4">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2 text-xs text-indigo-300">
              <Zap size={14} className={stats.autoLearning?.is_training ? "animate-pulse text-yellow-400" : ""} />
              <span>Auto-Learning Pipeline</span>
            </div>
            <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${stats.autoLearning?.is_training ? "bg-yellow-500/20 text-yellow-400" : "bg-slate-700 text-slate-400"}`}>
              {stats.autoLearning?.is_training ? "TRAINING" : "COLLECTING"}
            </span>
          </div>
          <div className="text-xl font-bold text-white">{stats.autoLearning?.data_count || 0} <span className="text-xs text-slate-500 font-normal">frames</span></div>
        </div>

        <CollisionStats stats={{
            pedestrian_hits: stats.pedestrianHits,
            npc_hits: stats.npcHits,
            boundary_hits: stats.boundary_hits,
            clean_laps: stats.clean_laps
        }} />

        <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
          <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
            <Target size={14} />
            <span>Peak Fitness</span>
          </div>
          <div className="text-2xl font-bold text-blue-400">{(stats.bestFitness || 0).toFixed(1)}</div>
        </div>
      </div>
    </div>
  )
}

export default StatsPanel
