"use client"

import { LayoutDashboard, Github, BookOpen, Zap } from "lucide-react"
import Link from "next/link"

const sdkDocsUrl = process.env.NEXT_PUBLIC_SDK_DOCS_URL || "https://ctrl-OVERR1DE.github.io/AI-Economy-Protocol/"

const links = [
  {
    icon: LayoutDashboard,
    title: "Marketplace Dashboard",
    href: "/",
  },
  {
    icon: Github,
    title: "GitHub",
    href: "https://github.com/ctrl-OVERR1DE/AI-Economy-Protocol/tree/x402",
  },
  {
    icon: BookOpen,
    title: "SDK Docs",
    href: sdkDocsUrl,
  },
  {
    icon: BookOpen,
    title: "API Docs",
    href: "http://localhost:8000/docs",
  },
  {
    icon: Zap,
    title: "x402 Health",
    href: "http://localhost:8001/health",
  },
]

export function Links() {
  return (
    <section className="px-4 sm:px-6 md:px-8 py-12 sm:py-16 border-t" style={{ borderColor: "#2a2a3e" }}>
      <div className="mx-auto max-w-5xl text-center">
        <h2 className="text-2xl sm:text-3xl font-bold mb-12 text-white">Resources</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {links.map((link) => {
            const Icon = link.icon
            return (
              <Link key={link.title} href={link.href} target={link.href.startsWith("http") ? "_blank" : undefined}>
                <div
                  className="w-full h-auto flex flex-col items-center gap-2 py-4 rounded-lg border transition-all duration-200 cursor-pointer"
                  style={{
                    backgroundColor: "#1a1a2e",
                    borderColor: "#2a2a3e",
                  }}
                  onMouseEnter={(e) => {
                    ;(e.currentTarget as HTMLElement).style.borderColor = "#8b5cf6"
                  }}
                  onMouseLeave={(e) => {
                    ;(e.currentTarget as HTMLElement).style.borderColor = "#2a2a3e"
                  }}
                >
                  <Icon className="h-5 w-5" style={{ color: "#8b5cf6" }} />
                  <span className="text-xs text-center text-white">{link.title}</span>
                </div>
              </Link>
            )
          })}
        </div>
      </div>
    </section>
  )
}
