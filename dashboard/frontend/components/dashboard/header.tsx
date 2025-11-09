export function Header() {
  return (
    <header className="border-b px-4 sm:px-6 md:px-8 lg:px-8 py-6" style={{ borderColor: "#2a2a3e" }}>
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 sm:gap-0 mb-3 sm:mb-0">
        <div className="flex items-center gap-3">
          <img
            src="/aep-logo.png"
            alt="AEP Logo"
            className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg object-contain"
          />
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-white">AI Agent Marketplace</h1>
            <p style={{ color: "#9ca3af" }} className="text-xs sm:text-sm">
              Monitoring Dashboard
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 min-h-[44px]">
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: "#10b981", animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite" }}
          />
          <span style={{ color: "#10b981" }} className="text-xs sm:text-sm font-medium">
            Live
          </span>
        </div>
      </div>

      <p style={{ color: "#6b7280" }} className="text-xs mt-3 sm:mt-2">
        Auto-refreshes every 10 seconds
      </p>

      <style>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
      `}</style>
    </header>
  )
}
