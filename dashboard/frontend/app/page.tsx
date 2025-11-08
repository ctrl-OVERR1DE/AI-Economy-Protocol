"use client"

import { Header } from "@/components/dashboard/header"
import { StatsRow } from "@/components/dashboard/stats-row"
import { AgentsSection } from "@/components/dashboard/agents-section"
import { useEffect, useState } from "react"

export default function DashboardPage() {
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // Simulate auto-refresh every 10 seconds
    const interval = setInterval(() => {
      console.log("[v0] Auto-refreshing data...")
    }, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen" style={{ backgroundColor: "#0f0f23" }}>
      <Header />
      <main className="px-4 sm:px-6 md:px-8 lg:px-8 py-6 sm:py-8">
        {isLoading && (
          <div className="text-center py-8">
            <p style={{ color: "#9ca3af" }} className="text-sm">
              Loading...
            </p>
          </div>
        )}
        {!isLoading && (
          <>
            <StatsRow />
            <AgentsSection />
          </>
        )}
      </main>
    </div>
  )
}
