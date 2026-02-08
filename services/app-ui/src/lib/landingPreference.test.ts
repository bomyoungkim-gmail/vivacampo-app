import { describe, expect, it, beforeEach } from 'vitest'
import { getLandingPreference, setLandingPreference } from './landingPreference'

describe('landingPreference', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('defaults to dashboard when no preference is set', () => {
    expect(getLandingPreference('user-1')).toBe('dashboard')
  })

  it('persists and reads map preference per user', () => {
    setLandingPreference('user-1', 'map')
    setLandingPreference('user-2', 'dashboard')

    expect(getLandingPreference('user-1')).toBe('map')
    expect(getLandingPreference('user-2')).toBe('dashboard')
  })
})
