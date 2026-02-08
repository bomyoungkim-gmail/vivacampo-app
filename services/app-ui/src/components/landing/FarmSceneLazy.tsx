'use client'

import dynamic from 'next/dynamic'
import { useEffect, useState } from 'react'
import { useReducedMotion } from '../../hooks/useReducedMotion'

const FarmScene = dynamic(() => import('./FarmScene').then((mod) => mod.FarmScene), {
    ssr: false,
})

export function FarmSceneLazy() {
    const prefersReducedMotion = useReducedMotion()
    const [isDesktop, setIsDesktop] = useState(false)

    useEffect(() => {
        const update = () => setIsDesktop(window.innerWidth >= 768)
        update()
        window.addEventListener('resize', update)
        return () => window.removeEventListener('resize', update)
    }, [])

    if (!isDesktop || prefersReducedMotion) return null

    return <FarmScene />
}
