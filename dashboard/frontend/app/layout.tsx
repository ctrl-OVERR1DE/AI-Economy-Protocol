import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import { Analytics } from '@vercel/analytics/react'
import './globals.css'

const _geist = Geist({ subsets: ["latin"] });
const _geistMono = Geist_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: 'AI Economy Protocol (x402)',
  description: 'Autonomous agent marketplace with proof-gated payments on Solana',
  generator: 'AEP',
  icons: {
    icon: [
      {
        url: '/aep-logo-32x32.png?v=1',
        sizes: '32x32',
        type: 'image/png',
      },
    ],
    apple: '/aep-logo.png?v=1',
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased" suppressHydrationWarning>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
