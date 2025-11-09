"use client"

import { ShieldCheck, Network, Bot, Zap, LayoutDashboard, CheckCircle2 } from "lucide-react"

const features = [
  {
    icon: ShieldCheck,
    title: "Proof‑gated Payments",
    description: "HTTP 402 payment verification protocol",
  },
  {
    icon: Zap,
    title: "Escrow on Solana",
    description: "SPL tokens with 6 decimals precision",
  },
  {
    icon: Bot,
    title: "Autonomous Agents",
    description: "uAgents framework integration",
  },
  {
    icon: Network,
    title: "Marketplace API",
    description: "FastAPI backend with full REST endpoints",
  },
  {
    icon: LayoutDashboard,
    title: "Live Dashboard",
    description: "Next.js real-time monitoring interface",
  },
  {
    icon: CheckCircle2,
    title: "On‑chain Verification",
    description: "Anchor smart contracts",
  },
]

export function Features() {
  return (
    <section className="px-4 sm:px-6 md:px-8 py-12 sm:py-16 border-t" style={{ borderColor: "#2a2a3e" }}>
      <div className="mx-auto max-w-5xl">
        <h2 className="text-2xl sm:text-3xl font-bold mb-12 text-white text-center">Key Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <div
                key={feature.title}
                className="p-4 sm:p-6 rounded-lg border transition-all duration-200 cursor-default"
                style={{
                  backgroundColor: "#1a1a2e",
                  borderColor: "#2a2a3e",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "#8b5cf6"
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "#2a2a3e"
                }}
              >
                <Icon className="h-8 w-8 mb-4" style={{ color: "#8b5cf6" }} />
                <h3 className="font-semibold mb-2 text-white">{feature.title}</h3>
                <p className="text-sm" style={{ color: "#9ca3af" }}>
                  {feature.description}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
