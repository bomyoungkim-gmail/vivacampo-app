export type ZoomSemanticLevel = 'macro' | 'meso' | 'micro'

export const ZOOM_LEVELS: Record<ZoomSemanticLevel, number> = {
  macro: 7,
  meso: 11,
  micro: 15,
}

export function getZoomSemanticLevel(zoom: number): ZoomSemanticLevel {
  if (zoom >= 13) return 'micro'
  if (zoom >= 10) return 'meso'
  return 'macro'
}
