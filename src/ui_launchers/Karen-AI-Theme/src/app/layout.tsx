
import type { Metadata } from 'next';
import { Inter, Roboto_Mono } from 'next/font/google';
import './globals.css';
import { Toaster } from "@/components/ui/toaster";
import { ThemeProvider } from '@/providers/theme-provider';
import { PluginRegistryProvider } from '@/plugin_host/registry';
import { MessageInjectionProvider } from '@/providers/MessageInjectionProvider';
import SessionWarning from '@/components/SessionWarning';

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
  description: 'Intelligent Assistant Application by Firebase Studio',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${robotoMono.variable} font-sans antialiased`}>
        <ThemeProvider>
          <PluginRegistryProvider>
            <MessageInjectionProvider>
              <SessionWarning />
              {children}
              <Toaster />
            </MessageInjectionProvider>
          </PluginRegistryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
