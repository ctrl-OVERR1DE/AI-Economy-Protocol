"use client"

import { X } from "lucide-react"
import { Circle } from "lucide-react"
import type { Agent } from "./types"

interface Job {
  id: number
  jobNumber: string
  client: string
  amount: number
  status: "Success" | "Failed"
  date: string
}

 

interface AgentModalProps {
  agent: Agent | null
  isOpen: boolean
  onClose: () => void
  jobs: Job[]
}

export function AgentModal({ agent, isOpen, onClose, jobs }: AgentModalProps) {
  if (!isOpen || !agent) return null

  return (
    <>
      <div
        className="fixed inset-0 bg-black/80 z-40 transition-opacity duration-200"
        onClick={onClose}
        style={{ animation: "fadeIn 0.3s ease-out" }}
        role="presentation"
      />

      <div
        className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full mx-4 sm:mx-0 max-w-md sm:max-w-2xl lg:max-w-3xl z-50 rounded-lg border max-h-[90vh] overflow-hidden flex flex-col transition-all duration-200"
        style={{
          backgroundColor: "#1a1a2e",
          borderColor: "#2a2a3e",
          animation: "slideIn 0.3s ease-out",
        }}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center rounded hover:bg-gray-700/50 focus:outline-none focus:ring-2"
          aria-label="Close modal"
          style={{ zIndex: 10 }}
        >
          <X size={24} />
        </button>

        <div style={{ overflow: "auto", flex: 1, padding: "2rem 1.5rem" }} className="sm:p-8">
          <div className="mb-6 sm:mb-8">
            <div className="flex flex-col sm:flex-row items-start justify-between gap-4 mb-4">
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">{agent.name}</h2>
                <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                  <span
                    className="px-3 py-1 rounded-full text-xs font-medium"
                    style={{
                      backgroundColor: "rgba(139, 92, 246, 0.1)",
                      color: "#8b5cf6",
                    }}
                  >
                    {agent.service}
                  </span>
                  <div className="flex items-center gap-2">
                    <Circle
                      size={8}
                      fill={agent.status === "Online" ? "#10b981" : "#ef4444"}
                      stroke={agent.status === "Online" ? "#10b981" : "#ef4444"}
                    />
                    <span
                      style={{ color: agent.status === "Online" ? "#10b981" : "#ef4444" }}
                      className="text-xs sm:text-sm font-medium"
                    >
                      {agent.status}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div style={{ color: "#9ca3af" }} className="text-xs sm:text-sm">
              Wallet: <span className="text-gray-300 break-all">{agent.wallet ?? "—"}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
            <div
              className="p-3 sm:p-4 rounded-lg"
              style={{
                backgroundColor: "#2a2a3e",
              }}
            >
              <div style={{ color: "#9ca3af" }} className="text-xs font-medium mb-2">
                Jobs Completed
              </div>
              <div className="text-lg sm:text-xl font-semibold text-white">{agent.jobsCompleted}</div>
            </div>
            <div
              className="p-3 sm:p-4 rounded-lg"
              style={{
                backgroundColor: "#2a2a3e",
              }}
            >
              <div style={{ color: "#9ca3af" }} className="text-xs font-medium mb-2">
                Success Rate
              </div>
              <div className="text-lg sm:text-xl font-semibold text-white">{agent.successRate}%</div>
            </div>
            <div
              className="p-3 sm:p-4 rounded-lg"
              style={{
                backgroundColor: "#2a2a3e",
              }}
            >
              <div style={{ color: "#9ca3af" }} className="text-xs font-medium mb-2">
                Current Balance
              </div>
              <div className="text-lg sm:text-xl font-semibold text-white">{agent.balance} Tokens</div>
            </div>
            <div
              className="p-3 sm:p-4 rounded-lg"
              style={{
                backgroundColor: "#2a2a3e",
              }}
            >
              <div style={{ color: "#9ca3af" }} className="text-xs font-medium mb-2">
                Total Earned
              </div>
              <div className="text-lg sm:text-xl font-semibold text-white">{agent.earned} Tokens</div>
            </div>
          </div>

          <div>
            <h3 className="text-base sm:text-lg font-semibold text-white mb-3 sm:mb-4">Recent Jobs</h3>
            {jobs.length === 0 ? (
              <div className="text-center py-8">
                <p style={{ color: "#9ca3af" }} className="text-sm">
                  No job history
                </p>
              </div>
            ) : (
              <div className="overflow-hidden rounded-lg border overflow-x-auto" style={{ borderColor: "#2a2a3e" }}>
                <table className="w-full text-xs sm:text-sm">
                  <thead>
                    <tr style={{ backgroundColor: "#2a2a3e" }}>
                      <th
                        className="px-3 sm:px-4 py-3 text-left font-medium whitespace-nowrap"
                        style={{ color: "#9ca3af" }}
                      >
                        Job #
                      </th>
                      <th
                        className="px-3 sm:px-4 py-3 text-left font-medium whitespace-nowrap"
                        style={{ color: "#9ca3af" }}
                      >
                        Client
                      </th>
                      <th
                        className="px-3 sm:px-4 py-3 text-left font-medium whitespace-nowrap"
                        style={{ color: "#9ca3af" }}
                      >
                        Amount
                      </th>
                      <th
                        className="px-3 sm:px-4 py-3 text-left font-medium whitespace-nowrap"
                        style={{ color: "#9ca3af" }}
                      >
                        Status
                      </th>
                      <th
                        className="px-3 sm:px-4 py-3 text-left font-medium whitespace-nowrap"
                        style={{ color: "#9ca3af" }}
                      >
                        Date
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.map((job, index) => (
                      <tr
                        key={job.id}
                        style={{
                          backgroundColor: index % 2 === 0 ? "#1a1a2e" : "#262637",
                        }}
                        className="hover:bg-[#2a2a3e] transition-colors duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        <td className="px-3 sm:px-4 py-3 text-white font-medium whitespace-nowrap">{job.jobNumber}</td>
                        <td className="px-3 sm:px-4 py-3 text-gray-300 break-all">{job.client}</td>
                        <td className="px-3 sm:px-4 py-3 text-white font-medium whitespace-nowrap">{job.amount} Tokens</td>
                        <td className="px-3 sm:px-4 py-3">
                          <span
                            className="px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap"
                            style={{
                              backgroundColor:
                                job.status === "Success" ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
                              color: job.status === "Success" ? "#10b981" : "#ef4444",
                            }}
                          >
                            {job.status}
                          </span>
                        </td>
                        <td style={{ color: "#9ca3af" }} className="px-3 sm:px-4 py-3 whitespace-nowrap">
                          {job.date}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translate(-50%, -48%);
          }
          to {
            opacity: 1;
            transform: translate(-50%, -50%);
          }
        }
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
      `}</style>
    </>
  )
}
