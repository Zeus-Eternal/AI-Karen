
import React from 'react';
import type { Metadata, Viewport } from 'next';
// Temporarily disabled Google Fonts due to network issues during build
// import { Inter } from 'next/font/google';
import '../styles/globals.css';
import { Toaster } from "@/components/ui/toaster";
import { Providers } from './providers';
import { ThemeBridge } from "@/components/theme/ThemeBridge";
import Script from 'next/script';
import { HealthStatusBadge } from '@/components/ui/health-status-badge';
import { SkipLinks, ColorBlindnessFilters } from '@/components/accessibility';
import { GlobalDegradationBanner } from '@/components/graceful-degradation/GlobalDegradationBanner';

// Import early extension fix first
import '@/lib/early-extension-fix';

// Import extension error recovery system early
import '@/lib/init-extension-error-recovery';

// Temporarily disabled Google Fonts due to network issues during build
// const inter = Inter({
//   variable: '--font-sans',
//   subsets: ['latin'],
//   display: 'swap',
//   preload: false,
//   fallback: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
// });

export const metadata: Metadata = {
  title: 'Karen AI - Intelligent Assistant',
  description: 'Advanced AI-powered intelligent assistant platform by Agustealo Studio. Experience seamless AI interactions, data analysis, and automation.',
  keywords: ['AI', 'assistant', 'artificial intelligence', 'automation', 'chat'],
  authors: [{ name: 'Agustealo Studio' }],
  creator: 'Agustealo Studio',
  openGraph: {
    title: 'Karen AI - Intelligent Assistant',
    description: 'Advanced AI-powered intelligent assistant platform',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Karen AI - Intelligent Assistant',
    description: 'Advanced AI-powered intelligent assistant platform',
  },
  robots: {
    index: false, // Prevent indexing in development/staging
    follow: false,
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  themeColor: [
    { media: '(prefers-color-scheme: dark)', color: '#1e1e1e' },
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="color-scheme" content="light dark" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className={`${inter.variable} font-sans antialiased scroll-smooth`}>
        {/* Console error fix script - load early to prevent interceptor issues */}
        <Script
          id="console-error-fix"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                if (typeof window === 'undefined') return;
                
                const originalConsoleError = console.error;
                const originalConsoleWarn = console.warn;
                
                console.error = function(...args) {
                  try {
                    const errorMessage = args[0]?.toString() || '';
                    if (
                      errorMessage.includes('console-error.js') ||
                      errorMessage.includes('use-error-handler.js') ||
                      errorMessage.includes('intercept-console-error.js') ||
                      (errorMessage.includes('ChatInterface') && errorMessage.includes('sendMessage'))
                    ) {
                      originalConsoleError.apply(console, ['[SAFE]', ...args]);
                      return;
                    }
                    originalConsoleError.apply(console, args);
                  } catch (e) {
                    originalConsoleError.apply(console, args);
                  }
                };
                
                window.addEventListener('error', function(event) {
                  if (
                    event.error?.stack?.includes('console-error.js') ||
                    event.error?.stack?.includes('use-error-handler.js') ||
                    event.error?.stack?.includes('intercept-console-error.js')
                  ) {
                    event.preventDefault();
                    event.stopPropagation();
                    originalConsoleError('[SAFE] Prevented console interceptor error:', {
                      message: event.error?.message,
                      filename: event.filename,
                      lineno: event.lineno,
                      colno: event.colno,

                    return false;
                  }

              })();
            `,
          }}
        />
        <SkipLinks />
        <ColorBlindnessFilters />
        <ThemeBridge>
          <Providers>
            <GlobalDegradationBanner />
            <HealthStatusBadge />
            <main id="main-content" role="main" className="min-h-dvh focus:outline-none smooth-transition" tabIndex={-1}>
              <div className="modern-layout-root">
                {children}
              </div>
            </main>
          </Providers>
        </ThemeBridge>
        <Toaster />
      </body>
    </html>
  );
}
