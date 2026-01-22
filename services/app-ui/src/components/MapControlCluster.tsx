import { useState, useRef, useEffect } from 'react'
import { useMap } from 'react-leaflet'
import { Layers, Maximize, Search, Eye, EyeOff, Map as MapIcon, AlertTriangle } from 'lucide-react'
import L from 'leaflet'
import { APP_CONFIG } from '@/lib/config'

interface MapControlClusterProps {
    // State for Layers
    activeBaseLayer: string
    setActiveBaseLayer: (l: string) => void
    activeOverlay: string | null
    setActiveOverlay: (l: string | null) => void
    overlayOpacity: number
    setOverlayOpacity: (o: number) => void

    // Toggles
    showAlerts: boolean
    setShowAlerts: (s: boolean) => void
    showAOIs: boolean
    setShowAOIs: (s: boolean) => void

    // Availability
    availableLayers: {
        ndvi: boolean
        ndwi: boolean
        ndmi: boolean
        savi: boolean
        anomaly: boolean
        falseColor: boolean
        trueColor: boolean

        ndre: boolean
        reci: boolean
        gndvi: boolean
        evi: boolean

        msi: boolean
        nbr: boolean
        bsi: boolean

        ari: boolean
        cri: boolean

        rvi: boolean
        ratio: boolean
    }

    // Data for FitBounds
    aois?: any[]

    // Search Handler (optional if handled internally)
}

