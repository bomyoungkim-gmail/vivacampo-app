'use client'

import dynamic from 'next/dynamic'
import { useEffect, useState } from 'react'
import { useReducedMotion } from '../../hooks/useReducedMotion'

const ScrollTracker = dynamic(() => import('./ScrollTracker').then((mod) => mod.ScrollTracker), {
    ssr: false,
})
const LandingScrollScenes = dynamic(() => import('./LandingScrollScenes').then((mod) => mod.LandingScrollScenes), {
    ssr: false,
})
const VideoTracker = dynamic(() => import('./VideoTracker').then((mod) => mod.VideoTracker), {
    ssr: false,
})

export function LandingDesktopEffects() {
    const prefersReducedMotion = useReducedMotion()
    const [isDesktop, setIsDesktop] = useState(false)

    useEffect(() => {
        const update = () => setIsDesktop(window.innerWidth >= 768)
        update()
        window.addEventListener('resize', update)
        return () => window.removeEventListener('resize', update)
    }, [])

    if (!isDesktop || prefersReducedMotion) return null

    return (
        <>
            <ScrollTracker />
            <LandingScrollScenes />
            <VideoTracker />
        </>
    )
}
