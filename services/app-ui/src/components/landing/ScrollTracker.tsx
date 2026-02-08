'use client'

import { useEffect, useRef } from 'react'
import { trackGoal } from '../../lib/analytics'

const SCROLL_MILESTONES = [25, 50, 75, 100]

export function ScrollTracker() {
    const milestonesRef = useRef(new Set<number>())

    useEffect(() => {
        const handleScroll = () => {
            const scrollTop = window.scrollY
            const docHeight = document.documentElement.scrollHeight - window.innerHeight
            if (docHeight <= 0) return

            const progress = Math.round((scrollTop / docHeight) * 100)
            SCROLL_MILESTONES.forEach((milestone) => {
                if (progress >= milestone && !milestonesRef.current.has(milestone)) {
                    milestonesRef.current.add(milestone)
                    trackGoal('Scroll Depth', { milestone })
                }
            })
        }

        window.addEventListener('scroll', handleScroll, { passive: true })
        handleScroll()

        return () => window.removeEventListener('scroll', handleScroll)
    }, [])

    useEffect(() => {
        const pricing = document.getElementById('planos')
        if (!pricing || !('IntersectionObserver' in window)) return

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        trackGoal('Pricing View')
                    }
                })
            },
            { threshold: 0.35 },
        )

        observer.observe(pricing)

        return () => observer.disconnect()
    }, [])

    return null
}
