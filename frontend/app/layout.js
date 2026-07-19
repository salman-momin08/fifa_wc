import { Inter, Outfit } from 'next/font/google';
import './globals.css';
import SWRegister from './SWRegister';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const outfit = Outfit({
  subsets: ['latin'],
  variable: '--font-outfit',
  display: 'swap',
});

export const viewport = {
  width: 'device-width',
  initialScale: 1,
};

export const metadata = {
  title: 'FIFA World Cup 2026 - Stadium Operations & Fan Portal',
  description: 'AI-Enabled Stadium Wayfinding, Crowd Intelligence, Accessibility Navigation, and Incident Command System',
  manifest: '/manifest.json',
  themeColor: '#0a0f1e',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable}`}>
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#0a0f1e" />
      </head>
      <body>
        {children}
        {/* Service Worker registration (client-only) */}
        <SWRegister />
      </body>
    </html>
  );
}
