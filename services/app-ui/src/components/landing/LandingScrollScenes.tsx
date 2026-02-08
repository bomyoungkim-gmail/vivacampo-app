'use client'

import { useEffect } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

export function LandingScrollScenes() {
    useEffect(() => {
        gsap.registerPlugin(ScrollTrigger)

        ScrollTrigger.create({
            trigger: '#hero',
            start: 'top top',
            end: '+=80%',
            pin: true,
            pinSpacing: true,
        })

        gsap.fromTo(
            '.farm-zoom-card',
            { scale: 0.96, y: 20 },
            {
                scale: 1.02,
                y: -10,
                scrollTrigger: {
                    trigger: '#journey',
                    start: 'top 70%',
                    end: 'bottom 40%',
                    scrub: true,
                },
            },
        )

        gsap.fromTo(
            '.farm-lines path',
            { strokeDashoffset: 1000 },
            {
                strokeDashoffset: 0,
                scrollTrigger: {
                    trigger: '#journey',
                    start: 'top 75%',
                    end: 'bottom 60%',
                    scrub: true,
                },
            },
        )

        gsap.fromTo(
            '.micro-card',
            { opacity: 0, y: 40 },
            {
                opacity: 1,
                y: 0,
                scrollTrigger: {
                    trigger: '#micro',
                    start: 'top 70%',
                    end: 'bottom 50%',
                    scrub: true,
                },
            },
        )

        gsap.fromTo(
            '.micro-visual',
            { scale: 0.95, y: 20 },
            {
                scale: 1.02,
                y: -10,
                scrollTrigger: {
                    trigger: '#micro',
                    start: 'top 75%',
                    end: 'bottom 45%',
                    scrub: true,
                },
            },
        )

        return () => {
            ScrollTrigger.getAll().forEach((trigger) => trigger.kill())
        }
    }, [])

    return null
}
