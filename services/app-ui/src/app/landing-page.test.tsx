import React from 'react'
import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'

vi.mock('next/image', () => ({
    default: ({ src, alt, ...rest }: { src: string; alt: string }) => {
        const resolvedSrc = typeof src === 'string' ? src : (src as { src: string }).src
        // eslint-disable-next-line jsx-a11y/alt-text
        return <img src={resolvedSrc} alt={alt} {...rest} />
    },
}))

vi.mock('next/link', () => ({
    default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => (
        <a href={href} {...rest}>
            {children}
        </a>
    ),
}))

vi.mock('next/font/google', () => ({
    Manrope: () => ({ className: 'font-manrope' }),
    Space_Grotesk: () => ({ className: 'font-space-grotesk' }),
}))

vi.mock('@vercel/edge-config', () => ({
    get: async () => null,
}))

vi.mock('../components/landing/Hero3D', () => ({
    Hero3D: () => <div data-testid="hero-3d" />,
}))

vi.mock('../components/landing/LandingHeader', () => ({
    LandingHeader: () => <div data-testid="landing-header" />,
}))

vi.mock('../components/landing/ScrollTracker', () => ({
    ScrollTracker: () => null,
}))

vi.mock('../components/landing/LandingScrollScenes', () => ({
    LandingScrollScenes: () => null,
}))

vi.mock('../components/landing/VideoTracker', () => ({
    VideoTracker: () => null,
}))

vi.mock('../components/landing/FarmScene', () => ({
    FarmScene: () => <div data-testid="farm-scene" />,
}))

vi.mock('../components/landing/MicroScene', () => ({
    MicroScene: () => <div data-testid="micro-scene" />,
}))

vi.mock('../components/landing/TrackLink', () => ({
    TrackLink: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => (
        <a href={href} {...rest}>
            {children}
        </a>
    ),
}))

import LandingPage from './page'

describe('LandingPage', () => {
    it('renders the hero headline and primary CTA', async () => {
        const ui = await LandingPage()
        render(ui as React.ReactElement)

        expect(
            screen.getByRole('heading', { name: /inteligência planetária/i })
        ).toBeInTheDocument()
        expect(screen.getByRole('link', { name: /entrar no futuro/i })).toBeInTheDocument()
    })

    it('renders pricing plans', async () => {
        const ui = await LandingPage()
        render(ui as React.ReactElement)

        expect(screen.getByText(/explorador/i)).toBeInTheDocument()
        expect(screen.getByText(/profissional/i)).toBeInTheDocument()
        expect(screen.getByText(/enterprise/i)).toBeInTheDocument()
    })
})
