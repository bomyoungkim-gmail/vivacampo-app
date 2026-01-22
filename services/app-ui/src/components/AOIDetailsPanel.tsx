import { useState, useEffect, useMemo } from 'react'
import type { AOI, Signal, DerivedAssets, RadarAssets, WeatherData } from '@/lib/types'
import { signalAPI, aoiAPI } from '@/lib/api'
import ChartComponent from './ChartComponent'
import WeatherChart from './WeatherChart'
import AOIActionsMenu from './AOIActionsMenu'
import { useErrorHandler } from '@/lib/errorHandler'
import { MapPin, Calendar, Activity, AlertTriangle, ChevronRight, CloudRain, Radio } from 'lucide-react'

interface AOIDetailsPanelProps {
    aoi: AOI
    onClose: () => void
    onDelete: () => void
    onEdit?: () => void
    onSave?: () => void
    onCancelEdit?: () => void
    isEditing?: boolean
}

type IndexType = 'NDVI' | 'NDWI' | 'NDMI' | 'SAVI' | 'ANOMALY' |
    'NDRE' | 'RECI' | 'GNDVI' | 'EVI' |
    'MSI' | 'NBR' | 'BSI' |
    'ARI' | 'CRI'

type RadarIndexType = 'RVI' | 'RATIO'
type TabType = 'OVERVIEW' | 'HEALTH' | 'WATER' | 'NUTRITION' | 'SOIL' | 'RADAR' | 'WEATHER' | 'ALERTS'

