export interface Agent {
  id: number
  name: string
  service: string
  status: "Online" | "Offline"
  jobsCompleted: number
  successRate: number
  balance: number
  earned: number
  agentAddress: string
  wallet?: string
}
