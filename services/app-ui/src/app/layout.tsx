import './globals.css'
import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import { ThemeProvider } from '@/contexts/ThemeContext'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
    title: 'VivaCampo - Monitoramento Agrícola',
    description: 'Plataforma de monitoramento agrícola via satélite',
    manifest: '/manifest.json',
}

export const viewport: Viewport = {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
    themeColor: '#16a34a',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="pt-BR" suppressHydrationWarning>
            <body className={inter.className}>
                <ThemeProvider>
                    {children}
                </ThemeProvider>
            </body>
        </html>
    )
}