export default function AOIDetailsPanel({
    aoi,
    onClose,
    onDelete,
    onEdit,
    onSave,
    onCancelEdit,
    isEditing = false
}: AOIDetailsPanelProps) {
    const [activeTab, setActiveTab] = useState<TabType>('OVERVIEW')
    const [signals, setSignals] = useState<Signal[]>([])
    const [history, setHistory] = useState<DerivedAssets[]>([])
    const [radarHistory, setRadarHistory] = useState<RadarAssets[]>([])
    const [weatherHistory, setWeatherHistory] = useState<WeatherData[]>([])

    const [loading, setLoading] = useState(false)
    const [selectedIndex, setSelectedIndex] = useState<IndexType>('NDVI')

    // Reset selected index when changing tabs to a default for that tab
    useEffect(() => {
        if (activeTab === 'HEALTH') setSelectedIndex('NDVI')
        if (activeTab === 'WATER') setSelectedIndex('NDMI')
        if (activeTab === 'NUTRITION') setSelectedIndex('RECI') // RECI is good proxy, or ARI
        if (activeTab === 'SOIL') setSelectedIndex('SAVI')
    }, [activeTab])

    const [selectedRadarIndex, setSelectedRadarIndex] = useState<RadarIndexType>('RVI')

    const { handleError } = useErrorHandler()

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true)
            try {
                // Parallel fetch for basic data
                const [signalsRes, historyRes] = await Promise.all([
                    signalAPI.list({ aoi_id: aoi.id }),
                    aoiAPI.getHistory(aoi.id)
                ])
                setSignals(signalsRes.data)
                setHistory(historyRes.data.sort((a, b) => {
                    if (a.year !== b.year) return a.year - b.year
                    return a.week - b.week
                }))

                // Fetch new data sources (non-blocking for initial render if we want, but simple await here)
                try {
                    const radarRes = await aoiAPI.getRadarHistory(aoi.id)
                    setRadarHistory(radarRes.data.sort((a, b) => {
                        if (a.year !== b.year) return a.year - b.year
                        return a.week - b.week
                    }))
                } catch (e) { console.warn("Radar fetch failed", e) }

                try {
                    const weatherRes = await aoiAPI.getWeatherHistory(aoi.id)
                    setWeatherHistory(weatherRes.data)
                } catch (e) { console.warn("Weather fetch failed", e) }

            } catch (err) {
                console.error("Failed to fetch data", err)
            } finally {
                setLoading(false)
            }
        }

        if (aoi) {
            fetchData()
        }
    }, [aoi])

    // Optical Chart Data
    const chartData = useMemo(() => {
        return history.map(item => {
            const date = new Date(item.year, 0, 1 + (item.week - 1) * 7)
            const dateStr = date.toISOString().split('T')[0]
            let value = 0
            switch (selectedIndex) {
                case 'NDVI': value = item.ndvi_mean || 0; break;
                case 'NDWI': value = item.ndwi_mean || 0; break;
                case 'NDMI': value = item.ndmi_mean || 0; break;
                case 'SAVI': value = item.savi_mean || 0; break;
                case 'ANOMALY': value = item.anomaly_mean || 0; break;

                // Advanced
                case 'NDRE': value = item.ndre_mean || 0; break;
                case 'RECI': value = item.reci_mean || 0; break;
                case 'GNDVI': value = item.gndvi_mean || 0; break;
                case 'EVI': value = item.evi_mean || 0; break;
                case 'MSI': value = item.msi_mean || 0; break;
                case 'NBR': value = item.nbr_mean || 0; break;
                case 'BSI': value = item.bsi_mean || 0; break;
                case 'ARI': value = item.ari_mean || 0; break;
                case 'CRI': value = item.cri_mean || 0; break;
            }
            return { date: dateStr, value: value }
        }).filter(d => d.value !== 0)
    }, [history, selectedIndex])

    // Radar Chart Data
    const radarChartData = useMemo(() => {
        return radarHistory.map(item => {
            const date = new Date(item.year, 0, 1 + (item.week - 1) * 7)
            const dateStr = date.toISOString().split('T')[0]
            let value = 0
            switch (selectedRadarIndex) {
                case 'RVI': value = item.rvi_mean || 0; break;
                case 'RATIO': value = item.ratio_mean || 0; break;
            }
            return { date: dateStr, value: value }
        }).filter(d => d.value !== 0)
    }, [radarHistory, selectedRadarIndex])

    const getChartProps = () => {
        switch (selectedIndex) {
            case 'NDVI': return { title: "Vigor Vegetativo (NDVI)", color: "#16a34a" }
            case 'NDWI': return { title: "Índice de Água (NDWI)", color: "#2563eb" }
            case 'NDMI': return { title: "Umidade de Vegetação (NDMI)", color: "#0891b2" }
            case 'SAVI': return { title: "Solo Ajustado (SAVI)", color: "#65a30d" }
            case 'ANOMALY': return { title: "Anomalia de Vigor", color: "#dc2626" }

            case 'NDRE': return { title: "Vigor Red-Edge (NDRE)", color: "#15803d" }
            case 'RECI': return { title: "Clorofila (RECI)", color: "#4d7c0f" }
            case 'GNDVI': return { title: "Biomassa Verde (GNDVI)", color: "#047857" }
            case 'EVI': return { title: "Vigor Melhorado (EVI)", color: "#10b981" }

            case 'MSI': return { title: "Estresse Hídrico (MSI)", color: "#0ea5e9" }

            case 'NBR': return { title: "Razão de Queimada (NBR)", color: "#ea580c" }
            case 'BSI': return { title: "Solo Exposto (BSI)", color: "#a16207" }

            case 'ARI': return { title: "Antocianina (ARI)", color: "#9333ea" }
            case 'CRI': return { title: "Carotenoides (CRI)", color: "#d97706" }

            default: return { title: "", color: "" }
        }
    }

    const getRadarProps = () => {
        switch (selectedRadarIndex) {
            case 'RVI': return { title: "Radar Vegetation Index (RVI)", color: "#d97706", domain: [0, 1] as [number, number] }
            case 'RATIO': return { title: "Razão VH/VV", color: "#9333ea", domain: ['auto', 'auto'] as ['auto', 'auto'] } // Ratio can exceed 1
            default: return { title: "", color: "", domain: [0, 1] as [number, number] }
        }
    }

    const uniqueAlerts = useMemo(() => {
        const seen = new Set()
        return signals.filter(s => {
            const dateSrc = s.detected_at ?? s.created_at ?? 0
            const key = `${s.signal_type}-${new Date(dateSrc).toDateString()}`
            if (seen.has(key)) return false
            seen.add(key)
            return true
        })
    }, [signals])

    const currentChartProps = getChartProps()
    const currentRadarProps = getRadarProps()

    return (
        <div className="h-full flex flex-col bg-white overflow-hidden rounded-t-xl sm:rounded-none">
            {/* Header */}
            <div className="p-4 border-b border-gray-100 flex justify-between items-start bg-white z-10">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <h2 className="font-bold text-xl text-gray-900 leading-tight">{aoi.name}</h2>
                        {isEditing && <span className="text-[10px] font-black tracking-wide text-orange-600 bg-orange-100 px-1.5 py-0.5 rounded uppercase animate-pulse">Editando</span>}
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-500">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide flex items-center gap-1
                            ${aoi.use_type === 'CROP' ? 'bg-orange-50 text-orange-600'
                                : aoi.use_type === 'TIMBER' ? 'bg-[#f4e4bc] text-[#8B4513]'
                                    : 'bg-green-50 text-green-600'}`}>
                            {aoi.use_type === 'PASTURE' ? 'Pastagem' : aoi.use_type === 'TIMBER' ? 'Madeira' : 'Lavoura'}
                        </span>
                        <span className="flex items-center gap-1">
                            <MapPin size={12} /> {aoi.area_ha ? `${aoi.area_ha.toFixed(1)} ha` : '--'}
                        </span>
                    </div>
                </div>
                <div className="flex items-center gap-1">
                    {isEditing ? (
                        <div className="flex gap-2">
                            <button onClick={onCancelEdit} className="px-3 py-1.5 text-xs font-bold text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg">Cancelar</button>
                            <button onClick={onSave} className="px-3 py-1.5 text-xs font-bold text-white bg-green-600 hover:bg-green-700 rounded-lg shadow-sm">Salvar</button>
                        </div>
                    ) : (
                        <>
                            <AOIActionsMenu
                                onEditGeometry={onEdit}
                                onDelete={onDelete}
                                onExport={() => alert("Exportar KML em breve")}
                            />
                            <button
                                onClick={onClose}
                                className="p-2 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
                                title="Voltar para lista"
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                                </svg>
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-200 px-4 pt-2 gap-4 bg-white shrink-0 overflow-x-auto">
                <button onClick={() => setActiveTab('OVERVIEW')} className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${activeTab === 'OVERVIEW' ? 'border-green-600 text-green-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>Visão Geral</button>
                <div className="h-6 w-px bg-gray-200 my-auto mx-2 hidden sm:block"></div>
                <button onClick={() => setActiveTab('HEALTH')} className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-1 ${activeTab === 'HEALTH' ? 'border-green-600 text-green-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>Saúde</button>
                <button onClick={() => setActiveTab('WATER')} className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-1 ${activeTab === 'WATER' ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>Água</button>
                <button onClick={() => setActiveTab('NUTRITION')} className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-1 ${activeTab === 'NUTRITION' ? 'border-purple-600 text-purple-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>Nutrição</button>
                <button onClick={() => setActiveTab('SOIL')} className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-1 ${activeTab === 'SOIL' ? 'border-orange-600 text-orange-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>Solo</button>
                <div className="h-6 w-px bg-gray-200 my-auto mx-2 hidden sm:block"></div>
                <button onClick={() => setActiveTab('RADAR')} className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-1 ${activeTab === 'RADAR' ? 'border-gray-600 text-gray-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>Radar</button>
                <button onClick={() => setActiveTab('WEATHER')} className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-1 ${activeTab === 'WEATHER' ? 'border-gray-600 text-gray-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>Clima</button>
                <button onClick={() => setActiveTab('ALERTS')} className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-1 ${activeTab === 'ALERTS' ? 'border-red-600 text-red-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>Alertas ({uniqueAlerts.length})</button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 bg-gray-50/50">

                {/* ---------- VISÃO GERAL ---------- */}
                {activeTab === 'OVERVIEW' && (
                    <div className="space-y-6">
                        <div className="grid grid-cols-2 gap-3">
                            <div className="bg-white p-3 rounded-xl border border-gray-100 shadow-sm">
                                <p className="text-xs text-gray-400 font-medium uppercase mb-1">Status</p>
                                <div className="flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                                    <p className="font-bold text-gray-800">Monitorado</p>
                                </div>
                            </div>
                            <div className="bg-white p-3 rounded-xl border border-gray-100 shadow-sm">
                                <p className="text-xs text-gray-400 font-medium uppercase mb-1">Última Imagem</p>
                                <div className="flex items-center gap-2">
                                    <Calendar size={14} className="text-gray-400" />
                                    <p className="font-bold text-gray-800">Há 5 dias</p>
                                </div>
                            </div>
                        </div>
                        {uniqueAlerts.length > 0 && (
                            <div className="bg-orange-50 border border-orange-100 rounded-xl p-4">
                                <div className="flex justify-between items-center mb-2">
                                    <h4 className="text-orange-900 font-bold text-sm flex items-center gap-2"><AlertTriangle size={16} /> Atenção Necessária</h4>
                                    <button onClick={() => setActiveTab('ALERTS')} className="text-xs font-bold text-orange-700 hover:underline flex items-center">Ver todos <ChevronRight size={12} /></button>
                                </div>
                                <p className="text-sm text-orange-800/80">Foram detectados {uniqueAlerts.length} alertas recentes. Verifique a aba de alertas.</p>
                            </div>
                        )}
                        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="font-bold text-gray-700 flex items-center gap-2"><Activity size={16} className="text-blue-500" /> Vigor Recente</h3>
                                <button className="text-xs text-blue-600 font-bold" onClick={() => setActiveTab('HEALTH')}>Detalhes</button>
                            </div>
                            <div className="h-40">
                                <ChartComponent title="NDVI (30 Dias)" data={chartData.slice(-4)} color="#16a34a" />
                            </div>
                        </div>
                        {/* Weather Snippet */}
                        {weatherHistory.length > 0 && (
                            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="font-bold text-gray-700 flex items-center gap-2"><CloudRain size={16} className="text-blue-500" /> Clima Recente</h3>
                                    <button className="text-xs text-blue-600 font-bold" onClick={() => setActiveTab('WEATHER')}>Detalhes</button>
                                </div>
                                <div className="grid grid-cols-2 gap-4 text-center">
                                    <div className="bg-gray-50 rounded p-2">
                                        <p className="text-xs text-gray-500">Chuva (7d)</p>
                                        <p className="font-bold text-blue-600 text-lg">
                                            {weatherHistory.slice(0, 7).reduce((a, b) => a + b.precip_sum, 0).toFixed(1)} mm
                                        </p>
                                    </div>
                                    <div className="bg-gray-50 rounded p-2">
                                        <p className="text-xs text-gray-500">Temp. Max (Ontem)</p>
                                        <p className="font-bold text-red-500 text-lg">
                                            {weatherHistory[weatherHistory.length - 1]?.temp_max?.toFixed(1) || '--'}°C
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ---------- SAÚDE (HEALTH) ---------- */}
                {activeTab === 'HEALTH' && (
                    <div className="space-y-4">
                        <div className="bg-gray-100 p-1 rounded-lg flex overflow-x-auto gap-1">
                            {(['NDVI', 'NDRE', 'RECI', 'GNDVI', 'EVI', 'ANOMALY'] as IndexType[]).map(type => (
                                <button key={type} onClick={() => setSelectedIndex(type)} className={`flex-1 min-w-[60px] py-1.5 text-xs font-bold rounded-md transition-all shadow-sm whitespace-nowrap ${selectedIndex === type ? 'bg-white text-green-700 border border-green-200' : 'text-gray-500 hover:text-gray-700 hover:bg-white/50'}`}>{type}</button>
                            ))}
                        </div>
                        <ChartComponent title={currentChartProps.title} data={chartData} color={currentChartProps.color} />
                    </div>
                )}

                {/* ---------- ÁGUA (WATER) ---------- */}
                {activeTab === 'WATER' && (
                    <div className="space-y-4">
                        <div className="bg-gray-100 p-1 rounded-lg flex overflow-x-auto gap-1">
                            {(['NDMI', 'NDWI', 'MSI'] as IndexType[]).map(type => (
                                <button key={type} onClick={() => setSelectedIndex(type)} className={`flex-1 min-w-[60px] py-1.5 text-xs font-bold rounded-md transition-all shadow-sm whitespace-nowrap ${selectedIndex === type ? 'bg-white text-blue-700 border border-blue-200' : 'text-gray-500 hover:text-gray-700 hover:bg-white/50'}`}>{type}</button>
                            ))}
                        </div>
                        <ChartComponent title={currentChartProps.title} data={chartData} color={currentChartProps.color} />
                    </div>
                )}

                {/* ---------- NUTRIÇÃO (NUTRITION) ---------- */}
                {activeTab === 'NUTRITION' && (
                    <div className="space-y-4">
                        <div className="bg-gray-100 p-1 rounded-lg flex overflow-x-auto gap-1">
                            {(['RECI', 'ARI', 'CRI'] as IndexType[]).map(type => (
                                <button key={type} onClick={() => setSelectedIndex(type)} className={`flex-1 min-w-[60px] py-1.5 text-xs font-bold rounded-md transition-all shadow-sm whitespace-nowrap ${selectedIndex === type ? 'bg-white text-purple-700 border border-purple-200' : 'text-gray-500 hover:text-gray-700 hover:bg-white/50'}`}>{type}</button>
                            ))}
                        </div>
                        <ChartComponent title={currentChartProps.title} data={chartData} color={currentChartProps.color} />
                    </div>
                )}

                {/* ---------- SOLO (SOIL) ---------- */}
                {activeTab === 'SOIL' && (
                    <div className="space-y-4">
                        <div className="bg-gray-100 p-1 rounded-lg flex overflow-x-auto gap-1">
                            {(['SAVI', 'NBR', 'BSI'] as IndexType[]).map(type => (
                                <button key={type} onClick={() => setSelectedIndex(type)} className={`flex-1 min-w-[60px] py-1.5 text-xs font-bold rounded-md transition-all shadow-sm whitespace-nowrap ${selectedIndex === type ? 'bg-white text-orange-700 border border-orange-200' : 'text-gray-500 hover:text-gray-700 hover:bg-white/50'}`}>{type}</button>
                            ))}
                        </div>
                        <ChartComponent title={currentChartProps.title} data={chartData} color={currentChartProps.color} />
                    </div>
                )}

                {/* ---------- RADAR (NEW) ---------- */}
                {activeTab === 'RADAR' && (
                    <div className="space-y-4">
                        <div className="bg-gray-200 p-1 rounded-lg flex overflow-x-auto">
                            {(['RVI', 'RATIO'] as RadarIndexType[]).map(type => (
                                <button key={type} onClick={() => setSelectedRadarIndex(type)} className={`flex-1 min-w-[60px] py-1.5 text-xs font-bold rounded-md transition-all shadow-sm ${selectedRadarIndex === type ? 'bg-white text-gray-900 border border-gray-200/50' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200/50'}`}>{type}</button>
                            ))}
                        </div>
                        <ChartComponent
                            title={currentRadarProps.title}
                            data={radarChartData}
                            color={currentRadarProps.color}
                            domain={currentRadarProps.domain} // Passing domain for Ratio
                        />
                        <div className="bg-purple-50 p-4 rounded-lg border border-purple-100 text-xs text-purple-800 leading-relaxed">
                            <strong>Radar (Sentinel-1):</strong> O radar penetra nuvens. Use RVI para biomassa e Razão VH/VV para estrutura da vegetação, mesmo em dias nublados.
                        </div>
                    </div>
                )}

                {/* ---------- WEATHER (NEW) ---------- */}
                {activeTab === 'WEATHER' && (
                    <div className="space-y-4">
                        <WeatherChart data={weatherHistory} />
                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 text-xs text-blue-800 leading-relaxed">
                            <strong>Fonte:</strong> Dados meteorológicos históricos baseados em reanálise (ERA5) e estações próximas via Open-Meteo.
                        </div>
                    </div>
                )}

                {/* ---------- ALERTAS ---------- */}
                {activeTab === 'ALERTS' && (
                    <div className="space-y-3">
                        {uniqueAlerts.length === 0 ? (
                            <div className="text-center py-10">
                                <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-3"><span className="text-2xl">🌿</span></div>
                                <h3 className="font-bold text-gray-800">Tudo limpo!</h3>
                                <p className="text-sm text-gray-500 mt-1">Nenhum alerta recente.</p>
                            </div>
                        ) : (
                            uniqueAlerts.map(signal => (
                                <div key={signal.id} className="bg-white border-l-4 border-yellow-400 rounded-r-lg shadow-sm p-3 flex flex-col gap-2">
                                    <div className="flex justify-between items-start">
                                        <h4 className="font-bold text-gray-800 text-sm">{signal.signal_type}</h4>
                                        <span className="text-[10px] uppercase font-bold text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{new Date(signal.detected_at || signal.created_at || new Date()).toLocaleDateString()}</span>
                                    </div>
                                    <p className="text-xs text-gray-600 line-clamp-2">{signal.metadata?.summary || "Anomalia detectada."}</p>
                                </div>
                            ))
                        )}
                    </div>
                )}

            </div>
        </div>
    )
}
