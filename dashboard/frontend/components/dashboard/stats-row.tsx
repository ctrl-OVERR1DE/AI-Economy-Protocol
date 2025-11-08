"use client"

import { useEffect, useState } from "react"
import { fetchStats, type MarketplaceStats } from "@/lib/api"

export function StatsRow() {
  const [stats, setStats] = useState<MarketplaceStats | null>(null)

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const s = await fetchStats()
        if (mounted) setStats(s)
      } catch (e) {
        // swallow; keep previous values
      }
    }
    load()
    const id = setInterval(load, 10000)
    return () => {
      mounted = false
      clearInterval(id)
    }
  }, [])

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
      <div className="p-4 sm:p-6 rounded-lg border transition-colors duration-200" style={{ backgroundColor: "#1a1a2e", borderColor: "#2a2a3e" }}>
        <div style={{ color: "#9ca3af" }} className="text-xs sm:text-sm font-medium mb-2">Total Agents</div>
        <div className="text-2xl sm:text-3xl font-bold text-white">{stats ? stats.total_providers.toLocaleString() : "-"}</div>
      </div>
      <div className="p-4 sm:p-6 rounded-lg border transition-colors duration-200" style={{ backgroundColor: "#1a1a2e", borderColor: "#2a2a3e" }}>
        <div style={{ color: "#9ca3af" }} className="text-xs sm:text-sm font-medium mb-2">Agents Online</div>
        <div className="text-2xl sm:text-3xl font-bold text-white">{stats ? stats.online_providers.toLocaleString() : "-"}</div>
      </div>
      <div className="p-4 sm:p-6 rounded-lg border transition-colors duration-200" style={{ backgroundColor: "#1a1a2e", borderColor: "#2a2a3e" }}>
        <div style={{ color: "#9ca3af" }} className="text-xs sm:text-sm font-medium mb-2">Total Volume</div>
        <div className="text-2xl sm:text-3xl font-bold text-white">{stats ? `${Number(stats.total_volume).toLocaleString(undefined, { maximumFractionDigits: 6 })} Tokens` : "-"}</div>
      </div>
      <div className="p-4 sm:p-6 rounded-lg border transition-colors duration-200" style={{ backgroundColor: "#1a1a2e", borderColor: "#2a2a3e" }}>
        <div style={{ color: "#9ca3af" }} className="text-xs sm:text-sm font-medium mb-2">Total Jobs</div>
        <div className="text-2xl sm:text-3xl font-bold text-white">{stats ? stats.total_transactions.toLocaleString() : "-"}</div>
      </div>
    </div>
  )
}
