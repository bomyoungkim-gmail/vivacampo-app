'use client'

import { useMapEvents } from 'react-leaflet'

interface DrawingControllerProps {
    points: [number, number][]
    setPoints: (points: [number, number][]) => void
}

export default function DrawingController({ points, setPoints }: DrawingControllerProps) {
    useMapEvents({
        click(e) {
            const newPoint: [number, number] = [e.latlng.lat, e.latlng.lng]
            setPoints([...points, newPoint])
        },
    })
    return null
}
