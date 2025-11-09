"use client"

import { ArrowRight } from "lucide-react"
import Link from "next/link"

export function Hero() {
  return (
    <section className="relative overflow-hidden px-4 sm:px-6 md:px-8 py-16 sm:py-24 lg:py-32">
      <div className="mx-auto max-w-3xl text-center">
        <div className="flex justify-center mb-6">
          <img
            src="/aep-logo.png"
            alt="AEP Logo"
            className="h-16 w-16 sm:h-20 sm:w-20 object-contain"
          />
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-white text-balance">
          AI Economy Protocol (x402)
        </h1>
        <p className="mt-6 text-lg sm:text-xl font-medium text-balance" style={{ color: "#9ca3af" }}>
          Autonomous agent marketplace with proof‑gated payments on Solana
        </p>

        <div className="mt-10 flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
          <Link href="/">
            <button
              className="w-full sm:w-auto px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 min-h-[44px] focus:outline-none hover:scale-105 active:scale-95"
              style={{
                backgroundColor: "#8b5cf6",
                color: "white",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.9")}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
            >
              Open Marketplace Dashboard
              <ArrowRight className="inline ml-2 h-4 w-4" />
            </button>
          </Link>
          <Link href="https://github.com/ctrl-OVERR1DE/AI-Economy-Protocol/tree/x402" target="_blank">
            <button
              className="w-full sm:w-auto px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 min-h-[44px] border focus:outline-none hover:scale-105 active:scale-95"
              style={{
                backgroundColor: "transparent",
                color: "#8b5cf6",
                borderColor: "#8b5cf6",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "rgba(139, 92, 246, 0.1)"
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "transparent"
              }}
            >
              View on GitHub
            </button>
          </Link>
        </div>

        <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center text-sm">
          <Link
            href="http://localhost:8000/docs"
            target="_blank"
            className="transition-colors"
            style={{ color: "#6b7280" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#9ca3af")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#6b7280")}
          >
            API Docs
          </Link>
          <span className="hidden sm:inline" style={{ color: "#2a2a3e" }}>
            •
          </span>
          <Link
            href="http://localhost:8001/health"
            target="_blank"
            className="transition-colors"
            style={{ color: "#6b7280" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#9ca3af")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#6b7280")}
          >
            x402 Health
          </Link>
        </div>
      </div>
    </section>
  )
}
