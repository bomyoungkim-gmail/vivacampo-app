'use client'

import { beforeEach, describe, expect, it, vi } from 'vitest'
import { trackGoal } from './analytics'

const { trackEventMock } = vi.hoisted(() => ({
    trackEventMock: vi.fn(() => Promise.resolve()),
}))

vi.mock('./api', () => ({
    analyticsAPI: {
        trackEvent: trackEventMock,
    },
}))

vi.mock('../stores/useUserStore', () => ({
    default: {
        getState: () => ({ token: 'token' }),
    },
}))

describe('analytics event tracking', () => {
    beforeEach(() => {
        trackEventMock.mockClear()
    })

    it('sends events to analytics API when authenticated', () => {
        trackGoal('zoom_semantic_transition', { from: 'macro', to: 'meso' })
        expect(trackEventMock).toHaveBeenCalledWith({
            event_name: 'zoom_semantic_transition',
            metadata: { from: 'macro', to: 'meso' },
            phase: 'F2',
        })
    })
})
