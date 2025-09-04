
import type { Metadata, Viewport } from 'next';
import { Inter, Roboto_Mono } from 'next/font/google';
import '../styles/globals.css';
import { Toaster } from "@/components/ui/toaster";
import { Providers } from './providers';
import { ThemeBridge } from "@/components/theme/ThemeBridge";
import Script from 'next/script';

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
  title: 'Karen AI',
  description: 'Intelligent Assistant Application by Agustealo Studio',
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
      <body className={`${inter.variable} ${robotoMono.variable} font-sans antialiased`}>
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
        
        {/* Accessible skip link for keyboard users */}
        <a href="#content" className="skip-link">Skip to content</a>
        <ThemeBridge>
          <Providers>
            <main id="content" role="main" className="min-h-dvh focus:outline-none">
              {children}
            </main>
          </Providers>
        </ThemeBridge>
        <Toaster />
      </body>
    </html>
  );
}
