import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import { Inter } from 'next/font/google'
import '../styles/globals.css'
import { Providers } from './providers'

// Optimize font loading with Next.js font optimization
const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  display: 'swap',
  preload: true,
  variable: '--font-inter',
})

// Next.js requires exporting metadata from layout files; suppress Fast Refresh warning.
// eslint-disable-next-line react-refresh/only-export-components
export const metadata: Metadata = {
  title: 'AI Karen',
  description: 'AI Assistant Interface',
  icons: {
    icon: '/favicon.ico',
  },
}

// Next.js requires a literal string for the `dynamic` export.
// Switch it manually if you need to force dynamic rendering.
// eslint-disable-next-line react-refresh/only-export-components
export const dynamic = 'auto'

// Enable static optimization where possible
// eslint-disable-next-line react-refresh/only-export-components
export const revalidate = 60 // Revalidate every 60 seconds

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <html lang="en" data-scroll-behavior="smooth" className={inter.variable}>
      <head>
        {/* Preconnect to critical domains */}
        <link rel="preconnect" href="http://localhost:8080" />
        <link rel="dns-prefetch" href="http://localhost:8080" />
      </head>
      <body className={`${inter.className} font-sans`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
