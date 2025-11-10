import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import '@fontsource/inter'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import '../styles/globals.css'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'AI Karen',
  description: 'AI Assistant Interface',
}

// Force dynamic rendering
export const dynamic = 'force-dynamic'

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}