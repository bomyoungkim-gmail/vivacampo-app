'use client'

/**
 * DynamicTileLayer Component
 *
 * A tile layer that supports both legacy (presigned COG URLs) and
 * new dynamic tiling (API-based MosaicJSON) modes.
 *
 * Part of ADR-0007: Dynamic Tiling with MosaicJSON
 */

import { TileLayer } from 'react-leaflet'
import { useState, useEffect } from 'react'
import { buildDynamicTileUrl, isDynamicTilingEnabled } from '@/lib/tiles'
import { APP_CONFIG } from '@/lib/config'

interface DynamicTileLayerProps {
  /** AOI ID (required for dynamic mode) */
  aoiId?: string
  /** Vegetation index name */
  index: string
  /** Legacy presigned tile URL (for backwards compatibility) */
  legacyTileUrl?: string | null
  /** ISO year for dynamic mode */
  year?: number
  /** ISO week for dynamic mode */
  week?: number
  /** Layer opacity (0-1) */
  opacity?: number
  /** Whether this layer is visible */
  visible?: boolean
  /** Colormap name for legacy mode */
  colormap?: string
  /** Rescale values for legacy mode */
  rescale?: string
}

// Colormap mapping for indices
const INDEX_COLORMAPS: Record<string, string> = {
  ndvi: 'rdylgn',
  ndwi: 'blues',
  ndmi: 'blues',
  evi: 'rdylgn',
  savi: 'greens',
  ndre: 'rdylgn',
  gndvi: 'rdylgn',
  anomaly: 'rdbu',
  rvi: 'viridis',
}

const INDEX_RESCALES: Record<string, string> = {
  ndvi: '-1,1',
  ndwi: '-1,1',
  ndmi: '-1,1',
  evi: '-1,1',
  savi: '-1,1',
  ndre: '-1,1',
  gndvi: '-1,1',
  anomaly: '-0.5,0.5',
  rvi: '0,1.5',
}

export default function DynamicTileLayer({
  aoiId,
  index,
  legacyTileUrl,
  year,
  week,
  opacity = 0.7,
  visible = true,
  colormap,
  rescale,
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
    } else if (legacyTileUrl) {
      // Use legacy presigned COG URL via TiTiler
      const tilerBaseUrl = APP_CONFIG.API_BASE_URL.replace(':8000', ':8080')
      const cm = colormap || INDEX_COLORMAPS[index] || 'viridis'
      const rs = rescale || INDEX_RESCALES[index] || '-1,1'

      const url = `${tilerBaseUrl}/cog/tiles/{z}/{x}/{y}?url=${encodeURIComponent(
        legacyTileUrl
      )}&rescale=${rs}&colormap_name=${cm}`

      setTileUrl(url)
    } else {
      setTileUrl(null)
    }
  }, [aoiId, index, legacyTileUrl, year, week, visible, colormap, rescale])

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
