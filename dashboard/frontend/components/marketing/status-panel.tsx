"use client"

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

interface StatusItem {
  name: string
  status: "loading" | "ok" | "error"
  message?: string
}

export function StatusPanel() {
  const [items, setItems] = useState<StatusItem[]>([
    { name: "Marketplace API", status: "loading" },
    { name: "x402 Gateway", status: "loading" },
    { name: "Stats", status: "loading" },
  ])

  useEffect(() => {
    const checkStatuses = async () => {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"
      const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8001"

      // Check Marketplace API
      try {
        await fetch(`${apiBase}/docs`, { mode: "no-cors" })
        setItems((prev) => prev.map((item) => (item.name === "Marketplace API" ? { ...item, status: "ok" } : item)))
      } catch {
        setItems((prev) =>
          prev.map((item) =>
            item.name === "Marketplace API" ? { ...item, status: "error", message: "Not detected" } : item,
          ),
        )
      }

      // Check x402 Gateway
      try {
        const response = await fetch(`${gatewayUrl}/health`)
        if (response.ok) {
          setItems((prev) => prev.map((item) => (item.name === "x402 Gateway" ? { ...item, status: "ok" } : item)))
        } else {
          throw new Error("Not ok")
        }
      } catch {
        setItems((prev) =>
          prev.map((item) =>
            item.name === "x402 Gateway" ? { ...item, status: "error", message: "Not detected" } : item,
          ),
        )
      }

      // Check Stats
      try {
        const response = await fetch(`${apiBase}/stats`)
        if (response.ok) {
          const data = await response.json()
          setItems((prev) =>
            prev.map((item) =>
              item.name === "Stats"
                ? {
                    ...item,
                    status: "ok",
                    message: `${data.providers || 0} providers, ${data.requests || 0} requests`,
                  }
                : item,
            ),
          )
        } else {
          throw new Error("Not ok")
        }
      } catch {
        setItems((prev) =>
          prev.map((item) => (item.name === "Stats" ? { ...item, status: "error", message: "Not detected" } : item)),
        )
      }
    }

    checkStatuses()
  }, [])

  return (
    <section className="px-4 sm:px-6 md:px-8 py-12 sm:py-16 border-t border-b" style={{ borderColor: "#2a2a3e" }}>
      <div className="mx-auto max-w-5xl">
        <h2 className="text-2xl sm:text-3xl font-bold mb-8 text-white">Demo Readiness</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {items.map((item) => (
            <div
              key={item.name}
              className="p-4 sm:p-6 rounded-lg border transition-all"
              style={{
                backgroundColor: "#1a1a2e",
                borderColor: "#2a2a3e",
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-white">{item.name}</h3>
                {item.status === "loading" && <Loader2 className="h-4 w-4 animate-spin" style={{ color: "#8b5cf6" }} />}
                {item.status === "ok" && (
                  <span
                    className="text-xs font-medium px-2 py-1 rounded"
                    style={{ backgroundColor: "rgba(16, 185, 129, 0.1)", color: "#10b981" }}
                  >
                    OK
                  </span>
                )}
                {item.status === "error" && (
                  <span
                    className="text-xs font-medium px-2 py-1 rounded"
                    style={{ backgroundColor: "rgba(239, 68, 68, 0.1)", color: "#ef4444" }}
                  >
                    Down
                  </span>
                )}
              </div>
              {item.message && (
                <p className="text-xs" style={{ color: "#6b7280" }}>
                  {item.message}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
