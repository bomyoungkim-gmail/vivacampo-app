'use client'

import dynamic from 'next/dynamic'
import { useReducedMotion } from '../../hooks/useReducedMotion'

const Hero3DCanvas = dynamic(() => import('./Hero3DCanvas').then((mod) => mod.Hero3DCanvas), {
    ssr: false,
})

type Hero3DProps = {
    scrollContent?: React.ReactNode
}

export function Hero3D({ scrollContent }: Hero3DProps) {
    const prefersReducedMotion = useReducedMotion()

    if (prefersReducedMotion) {
        return <div>{scrollContent}</div>
    }

    return <Hero3DCanvas scrollContent={scrollContent} />
}
