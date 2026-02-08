import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, beforeEach } from 'vitest'
import OnboardingTour from './OnboardingTour'
import useUserStore from '../stores/useUserStore'

describe('OnboardingTour', () => {
  beforeEach(() => {
    window.localStorage.clear()
    useUserStore.getState().actions.logout()
  })

  it('shows on first visit and can be skipped', async () => {
    useUserStore.getState().actions.login(
      { id: 'user-1', name: 'Test', email: 'test@example.com' },
      'token'
    )

    const user = userEvent.setup()
    render(<OnboardingTour />)

    expect(screen.getByRole('heading', { name: /Command Center/i })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /pular/i }))
    expect(window.localStorage.getItem('tour-completed:user-1')).toBe('true')
  })
})
