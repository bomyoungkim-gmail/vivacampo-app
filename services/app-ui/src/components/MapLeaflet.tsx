'use client'

import { useEffect, useState, useMemo, useCallback, useRef } from 'react'
import { MapContainer, TileLayer, Polygon, Popup, Marker, Polyline, useMapEvents, useMap, ZoomControl } from 'react-leaflet'
import L from 'leaflet'
import { Radio } from 'lucide-react'
import { APP_CONFIG } from '@/lib/config'
import type { AOI } from '@/lib/types'
import * as turf from '@turf/turf'
import 'leaflet/dist/leaflet.css'
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css'
import '@geoman-io/leaflet-geoman-free'

// Extend Leaflet types for PM
declare module 'leaflet' {
    interface Layer {
        pm: any;
    }
}

// ------------------------------------------------------------------
// Helpers & Sub-components (Outside Main Component)
// ------------------------------------------------------------------

// 0. MapReady Helper to expose map instance
function MapReady({ onMapReady }: { onMapReady?: (map: any) => void }) {
    const map = useMap()
    useEffect(() => {
        if (onMapReady) onMapReady(map)
    }, [map, onMapReady])
    return null
}

// Helper to parse WKT
// Supports MULTIPOLYGON and simple handling.
const parseWKT = (wkt: string): [number, number][][] => {
    if (!wkt) return []

    // Normalize WKT: remove MULTIPOLYGON/POLYGON prefix and outer parens logic
    const coordsMatch = wkt.match(/\([\d\s,.-]+\)/g)

    if (!coordsMatch) return []

    return coordsMatch.map(polygonStr => {
        // Remove parens
        const cleanStr = polygonStr.replace(/[()]/g, '')

        // Split by comma
        const pairs = cleanStr.split(',')

        return pairs.map(pair => {
            const parts = pair.trim().split(/\s+/) // split by any whitespace
            if (parts.length >= 2) {
                const lng = parseFloat(parts[0])
                const lat = parseFloat(parts[1])
                return [lat, lng] as [number, number] // Leaflet is [Lat, Lng]
            }
            return null
        }).filter(p => p !== null) as [number, number][]
    })
}

const geojsonToWkt = (geometry: any): string => {
    if (!geometry) return ''
    const toRing = (ring: number[][]) => ring.map((p) => `${p[0]} ${p[1]}`).join(', ')
    if (geometry.type === 'Polygon') {
        const ring = geometry.coordinates?.[0] ?? []
        return `MULTIPOLYGON(((${toRing(ring)})))`
    }
    if (geometry.type === 'MultiPolygon') {
        const parts = geometry.coordinates.map((poly: number[][][]) => `((${toRing(poly[0] ?? [])}))`).join(', ')
        return `MULTIPOLYGON(${parts})`
    }
    return ''
}

const getPolygonCenter = (coords: [number, number][]) => {
    const bounds = L.latLngBounds(coords)
    const center = bounds.getCenter()
    return [center.lat, center.lng] as [number, number]
}

type AoiStatus = 'normal' | 'processing' | 'alert' | 'warning' | 'split'

const STATUS_COLORS: Record<AoiStatus, string> = {
    normal: '#22c55e',
    processing: '#3b82f6',
    alert: '#ef4444',
    warning: '#eab308',
    split: '#0ea5e9',
}

type SignalBadge = 'water_stress' | 'disease_risk' | 'yield_risk' | 'general'

const SIGNAL_BADGE_LABELS: Record<SignalBadge, string> = {
    water_stress: 'H2O',
    disease_risk: 'DOENCA',
    yield_risk: 'YIELD',
    general: 'ALERTA',
}

const SIGNAL_BADGE_COLORS: Record<SignalBadge, string> = {
    water_stress: '#0284c7',
    disease_risk: '#dc2626',
    yield_risk: '#f97316',
    general: '#a855f7',
}

const hexToRgb = (hex: string) => {
    const value = hex.replace('#', '')
    const bigint = parseInt(value, 16)
    return {
        r: (bigint >> 16) & 255,
        g: (bigint >> 8) & 255,
        b: bigint & 255,
    }
}

const interpolateColor = (from: string, to: string, t: number) => {
    const a = hexToRgb(from)
    const b = hexToRgb(to)
    const r = Math.round(a.r + (b.r - a.r) * t)
    const g = Math.round(a.g + (b.g - a.g) * t)
    const bVal = Math.round(a.b + (b.b - a.b) * t)
    return `rgb(${r}, ${g}, ${bVal})`
}

