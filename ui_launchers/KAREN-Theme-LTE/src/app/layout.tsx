import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { UnifiedThemeProvider } from '@/providers/UnifiedThemeProvider'
import { AuthProvider } from '@/contexts/AuthContext'
import { AccessibilityProvider } from '@/contexts/AccessibilityContext'
import { initializeAccessibility } from '@/components/accessibility'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Karen AI - Refactored Theme',
  description: 'Intelligent AI assistant with modern interface and comprehensive accessibility features',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Initialize accessibility system
  initializeAccessibility();
  
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} karen-app`}>
        <AccessibilityProvider>
          <UnifiedThemeProvider>
            <AuthProvider>
              {children}
            </AuthProvider>
          </UnifiedThemeProvider>
        </AccessibilityProvider>
      </body>
    </html>
  )
}