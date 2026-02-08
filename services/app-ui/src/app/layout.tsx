import './globals.css'
import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import { Analytics } from '@vercel/analytics/react'
import { ThemeProvider } from '@/contexts/ThemeContext'

const inter = Inter({ subsets: ['latin'], display: 'swap', variable: '--font-inter' })

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://vivacampo.ag'

export const metadata: Metadata = {
    metadataBase: new URL(siteUrl),
    title: 'VivaCampo - Inteligência Planetária para Agricultura',
    description:
        'Monitore sua fazenda do satélite à raiz. IA que detecta pragas, otimiza irrigação e prediz produtividade com 98% de precisão.',
    keywords: [
        'agricultura de precisão',
        'IA agricultura',
        'satélite agricultura',
        'NDVI',
        'monitoramento de lavoura',
    ],
    authors: [{ name: 'VivaCampo' }],
    creator: 'VivaCampo',
    manifest: '/manifest.json',
    appleWebApp: {
        capable: true,
        statusBarStyle: 'black-translucent',
        title: 'VivaCampo',
    },
    openGraph: {
        type: 'website',
        locale: 'pt_BR',
        url: siteUrl,
        title: 'VivaCampo - Inteligência Planetária para Agricultura',
        description: 'Monitore sua fazenda do satélite à raiz.',
        siteName: 'VivaCampo',
        images: [
            {
                url: '/og-image.png',
                width: 1200,
                height: 630,
                alt: 'VivaCampo Platform',
            },
        ],
    },
    twitter: {
        card: 'summary_large_image',
        title: 'VivaCampo - Inteligência Planetária',
        description: 'Monitore sua fazenda do satélite à raiz.',
        images: ['/twitter-image.png'],
        creator: '@vivacampo',
    },
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
    icons: {
        icon: '/favicon.ico',
        shortcut: '/favicon-16x16.png',
        apple: '/apple-touch-icon.png',
    },
}

export const viewport: Viewport = {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 5,
    themeColor: '#050505',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="pt-BR" suppressHydrationWarning>
            <body className={`${inter.className} overflow-x-hidden`}>
                <ThemeProvider>
                    {children}
                    <Analytics />
                </ThemeProvider>
            </body>
        </html>
    )
}
