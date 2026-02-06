'use client'

import { useEffect, useState, useMemo, useCallback, useRef } from 'react'
import { MapContainer, TileLayer, Polygon, Popup, Marker, Polyline, useMapEvents, useMap, ZoomControl } from 'react-leaflet'
import L from 'leaflet'
import { Radio } from 'lucide-react'
import { APP_CONFIG } from '@/lib/config'
import type { AOI } from '@/lib/types'
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
    isProcessing?: boolean
    onUpdate?: (aoiId: string, newGeometry: any) => void
}

function AOIPolygon({ aoi, coords, getAOIColor, isEditing, isSelected, isProcessing, onUpdate }: AOIPolygonProps) {
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

    return (
        <Polygon
            ref={polygonRef}
            positions={coords}
            pathOptions={{
                color: getAOIColor(aoi.use_type, isProcessing),
                fillColor: getAOIColor(aoi.use_type, isProcessing),
                fillOpacity: isProcessing ? 0.1 : 0.4,
                weight: isSelected ? 4 : 2, // Thicker stroke if selected
                dashArray: (isSelected && !isEditing) || isProcessing ? '5, 5' : undefined // Dash if selected(not editing) OR processing
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
    onMapReady
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

                {/* 4. AOI Polygons */}
                {showAOIs && aois.map((aoi, idx) => {
                    const polygons = parseWKT(aoi.geometry)
                    const isSelected = selectedAOI?.id === aoi.id
                    const isProcessing = processingAois?.has(aoi.id)
                    return polygons.map((coords, pIdx) => (
                        <AOIPolygon
                            key={`${aoi.id}-${idx}-${pIdx}`}
                            aoi={aoi}
                            coords={coords}
                            getAOIColor={getAOIColor}
                            isEditing={isEditing}
                            isSelected={isSelected}
                            isProcessing={isProcessing}
                            onUpdate={onAOIUpdate}
                        />
                    ))
                })}

                {/* 5. Alert Markers */}
                <AlertMarkers signals={signals} showAlerts={showAlerts} aois={aois} />

                {/* 6. Drawing Tools */}
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
