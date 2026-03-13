import type { Metadata, Viewport } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Toaster } from "@/components/ui/toaster";
import { UnifiedThemeProvider } from '@/providers/UnifiedThemeProvider';
import { AuthProvider } from '@/contexts/AuthContext';

// Modern font configuration with performance optimizations
const inter = Inter({
  variable: '--font-sans',
  subsets: ['latin-ext', 'latin'],
  display: 'swap',
  preload: true,
  fallback: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
});

const jetbrainsMono = JetBrains_Mono({
  variable: '--font-mono',
  subsets: ['latin-ext', 'latin'],
  display: 'swap',
  preload: false, // Defer monospace font loading
  fallback: ['SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', 'monospace'],
});

// Enhanced metadata for SEO and performance
export const metadata: Metadata = {
  title: {
    default: 'Karen AI',
    template: '%s | Karen AI'
  },
  description: 'Intelligent Assistant Application with advanced AI capabilities and modern user experience',
  keywords: ['AI', 'assistant', 'chat', 'intelligence', 'automation'],
  authors: [{ name: 'Firebase Studio' }],
  creator: 'Firebase Studio',
  publisher: 'Firebase Studio',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://karen-ai.vercel.app',
    title: 'Karen AI',
    description: 'Intelligent Assistant Application with advanced AI capabilities',
    siteName: 'Karen AI',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Karen AI',
    description: 'Intelligent Assistant Application with advanced AI capabilities',
  },
  verification: {
    google: 'your-google-verification-code',
  },
};

// Viewport metadata for responsive design
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#3b82f6' },
    { media: '(prefers-color-scheme: dark)', color: '#1e40af' },
  ],
};

// Performance monitoring for development
if (process.env.NODE_ENV === 'development') {
  // Enable React DevTools Profiler
  if (typeof window !== 'undefined') {
    window.addEventListener('load', () => {
      console.log('🚀 Karen AI - Development Mode');
      console.log('📊 Performance monitoring enabled');
    });
  }
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="dark"
      suppressHydrationWarning
    >
      <head>
        {/* Preconnect to external domains for performance */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        
        {/* DNS prefetch for external resources */}
        <link rel="dns-prefetch" href="https://api.example.com" />
        
        {/* Critical CSS inline (will be populated by build process) */}
        <style dangerouslySetInnerHTML={{
          __html: `
            /* Critical CSS for above-the-fold content */
            body { margin: 0; padding: 0; }
            .loading { display: flex; justify-content: center; align-items: center; height: 100vh; }
          `
        }} />
      </head>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}
        suppressHydrationWarning
      >
        {/* Loading fallback for better UX */}
        <div className="loading" id="initial-loading">
          <div className="animate-pulse text-primary">Loading Karen AI...</div>
        </div>
        
        {/* Main app content */}
        <AuthProvider>
          <UnifiedThemeProvider>
            {children}
            <Toaster />
          </UnifiedThemeProvider>
        </AuthProvider>
        
        {/* Remove loading indicator after app loads */}
        <script dangerouslySetInnerHTML={{
          __html: `
            window.addEventListener('load', function() {
              const loader = document.getElementById('initial-loading');
              if (loader) {
                loader.style.display = 'none';
              }
            });
          `
        }} />
      </body>
    </html>
  );
}
