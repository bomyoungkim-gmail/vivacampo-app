'use client'

import { useState, useEffect, useMemo } from 'react'
import type { AOI, Signal, DerivedAssets } from '@/lib/types'
import { signalAPI, aoiAPI } from '@/lib/api'
import ChartComponent from './ChartComponent'
import AOIActionsMenu from './AOIActionsMenu'
import { useErrorHandler } from '@/lib/errorHandler'
import { MapPin, Calendar, Activity, AlertTriangle, ChevronRight } from 'lucide-react'

interface AOIDetailsPanelProps {
    aoi: AOI
    onClose: () => void
    onDelete: () => void
    onEdit?: () => void // Edit Geometry
    onSave?: () => void
    onCancelEdit?: () => void
    isEditing?: boolean
}

type IndexType = 'NDVI' | 'NDWI' | 'NDMI' | 'SAVI' | 'ANOMALY'
type TabType = 'OVERVIEW' | 'INDICES' | 'ALERTS'

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
    const [loading, setLoading] = useState(false)
    const [selectedIndex, setSelectedIndex] = useState<IndexType>('NDVI')
    const { handleError } = useErrorHandler()

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true)
            try {
                const signalsRes = await signalAPI.list({ aoi_id: aoi.id })
                setSignals(signalsRes.data)

                const historyRes = await aoiAPI.getHistory(aoi.id)
                // Sort ascending
                const sorted = historyRes.data.sort((a, b) => {
                    if (a.year !== b.year) return a.year - b.year
                    return a.week - b.week
                })
                setHistory(sorted)

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

    // Prepare chart data based on selected index
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
            }

            return {
                date: dateStr,
                value: value
            }
        }).filter(d => d.value !== 0)
    }, [history, selectedIndex])

    const getChartTitle = () => {
        switch (selectedIndex) {
            case 'NDVI': return "Vigor Vegetativo (NDVI)"
            case 'NDWI': return "Índice de Água (NDWI)"
            case 'NDMI': return "Umidade de Vegetação (NDMI)"
            case 'SAVI': return "Solo Ajustado (SAVI)"
            case 'ANOMALY': return "Anomalia de Vigor"
            default: return ""
        }
    }

    const getChartColor = () => {
        switch (selectedIndex) {
            case 'NDVI': return "#16a34a"
            case 'NDWI': return "#2563eb"
            case 'NDMI': return "#0891b2"
            case 'SAVI': return "#65a30d"
            case 'ANOMALY': return "#dc2626"
            default: return "#16a34a"
        }
    }

    // Deduplicate Alerts for display
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

    return (
        <div className="h-full flex flex-col bg-white overflow-hidden rounded-t-xl sm:rounded-none">
            {/* 1. Header with Actions */}
            <div className="p-4 border-b border-gray-100 flex justify-between items-start bg-white z-10">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <h2 className="font-bold text-xl text-gray-900 leading-tight">{aoi.name}</h2>
                        {isEditing && <span className="text-[10px] font-black tracking-wide text-orange-600 bg-orange-100 px-1.5 py-0.5 rounded uppercase animate-pulse">Editando</span>}
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-500">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide flex items-center gap-1
                            ${aoi.use_type === 'CROP' ? 'bg-orange-50 text-orange-600' : 'bg-green-50 text-green-600'}`}>
                            {aoi.use_type === 'PASTURE' ? 'Pastagem' : 'Lavoura'}
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
                                onDuplicate={() => alert("Duplicar em breve")}
                                onExport={() => alert("Exportar KML em breve")}
                            />
                            <button onClick={onClose} className="p-2 text-gray-400 hover:bg-gray-100 rounded-full sm:hidden">
                                ✕
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* 2. Tabs */}
            <div className="flex border-b border-gray-200 px-4 pt-2 gap-6 bg-white shrink-0">
                {(['OVERVIEW', 'INDICES', 'ALERTS'] as TabType[]).map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`pb-3 text-sm font-medium border-b-2 transition-colors relative ${activeTab === tab
                            ? 'border-green-600 text-green-700'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                    >
                        {tab === 'OVERVIEW' ? 'Visão Geral' : tab === 'INDICES' ? 'Índices' : `Alertas (${uniqueAlerts.length})`}
                    </button>
                ))}
            </div>

            {/* 3. Content */}
            <div className="flex-1 overflow-y-auto p-4 bg-gray-50/50">

                {/* ---------- VISÃO GERAL ---------- */}
                {activeTab === 'OVERVIEW' && (
                    <div className="space-y-6">
                        {/* KPI Cards */}
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

                        {/* Recent Alert Snippet */}
                        {uniqueAlerts.length > 0 && (
                            <div className="bg-orange-50 border border-orange-100 rounded-xl p-4">
                                <div className="flex justify-between items-center mb-2">
                                    <h4 className="text-orange-900 font-bold text-sm flex items-center gap-2">
                                        <AlertTriangle size={16} /> Atenção Necessária
                                    </h4>
                                    <button
                                        onClick={() => setActiveTab('ALERTS')}
                                        className="text-xs font-bold text-orange-700 hover:underline flex items-center"
                                    >
                                        Ver todos <ChevronRight size={12} />
                                    </button>
                                </div>
                                <p className="text-sm text-orange-800/80">
                                    Foram detectados {uniqueAlerts.length} alertas recentes neste talhão. Verifique a aba de alertas para detalhes.
                                </p>
                            </div>
                        )}

                        {/* Recent Index Snapshot */}
                        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="font-bold text-gray-700 flex items-center gap-2">
                                    <Activity size={16} className="text-blue-500" /> Vigor Recente
                                </h3>
                                <button className="text-xs text-blue-600 font-bold" onClick={() => setActiveTab('INDICES')}>Detalhes</button>
                            </div>
                            <div className="h-40">
                                <ChartComponent title="NDVI (30 Dias)" data={chartData.slice(-4)} color="#16a34a" />
                            </div>
                        </div>
                    </div>
                )}

                {/* ---------- ÍNDICES ---------- */}
                {activeTab === 'INDICES' && (
                    <div className="space-y-4">
                        {/* Segmented Control */}
                        <div className="bg-gray-200 p-1 rounded-lg flex overflow-x-auto">
                            {(['NDVI', 'NDWI', 'NDMI', 'SAVI', 'ANOMALY'] as IndexType[]).map(type => (
                                <button
                                    key={type}
                                    onClick={() => setSelectedIndex(type)}
                                    className={`flex-1 min-w-[60px] py-1.5 text-xs font-bold rounded-md transition-all shadow-sm ${selectedIndex === type
                                        ? 'bg-white text-gray-900 border border-gray-200/50'
                                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200/50'
                                        }`}
                                >
                                    {type}
                                </button>
                            ))}
                        </div>

                        <ChartComponent
                            title={getChartTitle()}
                            data={chartData}
                            color={getChartColor()}
                        />

                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 text-xs text-blue-800 leading-relaxed">
                            <strong>Dica:</strong> {getChartTitle()} é calculado a partir de imagens de satélite Sentinel-2. Nuvens podem causar falhas nos dados recentes.
                        </div>
                    </div>
                )}

                {/* ---------- ALERTAS ---------- */}
                {activeTab === 'ALERTS' && (
                    <div className="space-y-3">
                        {uniqueAlerts.length === 0 ? (
                            <div className="text-center py-10">
                                <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-3">
                                    <span className="text-2xl">🌿</span>
                                </div>
                                <h3 className="font-bold text-gray-800">Tudo limpo!</h3>
                                <p className="text-sm text-gray-500 mt-1">Nenhum alerta detectado nos últimos dias.</p>
                            </div>
                        ) : (
                            uniqueAlerts.map(signal => (
                                <div key={signal.id} className="bg-white border-l-4 border-yellow-400 rounded-r-lg shadow-sm p-3 flex flex-col gap-2">
                                    <div className="flex justify-between items-start">
                                        <h4 className="font-bold text-gray-800 text-sm">{signal.signal_type}</h4>
                                        <span className="text-[10px] uppercase font-bold text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                                            {new Date(signal.detected_at || signal.created_at || new Date()).toLocaleDateString()}
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-600 line-clamp-2">
                                        {signal.metadata?.summary || "Anomalia detectada na análise de satélite."}
                                    </p>
                                    <div className="flex justify-end pt-2 border-t border-gray-50">
                                        <button className="text-xs font-bold text-blue-600 hover:underline flex items-center gap-1">
                                            <MapPin size={10} /> Ver local no mapa
                                        </button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}

            </div>
        </div>
    )
}
