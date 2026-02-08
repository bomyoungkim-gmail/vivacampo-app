export type LandingPreference = 'dashboard' | 'map'

const STORAGE_PREFIX = 'landing-preference'

function getStorageKey(userId: string) {
  return `${STORAGE_PREFIX}:${userId}`
}

export function getLandingPreference(userId?: string | null): LandingPreference {
  if (!userId || typeof window === 'undefined') return 'dashboard'
  const raw = window.localStorage.getItem(getStorageKey(userId))
  return raw === 'map' ? 'map' : 'dashboard'
}

export function setLandingPreference(userId: string, preference: LandingPreference): void {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(getStorageKey(userId), preference)
}
