'use client'

import { useFrame } from '@react-three/fiber'
import { useScroll, useTexture } from '@react-three/drei'
import { useMemo, useRef } from 'react'
import { MathUtils, MeshStandardMaterial, Fog } from 'three'
import { EarthGlobe } from './EarthGlobe'

export function Experience() {
    const scroll = useScroll()
    const farmTexture = useTexture('/landing/farm-zoom.png')
    const farmOverlayTexture = useTexture('/landing/farm-zoom.png')
    const microTexture = useTexture('/landing/micro-analysis.png')
    const microOverlayTexture = useTexture('/landing/micro-analysis.png')
    const farmMaterialRef = useRef<MeshStandardMaterial | null>(null)
    const farmOverlayRef = useRef<MeshStandardMaterial | null>(null)
    const microMaterialRef = useRef<MeshStandardMaterial | null>(null)
    const microOverlayRef = useRef<MeshStandardMaterial | null>(null)
    const ranges = useMemo(
        () => ({
            hero: [0, 0.2],
            transition: [0.2, 0.4],
            farm: [0.4, 0.68],
            micro: [0.68, 0.9],
            outro: [0.9, 1],
        }),
        [],
    )
    const fogRef = useRef<Fog | null>(null)
    const snapLockRef = useRef({ stage: 'hero', until: 0 })

    useFrame((state, delta) => {
        const heroRange = scroll.range(ranges.hero[0], ranges.hero[1] - ranges.hero[0])
        const transitionRange = scroll.range(ranges.transition[0], ranges.transition[1] - ranges.transition[0])
        const farmRange = scroll.range(ranges.farm[0], ranges.farm[1] - ranges.farm[0])
        const microRange = scroll.range(ranges.micro[0], ranges.micro[1] - ranges.micro[0])
        const now = state.clock.getElapsedTime()

        let targetX = 0
        let targetY = 0
        let targetZ = 12

        if (heroRange > 0 && transitionRange === 0) {
            targetZ = MathUtils.lerp(12, 10.5, heroRange)
            targetY = MathUtils.lerp(0, 0.4, heroRange)
        }

        if (transitionRange > 0 && farmRange === 0) {
            targetZ = MathUtils.lerp(10.5, 7.4, transitionRange)
            targetY = MathUtils.lerp(0.4, 1.1, transitionRange)
            targetX = MathUtils.lerp(0, -0.5, transitionRange)
        }

        if (farmRange > 0 && microRange === 0) {
            targetZ = MathUtils.lerp(7.4, 4.8, farmRange)
            targetY = MathUtils.lerp(1.1, 0.7, farmRange)
            targetX = MathUtils.lerp(-0.5, -1.1, farmRange)
        }

        if (microRange > 0) {
            targetZ = MathUtils.lerp(4.8, 3.2, microRange)
            targetY = MathUtils.lerp(0.7, 0.3, microRange)
            targetX = MathUtils.lerp(-1.1, -1.7, microRange)
        }

        // Snap + focus lock for section entries
        const nextStage =
            microRange > 0.02
                ? 'micro'
                : farmRange > 0.02
                    ? 'farm'
                    : transitionRange > 0.02
                        ? 'transition'
                        : 'hero'

        if (snapLockRef.current.stage !== nextStage) {
            snapLockRef.current = { stage: nextStage, until: now + 1.2 }
        }

        const isLocked = now < snapLockRef.current.until
        const focusZ = nextStage === 'micro' ? 3.0 : nextStage === 'farm' ? 5.0 : nextStage === 'transition' ? 7.8 : 10.5
        const focusX = nextStage === 'micro' ? -1.4 : nextStage === 'farm' ? -0.8 : nextStage === 'transition' ? -0.3 : 0
        const focusY = nextStage === 'micro' ? 0.3 : nextStage === 'farm' ? 0.7 : nextStage === 'transition' ? 1.0 : 0.3

        if (isLocked) {
            targetZ = MathUtils.damp(targetZ, focusZ, 5, delta)
            targetX = MathUtils.damp(targetX, focusX, 5, delta)
            targetY = MathUtils.damp(targetY, focusY, 5, delta)
        }

        state.camera.position.x = MathUtils.damp(state.camera.position.x, targetX, 3, delta)
        state.camera.position.y = MathUtils.damp(state.camera.position.y, targetY, 3, delta)
        state.camera.position.z = MathUtils.damp(state.camera.position.z, targetZ, 3, delta)
        state.camera.lookAt(0, 0, 0)

        if (fogRef.current) {
            const fogTarget = MathUtils.clamp(0.1 + transitionRange * 0.9 + farmRange * 0.6, 0.1, 1)
            fogRef.current.near = MathUtils.damp(fogRef.current.near, 4 + fogTarget * 3, 3, delta)
            fogRef.current.far = MathUtils.damp(fogRef.current.far, 18 - fogTarget * 6, 3, delta)
        }

        if (farmMaterialRef.current) {
            const targetOpacity = MathUtils.clamp(farmRange * 1.15, 0, 1)
            farmMaterialRef.current.opacity = MathUtils.damp(farmMaterialRef.current.opacity, targetOpacity, 4, delta)
            farmMaterialRef.current.transparent = true
        }

        if (farmOverlayRef.current) {
            const targetOpacity = MathUtils.clamp(farmRange * 1.0, 0, 0.65)
            farmOverlayRef.current.opacity = MathUtils.damp(farmOverlayRef.current.opacity, targetOpacity, 4, delta)
            farmOverlayRef.current.transparent = true
        }

        if (microMaterialRef.current) {
            const targetOpacity = MathUtils.clamp(microRange * 1.2, 0, 1)
            microMaterialRef.current.opacity = MathUtils.damp(microMaterialRef.current.opacity, targetOpacity, 4, delta)
            microMaterialRef.current.transparent = true
        }

        if (microOverlayRef.current) {
            const targetOpacity = MathUtils.clamp(microRange * 1.0, 0, 0.6)
            microOverlayRef.current.opacity = MathUtils.damp(microOverlayRef.current.opacity, targetOpacity, 4, delta)
            microOverlayRef.current.transparent = true
        }
    })

    return (
        <>
            <fog ref={fogRef} attach="fog" args={['#050505', 6, 16]} />
            <EarthGlobe />
            <group position={[0, -1.4, -2.8]}>
                <mesh rotation-x={-Math.PI / 2.4}>
                    <planeGeometry args={[10, 7, 32, 32]} />
                    <meshStandardMaterial ref={farmMaterialRef} map={farmTexture} roughness={0.85} metalness={0.05} opacity={0} />
                </mesh>
                <mesh rotation-x={-Math.PI / 2.4} position={[0.2, 0.05, 0.3]}>
                    <planeGeometry args={[9.4, 6.5, 8, 8]} />
                    <meshStandardMaterial ref={farmOverlayRef} map={farmOverlayTexture} roughness={0.9} metalness={0.02} opacity={0} />
                </mesh>
            </group>
            <group position={[0.6, -0.6, -1.6]}>
                <mesh rotation-x={-Math.PI / 2.1}>
                    <planeGeometry args={[7.5, 5.5, 32, 32]} />
                    <meshStandardMaterial ref={microMaterialRef} map={microTexture} roughness={0.75} metalness={0.1} opacity={0} />
                </mesh>
                <mesh rotation-x={-Math.PI / 2.1} position={[-0.15, 0.04, 0.25]}>
                    <planeGeometry args={[6.7, 4.8, 8, 8]} />
                    <meshStandardMaterial ref={microOverlayRef} map={microOverlayTexture} roughness={0.8} metalness={0.08} opacity={0} />
                </mesh>
            </group>
        </>
    )
}
