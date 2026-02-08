'use client'

import { Canvas } from '@react-three/fiber'
import { Scroll, ScrollControls } from '@react-three/drei'
import { Suspense, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { Experience } from './Experience'

type Hero3DCanvasProps = {
    scrollContent?: ReactNode
}

export function Hero3DCanvas({ scrollContent }: Hero3DCanvasProps) {
    const cameraConfig = useMemo(() => ({ position: [0, 0, 12] as [number, number, number], fov: 45 }), [])
    const scrollRef = useRef<HTMLDivElement | null>(null)
    const [pages, setPages] = useState(6)

    useEffect(() => {
        ;(window as any).__landingPages = pages
    }, [pages])

    useEffect(() => {
        let attempts = 0
        let cancelled = false

        const resolveNode = () => scrollRef.current ?? document.getElementById('landing-scroll-root')

        const updatePages = (node: HTMLElement) => {
            const height = node.scrollHeight
            const viewportHeight = window.innerHeight || 1
            const nextPages = Math.max(1, height / viewportHeight + 0.02)
            setPages((prev) => (Math.abs(prev - nextPages) > 0.02 ? nextPages : prev))
        }

        const ensure = () => {
            if (cancelled) return
            const node = resolveNode()
            if (!node) {
                attempts += 1
                if (attempts < 30) {
                    window.setTimeout(ensure, 100)
                }
                return
            }
            updatePages(node)
        }

        ensure()
        const settleTimers = [
            window.setTimeout(() => {
                const node = resolveNode()
                if (node) updatePages(node)
            }, 150),
            window.setTimeout(() => {
                const node = resolveNode()
                if (node) updatePages(node)
            }, 600),
            window.setTimeout(() => {
                const node = resolveNode()
                if (node) updatePages(node)
            }, 1500),
            window.setTimeout(() => {
                const node = resolveNode()
                if (node) updatePages(node)
            }, 3000),
        ]
        let rafId = 0
        let start = performance.now()
        const tick = (now: number) => {
            if (now - start > 5000) return
            const node = resolveNode()
            if (node) updatePages(node)
            rafId = window.requestAnimationFrame(tick)
        }
        rafId = window.requestAnimationFrame(tick)

        const resizeObserver = new ResizeObserver(() => {
            const node = resolveNode()
            if (node) updatePages(node)
        })
        const initialNode = resolveNode()
        if (initialNode) resizeObserver.observe(initialNode)
        window.addEventListener('resize', () => {
            const node = resolveNode()
            if (node) updatePages(node)
        })
        window.addEventListener('load', () => {
            const node = resolveNode()
            if (node) updatePages(node)
        })

        return () => {
            cancelled = true
            settleTimers.forEach((timer) => window.clearTimeout(timer))
            if (rafId) window.cancelAnimationFrame(rafId)
            resizeObserver.disconnect()
        }
    }, [])

    return (
        <div className="fixed inset-0 z-0">
            <Canvas className="pointer-events-none" camera={cameraConfig} gl={{ antialias: true, alpha: true }}>
                <Suspense fallback={null}>
                    <ScrollControls key={Math.round(pages * 100)} pages={pages} damping={0.3}>
                        <Experience />
                        <Scroll html className="pointer-events-auto">
                            <div ref={scrollRef} id="landing-scroll-root" className="min-h-screen w-screen">
                                {scrollContent}
                            </div>
                        </Scroll>
                    </ScrollControls>
                </Suspense>
            </Canvas>
            <div className="pointer-events-none absolute inset-0">
                <div className="hero-vignette absolute inset-0" />
            </div>
        </div>
    )
}