export function MapControlCluster({
    activeBaseLayer, setActiveBaseLayer,
    activeOverlay, setActiveOverlay,
    overlayOpacity, setOverlayOpacity,
    showAlerts, setShowAlerts,
    showAOIs, setShowAOIs,
    availableLayers,
    aois = []
}: MapControlClusterProps) {
    const map = useMap()
    const [isPopoverOpen, setIsPopoverOpen] = useState(false)
    const [isSearchOpen, setIsSearchOpen] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')
    const [isSearching, setIsSearching] = useState(false)

    const clusterRef = useRef<HTMLDivElement>(null)
    const popoverRef = useRef<HTMLDivElement>(null)
    const searchInputRef = useRef<HTMLInputElement>(null)

    // Click Outside to close Popover
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (popoverRef.current && !popoverRef.current.contains(event.target as Node) &&
                clusterRef.current && !clusterRef.current.contains(event.target as Node)) {
                setIsPopoverOpen(false)
            }
        }
        document.addEventListener("mousedown", handleClickOutside)
        return () => document.removeEventListener("mousedown", handleClickOutside)
    }, [])

    // Fit Bounds Logic
    const handleFitBounds = () => {
        if (!aois || aois.length === 0) return

        // Quick extraction of points from WKT (simplified)
        // Ideally reuse the parseWKT utility, but we can't import internal helpers easily
        // We will rely on the main component ensuring valid geometries or basic parsing here
        const bounds = L.latLngBounds([])

        let hasPoints = false
        aois.forEach(aoi => {
            if (aoi.geometry) {
                const matches = aoi.geometry.match(/-?\d+\.\d+\s+-?\d+\.\d+/g)
                if (matches) {
                    matches.forEach((pair: string) => {
                        const [lng, lat] = pair.trim().split(/\s+/).map(Number)
                        if (!isNaN(lat) && !isNaN(lng)) {
                            bounds.extend([lat, lng])
                            hasPoints = true
                        }
                    })
                }
            }
        })

        if (hasPoints && bounds.isValid()) {
            map.fitBounds(bounds, { padding: [50, 50] })
        }
    }

    // Search Logic
    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!searchQuery.trim()) return

        setIsSearching(true)
        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch(`${APP_CONFIG.API_BASE_URL}/farms/geocode?q=${encodeURIComponent(searchQuery)}`, {
                headers: { 'Authorization': `Bearer ${token}` } // Mock doesn't need real token usually
            })

            if (response.ok) {
                const data = await response.json()
                if (data.length > 0) {
                    const { lat, lon } = data[0]
                    map.setView([parseFloat(lat), parseFloat(lon)], 13)
                    setIsSearchOpen(false) // Close search on success
                } else {
                    alert('Local não encontrado')
                }
            }
        } catch (err) {
            console.error(err)
        } finally {
            setIsSearching(false)
        }
    }

    const toggleSearch = () => {
        if (isSearchOpen) {
            setIsSearchOpen(false)
        } else {
            setIsSearchOpen(true)
            setTimeout(() => searchInputRef.current?.focus(), 100)
        }
    }

    // Prevent Map Click propagation
    const disablePropagation = (e: React.MouseEvent) => {
        e.stopPropagation()
        e.preventDefault() // Prevent map generic clicks
    }

    return (
        <div className="leaflet-bottom leaflet-right" style={{ pointerEvents: 'auto', zIndex: 9999, position: 'absolute', bottom: '20px', right: '10px' }}>
            <div
                ref={clusterRef}
                className="flex flex-col bg-white rounded-lg shadow-lg border border-gray-200 overflow-visible"
                onDoubleClick={(e) => e.stopPropagation()}
                onMouseDown={(e) => e.stopPropagation()} // Crucial for Leaflet
                onClick={(e) => e.stopPropagation()}
            >
                {/* 1. Layers Button */}
                <button
                    onClick={() => setIsPopoverOpen(!isPopoverOpen)}
                    className={`p-3 hover:bg-gray-50 border-b border-gray-100 flex items-center justify-center transition-colors ${isPopoverOpen ? 'bg-blue-50 text-blue-600' : 'text-gray-700'}`}
                    title="Camadas e Filtros"
                >
                    <Layers size={20} />
                </button>

                {/* 2. Toggle AOIs */}


                {/* 3. Fit Bounds */}
                <button
                    onClick={handleFitBounds}
                    className="p-3 hover:bg-gray-50 border-b border-gray-100 flex items-center justify-center text-gray-700"
                    title="Enquadrar Dados"
                >
                    <Maximize size={20} />
                </button>

                {/* 4. Search */}
                <div className="relative">
                    <button
                        onClick={toggleSearch}
                        className={`p-3 hover:bg-gray-50 flex items-center justify-center rounded-b-lg ${isSearchOpen ? 'bg-gray-100 text-blue-600' : 'text-gray-700'}`}
                        title="Buscar Local"
                    >
                        <Search size={20} />
                    </button>

                    {/* Floating Search Input */}
                    {isSearchOpen && (
                        <div className="absolute right-full top-0 mr-2 flex items-center bg-white rounded-lg shadow-lg p-1 border border-gray-200 w-64 animate-in slide-in-from-right-2">
                            <form onSubmit={handleSearch} className="flex w-full">
                                <input
                                    ref={searchInputRef}
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    placeholder="Buscar cidade..."
                                    className="flex-1 px-3 py-2 text-sm outline-none text-gray-700 placeholder-gray-400"
                                />
                                <button type="submit" disabled={isSearching} className="p-2 text-blue-600 font-medium hover:bg-blue-50 rounded-md">
                                    IR
                                </button>
                            </form>
                        </div>
                    )}
                </div>
            </div>

            {/* POPOVER: Layers & Settings */}
            {isPopoverOpen && (
                <div
                    ref={popoverRef}
                    className="absolute bottom-0 right-full mr-3 w-72 bg-white rounded-lg shadow-xl border border-gray-200 p-4 text-sm animate-in fade-in zoom-in-95 origin-bottom-right"
                    onMouseDown={(e) => e.stopPropagation()}
                    onDoubleClick={(e) => e.stopPropagation()}
                >
                    <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <Layers size={16} />
                        Camadas
                    </h3>

                    {/* Section: Base Map */}
                    <div className="mb-4">
                        <label className="text-xs font-semibold text-gray-500 uppercase mb-2 block">Mapa Base</label>
                        <div className="grid grid-cols-3 gap-2">
                            <button
                                onClick={() => setActiveBaseLayer('satellite')}
                                className={`px-3 py-2 rounded border text-center text-xs font-medium transition-all ${activeBaseLayer === 'satellite'
                                    ? 'bg-blue-50 border-blue-500 text-blue-700'
                                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                                    }`}
                            >
                                🛰️ Satélite
                            </button>
                            <button
                                onClick={() => setActiveBaseLayer('map')}
                                className={`px-3 py-2 rounded border text-center text-xs font-medium transition-all ${activeBaseLayer === 'map'
                                    ? 'bg-blue-50 border-blue-500 text-blue-700'
                                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                                    }`}
                            >
                                🗺️ Mapa
                            </button>
                            <button
                                onClick={() => setActiveBaseLayer('topo')}
                                className={`px-3 py-2 rounded border text-center text-xs font-medium transition-all ${activeBaseLayer === 'topo'
                                    ? 'bg-blue-50 border-blue-500 text-blue-700'
                                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                                    }`}
                            >
                                🏔️ Relevo
                            </button>
                        </div>
                    </div>

                    {/* Section: Groups */}
                    <div className="space-y-4 mb-4 max-h-[300px] overflow-y-auto pr-1 custom-scrollbar">

                        {/* Group: Basics */}
                        <div>
                            <label className="text-xs font-semibold text-gray-500 uppercase mb-2 block">Básico (Óptico)</label>
                            <div className="grid grid-cols-2 gap-2">
                                {[
                                    { id: 'trueColor', label: '📸 RGB', disabled: !availableLayers.trueColor },
                                    { id: 'falseColor', label: '🖌️ Falsa Cor', disabled: !availableLayers.falseColor },
                                    { id: 'ndvi', label: '🌱 NDVI', disabled: !availableLayers.ndvi },
                                    { id: 'anomaly', label: '📉 Anomalia', disabled: !availableLayers.anomaly },
                                ].map(layer => (
                                    <LayerButton key={layer.id} layer={layer} active={activeOverlay} onClick={setActiveOverlay} />
                                ))}
                            </div>
                        </div>

                        {/* Group: Health */}
                        <div>
                            <label className="text-xs font-semibold text-gray-500 uppercase mb-2 block">Saúde & Vigor</label>
                            <div className="grid grid-cols-2 gap-2">
                                {[
                                    { id: 'ndre', label: '🌿 NDRE', disabled: !availableLayers.ndre },
                                    { id: 'reci', label: '🍃 RECI', disabled: !availableLayers.reci },
                                    { id: 'gndvi', label: '🍀 GNDVI', disabled: !availableLayers.gndvi },
                                    { id: 'evi', label: '🌳 EVI', disabled: !availableLayers.evi },
                                ].map(layer => (
                                    <LayerButton key={layer.id} layer={layer} active={activeOverlay} onClick={setActiveOverlay} />
                                ))}
                            </div>
                        </div>

                        {/* Group: Water/Soil */}
                        <div>
                            <label className="text-xs font-semibold text-gray-500 uppercase mb-2 block">Água & Solo</label>
                            <div className="grid grid-cols-2 gap-2">
                                {[
                                    { id: 'ndwi', label: '💧 NDWI', disabled: !availableLayers.ndwi },
                                    { id: 'ndmi', label: '💦 NDMI', disabled: !availableLayers.ndmi },
                                    { id: 'msi', label: '🏜️ MSI', disabled: !availableLayers.msi },
                                    { id: 'savi', label: '🍂 SAVI', disabled: !availableLayers.savi },
                                    { id: 'bsi', label: '🟤 BSI', disabled: !availableLayers.bsi },
                                    { id: 'nbr', label: '🔥 NBR', disabled: !availableLayers.nbr },
                                ].map(layer => (
                                    <LayerButton key={layer.id} layer={layer} active={activeOverlay} onClick={setActiveOverlay} />
                                ))}
                            </div>
                        </div>

                        {/* Group: Nutrition */}
                        <div>
                            <label className="text-xs font-semibold text-gray-500 uppercase mb-2 block">Nutrição</label>
                            <div className="grid grid-cols-2 gap-2">
                                {[
                                    { id: 'ari', label: '🍇 ARI', disabled: !availableLayers.ari },
                                    { id: 'cri', label: '🥕 CRI', disabled: !availableLayers.cri },
                                ].map(layer => (
                                    <LayerButton key={layer.id} layer={layer} active={activeOverlay} onClick={setActiveOverlay} />
                                ))}
                            </div>
                        </div>

                        {/* Group: Radar */}
                        <div>
                            <label className="text-xs font-semibold text-gray-500 uppercase mb-2 block">Radar (S1)</label>
                            <div className="grid grid-cols-2 gap-2">
                                {[
                                    { id: 'rvi', label: '📻 RVI', disabled: !availableLayers.rvi },
                                    { id: 'ratio', label: '📡 VH/VV', disabled: !availableLayers.ratio },
                                ].map(layer => (
                                    <LayerButton key={layer.id} layer={layer} active={activeOverlay} onClick={setActiveOverlay} />
                                ))}
                            </div>
                        </div>

                        {activeOverlay && (
                            <button onClick={() => setActiveOverlay(null)} className="w-full text-center text-xs text-red-500 hover:text-red-700 mt-2 font-bold border border-red-100 rounded py-1">
                                Limpar Camada Ativa
                            </button>
                        )}
                    </div>


                    {/* Section: Opacity Slider */}
                    {activeOverlay && (
                        <div className="mb-4 animate-in slide-in-from-top-2">
                            <label className="text-xs font-semibold text-gray-500 uppercase mb-1 block flex justify-between">
                                Transparência
                                <span>{Math.round(overlayOpacity * 100)}%</span>
                            </label>
                            <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.1"
                                value={overlayOpacity}
                                onChange={(e) => setOverlayOpacity(parseFloat(e.target.value))}
                                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                            />
                        </div>
                    )}

                    {/* Section: Alerts & Toggles */}
                    <div className="border-t border-gray-100 pt-3 flex flex-col gap-3">
                        <label className="flex items-center gap-3 cursor-pointer group">
                            <div className={`w-10 h-6 flex items-center rounded-full p-1 transition-colors ${showAOIs ? 'bg-indigo-500' : 'bg-gray-300'}`}>
                                <div className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${showAOIs ? 'translate-x-4' : ''}`} />
                            </div>
                            <span className="text-sm font-medium text-gray-700 flex items-center gap-2">
                                <MapIcon size={14} className={showAOIs ? "text-indigo-500" : "text-gray-400"} />
                                Exibir Talhões
                            </span>
                            <input
                                type="checkbox"
                                className="hidden"
                                checked={showAOIs}
                                onChange={() => setShowAOIs(!showAOIs)}
                            />
                        </label>

                        <label className="flex items-center gap-3 cursor-pointer group">
                            <div className={`w-10 h-6 flex items-center rounded-full p-1 transition-colors ${showAlerts ? 'bg-red-500' : 'bg-gray-300'}`}>
                                <div className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${showAlerts ? 'translate-x-4' : ''}`} />
                            </div>
                            <span className="text-sm font-medium text-gray-700 flex items-center gap-2">
                                <AlertTriangle size={14} className={showAlerts ? "text-red-500" : "text-gray-400"} />
                                Exibir Alertas
                            </span>
                            <input
                                type="checkbox"
                                className="hidden"
                                checked={showAlerts}
                                onChange={() => setShowAlerts(!showAlerts)}
                            />
                        </label>
                    </div>

                </div>
            )}
        </div>
    )
}

function LayerButton({ layer, active, onClick }: { layer: any, active: string | null, onClick: (id: string | null) => void }) {
    return (
        <button
            onClick={() => onClick(active === layer.id ? null : layer.id)}
            disabled={layer.disabled}
            className={`px-3 py-2 rounded border text-left text-xs font-medium transition-all flex items-center justify-between ${active === layer.id
                ? 'bg-green-50 border-green-500 text-green-700 ring-1 ring-green-500'
                : layer.disabled
                    ? 'bg-gray-50 border-gray-100 text-gray-300 cursor-not-allowed'
                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
        >
            {layer.label}
            {active === layer.id && <div className="w-1.5 h-1.5 rounded-full bg-green-500" />}
        </button>
    )
}