const getNdviFill = (ndvi?: number | null) => {
    if (ndvi === null || ndvi === undefined) return null
    const clamped = Math.max(0, Math.min(1, ndvi))
    if (clamped <= 0.4) {
        return interpolateColor('#ef4444', '#eab308', clamped / 0.4)
    }
    if (clamped <= 0.7) {
        return interpolateColor('#eab308', '#22c55e', (clamped - 0.4) / 0.3)
    }
    return '#22c55e'
}

const STATUS_SVG: Record<AoiStatus, string> = {
    normal: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9"></circle>
            <path d="M9 12l2 2 4-4"></path>
        </svg>
    `,
    processing: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9"></circle>
            <path d="M12 7v5l3 3"></path>
        </svg>
    `,
    alert: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
            <path d="M12 9v4"></path>
            <path d="M12 17h.01"></path>
        </svg>
    `,
    warning: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polyline>
        </svg>
    `,
    split: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="6" cy="6" r="3"></circle>
            <circle cx="6" cy="18" r="3"></circle>
            <path d="M20 4L8.12 15.88"></path>
            <path d="M14.47 14.48 20 20"></path>
            <path d="M8.12 8.12 12 12"></path>
        </svg>
    `,
}

const getStatusIconHtml = (status: AoiStatus) => {
    const color = STATUS_COLORS[status] ?? STATUS_COLORS.normal
    return `
        <div style="
            width: 26px;
            height: 26px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(15, 23, 42, 0.15);
            display: grid;
            place-items: center;
            color: ${color};
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        ">
            <div style="width: 16px; height: 16px;">
                ${STATUS_SVG[status]}
            </div>
        </div>
    `
}

const getSignalBadgeHtml = (badge: SignalBadge) => {
    const color = SIGNAL_BADGE_COLORS[badge]
    const title = badge === 'water_stress'
        ? 'Water Stress'
        : badge === 'disease_risk'
            ? 'Disease Risk'
            : badge === 'yield_risk'
                ? 'Yield Risk'
                : 'Alert'
    return `
        <div title="${title}" style="
            padding: 2px 8px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(15, 23, 42, 0.12);
            font-size: 9px;
            font-weight: 700;
            color: ${color};
            letter-spacing: 0.02em;
            box-shadow: 0 4px 10px rgba(0,0,0,0.12);
        ">
            ${SIGNAL_BADGE_LABELS[badge]}
        </div>
    `
}

// 1. Force Resize on Mount
function MapResizer() {
    const map = useMap()
    useEffect(() => {
        const timer = setTimeout(() => {
            map.invalidateSize()
        }, 100)
        return () => clearTimeout(timer)
    }, [map])
    return null
}

// 2. Intelligent View Controller
function ViewController({ center, aois }: { center: [number, number], aois: AOI[] }) {
    const map = useMap()
    const [initialized, setInitialized] = useState(false)

    useEffect(() => {
        if (!initialized) {
            map.setView(center, 11)
            setInitialized(true)
        }
    }, [map, center, initialized])

    return null
}

// 3. Robust Search Component (Nominatim via Proxy)
function LocationSearch() {
    const map = useMap()
    const [query, setQuery] = useState('')
    const [searching, setSearching] = useState(false)
    const [results, setResults] = useState<any[]>([])

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!query.trim()) return

        setSearching(true)
        try {
            // Use backend proxy to avoid CORS/User-Agent issues
            const token = localStorage.getItem('access_token')
            const response = await fetch(`${APP_CONFIG.API_BASE_URL}/farms/geocode?q=${encodeURIComponent(query)}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })

            if (!response.ok) throw new Error('Falha na busca')

            const data = await response.json()
            setResults(data)

            if (data.length > 0) {
                const first = data[0]
                const lat = parseFloat(first.lat)
                const lon = parseFloat(first.lon)
                map.flyTo([lat, lon], 12)
                setResults([]) // Clear dropdown
                setQuery(first.display_name.split(',')[0])
            } else {
                alert('Local não encontrado.')
            }
        } catch (err) {
            console.error(err)
            alert('Erro na busca.')
        } finally {
            setSearching(false)
        }
    }

    const stopProp = (e: React.MouseEvent | React.KeyboardEvent) => {
        e.stopPropagation()
    }

    return (
        <div className="leaflet-top leaflet-left" style={{ marginTop: '80px', marginLeft: '10px' }}>
            <div className="leaflet-control flex flex-col items-start font-sans" onDoubleClick={stopProp} onMouseDown={stopProp} onClick={stopProp}>
                <form onSubmit={handleSearch} className="flex bg-white rounded-md shadow-md overflow-hidden border border-gray-300">
                    <input
                        type="text"
                        className="px-3 py-2 text-sm text-gray-700 outline-none w-48"
                        placeholder="Buscar cidade, local..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <button
                        type="submit"
                        disabled={searching}
                        className="bg-green-600 text-white px-3 py-2 text-sm font-medium hover:bg-green-700 disabled:opacity-50"
                    >
                        {searching ? '...' : '🔍'}
                    </button>
                </form>
            </div>
        </div>
    )
}

