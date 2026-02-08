export type SpatialAnalyticsProps = Record<string, string | number | boolean>

export function trackSpatialEvent(event: string, props?: SpatialAnalyticsProps) {
  if (typeof window !== 'undefined' && typeof window.plausible === 'function') {
    window.plausible(event, { props })
    return
  }

  if (process.env.NODE_ENV === 'development') {
    // eslint-disable-next-line no-console
    console.log('SpatialEvent:', event, props)
  }
}

declare global {
  interface Window {
    plausible?: (event: string, options?: { props?: SpatialAnalyticsProps }) => void
  }
}
