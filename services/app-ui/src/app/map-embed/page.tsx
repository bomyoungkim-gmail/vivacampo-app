'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet'
import api from '@/lib/api'
import 'leaflet/dist/leaflet.css'

interface AOIGeometry {
  type: string
  coordinates: number[][][]
}

interface AOIData {
  id: string
  geometry: AOIGeometry
  center: [number, number]
}

const INDEX_COLORMAPS: Record<string, string> = {
  srre: 'rdylgn',
  ndvi: 'rdylgn',
  ndre: 'rdylgn',
  ndwi: 'blues',
  ndmi: 'blues',
  evi: 'rdylgn',
  savi: 'rdylgn',
  rvi: 'viridis',
}

const INDEX_RESCALES: Record<string, string> = {
  srre: '0.5,8',
  ndvi: '-0.2,0.8',
  ndre: '-0.2,0.8',
  ndwi: '-0.5,0.5',
  ndmi: '-0.5,0.5',
  evi: '-0.2,0.8',
  savi: '-0.2,0.8',
  rvi: '0,1.5',
}

export default function MapEmbedPage() {
  const searchParams = useSearchParams()
  const aoiId = searchParams.get('aoi')
  const layer = searchParams.get('layer') || 'ndvi'

  const [aoi, setAoi] = useState<AOIData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!aoiId) {
      setError('AOI ID não fornecido')
      setLoading(false)
      return
    }

    // Fetch AOI geometry
    api.get(`/v1/app/aois/${aoiId}`)
      .then((res) => {
        const data = res.data
        const geom = data.geometry || data.geom

        // Calculate center from geometry
        let center: [number, number] = [-23.5, -52.5] // Default
        if (geom && geom.coordinates && geom.coordinates[0]) {
          const coords = geom.coordinates[0]
          const lats = coords.map((c: number[]) => c[1])
          const lngs = coords.map((c: number[]) => c[0])
          center = [
            (Math.min(...lats) + Math.max(...lats)) / 2,
            (Math.min(...lngs) + Math.max(...lngs)) / 2,
          ]
        }

        setAoi({
          id: aoiId,
          geometry: geom,
          center,
        })
      })
      .catch((err) => {
        console.error('Failed to fetch AOI:', err)
        setError('Falha ao carregar AOI')
      })
      .finally(() => setLoading(false))
  }, [aoiId])

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-gray-100">
        <div className="text-gray-500">Carregando mapa...</div>
      </div>
    )
  }

  if (error || !aoi) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-gray-100">
        <div className="text-red-500">{error || 'AOI não encontrado'}</div>
      </div>
    )
  }

  const colormap = INDEX_COLORMAPS[layer] || 'rdylgn'
  const rescale = INDEX_RESCALES[layer] || '-1,1'

  // Build tile URL for the vegetation index
  const tileUrl = `/api/v1/tiles/aois/${aoiId}/{z}/{x}/{y}.png?index=${layer}&colormap=${colormap}&rescale=${rescale}`

  return (
    <div className="h-screen w-screen">
      <MapContainer
        center={aoi.center}
        zoom={14}
        className="h-full w-full"
        zoomControl={true}
        attributionControl={false}
      >
        {/* Base layer */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution=""
        />

        {/* Vegetation index layer */}
        <TileLayer
          url={tileUrl}
          opacity={0.8}
          tms={false}
        />

        {/* AOI boundary */}
        {aoi.geometry && (
          <GeoJSON
            data={{
              type: 'Feature',
              properties: {},
              geometry: aoi.geometry,
            } as GeoJSON.Feature}
            style={{
              color: '#3b82f6',
              weight: 2,
              fillOpacity: 0,
            }}
          />
        )}
      </MapContainer>

      {/* Layer indicator */}
      <div className="absolute bottom-4 right-4 z-[1000] rounded bg-white/90 px-3 py-1.5 text-xs font-medium shadow">
        {layer.toUpperCase()}
      </div>
    </div>
  )
}
