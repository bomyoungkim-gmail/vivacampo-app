'use client'

import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Stats } from '@react-three/drei'
import { Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { BufferGeometry, Float32BufferAttribute, ShaderMaterial } from 'three'
import { useReducedMotion } from '../../hooks/useReducedMotion'

function ParticleField({ count = 500 }: { count?: number }) {
    const geometry = useMemo(() => {
        const positions = new Float32Array(count * 3)
        for (let i = 0; i < count; i += 1) {
            positions[i * 3] = (Math.random() - 0.5) * 8
            positions[i * 3 + 1] = Math.random() * 4
            positions[i * 3 + 2] = (Math.random() - 0.5) * 4
        }
        const geo = new BufferGeometry()
        geo.setAttribute('position', new Float32BufferAttribute(positions, 3))
        return geo
    }, [count])

    return (
        <points geometry={geometry}>
            <pointsMaterial color="#38bdf8" size={0.04} opacity={0.6} transparent />
        </points>
    )
}

function ScanPlane() {
    const materialRef = useRef<ShaderMaterial>(null)

    useFrame((_, delta) => {
        if (materialRef.current) {
            materialRef.current.uniforms.uTime.value += delta
        }
    })

    return (
        <mesh position={[0, 1.2, 0]} rotation-x={-Math.PI / 2.3}>
            <planeGeometry args={[8, 6, 1, 1]} />
            <shaderMaterial
                ref={materialRef}
                transparent
                uniforms={{ uTime: { value: 0 } }}
                vertexShader={`
                    varying vec2 vUv;
                    void main() {
                      vUv = uv;
                      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                    }
                `}
                fragmentShader={`
                    varying vec2 vUv;
                    uniform float uTime;
                    void main() {
                      float scan = abs(sin(uTime * 0.8 + vUv.x * 3.14));
                      float line = smoothstep(0.45, 0.5, scan);
                      vec3 color = vec3(0.06, 0.9, 0.6);
                      float alpha = line * 0.35;
                      gl_FragColor = vec4(color, alpha);
                    }
                `}
            />
        </mesh>
    )
}

function MicroCanvas() {
    return (
        <Canvas className="absolute inset-0" gl={{ antialias: true }} camera={{ position: [0, 3, 6], fov: 50 }}>
            <Suspense fallback={null}>
                <ambientLight intensity={0.5} />
                <directionalLight position={[2, 4, 2]} intensity={1.1} />
                <ParticleField count={500} />
                <ScanPlane />
                <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.3} />
                {process.env.NODE_ENV === 'development' ? <Stats /> : null}
            </Suspense>
        </Canvas>
    )
}

export function MicroScene() {
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

    return (
        <div ref={containerRef} className="absolute inset-0">
            {!prefersReducedMotion && isVisible ? <MicroCanvas /> : null}
        </div>
    )
}
