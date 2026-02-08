'use client'

import { useFrame } from '@react-three/fiber'
import { Detailed } from '@react-three/drei'
import { useEffect, useRef, useState } from 'react'
import type { Mesh } from 'three'
import { AdditiveBlending, BackSide, Color } from 'three'
import { useCompressedTexture } from '@/hooks/useCompressedTexture'

export function EarthGlobe() {
    const globeRef = useRef<Mesh>(null)
    const cloudsRef = useRef<Mesh>(null)
    const [segments, setSegments] = useState(64)
    const debug = process.env.NODE_ENV !== 'production'

    // KTX2 com fallback automático para JPG/PNG
    const [dayMap, cloudsMap] = useCompressedTexture([
        {
            ktx2: '/textures/compressed/earth_day.ktx2',
            fallback: '/textures/earth_day_2048.jpg',
            mobile: '/textures/compressed/earth_day_mobile.ktx2',
        },
        {
            ktx2: '/textures/compressed/earth_clouds.ktx2',
            fallback: '/textures/earth_clouds_1024.png',
        },
    ])

    useEffect(() => {
        const cores = navigator.hardwareConcurrency || 4
        if (cores <= 4) {
            setSegments(32)
        }
    }, [])

    useEffect(() => {
        if (debug) {
            console.log('🧪 EarthGlobe mount')
        }
        return () => {
            if (debug) {
                console.log('🧪 EarthGlobe unmount')
            }
        }
    }, [debug])

    useEffect(() => {
        if (!debug) return
        if (!dayMap || !cloudsMap) {
            console.log('🧪 EarthGlobe waiting for textures', { dayMap: !!dayMap, cloudsMap: !!cloudsMap })
        } else {
            console.log('🧪 EarthGlobe textures ready')
        }
    }, [debug, dayMap, cloudsMap])

    useFrame(() => {
        if (globeRef.current) {
            globeRef.current.rotation.y += 0.001
        }
        if (cloudsRef.current) {
            cloudsRef.current.rotation.y += 0.0015
        }
    })

    // Loading state - aguardar texturas carregarem
    if (!dayMap || !cloudsMap) {
        return null // Ou retornar <Skeleton /> se preferir
    }

    return (
        <group>
            <ambientLight intensity={0.25} />
            <directionalLight position={[6, 3, 6]} intensity={1.4} />
            <pointLight position={[-6, -2, -6]} intensity={0.4} color={new Color('#3b82f6')} />
            <Detailed distances={[0, 12, 20]}>
                <mesh ref={globeRef}>
                    <sphereGeometry args={[5, segments, segments]} />
                    <meshStandardMaterial map={dayMap} metalness={0.1} roughness={0.7} />
                </mesh>
                <mesh>
                    <sphereGeometry args={[5, 24, 24]} />
                    <meshStandardMaterial map={dayMap} metalness={0.05} roughness={0.8} />
                </mesh>
                <mesh>
                    <sphereGeometry args={[5, 16, 16]} />
                    <meshStandardMaterial map={dayMap} metalness={0.05} roughness={0.85} />
                </mesh>
            </Detailed>
            <mesh scale={1.04}>
                <sphereGeometry args={[5, 64, 64]} />
                <meshBasicMaterial
                    color={new Color('#38bdf8')}
                    blending={AdditiveBlending}
                    transparent
                    opacity={0.18}
                    side={BackSide}
                />
            </mesh>
            <mesh ref={cloudsRef} scale={1.02}>
                <sphereGeometry args={[5, 64, 64]} />
                <meshStandardMaterial
                    map={cloudsMap}
                    transparent
                    opacity={0.35}
                    metalness={0}
                    roughness={1}
                    depthWrite={false}
                />
            </mesh>
        </group>
    )
}
