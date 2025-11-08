"use client"

import { useEffect, useMemo, useState } from "react"
import { AgentCard } from "./agent-card"
import { AgentModal } from "./agent-modal"
import { fetchAllProviders, fetchProviderRequests, fetchProviderBalance, TOKEN_MINT, formatServiceType, type Provider, type ServiceRequest, type ServiceOffering } from "@/lib/api"
import type { Agent } from "./types"

 

interface Job {
  id: number
  jobNumber: string
  client: string
  amount: number
  status: "Success" | "Failed"
  date: string
}

function truncate(addr: string, left = 4, right = 4) {
  if (!addr) return ""
  if (addr.length <= left + right) return addr
  return `${addr.slice(0, left)}...${addr.slice(-right)}`
}

function toRelative(iso: string): string {
  if (!iso) return ""
  let s = iso.trim()
  // Reduce fractional seconds to 3 digits for JS Date compatibility
  s = s.replace(/(\.\d{3})\d+/, "$1")
  // Treat as UTC if no timezone indicator is present
  if (!/[zZ]|[+-]\d{2}:?\d{2}$/.test(s)) s += "Z"
  const d = new Date(s)
  const diffMs = Date.now() - d.getTime()
  const minsFloat = diffMs / 60000
  if (minsFloat < 1) return "just now"
  const mins = Math.max(1, Math.round(minsFloat))
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 48) return `${hrs}h ago`
  const days = Math.round(hrs / 24)
  return `${days}d ago`
}

export function AgentsSection() {
  const [allProviders, setAllProviders] = useState<Provider[]>([])
  const [onlineProviders, setOnlineProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [jobsByAgent, setJobsByAgent] = useState<Record<string, Job[]>>({})
  const [balancesByAgent, setBalancesByAgent] = useState<Record<string, number>>({})

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const list = await fetchAllProviders()
        if (!mounted) return
        setAllProviders(list)
        setOnlineProviders(list.filter((p) => p.status === "online"))
        // fetch balances for all providers
        try {
          const results = await Promise.all(
            list.map(async (p) => {
              try {
                const bal = await fetchProviderBalance(p.agent_address, TOKEN_MINT)
                return [p.agent_address, bal.amount] as const
              } catch {
                return [p.agent_address, 0] as const
              }
            })
          )
          if (!mounted) return
          const map: Record<string, number> = {}
          for (const [addr, amt] of results) map[addr] = amt
          setBalancesByAgent(map)
        } catch {
          if (mounted) setBalancesByAgent({})
        }
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    const id = setInterval(load, 10000)
    return () => {
      mounted = false
      clearInterval(id)
    }
  }, [])

  const agentsDataOnline: Agent[] = useMemo(() => {
    return onlineProviders.map((p: Provider, idx: number) => {
      const successRate = p.total_jobs > 0 ? Math.round((p.completed_jobs / p.total_jobs) * 100) : 100
      const services = (p.services || []).map((s: ServiceOffering) => formatServiceType(s.service_type))
      return {
        id: idx + 1,
        name: p.agent_name,
        service: services.join(", ") || "—",
        status: p.status === "online" ? "Online" : "Offline",
        jobsCompleted: p.completed_jobs,
        successRate,
        balance: balancesByAgent[p.agent_address] ?? 0,
        earned: Math.round(p.total_earned),
        agentAddress: p.agent_address,
        wallet: truncate(p.solana_address),
      }
    })
  }, [onlineProviders, balancesByAgent])

  const agentsDataAll: Agent[] = useMemo(() => {
    return allProviders.map((p: Provider, idx: number) => {
      const successRate = p.total_jobs > 0 ? Math.round((p.completed_jobs / p.total_jobs) * 100) : 100
      const services = (p.services || []).map((s: ServiceOffering) => formatServiceType(s.service_type))
      return {
        id: idx + 1,
        name: p.agent_name,
        service: services.join(", ") || "—",
        status: p.status === "online" ? "Online" : "Offline",
        jobsCompleted: p.completed_jobs,
        successRate,
        balance: balancesByAgent[p.agent_address] ?? 0,
        earned: Math.round(p.total_earned),
        agentAddress: p.agent_address,
        wallet: truncate(p.solana_address),
      }
    })
  }, [allProviders, balancesByAgent])

  // keep selectedAgent's balance in sync when balances refresh
  useEffect(() => {
    if (!selectedAgent) return
    const latest = balancesByAgent[selectedAgent.agentAddress]
    if (typeof latest === "number" && latest !== selectedAgent.balance) {
      setSelectedAgent({ ...selectedAgent, balance: latest })
    }
  }, [balancesByAgent, selectedAgent])

  const handleViewDetails = (agent: Agent) => {
    setSelectedAgent(agent)
    setIsModalOpen(true)
    // Lazy-load recent jobs for this agent
    if (!jobsByAgent[agent.agentAddress]) {
      ;(async () => {
        try {
          const reqs: ServiceRequest[] = await fetchProviderRequests(agent.agentAddress, 10)
          const jobs: Job[] = reqs
            .filter((r) => r.status === "completed" || r.status === "failed")
            .map((r, i) => ({
              id: i + 1,
              jobNumber: String(i + 1),
              client: truncate(r.client_address, 4, 4),
              amount: r.amount,
              status: r.status === "completed" ? "Success" : "Failed",
              date: toRelative(((r as any).completed_at ?? (r as any).updated_at ?? r.created_at) as string),
            }))
          setJobsByAgent((prev: Record<string, Job[]>) => ({ ...prev, [agent.agentAddress]: jobs }))
        } catch (e) {
          setJobsByAgent((prev: Record<string, Job[]>) => ({ ...prev, [agent.agentAddress]: [] }))
        }
      })()
    }
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedAgent(null)
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <p style={{ color: "#9ca3af" }} className="text-sm">Loading agents...</p>
      </div>
    )
  }

  return (
    <>
      <div>
        <h2 className="text-lg sm:text-xl font-semibold text-white mb-4 sm:mb-6">Active Agents</h2>
        {agentsDataOnline.length === 0 ? (
          <div className="text-center py-6">
            <p style={{ color: "#9ca3af" }} className="text-sm">No agents online</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {agentsDataOnline.map((agent) => (
              <AgentCard key={`online-${agent.id}`} agent={agent} onViewDetails={handleViewDetails} />
            ))}
          </div>
        )}
      </div>

      <div className="mt-10">
        <h2 className="text-lg sm:text-xl font-semibold text-white mb-4 sm:mb-6">All Agents</h2>
        {agentsDataAll.length === 0 ? (
          <div className="text-center py-6">
            <p style={{ color: "#9ca3af" }} className="text-sm">No agents registered</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {agentsDataAll.map((agent) => (
              <AgentCard key={`all-${agent.id}`} agent={agent} onViewDetails={handleViewDetails} />
            ))}
          </div>
        )}
      </div>

      <AgentModal
        agent={selectedAgent}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        jobs={selectedAgent ? jobsByAgent[selectedAgent.agentAddress] || [] : []}
      />
    </>
  )
}
