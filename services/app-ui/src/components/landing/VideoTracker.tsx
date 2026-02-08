'use client'

import { useEffect } from 'react'
import { trackGoal } from '../../lib/analytics'

export function VideoTracker() {
    useEffect(() => {
        const videos = Array.from(document.querySelectorAll<HTMLVideoElement>('video[data-track-video]'))
        if (videos.length === 0) return

        const handlers = new Map<HTMLVideoElement, () => void>()

        videos.forEach((video) => {
            const handler = () => {
                trackGoal('Video Play', { id: video.dataset.trackVideo || 'hero' })
            }
            handlers.set(video, handler)
            video.addEventListener('play', handler, { once: true })
        })

        return () => {
            handlers.forEach((handler, video) => {
                video.removeEventListener('play', handler)
            })
        }
    }, [])

    return null
}
