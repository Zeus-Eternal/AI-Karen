import type { Metadata } from 'next'
import '@fontsource/inter'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import '../styles/globals.css'
import { AuthProvider } from '@/contexts/AuthContext'
import { ThemeProvider } from '@/providers/theme-provider'
import { HookProvider } from '@/contexts/HookContext'

export const metadata: Metadata = {
  title: 'AI Karen',
  description: 'AI Assistant Interface',
}

// Force dynamic rendering
export const dynamic = 'force-dynamic'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        <ThemeProvider>
          <HookProvider>
            <AuthProvider>
              {children}
            </AuthProvider>
          </HookProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}