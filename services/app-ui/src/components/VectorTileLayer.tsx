'use client'

import { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet.vectorgrid'

declare module 'leaflet' {
    namespace vectorGrid {
        function protobuf(url: string, options: Record<string, unknown>): L.Layer
    }
}

interface VectorTileLayerProps {
    url: string
    opacity?: number
}

const VECTOR_TILE_STYLES: Record<string, L.PathOptions> = {
    water: { fill: true, fillColor: '#1d4ed8', fillOpacity: 0.35, color: '#1e3a8a', weight: 0.5 },
    landuse: { fill: true, fillColor: '#22c55e', fillOpacity: 0.08, color: '#16a34a', weight: 0.5 },
    boundaries: { color: '#64748b', weight: 1, opacity: 0.6 },
    buildings: { fill: true, fillColor: '#cbd5f5', fillOpacity: 0.25, color: '#94a3b8', weight: 0.5 },
    roads: { color: '#94a3b8', weight: 1.2, opacity: 0.9 },
    transport: { color: '#94a3b8', weight: 1.2, opacity: 0.9 },
    places: { color: '#0f172a', weight: 0.5, opacity: 0.6 },
}

export function VectorTileLayer({ url, opacity = 1 }: VectorTileLayerProps) {
    const map = useMap()
    const layerRef = useRef<L.Layer | null>(null)

    useEffect(() => {
        if (!map || !url) return

        const layer = L.vectorGrid.protobuf(url, {
            maxZoom: 18,
            interactive: false,
            vectorTileLayerStyles: VECTOR_TILE_STYLES,
            rendererFactory: (L.canvas as unknown as { tile: L.Renderer }).tile,
        })

        if ('setOpacity' in layer && typeof (layer as any).setOpacity === 'function') {
            ;(layer as any).setOpacity(opacity)
        }

        layer.addTo(map)
        layerRef.current = layer

        return () => {
            if (layerRef.current) {
                map.removeLayer(layerRef.current)
                layerRef.current = null
            }
        }
    }, [map, url, opacity])

    return null
}
