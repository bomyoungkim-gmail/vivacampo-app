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
    ndviS3Url?: string | null
    ndwiS3Url?: string | null
    ndmiS3Url?: string | null
    saviS3Url?: string | null
    anomalyS3Url?: string | null
    falseColorS3Url?: string | null
    trueColorS3Url?: string | null

    // New Indices
    ndreS3Url?: string | null
    reciS3Url?: string | null
    gndviS3Url?: string | null
    eviS3Url?: string | null
    msiS3Url?: string | null
    nbrS3Url?: string | null
    bsiS3Url?: string | null
    ariS3Url?: string | null
    criS3Url?: string | null

    // Radar
    rviS3Url?: string | null
    ratioS3Url?: string | null
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
