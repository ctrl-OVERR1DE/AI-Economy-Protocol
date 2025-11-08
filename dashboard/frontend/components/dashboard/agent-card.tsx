"use client"

import { useState } from "react"
import { Circle } from "lucide-react"
import type { Agent } from "./types"

 

interface AgentCardProps {
  agent: Agent
  onViewDetails: (agent: Agent) => void
}

export function AgentCard({ agent, onViewDetails }: AgentCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const isOnline = agent.status === "Online"

  return (
    <div
      className="p-4 sm:p-6 rounded-lg border transition-all duration-200 cursor-default hover:shadow-lg"
      style={{
        backgroundColor: "#1a1a2e",
        borderColor: isHovered ? "#8b5cf6" : "#2a2a3e",
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Agent Name */}
      <div className="mb-4">
        <h3 className="text-white font-bold text-lg">{agent.name}</h3>
      </div>

      {/* Service Badge */}
      <div className="mb-4 flex items-center gap-2">
        <span
          className="px-3 py-1 rounded-full text-xs font-medium"
          style={{
            backgroundColor: "rgba(139, 92, 246, 0.1)",
            color: "#8b5cf6",
          }}
        >
          {agent.service}
        </span>
      </div>

      {/* Status */}
      <div className="mb-6 flex items-center gap-2">
        <Circle size={8} fill={isOnline ? "#10b981" : "#ef4444"} stroke={isOnline ? "#10b981" : "#ef4444"} />
        <span
          style={{
            color: isOnline ? "#10b981" : "#ef4444",
          }}
          className="text-sm font-medium"
        >
          {agent.status}
        </span>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <div style={{ color: "#9ca3af" }} className="text-xs font-medium mb-1">
            Jobs Completed
          </div>
          <div className="text-white font-semibold text-lg">{agent.jobsCompleted}</div>
        </div>
        <div>
          <div style={{ color: "#9ca3af" }} className="text-xs font-medium mb-1">
            Success Rate
          </div>
          <div className="text-white font-semibold text-lg">{agent.successRate}%</div>
        </div>
        <div>
          <div style={{ color: "#9ca3af" }} className="text-xs font-medium mb-1">
            Balance
          </div>
          <div className="text-white font-semibold text-lg">{agent.balance} Tokens</div>
        </div>
        <div>
          <div style={{ color: "#9ca3af" }} className="text-xs font-medium mb-1">
            Total Earned
          </div>
          <div className="text-white font-semibold text-lg">{agent.earned} Tokens</div>
        </div>
      </div>

      {/* View Details Button */}
      <button
        onClick={() => onViewDetails(agent)}
        className="w-full py-3 px-4 rounded-lg text-sm font-medium transition-all duration-200 min-h-[44px] focus:outline-none focus:ring-2 focus:ring-offset-2 hover:scale-105 active:scale-95"
        style={{
          backgroundColor: "#8b5cf6",
          color: "white",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.opacity = "0.9"
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.opacity = "1"
        }}
      >
        View Details
      </button>
    </div>
  )
}
