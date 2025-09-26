
import type { Metadata, Viewport } from 'next';
import { Inter, Roboto_Mono } from 'next/font/google';
import '../styles/globals.css';
import { Toaster } from "@/components/ui/toaster";
import { Providers } from './providers';
import { ThemeBridge } from "@/components/theme/ThemeBridge";
import Script from 'next/script';
import { HealthStatusBadge } from '@/components/ui/health-status-badge';

const inter = Inter({
  variable: '--font-sans',
  subsets: ['latin'],
  display: 'swap',
});

const robotoMono = Roboto_Mono({
  variable: '--font-mono',
  subsets: ['latin'],
  display: 'swap',
});

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
      </head>
      <body className={`${inter.variable} ${robotoMono.variable} font-sans antialiased scroll-smooth`}>
        {/* Skip to main content link for accessibility */}
        <a
          href="#main-content"
          className="skip-link sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary text-primary-foreground px-4 py-2 rounded-md z-50 interactive"
          aria-label="Skip to main content"
        >
          Skip to main content
        </a>
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
                    });
                    return false;
                  }
                });
              })();
            `,
          }}
        />
        
        <ThemeBridge>
          <Providers>
            <HealthStatusBadge />
            <main
              id="main-content"
              role="main"
              tabIndex={-1}
              className="min-h-dvh focus:outline-none smooth-transition content-area"
            >
              <div className="container-fluid modern-layout-root">
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
