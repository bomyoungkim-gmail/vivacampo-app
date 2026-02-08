'use client'

import dynamic from 'next/dynamic'
import { LoadingSpinner } from './LoadingSpinner'
import { cn } from '../lib/utils'
import type { AOI } from '@/lib/types'

const MapLeaflet = dynamic(
    () => import('./MapLeaflet'),
    {
        ssr: false,
        loading: () => <LoadingSpinner message="Carregando mapa..." fullScreen={false} />
    }
)

interface MapComponentProps {
    className?: string
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
    splitPreviewPolygons?: Array<{ id: string; geometry_wkt: string; area_ha?: number; name?: string }>
    splitSelectedIds?: string[]
    splitEditableId?: string | null
    splitMaxAreaHa?: number
    onSplitPreviewUpdate?: (id: string, geometryWkt: string, areaHa: number) => void
    onSplitPreviewSelect?: (id: string) => void
    mergeModeActive?: boolean
    mergeSelectedIds?: string[]
    onMergeSelect?: (id: string) => void
}

export default function MapComponent(props: MapComponentProps) {
    return (
        <div className={cn('relative h-full w-full overflow-hidden bg-muted', props.className)}>
            <MapLeaflet {...props} />
        </div>
    )
}
