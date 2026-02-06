'use client'

/**
 * DynamicTileLayer Component
 *
 * A tile layer that supports dynamic tiling (API-based MosaicJSON).
 *
 * Part of ADR-0007: Dynamic Tiling with MosaicJSON
 */

import { TileLayer } from 'react-leaflet'
import { useState, useEffect } from 'react'
import { buildDynamicTileUrl, isDynamicTilingEnabled } from '@/lib/tiles'

interface DynamicTileLayerProps {
  /** AOI ID (required for dynamic mode) */
  aoiId?: string
  /** Vegetation index name */
  index: string
  /** ISO year for dynamic mode */
  year?: number
  /** ISO week for dynamic mode */
  week?: number
  /** Layer opacity (0-1) */
  opacity?: number
  /** Whether this layer is visible */
  visible?: boolean
}

export default function DynamicTileLayer({
  aoiId,
  index,
  year,
  week,
  opacity = 0.7,
  visible = true,
}: DynamicTileLayerProps) {
  const [tileUrl, setTileUrl] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (!visible) {
      setTileUrl(null)
      return
    }

    const useDynamic = isDynamicTilingEnabled() && aoiId

    if (useDynamic) {
      // Use new dynamic tiling API
      const url = buildDynamicTileUrl(aoiId, index, year, week)
      setTileUrl(url)
    } else {
      setTileUrl(null)
    }
  }, [aoiId, index, year, week, visible])

  if (!visible || !tileUrl) {
    return null
  }

  return (
    <TileLayer
      url={tileUrl}
      maxNativeZoom={14}
      maxZoom={20}
      opacity={opacity}
      eventHandlers={{
        loading: () => setIsLoading(true),
        load: () => setIsLoading(false),
        tileerror: (e) => {
          console.warn('Tile load error:', e)
        },
      }}
    />
  )
}

/**
 * Hook to manage dynamic tile state for an AOI.
 */
export function useDynamicTiles(aoiId?: string) {
  const [selectedIndex, setSelectedIndex] = useState<string>('ndvi')
  const [selectedYear, setSelectedYear] = useState<number | undefined>()
  const [selectedWeek, setSelectedWeek] = useState<number | undefined>()

  // Build tile URL for current selection
  const tileUrl = aoiId
    ? buildDynamicTileUrl(aoiId, selectedIndex, selectedYear, selectedWeek)
    : null

  return {
    selectedIndex,
    setSelectedIndex,
    selectedYear,
    setSelectedYear,
    selectedWeek,
    setSelectedWeek,
    tileUrl,
    isDynamic: isDynamicTilingEnabled(),
  }
}