function DrawingController({ points, setPoints }: { points: [number, number][], setPoints: (p: [number, number][]) => void }) {
    useMapEvents({
        click(e) {
            const newPoint: [number, number] = [e.latlng.lat, e.latlng.lng]
            setPoints([...points, newPoint])
        },
    })
    return null
}

function ZoomToDataControl({ aois }: { aois: AOI[] }) {
    const map = useMap()

    const fitBoundsToAOIs = useCallback(() => {
        if (aois.length === 0) return

        const allCoords: L.LatLngExpression[] = []
        aois.forEach(aoi => {
            const polygons = parseWKT(aoi.geometry)
            polygons.forEach(coords => {
                coords.forEach(point => allCoords.push(point))
            })
        })

        if (allCoords.length > 0) {
            const bounds = L.latLngBounds(allCoords)
            map.fitBounds(bounds, { padding: [50, 50] })
        }
    }, [aois, map])

    const stopProp = (e: React.MouseEvent | React.KeyboardEvent) => {
        e.stopPropagation()
    }

    return (
        <div className="leaflet-top leaflet-left" style={{ marginTop: '10px', marginLeft: '10px' }}>
            <div className="leaflet-control flex flex-col items-start font-sans" onDoubleClick={stopProp} onMouseDown={stopProp} onClick={stopProp}>
                <button
                    onClick={fitBoundsToAOIs}
                    disabled={aois.length === 0}
                    className="bg-blue-600 text-white px-3 py-2 text-sm font-medium rounded-md shadow-md hover:bg-blue-700 disabled:opacity-50"
                >
                    Zoom para Dados
                </button>
            </div>
        </div>
    )
}

// Sub-component to handle FlyTo
function FlyToSelected({ aoi }: { aoi?: AOI | null }) {
    const map = useMap()

    useEffect(() => {
        if (!aoi || !aoi.geometry) return

        try {
            const polygons = parseWKT(aoi.geometry)
            if (polygons.length > 0) {
                const allPoints = polygons.flat()
                if (allPoints.length > 0) {
                    const bounds = L.latLngBounds(allPoints)
                    if (bounds.isValid()) {
                        map.fitBounds(bounds, { padding: [100, 100], maxZoom: 16 })
                    }
                }
            }
        } catch (e) {
            console.error('Error flying to AOI', e)
        }
    }, [aoi, map])

    return null
}

// 4. Smart Polygon Component with Geoman Support
interface AOIPolygonProps {
    aoi: AOI
    coords: [number, number][]
    getAOIColor: (type: string, isProcessing?: boolean) => string
    isEditing: boolean
    isSelected: boolean
    isMergeSelected?: boolean
    isProcessing?: boolean
    status?: AoiStatus
    ndviMean?: number | null
    onUpdate?: (aoiId: string, newGeometry: any) => void
    onSelect?: (aoiId: string) => void
}

