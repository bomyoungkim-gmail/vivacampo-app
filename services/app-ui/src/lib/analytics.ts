'use client'

import useUserStore from '../stores/useUserStore'
import { analyticsAPI } from './api'

export type AnalyticsProps = Record<string, string | number | boolean>

type AnalyticsPhase = 'F1' | 'F2' | 'F3'

const EVENT_PHASE_MAP: Record<string, AnalyticsPhase> = {
    onboarding_step: 'F1',
    zoom_semantic_transition: 'F2',
    aoi_selected: 'F2',
    aoi_created: 'F2',
    aoi_batch_created: 'F2',
    bottom_sheet_interaction: 'F3',
}

export function trackGoal(goalName: string, metadata?: AnalyticsProps) {
    if (typeof window !== 'undefined' && typeof window.plausible === 'function') {
        window.plausible(goalName, { props: metadata })
    }

    if (typeof window !== 'undefined') {
        const token = useUserStore.getState().token
        if (token) {
            const phase = EVENT_PHASE_MAP[goalName]
            analyticsAPI.trackEvent({ event_name: goalName, metadata, phase }).catch(() => null)
        }
    }

    if (process.env.NODE_ENV === 'development') {
        // eslint-disable-next-line no-console
        console.log('Goal:', goalName, metadata)
    }
}

declare global {
    interface Window {
        plausible?: (event: string, options?: { props?: AnalyticsProps }) => void
    }
}
