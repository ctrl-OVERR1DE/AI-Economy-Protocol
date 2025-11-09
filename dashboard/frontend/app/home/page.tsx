"use client"

import { useEffect, useState } from "react"
import { Hero } from "@/components/marketing/hero"
import { WhatWeBuilt } from "@/components/marketing/what-we-built"
import { Features } from "@/components/marketing/features"
import { StatusPanel } from "@/components/marketing/status-panel"
import { Architecture } from "@/components/marketing/architecture"
import { Links } from "@/components/marketing/links"
import { Footer } from "@/components/marketing/footer"

export default function MarketingHomePage() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  if (!mounted) return null
  return (
    <div className="min-h-screen" style={{ backgroundColor: "#0f0f23" }}>
      <Hero />
      <WhatWeBuilt />
      <Features />
      <StatusPanel />
      <Architecture />
      <Links />
      <Footer />
    </div>
  )
}