function AOIPolygon({
    aoi,
    coords,
    getAOIColor,
    isEditing,
    isSelected,
    isMergeSelected,
    isProcessing,
    status = 'normal',
    ndviMean,
    onUpdate,
    onSelect
}: AOIPolygonProps) {
    const polygonRef = useRef<L.Polygon>(null)

    useEffect(() => {
        const layer = polygonRef.current
        if (!layer) return

        if (isSelected && isEditing) {
            // Enable editing
            layer.pm.enable({
                allowSelfIntersection: false,
                draggable: true,
            })

            // Verify L.PM is available
            if (!layer.pm) {
                console.warn('Leaflet Geoman not loaded')
                return
            }

            const handleUpdate = (e: any) => {
                if (onUpdate) {
                    const geojson = layer.toGeoJSON()
                    // Extract geometry only
                    onUpdate(aoi.id, geojson.geometry)
                }
            }

            layer.on('pm:edit', handleUpdate)
            layer.on('pm:dragend', handleUpdate)
            layer.on('pm:rotateend', handleUpdate)
            layer.on('pm:markerdragend', handleUpdate) // Catch vertex moves

            return () => {
                layer.pm.disable()
                layer.off('pm:edit', handleUpdate)
                layer.off('pm:dragend', handleUpdate)
                layer.off('pm:rotateend', handleUpdate)
                layer.off('pm:markerdragend', handleUpdate)
            }
        } else {
            if (layer.pm && layer.pm.enabled()) {
                layer.pm.disable()
            }
        }
    }, [isSelected, isEditing, onUpdate, aoi.id])

    const statusColor = STATUS_COLORS[status] ?? getAOIColor(aoi.use_type, isProcessing)
    const ndviFill = getNdviFill(ndviMean)
    const fillColor = ndviFill ?? getAOIColor(aoi.use_type, isProcessing)
    const borderColor = isMergeSelected ? '#f97316' : statusColor

    return (
        <Polygon
            ref={polygonRef}
            positions={coords}
            eventHandlers={{
                click: () => onSelect?.(aoi.id),
            }}
            pathOptions={{
                color: borderColor,
                fillColor: fillColor,
                fillOpacity: isProcessing ? 0.1 : isMergeSelected ? 0.35 : 0.25,
                weight: isSelected || isMergeSelected ? 4 : 2, // Thicker stroke if selected
                dashArray: (isSelected && !isEditing) || isProcessing || isMergeSelected ? '5, 5' : undefined
            }}
        >
            <Popup>
                <div className="p-2">
                    <h3 className="font-semibold flex items-center gap-2">
                        {aoi.name}
                        {isProcessing && <span className="text-xs bg-amber-100 text-amber-800 px-1 rounded animate-pulse">Processando...</span>}
                    </h3>
                    <p className="text-sm text-gray-600">Tipo: {aoi.use_type}</p>
                    {aoi.area_ha && (
                        <p className="text-sm text-gray-600">Área: {aoi.area_ha.toFixed(2)} ha</p>
                    )}
                </div>
            </Popup>
        </Polygon>
    )
}

interface SplitPreviewPolygonProps {
    id: string
    coords: [number, number][]
    areaHa?: number
    maxAreaHa?: number
    isSelected: boolean
    isEditable: boolean
    onSelect?: (id: string) => void
    onUpdate?: (id: string, geometryWkt: string, areaHa: number) => void
}

function SplitPreviewPolygon({ id, coords, areaHa, maxAreaHa = 2000, isSelected, isEditable, onSelect, onUpdate }: SplitPreviewPolygonProps) {
    const polygonRef = useRef<L.Polygon>(null)

    useEffect(() => {
        const layer = polygonRef.current
        if (!layer) return

        if (isEditable) {
            layer.pm.enable({
                allowSelfIntersection: false,
                draggable: true,
            })

            const handleUpdate = () => {
                if (!onUpdate) return
                const geojson = layer.toGeoJSON()
                const geometry = geojson.geometry
                const wkt = geojsonToWkt(geometry)
                const area = turf.area(geometry) / 10000
                onUpdate(id, wkt, area)
            }

            layer.on('pm:edit', handleUpdate)
            layer.on('pm:dragend', handleUpdate)
            layer.on('pm:rotateend', handleUpdate)
            layer.on('pm:markerdragend', handleUpdate)

            return () => {
                layer.pm.disable()
                layer.off('pm:edit', handleUpdate)
                layer.off('pm:dragend', handleUpdate)
                layer.off('pm:rotateend', handleUpdate)
                layer.off('pm:markerdragend', handleUpdate)
            }
        }

        if (layer.pm && layer.pm.enabled()) {
            layer.pm.disable()
        }
    }, [id, isEditable, onUpdate])

    const isOver = (areaHa ?? 0) > maxAreaHa

    return (
        <Polygon
            ref={polygonRef}
            positions={coords}
            eventHandlers={{
                click: () => onSelect?.(id),
            }}
            pathOptions={{
                color: isOver ? STATUS_COLORS.alert : STATUS_COLORS.split,
                fillColor: isOver ? 'rgba(239, 68, 68, 0.15)' : 'rgba(14, 165, 233, 0.12)',
                fillOpacity: 0.2,
                weight: isSelected ? 4 : 2,
                dashArray: '6, 6',
            }}
        >
            <Popup>
                <div className="p-2">
                    <h3 className="font-semibold">Talhão (Preview)</h3>
                    <p className="text-sm text-gray-600">Área: {areaHa ? areaHa.toFixed(1) : '--'} ha</p>
                    {isOver && (
                        <p className="text-sm text-red-600 mt-1">Acima do limite ({maxAreaHa} ha)</p>
                    )}
                </div>
            </Popup>
        </Polygon>
    )
}

