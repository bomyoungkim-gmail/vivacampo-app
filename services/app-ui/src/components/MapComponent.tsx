'use client'

import dynamic from 'next/dynamic'
import { LoadingSpinner } from './LoadingSpinner'
import type { AOI } from '@/lib/types'

const MapLeaflet = dynamic(
    () => import('./MapLeaflet'),
    {
        ssr: false,
        loading: () => <LoadingSpinner message="Carregando mapa..." fullScreen={false} />
    }
)

interface MapComponentProps {
    farmId?: string
    aois?: AOI[]
    selectedAOI?: AOI | null
    timezone?: string
    isDrawing?: boolean
    drawingPoints?: [number, number][]
    setDrawingPoints?: (points: [number, number][]) => void
    ndviTileUrl?: string | null
    ndwiTileUrl?: string | null
    ndmiTileUrl?: string | null
    saviTileUrl?: string | null
    anomalyTileUrl?: string | null
    falseColorTileUrl?: string | null
    trueColorTileUrl?: string | null

    // New Indices
    ndreTileUrl?: string | null
    reciTileUrl?: string | null
    gndviTileUrl?: string | null
    eviTileUrl?: string | null
    msiTileUrl?: string | null
    nbrTileUrl?: string | null
    bsiTileUrl?: string | null
    ariTileUrl?: string | null
    criTileUrl?: string | null

    // Radar
    rviTileUrl?: string | null
    ratioTileUrl?: string | null
    showAOIs?: boolean
    processingAois?: Set<string>
    signals?: any[]
    onMapReady?: (map: any) => void
}

export default function MapComponent(props: MapComponentProps) {
    return (
        <div className="h-full w-full rounded-lg overflow-hidden shadow-lg bg-gray-100 relative group">
            <MapLeaflet {...props} />
        </div>
    )
}
