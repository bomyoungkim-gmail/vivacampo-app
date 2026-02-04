import { useState, useEffect, useMemo } from 'react'
import type { AOI, Signal, DerivedAssets, RadarAssets, WeatherData } from '@/lib/types'
import { signalAPI, aoiAPI } from '@/lib/api'
import ChartComponent from './ChartComponent'
import WeatherChart from './WeatherChart'
import AOIActionsMenu from './AOIActionsMenu'
import { useErrorHandler } from '@/lib/errorHandler'
import { MapPin, Calendar, Activity, AlertTriangle, ChevronRight, CloudRain, Radio, Leaf, Droplets, Sparkles, Mountain, BarChart3 } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { NitrogenAlert } from './NitrogenAlert'
import { AnalysisTab } from './AnalysisTab'

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
type TabType = 'OVERVIEW' | 'ANALYSIS' | 'HEALTH' | 'WATER' | 'NUTRITION' | 'SOIL' | 'RADAR' | 'WEATHER' | 'ALERTS'

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
        <div className="h-full flex flex-col bg-background overflow-hidden rounded-t-xl sm:rounded-none">
            {/* Header */}
            <div className="p-4 border-b border-border flex justify-between items-start bg-card z-10">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <h2 className="font-bold text-xl text-foreground leading-tight">{aoi.name}</h2>
                        {isEditing && <Badge variant="outline" className="text-[10px] bg-orange-100 text-orange-600 border-orange-200 animate-pulse">Editando</Badge>}
                    </div>
                    <div className="flex items-center gap-3 text-sm text-muted-foreground">
                        <Badge variant="secondary" className={`text-[10px] font-bold uppercase
                            ${aoi.use_type === 'CROP' ? 'bg-orange-100 text-orange-700 hover:bg-orange-100'
                                : aoi.use_type === 'TIMBER' ? 'bg-amber-100 text-amber-800 hover:bg-amber-100'
                                    : 'bg-green-100 text-green-700 hover:bg-green-100'}`}>
                            {aoi.use_type === 'PASTURE' ? 'Pastagem' : aoi.use_type === 'TIMBER' ? 'Madeira' : 'Lavoura'}
                        </Badge>
                        <span className="flex items-center gap-1">
                            <MapPin size={12} /> {aoi.area_ha ? `${aoi.area_ha.toFixed(1)} ha` : '--'}
                        </span>
                    </div>
                </div>
                <div className="flex items-center gap-1">
                    {isEditing ? (
                        <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={onCancelEdit}>Cancelar</Button>
                            <Button size="sm" onClick={onSave}>Salvar</Button>
                        </div>
                    ) : (
                        <>
                            <AOIActionsMenu
                                onEditGeometry={onEdit}
                                onDelete={onDelete}
                                onExport={() => alert("Exportar KML em breve")}
                            />
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={onClose}
                                className="h-9 w-9 p-0"
                                title="Voltar para lista"
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                                </svg>
                            </Button>
                        </>
                    )}
                </div>
            </div>

            {/* Tabs - Reorganized with icons */}
            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabType)} className="flex-1 flex flex-col overflow-hidden">
                <div className="bg-card border-b border-border px-2 shrink-0">
                    <TabsList className="h-12 w-full justify-start bg-transparent gap-1 overflow-x-auto">
                        <TabsTrigger value="OVERVIEW" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary gap-1.5">
                            <Activity size={14} /> Geral
                        </TabsTrigger>
                        <TabsTrigger value="ANALYSIS" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary gap-1.5">
                            <BarChart3 size={14} /> Análise
                        </TabsTrigger>
                        <Separator orientation="vertical" className="h-5 mx-1" />
                        <TabsTrigger value="HEALTH" className="data-[state=active]:bg-green-100 data-[state=active]:text-green-700 gap-1.5">
                            <Leaf size={14} /> Saúde
                        </TabsTrigger>
                        <TabsTrigger value="WATER" className="data-[state=active]:bg-blue-100 data-[state=active]:text-blue-700 gap-1.5">
                            <Droplets size={14} /> Água
                        </TabsTrigger>
                        <TabsTrigger value="NUTRITION" className="data-[state=active]:bg-purple-100 data-[state=active]:text-purple-700 gap-1.5">
                            <Sparkles size={14} /> Nutrição
                        </TabsTrigger>
                        <TabsTrigger value="SOIL" className="data-[state=active]:bg-orange-100 data-[state=active]:text-orange-700 gap-1.5">
                            <Mountain size={14} /> Solo
                        </TabsTrigger>
                        <Separator orientation="vertical" className="h-5 mx-1" />
                        <TabsTrigger value="RADAR" className="data-[state=active]:bg-accent gap-1.5">
                            <Radio size={14} /> Radar
                        </TabsTrigger>
                        <TabsTrigger value="WEATHER" className="data-[state=active]:bg-accent gap-1.5">
                            <CloudRain size={14} /> Clima
                        </TabsTrigger>
                        <TabsTrigger value="ALERTS" className="data-[state=active]:bg-red-100 data-[state=active]:text-red-700 gap-1.5">
                            <AlertTriangle size={14} /> Alertas
                            {uniqueAlerts.length > 0 && <Badge variant="destructive" className="h-5 px-1.5 text-[10px]">{uniqueAlerts.length}</Badge>}
                        </TabsTrigger>
                    </TabsList>
                </div>

                {/* Content - Scrollable */}
                <ScrollArea className="flex-1 bg-muted/30">

                    <div className="p-4 space-y-6">

                    {/* ---------- VISÃO GERAL ---------- */}
                    <TabsContent value="OVERVIEW" className="mt-0 space-y-6">
                        <div className="grid grid-cols-2 gap-3">
                            <Card>
                                <CardContent className="p-4">
                                    <p className="text-xs text-muted-foreground font-medium uppercase mb-1">Status</p>
                                    <div className="flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                                        <p className="font-bold text-foreground">Monitorado</p>
                                    </div>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardContent className="p-4">
                                    <p className="text-xs text-muted-foreground font-medium uppercase mb-1">Última Imagem</p>
                                    <div className="flex items-center gap-2">
                                        <Calendar size={14} className="text-muted-foreground" />
                                        <p className="font-bold text-foreground">Há 5 dias</p>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                        <NitrogenAlert aoiId={aoi.id} />
                        {uniqueAlerts.length > 0 && (
                            <Card className="border-orange-200 bg-orange-50 dark:bg-orange-950/20">
                                <CardContent className="p-4">
                                    <div className="flex justify-between items-center mb-2">
                                        <h4 className="text-orange-900 dark:text-orange-200 font-bold text-sm flex items-center gap-2"><AlertTriangle size={16} /> Atenção Necessária</h4>
                                        <Button variant="ghost" size="sm" onClick={() => setActiveTab('ALERTS')} className="text-orange-700 dark:text-orange-300 h-auto py-1 px-2">
                                            Ver todos <ChevronRight size={12} />
                                        </Button>
                                    </div>
                                    <p className="text-sm text-orange-800/80 dark:text-orange-200/80">Foram detectados {uniqueAlerts.length} alertas recentes.</p>
                                </CardContent>
                            </Card>
                        )}
                        <Card>
                            <CardHeader className="pb-2">
                                <div className="flex justify-between items-center">
                                    <CardTitle className="text-base flex items-center gap-2"><Activity size={16} className="text-primary" /> Vigor Recente</CardTitle>
                                    <Button variant="link" size="sm" className="h-auto p-0" onClick={() => setActiveTab('HEALTH')}>Detalhes</Button>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="h-56">
                                    <ChartComponent title="NDVI (30 Dias)" data={chartData.slice(-4)} color="hsl(var(--chart-1))" />
                                </div>
                            </CardContent>
                        </Card>
                        {/* Weather Snippet */}
                        {weatherHistory.length > 0 && (
                            <Card>
                                <CardHeader className="pb-2">
                                    <div className="flex justify-between items-center">
                                        <CardTitle className="text-base flex items-center gap-2"><CloudRain size={16} className="text-blue-500" /> Clima Recente</CardTitle>
                                        <Button variant="link" size="sm" className="h-auto p-0" onClick={() => setActiveTab('WEATHER')}>Detalhes</Button>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid grid-cols-2 gap-4 text-center">
                                        <div className="bg-muted rounded-lg p-3">
                                            <p className="text-xs text-muted-foreground">Chuva (7d)</p>
                                            <p className="font-bold text-blue-600 text-xl">
                                                {weatherHistory.slice(0, 7).reduce((a, b) => a + b.precip_sum, 0).toFixed(1)} mm
                                            </p>
                                        </div>
                                        <div className="bg-muted rounded-lg p-3">
                                            <p className="text-xs text-muted-foreground">Temp. Max (Ontem)</p>
                                            <p className="font-bold text-red-500 text-xl">
                                                {weatherHistory[weatherHistory.length - 1]?.temp_max?.toFixed(1) || '--'}°C
                                            </p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </TabsContent>

                    {/* ---------- ANÁLISE ---------- */}
                    <TabsContent value="ANALYSIS" className="mt-0 space-y-6">
                        <AnalysisTab aoiId={aoi.id} />
                    </TabsContent>

                    {/* ---------- SAÚDE (HEALTH) ---------- */}
                    <TabsContent value="HEALTH" className="mt-0 space-y-4">
                        <Card>
                            <CardContent className="p-3">
                                <div className="flex flex-wrap gap-2">
                                    {(['NDVI', 'NDRE', 'RECI', 'GNDVI', 'EVI', 'ANOMALY'] as IndexType[]).map(type => (
                                        <Button key={type} variant={selectedIndex === type ? 'default' : 'outline'} size="sm" onClick={() => setSelectedIndex(type)} className={`text-xs ${selectedIndex === type ? 'bg-green-600 hover:bg-green-700' : ''}`}>{type}</Button>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="h-72">
                                    <ChartComponent title={currentChartProps.title} data={chartData} color={currentChartProps.color} />
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* ---------- ÁGUA (WATER) ---------- */}
                    <TabsContent value="WATER" className="mt-0 space-y-4">
                        <Card>
                            <CardContent className="p-3">
                                <div className="flex flex-wrap gap-2">
                                    {(['NDMI', 'NDWI', 'MSI'] as IndexType[]).map(type => (
                                        <Button key={type} variant={selectedIndex === type ? 'default' : 'outline'} size="sm" onClick={() => setSelectedIndex(type)} className={`text-xs ${selectedIndex === type ? 'bg-blue-600 hover:bg-blue-700' : ''}`}>{type}</Button>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="h-72">
                                    <ChartComponent title={currentChartProps.title} data={chartData} color={currentChartProps.color} />
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* ---------- NUTRIÇÃO (NUTRITION) ---------- */}
                    <TabsContent value="NUTRITION" className="mt-0 space-y-4">
                        <Card>
                            <CardContent className="p-3">
                                <div className="flex flex-wrap gap-2">
                                    {(['RECI', 'ARI', 'CRI'] as IndexType[]).map(type => (
                                        <Button key={type} variant={selectedIndex === type ? 'default' : 'outline'} size="sm" onClick={() => setSelectedIndex(type)} className={`text-xs ${selectedIndex === type ? 'bg-purple-600 hover:bg-purple-700' : ''}`}>{type}</Button>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="h-72">
                                    <ChartComponent title={currentChartProps.title} data={chartData} color={currentChartProps.color} />
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* ---------- SOLO (SOIL) ---------- */}
                    <TabsContent value="SOIL" className="mt-0 space-y-4">
                        <Card>
                            <CardContent className="p-3">
                                <div className="flex flex-wrap gap-2">
                                    {(['SAVI', 'NBR', 'BSI'] as IndexType[]).map(type => (
                                        <Button key={type} variant={selectedIndex === type ? 'default' : 'outline'} size="sm" onClick={() => setSelectedIndex(type)} className={`text-xs ${selectedIndex === type ? 'bg-orange-600 hover:bg-orange-700' : ''}`}>{type}</Button>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="h-72">
                                    <ChartComponent title={currentChartProps.title} data={chartData} color={currentChartProps.color} />
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* ---------- RADAR ---------- */}
                    <TabsContent value="RADAR" className="mt-0 space-y-4">
                        <Card>
                            <CardContent className="p-3">
                                <div className="flex flex-wrap gap-2">
                                    {(['RVI', 'RATIO'] as RadarIndexType[]).map(type => (
                                        <Button key={type} variant={selectedRadarIndex === type ? 'default' : 'outline'} size="sm" onClick={() => setSelectedRadarIndex(type)} className="text-xs">{type}</Button>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <div className="h-72">
                                    <ChartComponent
                                        title={currentRadarProps.title}
                                        data={radarChartData}
                                        color={currentRadarProps.color}
                                        domain={currentRadarProps.domain}
                                    />
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="border-purple-200 bg-purple-50 dark:bg-purple-950/20">
                            <CardContent className="p-4 text-sm text-purple-800 dark:text-purple-200">
                                <strong>Radar (Sentinel-1):</strong> O radar penetra nuvens. Use RVI para biomassa e Razão VH/VV para estrutura da vegetação, mesmo em dias nublados.
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* ---------- WEATHER ---------- */}
                    <TabsContent value="WEATHER" className="mt-0 space-y-4">
                        <Card>
                            <CardContent className="p-4">
                                <div className="h-80">
                                    <WeatherChart data={weatherHistory} />
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950/20">
                            <CardContent className="p-4 text-sm text-blue-800 dark:text-blue-200">
                                <strong>Fonte:</strong> Dados meteorológicos históricos baseados em reanálise (ERA5) e estações próximas via Open-Meteo.
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* ---------- ALERTAS ---------- */}
                    <TabsContent value="ALERTS" className="mt-0 space-y-3">
                        {uniqueAlerts.length === 0 ? (
                            <Card>
                                <CardContent className="text-center py-10">
                                    <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-3">
                                        <Leaf className="w-8 h-8 text-green-600" />
                                    </div>
                                    <h3 className="font-bold text-foreground">Tudo limpo!</h3>
                                    <p className="text-sm text-muted-foreground mt-1">Nenhum alerta recente.</p>
                                </CardContent>
                            </Card>
                        ) : (
                            uniqueAlerts.map(signal => (
                                <Card key={signal.id} className="border-l-4 border-l-yellow-400">
                                    <CardContent className="p-3">
                                        <div className="flex justify-between items-start mb-1">
                                            <h4 className="font-bold text-foreground text-sm">{signal.signal_type}</h4>
                                            <Badge variant="secondary" className="text-[10px]">
                                                {new Date(signal.detected_at || signal.created_at || new Date()).toLocaleDateString()}
                                            </Badge>
                                        </div>
                                        <p className="text-sm text-muted-foreground line-clamp-2">{signal.metadata?.summary || "Anomalia detectada."}</p>
                                    </CardContent>
                                </Card>
                            ))
                        )}
                    </TabsContent>

                    </div>
                </ScrollArea>
            </Tabs>
        </div>
    )
}