function StatusIconMarker({ position, status }: { position: [number, number]; status: AoiStatus }) {
    const icon = useMemo(() => {
        return L.divIcon({
            className: 'aoi-status-icon',
            html: getStatusIconHtml(status),
            iconSize: [26, 26],
            iconAnchor: [13, 13],
        })
    }, [status])

    return <Marker position={position} icon={icon} interactive={false} />
}

function SignalBadgeMarker({ position, badge }: { position: [number, number]; badge: SignalBadge }) {
    const icon = useMemo(() => {
        return L.divIcon({
            className: 'aoi-signal-badge',
            html: getSignalBadgeHtml(badge),
            iconAnchor: [16, 16],
        })
    }, [badge])

    return <Marker position={position} icon={icon} interactive={false} />
}

// ------------------------------------------------------------------
// Main Component
// ------------------------------------------------------------------

import { MapControlCluster } from './MapControlCluster'

interface MapProps {
    farmId?: string
    aois?: AOI[]
    selectedAOI?: AOI | null
    isDrawing?: boolean
    drawingPoints?: [number, number][]
    setDrawingPoints?: (points: [number, number][]) => void
    timezone?: string
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
    isEditing?: boolean
    onAOIUpdate?: (aoiId: string, newGeometry: any) => void
    processingAois?: Set<string>
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

// ... Styles (PASTURE_STYLE etc) reused ...

const PROCESSING_STYLE = { color: '#d97706', weight: 2, dashArray: '5, 5', fillOpacity: 0.1 }

const TIMEZONE_COORDINATES: Record<string, [number, number]> = {
    'America/Sao_Paulo': [-23.5505, -46.6333],
    'America/Manaus': [-3.1190, -60.0217],
    'America/Cuiaba': [-15.6014, -56.0979],
    'America/Campo_Grande': [-20.4697, -54.6201],
    'America/Rio_Branco': [-9.9754, -67.8105],
    'America/Belem': [-1.4558, -48.4902],
    'America/Fortaleza': [-3.7172, -38.5434],
    'America/Noronha': [-3.8576, -32.4297],
}

// 5. Alert Markers Component
function AlertMarkers({ signals, showAlerts, aois }: { signals: any[], showAlerts: boolean, aois: AOI[] }) {
    if (!showAlerts || !signals || signals.length === 0) return null

    return (
        <>
            {signals.map((signal) => {
                let position: [number, number] | null = null

                // 1. Try explicit lat/lon in metadata
                if (signal.metadata?.lat && signal.metadata?.lon) {
                    position = [signal.metadata.lat, signal.metadata.lon]
                }
                // 2. Fallback: Find center of associated AOI
                else if (signal.aoi_id) {
                    const aoi = aois.find(a => a.id === signal.aoi_id)
                    if (aoi && aoi.geometry) {
                        const polys = parseWKT(aoi.geometry)
                        if (polys.length > 0 && polys[0].length > 0) {
                            // Simple centroid of first polygon
                            position = polys[0][0]
                        }
                    }
                }

                if (position) {
                    return (
                        <Marker
                            key={signal.id}
                            position={position}
                        >
                            <Popup>
                                <div className="p-2">
                                    <h4 className="font-bold text-sm mb-1">{signal.signal_type}</h4>
                                    <p className="text-xs text-gray-600">Severidade: {signal.severity}</p>
                                    <p className="text-xs text-gray-500">{new Date(signal.detected_at || signal.created_at).toLocaleDateString()}</p>
                                </div>
                            </Popup>
                        </Marker>
                    )
                }
                return null
            })}
        </>
    )
}

export default function MapLeaflet({
    farmId,
    aois = [],
    selectedAOI,
    timezone,
    isDrawing = false,
    drawingPoints = [],
    setDrawingPoints,
    ndviTileUrl,
    ndwiTileUrl,
    ndmiTileUrl,
    saviTileUrl,
    anomalyTileUrl,
    falseColorTileUrl,
    trueColorTileUrl,

    ndreTileUrl, reciTileUrl, gndviTileUrl, eviTileUrl,
    msiTileUrl, nbrTileUrl, bsiTileUrl, ariTileUrl, criTileUrl,
    rviTileUrl, ratioTileUrl,
    showAOIs: initialShowAOIs = true,
    isEditing = false,
    onAOIUpdate,
    processingAois,
    signals = [],
    onMapReady,
    splitPreviewPolygons = [],
    splitSelectedIds = [],
    splitEditableId,
    splitMaxAreaHa,
    onSplitPreviewUpdate,
    onSplitPreviewSelect,
    mergeModeActive = false,
    mergeSelectedIds = [],
    onMergeSelect
}: MapProps & { signals?: any[] }) {

    // --- State Management ---
    const [activeBaseLayer, setActiveBaseLayer] = useState<string>('satellite')
    const [activeOverlay, setActiveOverlay] = useState<string | null>(null)
    const [overlayOpacity, setOverlayOpacity] = useState<number>(0.7)
    const [showAOIs, setShowAOIs] = useState<boolean>(initialShowAOIs)
    const [showAlerts, setShowAlerts] = useState<boolean>(false)

    // Sync prop changes to activeOverlay if needed (e.g. if User selects a new week, maybe auto-select NDVI?)
    // For now, we prefer manual control unless it's the first load
    useEffect(() => {
        if (ndviTileUrl && !activeOverlay) {
            // Optional: Auto-select NDVI if nothing selected? 
            // setOverlayOpacity(0.7)
            // setActiveOverlay('ndvi') 
        }
    }, [ndviTileUrl])

    // Sync external showAOIs prop to internal state
    useEffect(() => {
        if (initialShowAOIs !== undefined) {
            setShowAOIs(initialShowAOIs)
        }
    }, [initialShowAOIs])

    const getAOIColor = useCallback((useType: string, isProcessing?: boolean) => {
        if (isProcessing) return '#d97706'
        return APP_CONFIG.COLORS.AOI_TYPES[useType as keyof typeof APP_CONFIG.COLORS.AOI_TYPES] || '#6366f1'
    }, [])

    const center = useMemo((): [number, number] => {
        if (aois.length > 0 && aois[0].geometry) {
            const parsed = parseWKT(aois[0].geometry)
            return parsed[0]?.[0] || APP_CONFIG.DEFAULT_MAP_CENTER
        }
        if (timezone && TIMEZONE_COORDINATES[timezone]) {
            return TIMEZONE_COORDINATES[timezone]
        }
        return APP_CONFIG.DEFAULT_MAP_CENTER
    }, [aois, timezone])

    const getAoiStatus = useCallback((aoi: AOI): AoiStatus => {
        if (processingAois?.has(aoi.id)) return 'processing'
        const aoiSignals = signals?.filter((signal) => signal.aoi_id === aoi.id) ?? []
        if (aoiSignals.some((signal) => signal.severity === 'HIGH')) return 'alert'
        if (aoiSignals.some((signal) => signal.severity === 'MEDIUM')) return 'warning'
        return 'normal'
    }, [processingAois, signals])

    const getAoiBadge = useCallback((aoi: AOI): SignalBadge | null => {
        const aoiSignals = signals?.filter((signal) => signal.aoi_id === aoi.id) ?? []
        if (aoiSignals.length === 0) return null

        const priority = (signal: any) => {
            if (signal.severity === 'HIGH') return 3
            if (signal.severity === 'MEDIUM') return 2
            return 1
        }

        const top = [...aoiSignals].sort((a, b) => priority(b) - priority(a))[0]
        switch (top.signal_type) {
            case 'CROP_STRESS':
                return 'water_stress'
            case 'PEST_OUTBREAK':
                return 'disease_risk'
            case 'PASTURE_FORAGE_RISK':
                return 'yield_risk'
            default:
                return 'general'
        }
    }, [signals])

    // Construct Available Layers Object
    const availableLayers = {
        ndvi: !!ndviTileUrl,
        ndwi: !!ndwiTileUrl,
        ndmi: !!ndmiTileUrl,
        savi: !!saviTileUrl,
        anomaly: !!anomalyTileUrl,
        falseColor: !!falseColorTileUrl,
        trueColor: !!trueColorTileUrl,

        ndre: !!ndreTileUrl,
        reci: !!reciTileUrl,
        gndvi: !!gndviTileUrl,
        evi: !!eviTileUrl,
        msi: !!msiTileUrl,
        nbr: !!nbrTileUrl,
        bsi: !!bsiTileUrl,
        ari: !!ariTileUrl,
        cri: !!criTileUrl,
        rvi: !!rviTileUrl,
        ratio: !!ratioTileUrl
    }

    return (
        <>
            <link
                rel="stylesheet"
                href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
            />

            {isDrawing && (
                <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-[1000] bg-white px-4 py-2 rounded-full shadow-lg border-2 border-green-500 font-semibold text-green-700 animate-pulse text-sm whitespace-nowrap">
                    ✏️ Clique no mapa para marcar os pontos
                </div>
            )}
            {activeOverlay === 'rvi' && (
                <div className="absolute bottom-4 left-4 z-[1000] rounded-full border bg-background/80 px-3 py-1.5 text-xs font-medium shadow">
                    <Radio className="mr-1 inline h-3 w-3" />
                    Modo Radar / Estimativa
                </div>
            )}

            <MapContainer
                center={center}
                zoom={11}
                className="absolute inset-0 z-0"
                style={{ cursor: isDrawing ? 'crosshair' : 'grab' }}
                zoomControl={false} // Disable default zoom control
            >
                <MapResizer />
                <MapReady onMapReady={onMapReady} />
                <ViewController center={center} aois={aois} />
                <FlyToSelected aoi={selectedAOI} />

                {/* 1. Base Layers */}
                {activeBaseLayer === 'satellite' ? (
                    <TileLayer
                        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                        attribution="Tiles &copy; Esri"
                        maxNativeZoom={18}
                        maxZoom={19}
                    />
                ) : activeBaseLayer === 'topo' ? (
                    <TileLayer
                        url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
                        attribution='Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)'
                        maxNativeZoom={17}
                        maxZoom={19}
                    />
                ) : (
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        maxNativeZoom={19}
                        maxZoom={19}
                    />
                )}

                {/* 2. Hybrid Labels (Reference) - Always on for Satellite */}
                {activeBaseLayer === 'satellite' && (
                    <TileLayer
                        url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
                        maxNativeZoom={17}
                        maxZoom={19}
                    />
                )}

                {/* 3. Overlays (Z-Index handled by order) */}

                {activeOverlay === 'ndvi' && ndviTileUrl && (
                    <TileLayer
                        url={`${APP_CONFIG.API_BASE_URL.replace(':8000', ':8080')}/cog/tiles/{z}/{x}/{y}?url=${encodeURIComponent(ndviTileUrl)}&rescale=-1,1&colormap_name=rdylgn`}
                        maxNativeZoom={14}
                        maxZoom={20}
                        opacity={overlayOpacity}
                    />
                )}
                {activeOverlay === 'ndwi' && ndwiTileUrl && (
                    <TileLayer
                        url={`${APP_CONFIG.API_BASE_URL.replace(':8000', ':8080')}/cog/tiles/{z}/{x}/{y}?url=${encodeURIComponent(ndwiTileUrl)}&rescale=-1,1&colormap_name=blues`}
                        maxNativeZoom={14}
                        maxZoom={20}
                        opacity={overlayOpacity}
                    />
                )}
                {activeOverlay === 'savi' && saviTileUrl && (
                    <TileLayer
                        url={`${APP_CONFIG.API_BASE_URL.replace(':8000', ':8080')}/cog/tiles/{z}/{x}/{y}?url=${encodeURIComponent(saviTileUrl)}&rescale=-1,1&colormap_name=greens`}
                        maxNativeZoom={14}
                        maxZoom={20}
                        opacity={overlayOpacity}
                    />
                )}
                {activeOverlay === 'anomaly' && anomalyTileUrl && (
                    <TileLayer
                        url={`${APP_CONFIG.API_BASE_URL.replace(':8000', ':8080')}/cog/tiles/{z}/{x}/{y}?url=${encodeURIComponent(anomalyTileUrl)}&rescale=-0.5,0.5&colormap_name=rdbu`}
                        maxNativeZoom={14}
                        maxZoom={20}
                        opacity={overlayOpacity}
                    />
                )}
                {activeOverlay === 'falseColor' && falseColorTileUrl && (
                    <TileLayer
                        url={`${APP_CONFIG.API_BASE_URL.replace(':8000', ':8080')}/cog/tiles/{z}/{x}/{y}?url=${encodeURIComponent(falseColorTileUrl)}&rescale=0,1`}
                        maxNativeZoom={14}
                        maxZoom={20}
                        opacity={overlayOpacity}
                    />
                )}
                {activeOverlay === 'trueColor' && trueColorTileUrl && (
                    <TileLayer
                        url={`${APP_CONFIG.API_BASE_URL.replace(':8000', ':8080')}/cog/tiles/{z}/{x}/{y}?url=${encodeURIComponent(trueColorTileUrl)}&rescale=0,1`}
                        maxNativeZoom={14}
                        maxZoom={20}
                        opacity={overlayOpacity}
                    />
                )}

                {/* 4. Split Preview Polygons */}
                {splitPreviewPolygons.map((preview) => {
                    const polygons = parseWKT(preview.geometry_wkt)
                    return polygons.map((coords, pIdx) => (
                        <SplitPreviewPolygon
                            key={`${preview.id}-${pIdx}`}
                            id={preview.id}
                            coords={coords}
                            areaHa={preview.area_ha}
                            maxAreaHa={splitMaxAreaHa}
                            isSelected={splitSelectedIds.includes(preview.id)}
                            isEditable={splitEditableId === preview.id}
                            onSelect={onSplitPreviewSelect}
                            onUpdate={onSplitPreviewUpdate}
                        />
                    ))
                })}

                {/* 5. AOI Polygons */}
                {showAOIs && aois.map((aoi, idx) => {
                    const polygons = parseWKT(aoi.geometry)
                    const isSelected = selectedAOI?.id === aoi.id
                    const isProcessing = processingAois?.has(aoi.id)
                    const status = getAoiStatus(aoi)
                    const isMergeSelected = mergeSelectedIds.includes(aoi.id)
                    return polygons.map((coords, pIdx) => (
                        <AOIPolygon
                            key={`${aoi.id}-${idx}-${pIdx}`}
                            aoi={aoi}
                            coords={coords}
                            getAOIColor={getAOIColor}
                            isEditing={isEditing}
                            isSelected={isSelected}
                            isMergeSelected={isMergeSelected}
                            isProcessing={isProcessing}
                            status={status}
                            ndviMean={aoi.ndvi_mean}
                            onUpdate={onAOIUpdate}
                            onSelect={mergeModeActive ? onMergeSelect : undefined}
                        />
                    ))
                })}

                {/* 6. Status Icons */}
                {showAOIs && aois.map((aoi) => {
                    const polygons = parseWKT(aoi.geometry)
                    const coords = polygons[0]
                    if (!coords || coords.length === 0) return null
                    const status = getAoiStatus(aoi)
                    const badge = getAoiBadge(aoi)
                    if (status === 'normal') return null
                    return (
                        <StatusIconMarker
                            key={`status-${aoi.id}`}
                            position={getPolygonCenter(coords)}
                            status={status}
                        />
                    )
                })}

                {splitPreviewPolygons.map((preview) => {
                    const polygons = parseWKT(preview.geometry_wkt)
                    const coords = polygons[0]
                    if (!coords || coords.length === 0) return null
                    const isOver = (preview.area_ha ?? 0) > (splitMaxAreaHa ?? 2000)
                    return (
                        <StatusIconMarker
                            key={`split-${preview.id}`}
                            position={getPolygonCenter(coords)}
                            status={isOver ? 'alert' : 'split'}
                        />
                    )
                })}

                {showAOIs && aois.map((aoi) => {
                    const polygons = parseWKT(aoi.geometry)
                    const coords = polygons[0]
                    if (!coords || coords.length === 0) return null
                    const badge = getAoiBadge(aoi)
                    if (!badge) return null
                    const center = getPolygonCenter(coords)
                    const offset = [center[0] + 0.0008, center[1] + 0.0008] as [number, number]
                    return (
                        <SignalBadgeMarker
                            key={`badge-${aoi.id}`}
                            position={offset}
                            badge={badge}
                        />
                    )
                })}

                {/* 7. Alert Markers */}
                <AlertMarkers signals={signals} showAlerts={showAlerts} aois={aois} />

                {/* 8. Drawing Tools */}
                {isDrawing && setDrawingPoints && (
                    <>
                        <DrawingController points={drawingPoints} setPoints={setDrawingPoints} />
                        {drawingPoints.map((point, idx) => (
                            <Marker key={idx} position={point} interactive={false} />
                        ))}
                        {drawingPoints.length > 1 && (
                            <Polyline positions={drawingPoints} color="red" dashArray="5, 10" />
                        )}
                        {drawingPoints.length > 2 && (
                            <Polygon positions={drawingPoints} pathOptions={{ color: 'red', fillOpacity: 0.1 }} />
                        )}
                    </>
                )}

                <ZoomControl position="bottomright" />

                {/* 6. NEW CONTROL CLUSTER */}
                <MapControlCluster
                    activeBaseLayer={activeBaseLayer}
                    setActiveBaseLayer={setActiveBaseLayer}
                    activeOverlay={activeOverlay}
                    setActiveOverlay={setActiveOverlay}
                    overlayOpacity={overlayOpacity}
                    setOverlayOpacity={setOverlayOpacity}
                    showAlerts={showAlerts}
                    setShowAlerts={setShowAlerts}
                    showAOIs={showAOIs}
                    setShowAOIs={setShowAOIs}
                    availableLayers={availableLayers}
                    aois={aois}
                />

            </MapContainer>
        </>
    )
}
