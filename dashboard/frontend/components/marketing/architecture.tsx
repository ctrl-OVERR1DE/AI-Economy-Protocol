import { ArrowRight } from "lucide-react"

export function Architecture() {
  return (
    <section className="px-4 sm:px-6 md:px-8 py-12 sm:py-16 border-t border-b" style={{ borderColor: "#2a2a3e" }}>
      <div className="mx-auto max-w-5xl">
        <h2 className="text-2xl sm:text-3xl font-bold mb-12 text-white text-center">Architecture</h2>
        <div className="overflow-x-auto">
          <div className="flex items-center justify-between gap-2 sm:gap-4 min-w-max">
            {[
              { label: "Dashboard\n(Next.js)" },
              { label: "Marketplace API\n(FastAPI)" },
              { label: "Agents\n(uAgents)" },
              { label: "x402 Gateway" },
              { label: "Solana\n(Escrow)" },
            ].map((box, idx) => (
              <div key={idx}>
                <div
                  className="flex items-center justify-center px-4 py-3 rounded-lg font-semibold whitespace-pre-wrap text-sm text-center"
                  style={{
                    backgroundColor: "#8b5cf6",
                    color: "white",
                  }}
                >
                  {box.label}
                </div>
                {idx < 4 && <ArrowRight className="h-6 w-6 flex-shrink-0 mx-2" style={{ color: "#6b7280" }} />}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
