import { AlertTriangle, UserX, Car, ShieldAlert } from 'lucide-react'

interface CollisionStatsProps {
  stats: {
    pedestrian_hits?: number
    npc_hits?: number
    boundary_hits?: number
    clean_laps?: number
  }
}

const CollisionStats = ({ stats }: CollisionStatsProps) => {
  return (
    <div className="rounded-xl bg-gray-900 border border-orange-500/20 p-4">
      <div className="flex items-center gap-2 text-xs text-orange-400 mb-3">
        <AlertTriangle size={14} />
        <span className="font-bold uppercase tracking-wider">Collision Telemetry</span>
      </div>
      
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="bg-black/50 p-3 rounded-lg border border-red-900/30 flex flex-col">
          <div className="flex items-center gap-1.5 text-[10px] text-red-400 uppercase mb-1">
            <UserX size={12} />
            <span>Pedestrian Hits</span>
          </div>
          <div className="text-xl font-bold text-white">{stats?.pedestrian_hits || 0}</div>
        </div>
        
        <div className="bg-black/50 p-3 rounded-lg border border-orange-900/30 flex flex-col">
          <div className="flex items-center gap-1.5 text-[10px] text-orange-400 uppercase mb-1">
            <Car size={12} />
            <span>NPC Collisions</span>
          </div>
          <div className="text-xl font-bold text-white">{stats?.npc_hits || 0}</div>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-black/50 p-3 rounded-lg border border-gray-800 flex flex-col">
          <div className="flex items-center gap-1.5 text-[10px] text-gray-400 uppercase mb-1">
            <ShieldAlert size={12} />
            <span>Boundary Faults</span>
          </div>
          <div className="text-xl font-bold text-white">{stats?.boundary_hits || 0}</div>
        </div>
        <div className="bg-emerald-900/20 p-3 rounded-lg border border-emerald-900/30 flex flex-col">
          <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 uppercase mb-1">
            <span>Clean Completions</span>
          </div>
          <div className="text-xl font-bold text-emerald-500">{stats?.clean_laps || 0}</div>
        </div>
      </div>
    </div>
  )
}

export default CollisionStats
