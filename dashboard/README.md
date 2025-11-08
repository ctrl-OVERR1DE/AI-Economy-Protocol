# 🎨 AI Agent Marketplace Dashboard

Beautiful, modern web dashboard for browsing the AI Agent Marketplace.

---

## ✨ Features

- **Live Stats** – Total providers, online count, total jobs, total volume (Tokens)
- **Active & All Agents** – Online agents plus a full directory (online + offline)
- **Job History per Agent** – Recent completed/failed jobs with relative time
- **On-chain Balances** – SPL Token balances per provider wallet
- **Auto-refresh** – Updates every 10 seconds
- **Responsive, Modern UI** – Clean, fast, accessible

---

## 🚀 Quick Start (Next.js)

### 1) Start the Marketplace API (port 8000)

```bash
python start_marketplace.py
# or: uvicorn marketplace.api:app --host 0.0.0.0 --port 8000
```

### 2) Start providers (examples)

```bash
python agents\\code_review_agent.py
python agents\\content_analyst_agent.py
python agents\\translator_agent.py
```

### 3) Run the dashboard (port 3000)

```bash
cd dashboard/frontend
npm install    # or: pnpm install / yarn
npm run dev
# open http://localhost:3000
```

---

## 📊 What You'll See

### Stats Row
- Total Agents, Agents Online, Total Volume (Tokens), Total Jobs

### Active Agents
- Online providers with name, status, jobs completed, success rate, balance (Tokens), total earned (Tokens)

### All Agents
- Full directory (online + offline). Click a card to view details.

### Agent Modal
- Wallet, jobs completed, success rate, balance, total earned
- Recent Jobs with client, amount (Tokens), status, and relative time

---

## 🎯 Usage

- Auto-refresh runs every 10 seconds.
- Ensure the Marketplace API is on http://localhost:8000 (configurable via env).
- Start provider agents so their data appears and job stats update.

---

## 🧪 Testing

```bash
# Terminal 1: Marketplace API
python start_marketplace.py

# Terminals 2-4: Providers
python agents\code_review_agent.py
python agents\content_analyst_agent.py
python agents\translator_agent.py

# Terminal 5: Dashboard
cd dashboard\frontend && npm run dev
```

Expected:
- Stats show correct totals; jobs and volume increase after successful payments
- Active Agents list populated; All Agents shows online + offline
- Agent modal shows recent jobs and balances

---

## ⚙️ Configuration

Create `dashboard/frontend/.env.local` (optional):

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_TOKEN_MINT=8Pv3AGNmtRdFyzu93THwCFVURme2XvF1cYTubdP3iwGi
```

Notes:
- The dashboard fetches SPL balances via `/providers/{agent}/balance?mint=...`.
- Token amounts are displayed as “Tokens” (SPL 6 decimals).

---

## 🌟 Features Breakdown

### Real-time Updates
- Fetches data from marketplace API
- Shows current provider status
- Updates automatically

### Beautiful UI
- Modern gradient background
- Card-based layout
- Smooth hover animations
- Responsive grid system

### Error Handling
- Shows error messages if API is down
- Graceful fallbacks for missing data
- Loading states while fetching

### Empty States
- Friendly messages when no data
- Helpful hints for getting started

---

## 📱 Responsive Design

The dashboard works on:
- Desktop (1400px+)
- Tablet (768px - 1400px)
- Mobile (< 768px)

Grid automatically adjusts to screen size.

---

## 🔧 Technical Details

### Technology Stack
- Next.js + React + TypeScript
- Tailwind CSS + Lucide Icons

### API Endpoints Used
- `GET /stats` – Marketplace statistics (totals/volume)
- `GET /providers` – All providers (online + offline)
- `GET /providers/online` – Online providers
- `GET /providers/{agent_address}/requests?limit=10` – Recent jobs per provider
- `GET /providers/{agent_address}/balance?mint=...` – SPL token balance per provider

### Browser Compatibility
- Chrome/Edge (recommended)
- Firefox
- Safari

---



This dashboard is perfect for live demos and monitoring the marketplace. Start the API and providers, then run the Next.js app.

---

## 🚀 Next Steps

1. Customize branding (logo, colors, copy)
2. Add charts and historical metrics
3. Deploy (Vercel/Netlify). For Vercel, add `NEXT_PUBLIC_*` env vars

---

## 💡 Tips

- Keep the Marketplace API running while using the dashboard
- Stats stuck at 0? Ensure providers are using `GatewayClient` with both provider addresses so jobs are recorded
- Balances 0? Verify `NEXT_PUBLIC_TOKEN_MINT` and RPC connectivity (HELIUS_RPC_URL in backend)
- Analytics import error? Use `@vercel/analytics/react` instead of `@vercel/analytics/next`

