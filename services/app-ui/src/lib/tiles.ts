/**
 * Dynamic Tiling Utilities
 *
 * Part of ADR-0007: Dynamic Tiling with MosaicJSON
 *
 * Provides URL builders and utilities for the new tile API endpoint.
 */

import { APP_CONFIG } from './config'

/**
 * Build a tile URL for the new dynamic tiling API.
 *
 * @param aoiId - Area of Interest UUID
 * @param index - Vegetation index (ndvi, ndwi, etc.)
 * @param year - ISO year (optional, defaults to current)
 * @param week - ISO week (optional, defaults to current)
 * @returns Tile URL template with {z}/{x}/{y} placeholders
 */
export function buildDynamicTileUrl(
  aoiId: string,
  index: string = 'ndvi',
  year?: number,
  week?: number
): string {
  const baseUrl = APP_CONFIG.API_BASE_URL
  const params = new URLSearchParams()

  params.set('index', index)
  if (year) params.set('year', year.toString())
  if (week) params.set('week', week.toString())

  // Note: {z}/{x}/{y} are Leaflet template variables
  return `${baseUrl}/v1/tiles/aois/${aoiId}/{z}/{x}/{y}.png?${params.toString()}`
}

/**
 * Build a TileJSON URL for GIS tool integration.
 *
 * @param aoiId - Area of Interest UUID
 * @param index - Vegetation index
 * @param year - ISO year
 * @param week - ISO week
 * @returns TileJSON endpoint URL
 */
export function buildTileJsonUrl(
  aoiId: string,
  index: string = 'ndvi',
  year?: number,
  week?: number
): string {
  const baseUrl = APP_CONFIG.API_BASE_URL
  const params = new URLSearchParams()

  params.set('index', index)
  if (year) params.set('year', year.toString())
  if (week) params.set('week', week.toString())

  return `${baseUrl}/v1/tiles/aois/${aoiId}/tilejson.json?${params.toString()}`
}

/**
 * Get current ISO week number.
 */
export function getCurrentISOWeek(): { year: number; week: number } {
  const now = new Date()
  const startOfYear = new Date(now.getFullYear(), 0, 1)
  const days = Math.floor((now.getTime() - startOfYear.getTime()) / (24 * 60 * 60 * 1000))
  const week = Math.ceil((days + startOfYear.getDay() + 1) / 7)
  return { year: now.getFullYear(), week }
}

/**
 * Available vegetation indices for the tile API.
 */
export const VEGETATION_INDICES = [
  { id: 'ndvi', name: 'NDVI', description: 'Vegetation health and density' },
  { id: 'ndwi', name: 'NDWI', description: 'Water content in vegetation' },
  { id: 'ndmi', name: 'NDMI', description: 'Vegetation moisture' },
  { id: 'evi', name: 'EVI', description: 'Enhanced vegetation index' },
  { id: 'savi', name: 'SAVI', description: 'Soil adjusted vegetation' },
  { id: 'ndre', name: 'NDRE', description: 'Red edge chlorophyll' },
  { id: 'gndvi', name: 'GNDVI', description: 'Green NDVI' },
] as const

export type VegetationIndex = (typeof VEGETATION_INDICES)[number]['id']

/**
 * Check if dynamic tiling is enabled.
 * Can be controlled via environment variable or feature flag.
 */
export function isDynamicTilingEnabled(): boolean {
  // Check environment variable (set in .env)
  const envFlag = process.env.NEXT_PUBLIC_ENABLE_DYNAMIC_TILING
  if (envFlag !== undefined) {
    return envFlag === 'true'
  }

  // Default: enabled in development, disabled in production until tested
  return !APP_CONFIG.IS_PRODUCTION
}

