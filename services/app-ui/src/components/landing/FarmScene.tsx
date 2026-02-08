'use client'

import { Canvas, useFrame } from '@react-three/fiber'
import { OrthographicCamera, Stats, useTexture } from '@react-three/drei'
import { Suspense, useEffect, useMemo, useRef, useState } from 'react'
import type { Mesh } from 'three'
import { useReducedMotion } from '../../hooks/useReducedMotion'

function FarmPlane() {
    const meshRef = useRef<Mesh>(null)
    const texture = useTexture('/landing/farm-zoom.png')

    useFrame(({ clock }) => {
        if (!meshRef.current) return
        const t = clock.getElapsedTime()
        meshRef.current.rotation.z = Math.sin(t * 0.1) * 0.002
    })

    return (
        <mesh ref={meshRef} rotation-x={-Math.PI / 2.4}>
            <planeGeometry args={[14, 10, 32, 32]} />
            <meshStandardMaterial map={texture} roughness={0.8} metalness={0.05} />
        </mesh>
    )
}

function FarmCanvas() {
    return (
        <Canvas className="absolute inset-0" gl={{ antialias: true }}>
            <Suspense fallback={null}>
                <OrthographicCamera makeDefault position={[0, 8, 8]} zoom={70} />
                <ambientLight intensity={0.6} />
                <directionalLight position={[4, 6, 4]} intensity={1} />
                <FarmPlane />
                {process.env.NODE_ENV === 'development' ? <Stats /> : null}
            </Suspense>
        </Canvas>
    )
}

export function FarmScene() {
    const prefersReducedMotion = useReducedMotion()
    const [isVisible, setIsVisible] = useState(false)
    const containerRef = useRef<HTMLDivElement | null>(null)

    useEffect(() => {
        const target = containerRef.current
        if (!target || prefersReducedMotion) return

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setIsVisible(true)
                    }
                })
            },
            { threshold: 0.25 },
        )

        observer.observe(target)

        return () => observer.disconnect()
    }, [prefersReducedMotion])

    const shouldRender = useMemo(() => !prefersReducedMotion && isVisible, [isVisible, prefersReducedMotion])

    return (
        <div ref={containerRef} className="absolute inset-0">
            {shouldRender ? <FarmCanvas /> : null}
        </div>
    )
}
