import React from 'react'
import Script from 'next/script'
import { get } from '@vercel/edge-config'
import { Manrope, Space_Grotesk } from 'next/font/google'
import { Hero3D } from '../components/landing/Hero3D'
import { LandingHeader } from '../components/landing/LandingHeader'
import { LandingScrollContent } from '../components/landing/LandingScrollContent'

const displayFont = Space_Grotesk({
    subsets: ['latin'],
    weight: ['600'],
    display: 'optional',
    preload: true,
    variable: '--font-display',
})
const bodyFont = Manrope({
    subsets: ['latin'],
    weight: ['400', '500'],
    display: 'swap',
    preload: true,
    variable: '--font-body',
})

const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'VivaCampo',
    applicationCategory: 'BusinessApplication',
    operatingSystem: 'Web, iOS, Android',
    offers: {
        '@type': 'Offer',
        price: '0',
        priceCurrency: 'BRL',
        priceValidUntil: '2026-12-31',
    },
    aggregateRating: {
        '@type': 'AggregateRating',
        ratingValue: '4.8',
        ratingCount: '127',
    },
    description: 'Plataforma de agricultura de precisão com IA e satélite',
}

async function getCtaVariant() {
    if (!process.env.EDGE_CONFIG) return null
    try {
        const variant = await get('cta_variant')
        return typeof variant === 'string' ? variant : null
    } catch (error) {
        return null
    }
}

export default async function LandingPage() {
    const ctaVariant = await getCtaVariant()
    const heroCtaText = ctaVariant || 'Entrar no futuro'

    return (
        <div className={`${bodyFont.className} ${bodyFont.variable} ${displayFont.variable} min-h-screen bg-[#050505] text-white`}>
            <Script
                defer
                data-domain={process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN || 'vivacampo.ag'}
                src="https://plausible.io/js/script.js"
            />
            <Script
                id="vivacampo-ld"
                type="application/ld+json"
                dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
            />

            <a
                href="#content"
                className="sr-only focus:not-sr-only focus:fixed focus:left-6 focus:top-6 focus:z-[100] focus:rounded-full focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-black"
            >
                Pular para o conteúdo
            </a>

            <LandingHeader displayClassName={displayFont.className} />
            <Hero3D
                scrollContent={(
                    <LandingScrollContent
                        displayFontClassName={displayFont.className}
                        heroCtaText={heroCtaText}
                    />
                )}
            />
        </div>
    )
}
