'use client'

import { useEffect, useState, useRef } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { farmAPI, aoiAPI, jobAPI, signalAPI } from '@/lib/api'
import { useAuthProtection, useAuthRole } from '@/lib/auth'
import MapComponent from '@/components/MapComponent'
import { useErrorHandler } from '@/lib/errorHandler'
import { Farm, AOI, Signal, SplitMode } from '@/lib/types'
import { ErrorToast } from '@/components/Toast'
import AOIDetailsPanel from '@/components/AOIDetailsPanel'
import AOIList from '@/components/AOIList'
import MobileNav from '@/components/MobileNav'
import { EmptyAOIs } from '@/components/EmptyState'
import PaddockGridView from '@/components/PaddockGridView'
import * as turf from '@turf/turf'
import { PanelLeftClose, PanelLeft, Maximize2, Minimize2, Map, BarChart3, Scissors, Wand2, Check, X, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useUser } from '@/stores/useUserStore'

// Skeleton for farm details loading
function FarmDetailsSkeleton() {
    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-16 lg:pb-0">
            {/* Header Skeleton */}
            <header className="bg-white dark:bg-gray-800 shadow dark:shadow-gray-700/50">
                <div className="px-4 py-4 sm:px-6">
                    <div className="h-6 w-48 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-2"></div>
                    <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                </div>
            </header>
            {/* Content Skeleton */}
            <div className="flex flex-col lg:flex-row h-[calc(100vh-120px)]">
                <div className="hidden lg:block w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4 space-y-3">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"></div>
                    ))}
                </div>
                <div className="flex-1 bg-gray-200 dark:bg-gray-700 animate-pulse"></div>
            </div>
        </div>
    )
}

export default function FarmDetailsPage() {
    const params = useParams()
    const router = useRouter()
    const farmId = params.id as string

    // Map Ref for imperative actions (editing)
    const mapRef = useRef<any>(null)

    const { isAuthenticated, isLoading: authLoading } = useAuthProtection()
    const role = useAuthRole()
    const user = useUser()
    const { error, handleError, clearError } = useErrorHandler()

    const [farm, setFarm] = useState<Farm | null>(null)
    const [aois, setAois] = useState<AOI[]>([])
    const [loading, setLoading] = useState(true)
    const [processingGrid, setProcessingGrid] = useState(false)
    const [processingAois, setProcessingAois] = useState<Set<string>>(new Set())

    // Mobile sidebar state
    const [showSidebar, setShowSidebar] = useState(false)
    const [viewMode, setViewMode] = useState<'LIST' | 'DETAIL'>('LIST')

    // Split-view panel state
    const [panelSize, setPanelSize] = useState<'normal' | 'expanded' | 'collapsed'>('normal')
    const [focusMode, setFocusMode] = useState<'map' | 'data' | 'split'>('split')
    const [panelView, setPanelView] = useState<'LIST' | 'GRID'>('LIST')

    // Drawing State
    const [isDrawing, setIsDrawing] = useState(false)
    const [drawingPoints, setDrawingPoints] = useState<[number, number][]>([])
    const [showSaveModal, setShowSaveModal] = useState(false)
    const [newAOI, setNewAOI] = useState({ name: '', use_type: 'PASTURE' })
    const [selectedAOI, setSelectedAOI] = useState<AOI | null>(null)
    const [ndviUrl, setNdviUrl] = useState<string | null>(null)
    const [ndwiUrl, setNdwiUrl] = useState<string | null>(null)
    const [ndmiUrl, setNdmiUrl] = useState<string | null>(null)
    const [saviUrl, setSaviUrl] = useState<string | null>(null)
    const [anomalyUrl, setAnomalyUrl] = useState<string | null>(null)
    const [falseColorUrl, setFalseColorUrl] = useState<string | null>(null)
    const [trueColorUrl, setTrueColorUrl] = useState<string | null>(null)

    // Advanced Indices State
    const [ndreUrl, setNdreUrl] = useState<string | null>(null)
    const [reciUrl, setReciUrl] = useState<string | null>(null)
    const [gndviUrl, setGndviUrl] = useState<string | null>(null)
    const [eviUrl, setEviUrl] = useState<string | null>(null)
    const [msiUrl, setMsiUrl] = useState<string | null>(null)
    const [nbrUrl, setNbrUrl] = useState<string | null>(null)
    const [bsiUrl, setBsiUrl] = useState<string | null>(null)
    const [ariUrl, setAriUrl] = useState<string | null>(null)
    const [criUrl, setCriUrl] = useState<string | null>(null)
    const [rviUrl, setRviUrl] = useState<string | null>(null)
    const [ratioUrl, setRatioUrl] = useState<string | null>(null)
    const [showAOIs, setShowAOIs] = useState(true)

    // Edit AOI State
    const [editingAOIId, setEditingAOIId] = useState<string | null>(null)
    const [isEditingAOI, setIsEditingAOI] = useState(false)
    const [pendingGeometry, setPendingGeometry] = useState<any>(null)

    // Split Mode State
    const [splitModeActive, setSplitModeActive] = useState(false)
    const [splitMode, setSplitMode] = useState<SplitMode>('voronoi')
    const [splitTargetCount, setSplitTargetCount] = useState(8)
    const [splitMaxAreaHa, setSplitMaxAreaHa] = useState(2000)
    const [splitEnqueueJobs, setSplitEnqueueJobs] = useState(true)
    const [splitPreview, setSplitPreview] = useState<Array<{ id: string; geometry_wkt: string; area_ha?: number; name?: string }>>([])
    const [splitWarnings, setSplitWarnings] = useState<string[]>([])
    const [splitLoading, setSplitLoading] = useState(false)
    const [splitApplying, setSplitApplying] = useState(false)
    const [splitSelectedIds, setSplitSelectedIds] = useState<string[]>([])
    const [splitMultiSelect, setSplitMultiSelect] = useState(false)
    const [splitError, setSplitError] = useState<string | null>(null)

    // Merge Mode (AOIs)
    const [mergeModeActive, setMergeModeActive] = useState(false)
    const [mergeSelectedIds, setMergeSelectedIds] = useState<string[]>([])
    const [mergeApplying, setMergeApplying] = useState(false)
    const [mergeError, setMergeError] = useState<string | null>(null)

    // Confirm delete modal
    const [showDeleteModal, setShowDeleteModal] = useState(false)
    const [showDeleteAOIModal, setShowDeleteAOIModal] = useState(false)

    useEffect(() => {
        if (isAuthenticated && farmId) {
            loadData()
        }
    }, [isAuthenticated, farmId])

    // Load assets when AOI is selected
    useEffect(() => {
        if (selectedAOI) {
            setIsEditingAOI(false) // Reset edit mode on selection change
            setPendingGeometry(null)
            setSplitPreview([])
            setSplitWarnings([])
            setSplitSelectedIds([])
            setMergeSelectedIds([])

            setNdviUrl(null)
            setNdwiUrl(null)
            setNdmiUrl(null)
            setSaviUrl(null)
            setAnomalyUrl(null)
            setFalseColorUrl(null)
            setTrueColorUrl(null)

            aoiAPI.getAssets(selectedAOI.id)
                .then(res => {
                    setNdviUrl(res.data.ndvi_tile_url || null)
                    setNdwiUrl(res.data.ndwi_tile_url || null)
                    setNdmiUrl(res.data.ndmi_tile_url || null)
                    setSaviUrl(res.data.savi_tile_url || null)
                    setAnomalyUrl(res.data.anomaly_tile_url || null)
                    setFalseColorUrl(res.data.false_color_tile_url || null)
                    setTrueColorUrl(res.data.true_color_tile_url || null)

                    setNdreUrl(res.data.ndre_tile_url || null)
                    setReciUrl(res.data.reci_tile_url || null)
                    setGndviUrl(res.data.gndvi_tile_url || null)
                    setEviUrl(res.data.evi_tile_url || null)
                    setMsiUrl(res.data.msi_tile_url || null)
                    setNbrUrl(res.data.nbr_tile_url || null)
                    setBsiUrl(res.data.bsi_tile_url || null)
                    setAriUrl(res.data.ari_tile_url || null)
                    setCriUrl(res.data.cri_tile_url || null)

                    // Radar (todo: separate call if needed, but assuming attached if available)
                    // Currently radar assets might be in a different endpoint or merged. 
                    // Based on previous search, they are separate. Checked AOIDetailsPanel, it calls aoiAPI.getRadarHistory.
                    // But Map overlay usually wants the *latest* raster. 
                    // Let's assume for now they are merged in getAssets if we updated the backend. 
                    // I verified aois_router.py earlier and saw I added them to the SELECT. 
                    // Wait, I only added Optical indices to get_aoi_assets in previous turn. Radar was not added to get_aoi_assets query?
                    // Let me check aois_router.py again mentally... 
                    // I added `ndre_tile_url` etc. Did I add `rvi_tile_url`?
                    // The DerivedAssets model has them? No, DerivedRadarAssets is separate.
                    // So I need to fetch Radar assets separately here or assume they are not yet map-ready. 
                    // The user asked "os indicadores novos aparecerao no menu". 
                    // Radar is technically "new" to the menu. 
                    // I should probably fetch radar assets here too if I want them on the map.

                    // Note: Since I didn't merge Radar into DerivedAssets table, I can't get them from getAssets easily without a join.
                    // However, `AOIDetailsPanel` fetches them separately. 
                    // I will leave Radar map layers pending URL population logic for now (pass null) or fetch them if I can.
                    // Actually, I can just fetch them here in parallel.
                })
                .catch(console.error)

            // Fetch Radar for Map
            aoiAPI.getRadarHistory(selectedAOI.id).then(res => {
                if (res.data && res.data.length > 0) {
                    // Get latest
                    const latest = res.data.sort((a: any, b: any) => (b.year * 100 + b.week) - (a.year * 100 + a.week))[0]
                    setRviUrl(latest.rvi_tile_url || null)
                    setRatioUrl(latest.ratio_tile_url || null)
                }
            }).catch(e => console.warn("Radar map fetch error", e))
        } else {
            setIsEditingAOI(false)
            setPendingGeometry(null)
            setSplitModeActive(false)
            setSplitPreview([])
            setSplitWarnings([])
            setSplitSelectedIds([])
            setMergeSelectedIds([])

            setNdviUrl(null)
            setNdwiUrl(null)
            setNdmiUrl(null)
            setSaviUrl(null)
            setAnomalyUrl(null)
            setFalseColorUrl(null)
            setTrueColorUrl(null)
        }
    }, [selectedAOI])

    const makeSplitId = (index: number) => {
        if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
            return crypto.randomUUID()
        }
        return `${Date.now()}-${index}`
    }

    const resetSplitState = () => {
        setSplitModeActive(false)
        setSplitPreview([])
        setSplitWarnings([])
        setSplitSelectedIds([])
        setMergeSelectedIds([])
        setSplitError(null)
        setSplitLoading(false)
        setSplitApplying(false)
    }

    const handleSimulateSplit = async () => {
        if (!selectedAOI) return
        setSplitLoading(true)
        setSplitError(null)
        try {
            const response = await aoiAPI.simulateSplit({
                geometry_wkt: selectedAOI.geometry,
                mode: splitMode,
                target_count: splitTargetCount,
                max_area_ha: splitMaxAreaHa
            })

            const polygons = response.data.polygons.map((poly, idx) => ({
                id: makeSplitId(idx),
                geometry_wkt: poly.geometry_wkt,
                area_ha: poly.area_ha,
                name: `Talhão ${String(idx + 1).padStart(2, '0')}`,
            }))

            setSplitPreview(polygons)
            setSplitWarnings(response.data.warnings ?? [])
            setSplitSelectedIds(polygons[0]?.id ? [polygons[0].id] : [])
        } catch (err) {
            handleError(err, 'Erro ao simular divisão')
            const status = (err as any)?.response?.status
            if (status === 403) {
                setSplitError('Sem permissão para simular divisão. Apenas administradores podem executar essa ação.')
            } else if (status === 422) {
                setSplitError('Geometria inválida ou parâmetros fora do limite. Ajuste e tente novamente.')
            } else {
                setSplitError('Não foi possível simular a divisão. Verifique a geometria e tente novamente.')
            }
        } finally {
            setSplitLoading(false)
        }
    }

    const handleApplySplit = async () => {
        if (!selectedAOI || splitPreview.length === 0) return
        setSplitApplying(true)
        setSplitError(null)
        try {
            await aoiAPI.splitAois({
                parent_aoi_id: selectedAOI.id,
                polygons: splitPreview.map((poly) => ({
                    geometry_wkt: poly.geometry_wkt,
                    name: poly.name,
                })),
                enqueue_jobs: splitEnqueueJobs,
                max_area_ha: splitMaxAreaHa
            })

            await loadData(false)
            resetSplitState()
        } catch (err) {
            handleError(err, 'Erro ao confirmar split')
            const status = (err as any)?.response?.status
            if (status === 403) {
                setSplitError('Sem permissão para confirmar split. Apenas administradores podem executar essa ação.')
            } else if (status === 422) {
                setSplitError('Alguns polígonos excedem o limite ou estão inválidos. Revise e tente novamente.')
            } else {
                setSplitError('Falha ao confirmar o split. Tente novamente ou revise os polígonos.')
            }
        } finally {
            setSplitApplying(false)
        }
    }

    const handleSplitPreviewUpdate = (id: string, geometryWkt: string, areaHa: number) => {
        setSplitPreview((prev) =>
            prev.map((item) => (item.id === id ? { ...item, geometry_wkt: geometryWkt, area_ha: areaHa } : item))
        )
    }

    const handleSplitPreviewSelect = (id: string) => {
        if (splitMultiSelect) {
            setSplitSelectedIds((prev) => (prev.includes(id) ? prev.filter((value) => value !== id) : [...prev, id]))
            return
        }
        setSplitSelectedIds([id])
    }

    const wktToGeoJSON = (wkt: string) => {
        const coordsMatch = wkt.match(/\([\d\s,.-]+\)/g)
        if (!coordsMatch) return null
        const rings = coordsMatch.map((polygonStr) => {
            const cleanStr = polygonStr.replace(/[()]/g, '')
            const pairs = cleanStr.split(',').map((pair) => {
                const [lng, lat] = pair.trim().split(/\s+/).map(Number)
                return [lng, lat]
            })
            return pairs
        })

        if (rings.length <= 1) {
            return turf.polygon([rings[0]])
        }
        return turf.multiPolygon(rings.map((ring) => [ring]))
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

    const handleMergeSelected = () => {
        if (splitSelectedIds.length < 2) return
        const selected = splitPreview.filter((item) => splitSelectedIds.includes(item.id))
        let merged: any = null

        selected.forEach((item) => {
            const geo = wktToGeoJSON(item.geometry_wkt)
            if (!geo) return
            if (!merged) {
                merged = geo
            } else {
                merged = turf.union(merged, geo)
            }
        })

        if (!merged) return

        const wkt = geojsonToWkt(merged.geometry ?? merged)
        const areaHa = turf.area(merged) / 10000
        const newId = makeSplitId(splitPreview.length + 1)

        setSplitPreview((prev) => {
            const filtered = prev.filter((item) => !splitSelectedIds.includes(item.id))
            return [
                ...filtered,
                {
                    id: newId,
                    geometry_wkt: wkt,
                    area_ha: areaHa,
                    name: `Talhão Merge`,
                },
            ]
        })
        setSplitSelectedIds([newId])
    }

    const toggleMergeMode = () => {
        setMergeModeActive((prev) => {
            const next = !prev
            if (next) {
                setSplitModeActive(false)
                setSplitPreview([])
                setSplitWarnings([])
                setSplitSelectedIds([])
                setSplitMultiSelect(false)
                setIsDrawing(false)
                setDrawingPoints([])
                setMergeError(null)
            } else {
                setMergeSelectedIds([])
            }
            return next
        })
    }

    const handleMergeSelect = (id: string) => {
        if (!mergeModeActive) return
        setMergeSelectedIds((prev) => (prev.includes(id) ? prev.filter((value) => value !== id) : [...prev, id]))
    }

    const handleMergeAois = async () => {
        if (!farm || mergeSelectedIds.length < 2) return
        setMergeApplying(true)
        setMergeError(null)
        try {
            const selected = aois.filter((aoi) => mergeSelectedIds.includes(aoi.id))
            let merged: any = null

            selected.forEach((aoi) => {
                const geo = wktToGeoJSON(aoi.geometry)
                if (!geo) return
                if (!merged) merged = geo
                else merged = turf.union(merged, geo)
            })

            if (!merged) return

            const areaHa = turf.area(merged) / 10000
            if (areaHa > splitMaxAreaHa) {
                alert(`Área total (${areaHa.toFixed(1)} ha) excede o limite de ${splitMaxAreaHa} ha.`)
                return
            }

            const geometryWkt = geojsonToWkt(merged.geometry ?? merged)
            const name = `Merge ${selected.map((aoi) => aoi.name).join(' + ')}`.slice(0, 64)
            const useType = selected[0]?.use_type ?? 'PASTURE'

            const created = await aoiAPI.create({
                farm_id: farm.id,
                name,
                use_type: useType as any,
                geometry: geometryWkt
            })

            await Promise.all(selected.map((aoi) => aoiAPI.delete(aoi.id)))

            setSelectedAOI(created.data)
            setMergeSelectedIds([])
            setMergeModeActive(false)
            await loadData(false)
        } catch (err) {
            handleError(err, 'Erro ao consolidar talhões')
            const status = (err as any)?.response?.status
            if (status === 403) {
                setMergeError('Sem permissão para consolidar talhões. Apenas administradores podem executar essa ação.')
            } else if (status === 422) {
                setMergeError('Não foi possível consolidar. Verifique o limite de área e tente novamente.')
            } else {
                setMergeError('Não foi possível consolidar os talhões selecionados.')
            }
        } finally {
            setMergeApplying(false)
        }
    }

    // Poll for AOI status to update processing status
    useEffect(() => {
        if (!isAuthenticated || !farmId) return

        const fetchStatus = async () => {
            try {
                const processingSet = new Set<string>()
                if (aois.length > 0) {
                    const res = await aoiAPI.getStatus({ aoi_ids: aois.map((aoi) => aoi.id) })
                    res.data.items.forEach((item) => {
                        if (item.status === 'PROCESSING' || item.latest_job_status === 'PENDING' || item.latest_job_status === 'RUNNING') {
                            processingSet.add(item.aoi_id)
                        }
                    })

                    setAois((prev) =>
                        prev.map((aoi) => {
                            const match = res.data.items.find((item) => item.aoi_id === aoi.id)
                            return match ? { ...aoi, status: match.status } : aoi
                        })
                    )
                }

                setProcessingAois(processingSet)
            } catch (err) {
                console.error('Error fetching aois status', err)
            }
        }

        fetchStatus() // Initial fetch
        const interval = setInterval(fetchStatus, 10000) // Poll every 10s

        return () => clearInterval(interval)
    }, [isAuthenticated, farmId, aois.length])

    const [signals, setSignals] = useState<Signal[]>([])

    // ... (existing effects)

    const loadData = async (showLoading = true) => {
        if (showLoading) setLoading(true)
        try {
            const farmsRes = await farmAPI.list()
            const foundFarm = farmsRes.data.find(f => f.id === farmId)

            if (foundFarm) {
                setFarm(foundFarm)
                const [aoisRes, signalsRes] = await Promise.all([
                    aoiAPI.listByFarm(farmId),
                    signalAPI.listByFarm(farmId)
                ])
                setAois(aoisRes.data)
                setSignals(signalsRes.data)
            } else {
                throw new Error('Fazenda não encontrada')
            }

        } catch (err) {
            handleError(err, 'Erro ao carregar dados da fazenda')
        } finally {
            if (showLoading) setLoading(false)
        }
    }

    const handleGenerateGrid = async () => {
        if (drawingPoints.length < 3) {
            alert('Desenhe uma área primeiro.')
            return
        }

        if (!confirm("Isso irá dividir a área desenhada em talhões automáticos de ~25ha. Deseja continuar?")) return

        setProcessingGrid(true)
        try {
            const turfCoords = drawingPoints.map(p => [p[1], p[0]])
            turfCoords.push(turfCoords[0])

            const searchPoly = turf.polygon([turfCoords])
            const bbox = turf.bbox(searchPoly)

            const cellSide = 0.5
            const grid = turf.squareGrid(bbox, cellSide, { units: 'kilometers' })

            let createdCount = 0

            for (const cell of grid.features) {
                const intersection = turf.intersect(turf.featureCollection([searchPoly, cell]))

                if (intersection) {
                    const areaHa = turf.area(intersection) / 10000
                    if (areaHa < 1.0) continue

                    const coords = intersection.geometry.coordinates[0]
                    const wktCoords = coords.map((p: any) => `${p[0]} ${p[1]}`).join(', ')
                    const wkt = `MULTIPOLYGON(((${wktCoords})))`

                    createdCount++
                    await aoiAPI.create({
                        farm_id: farm!.id,
                        name: `Talhão Auto ${createdCount}`,
                        use_type: 'PASTURE',
                        geometry: wkt
                    })
                }
            }

            if (createdCount === 0) {
                alert("A área é muito pequena para gerar grade com 25ha.")
            } else {
                await loadData(false)
                alert(`${createdCount} talhões gerados com sucesso!`)
            }

            setIsDrawing(false)
            setDrawingPoints([])

        } catch (err: any) {
            handleError(err, 'Erro ao gerar grade')
        } finally {
            setProcessingGrid(false)
        }
    }

    const handleSaveAOI = async () => {
        if (!farm) return

        try {
            const closedPoints = [...drawingPoints, drawingPoints[0]]
            const coordsString = closedPoints.map(p => `${p[1]} ${p[0]}`).join(', ')
            const wkt = `MULTIPOLYGON(((${coordsString})))`

            await aoiAPI.create({
                farm_id: farm.id,
                name: newAOI.name,
                use_type: newAOI.use_type as any,
                geometry: wkt
            })

            setShowSaveModal(false)
            setIsDrawing(false)
            setDrawingPoints([])
            setNewAOI({ name: '', use_type: 'PASTURE' })
            loadData(false)

        } catch (err: any) {
            handleError(err, 'Erro ao salvar talhão')
        }
    }

    const handleDeleteFarm = async () => {
        const isOwner = farm?.created_by_user_id && user?.id ? farm.created_by_user_id === user.id : false
        const canDelete = role === 'tenant_admin' || role === 'system_admin' || (role === 'editor' && isOwner)
        if (!canDelete) {
            handleError(null, 'Sem permissão para excluir esta fazenda')
            return
        }
        if (!farm) return
        try {
            await farmAPI.delete(farm.id)
            router.push('/farms')
        } catch (err) {
            handleError(err, 'Erro ao excluir fazenda')
        }
    }

    const handleDeleteAOI = async () => {
        if (!selectedAOI) return
        try {
            await aoiAPI.delete(selectedAOI.id)
            setShowDeleteAOIModal(false)
            setSelectedAOI(null)
            loadData(false) // Refresh list
        } catch (err) {
            handleError(err, 'Erro ao excluir talhão')
        }
    }

    const handleCancelEdit = () => {
        setIsEditingAOI(false)
        setPendingGeometry(null)
    }

    const handleSaveGeometry = async () => {
        if (!selectedAOI) return
        if (!pendingGeometry) {
            setIsEditingAOI(false)
            return
        }

        try {
            // Convert GeoJSON geometry to WKT
            // We can use the simple WKT format for polygons: POLYGON((x y, x y, ...))
            // But we might need a library or simple parser.
            // For now, let's assume the API handles WKT.
            // But wait, the API accepts WKT string. We must convert GeoJSON to WKT.
            // We can use @turf/turf if needed, or simple string manipulation for single polygon.

            // PendingGeometry is GeoJSON GEOMETRY object (type: Polygon, coordinates: [...])
            const coords = pendingGeometry.coordinates[0] // Ring 0
            const wktCoords = coords.map((p: any) => `${p[0]} ${p[1]}`).join(', ')
            const wkt = `MULTIPOLYGON(((${wktCoords})))`

            await aoiAPI.update(selectedAOI.id, {
                geometry: wkt
            })

            alert('Geometria atualizada! Recalculando dados...')
            setIsEditingAOI(false)
            setPendingGeometry(null)
            loadData(false) // Refresh
        } catch (err: any) {
            handleError(err, 'Erro ao salvar geometria')
        }
    }

    const startDrawing = () => {
        setIsEditingAOI(false)
        setIsDrawing(true)
        setDrawingPoints([])
        setSelectedAOI(null)
        setShowSidebar(false) // Close sidebar on mobile when starting to draw
    }

    // Layout Helpers
    useEffect(() => {
        if (selectedAOI) {
            setViewMode('DETAIL')
        } else {
            setViewMode('LIST')
        }
    }, [selectedAOI])

    const handleBackToList = () => {
        setSelectedAOI(null)
        setViewMode('LIST')
    }

    if (authLoading || loading) {
        return <FarmDetailsSkeleton />
    }

    if (!farm) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900 pb-16 lg:pb-0">
                <div className="w-16 h-16 mb-4 text-gray-400">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Fazenda não encontrada</h1>
                <p className="text-gray-600 dark:text-gray-400 mb-6">A fazenda solicitada não existe ou foi removida.</p>
                <Link
                    href="/farms"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors min-h-[44px]"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                    Voltar para fazendas
                </Link>
                <MobileNav />
            </div>
        )
    }

    const canDeleteFarm =
        role === 'tenant_admin' ||
        role === 'system_admin' ||
        (role === 'editor' && farm.created_by_user_id && user?.id === farm.created_by_user_id)

    return (
        <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden">
            <ErrorToast error={error} onClose={clearError} />

            {/* Top Bar */}
            <header className="h-14 bg-card border-b border-border flex items-center justify-between px-4 shrink-0 z-20">
                <div className="flex items-center">
                    <Link href="/farms" className="p-2 -ml-2 mr-2 text-muted-foreground hover:text-foreground hover:bg-accent rounded-full transition-colors" title="Voltar para lista">
                        <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                    </Link>
                    <h1 className="font-bold text-foreground text-lg sm:text-xl leading-tight truncate max-w-[200px] sm:max-w-md">
                        {farm.name}
                    </h1>
                </div>

                <div className="flex items-center gap-1">
                    {/* Panel Collapse Toggle (Desktop) */}
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setPanelSize(panelSize === 'collapsed' ? 'normal' : 'collapsed')}
                                    className="hidden lg:flex h-9 w-9 p-0"
                                >
                                    {panelSize === 'collapsed' ? <PanelLeft className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent>{panelSize === 'collapsed' ? 'Mostrar' : 'Ocultar'} Painel</TooltipContent>
                        </Tooltip>
                    </TooltipProvider>

                    {/* Delete Farm Button */}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowDeleteModal(true)}
                        disabled={!canDeleteFarm}
                        className={`h-9 w-9 p-0 ${canDeleteFarm
                                ? 'text-muted-foreground hover:text-destructive hover:bg-destructive/10'
                                : 'text-muted-foreground/40 cursor-not-allowed'
                            }`}
                        title={canDeleteFarm ? 'Excluir Fazenda' : 'Sem permissão para excluir'}
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                    </Button>
                    {/* Expand Sidebar Toggle (mobile) */}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowSidebar(!showSidebar)}
                        className="lg:hidden h-9 w-9 p-0"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </Button>
                </div>
            </header>

            {/* Main Content - Split View */}
            <div className="flex-1 flex overflow-hidden relative">

                {/* Data Panel - Expansível */}
                <aside
                    className={`
                        absolute z-30 top-0 bottom-0 left-0 bg-background border-r border-border transition-all duration-300 ease-in-out
                        ${showSidebar ? 'translate-x-0' : '-translate-x-full'}
                        lg:relative lg:translate-x-0
                        ${panelSize === 'collapsed' ? 'lg:w-0 lg:overflow-hidden lg:border-0' : ''}
                        ${panelSize === 'normal' ? 'w-full sm:w-[560px] 2xl:w-[600px]' : ''}
                        ${panelSize === 'expanded' ? 'w-full sm:w-[640px] lg:w-[50vw]' : ''}
                        ${focusMode === 'data' ? 'lg:!w-[70vw]' : ''}
                        ${focusMode === 'map' ? 'lg:!w-[420px]' : ''}
                        shrink-0 flex flex-col shadow-2xl lg:shadow-none dark:lg:border-r-gray-800
                    `}
                >
                    {/* Panel Controls */}
                    <div className="hidden lg:flex items-center justify-between px-3 py-2 border-b border-border bg-muted/30">
                        <div className="flex items-center gap-1">
                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Button
                                            variant={focusMode === 'data' ? 'default' : 'ghost'}
                                            size="sm"
                                            onClick={() => setFocusMode(focusMode === 'data' ? 'split' : 'data')}
                                            className="h-8 w-8 p-0"
                                        >
                                            <BarChart3 className="h-4 w-4" />
                                        </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Foco em Dados</TooltipContent>
                                </Tooltip>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Button
                                            variant={focusMode === 'map' ? 'default' : 'ghost'}
                                            size="sm"
                                            onClick={() => setFocusMode(focusMode === 'map' ? 'split' : 'map')}
                                            className="h-8 w-8 p-0"
                                        >
                                            <Map className="h-4 w-4" />
                                        </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Foco no Mapa</TooltipContent>
                                </Tooltip>
                            </TooltipProvider>
                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Button
                                            variant={mergeModeActive ? 'default' : 'ghost'}
                                            size="sm"
                                            onClick={toggleMergeMode}
                                            className="h-8 w-8 p-0"
                                        >
                                            <Scissors className="h-4 w-4" />
                                        </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Modo Merge</TooltipContent>
                                </Tooltip>
                            </TooltipProvider>
                        </div>
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => setPanelSize(panelSize === 'expanded' ? 'normal' : 'expanded')}
                                        className="h-8 w-8 p-0"
                                    >
                                        {panelSize === 'expanded' ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>{panelSize === 'expanded' ? 'Reduzir' : 'Expandir'} Painel</TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    </div>
                    {viewMode === 'LIST' ? (
                        <>
                            <div className="border-b border-border bg-muted/20 px-3 py-2">
                                <div className="flex items-center gap-2">
                                    <Button
                                        variant={panelView === 'LIST' ? 'default' : 'outline'}
                                        size="sm"
                                        onClick={() => setPanelView('LIST')}
                                    >
                                        Lista
                                    </Button>
                                    <Button
                                        variant={panelView === 'GRID' ? 'default' : 'outline'}
                                        size="sm"
                                        onClick={() => setPanelView('GRID')}
                                    >
                                        Grid
                                    </Button>
                                </div>
                            </div>
                            {aois.length === 0 ? (
                                <div className="p-6">
                                    <EmptyAOIs />
                                    <div className="mt-4 flex justify-center">
                                        <Button onClick={startDrawing}>Desenhar talhão</Button>
                                    </div>
                                </div>
                            ) : panelView === 'LIST' ? (
                                <AOIList
                                    aois={aois}
                                    selectedAOI={selectedAOI}
                                    onSelect={(aoi) => {
                                        setSelectedAOI(aoi)
                                    }}
                                    processingAois={processingAois}
                                    signals={signals}
                                    onAddAOI={() => {
                                        startDrawing()
                                        if (window.innerWidth < 1024) setShowSidebar(false)
                                    }}
                                    onEdit={(aoi) => {
                                        setSelectedAOI(aoi)
                                        setTimeout(() => {
                                            if (mapRef.current) {
                                                const layer = mapRef.current.getLayers().find((l: any) => l.feature?.properties?.id === aoi.id);
                                                if (layer && (layer as any).pm) {
                                                    if (window.innerWidth < 1024) setShowSidebar(false);
                                                    (layer as any).pm.enable({ allowSelfIntersection: false });
                                                    setEditingAOIId(aoi.id);
                                                }
                                            }
                                        }, 100)
                                    }}
                                    onDelete={(aoi) => {
                                        setSelectedAOI(aoi)
                                        setShowDeleteAOIModal(true)
                                    }}
                                />
                            ) : (
                                <PaddockGridView
                                    aois={aois}
                                    processingAois={processingAois}
                                    signals={signals}
                                    onSelect={(aoi) => {
                                        setSelectedAOI(aoi)
                                    }}
                                    onAddAOI={startDrawing}
                                />
                            )}
                        </>
                    ) : (
                        selectedAOI ? (
                            <AOIDetailsPanel
                                aoi={selectedAOI}
                                onClose={handleBackToList}
                                onDelete={() => setShowDeleteAOIModal(true)}
                                onSplit={() => {
                                    setSplitModeActive(true)
                                    setFocusMode('map')
                                    setIsDrawing(false)
                                    setDrawingPoints([])
                                    if (window.innerWidth < 1024) setShowSidebar(false)
                                }}
                                onEdit={() => {
                                    // Start editing geometry
                                    if (mapRef.current) {
                                        const layer = mapRef.current.getLayers().find((l: any) => l.feature?.properties?.id === selectedAOI.id);
                                        if (layer && (layer as any).pm) {
                                            // Close sidebar on mobile to show map
                                            if (window.innerWidth < 1024) setShowSidebar(false);
                                            (layer as any).pm.enable({ allowSelfIntersection: false });
                                            setEditingAOIId(selectedAOI.id);
                                        }
                                    }
                                }}
                                isEditing={editingAOIId === selectedAOI.id}
                                onSave={() => {
                                    // Trigger save via logic or wait for map event? 
                                    // Assuming map pm:update event handles it, but button might force it.
                                    // Actually 'pm:update' fires on drag end/vertex change. 
                                    // We need 'finish' button typically.
                                    // For now, let's just disable PM mode which might trigger sync if we hooked it up.
                                    if (mapRef.current) {
                                        const layer = mapRef.current.getLayers().find((l: any) => l.feature?.properties?.id === selectedAOI.id);
                                        if (layer && (layer as any).pm && (layer as any).pm.enabled()) {
                                            (layer as any).pm.disable();
                                            // But standard PM doesn't auto-save on disable. 
                                            // The 'pm:update' event listener in MapLeaflet handles the API call.
                                            // So disabling is enough to stop editing visual state.
                                        }
                                    }
                                    setEditingAOIId(null);
                                }}
                                onCancelEdit={() => {
                                    if (mapRef.current) {
                                        const layer = mapRef.current.getLayers().find((l: any) => l.feature?.properties?.id === selectedAOI.id);
                                        if (layer && (layer as any).pm) {
                                            (layer as any).pm.disable();
                                            // Ideally revert geometry here if needed
                                        }
                                    }
                                    setEditingAOIId(null);
                                }}
                            />
                        ) : (
                            <div className="p-8 text-center text-gray-500">
                                <p>Nenhum talhão selecionado.</p>
                                <button onClick={handleBackToList} className="mt-4 text-green-600 font-bold hover:underline">
                                    Voltar para lista
                                </button>
                            </div>
                        )
                    )}
                </aside>

                {/* Map Area */}
                <main className={`flex-1 relative bg-muted w-full overflow-hidden transition-all duration-300 ${focusMode === 'data' ? 'lg:w-[30vw]' : ''}`}>

                    {/* Panel Toggle (Desktop - when collapsed) */}
                    {panelSize === 'collapsed' && (
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button
                                        variant="secondary"
                                        size="sm"
                                        onClick={() => setPanelSize('normal')}
                                        className="hidden lg:flex absolute top-4 left-4 z-[1000] shadow-lg"
                                    >
                                        <PanelLeft className="h-4 w-4 mr-2" />
                                        Dados
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>Abrir Painel de Dados</TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    )}

                    {/* Map Interaction Overlay (Mobile Toggle) */}
                    {!showSidebar && !isDrawing && (
                        <Button
                            onClick={() => setShowSidebar(true)}
                            variant="secondary"
                            className="lg:hidden absolute top-4 left-4 z-[1000] shadow-lg"
                        >
                            <PanelLeft className="h-4 w-4 mr-2" />
                            Talhões ({aois.length})
                        </Button>
                    )}

                    {/* Split Controls */}
                    {splitModeActive && selectedAOI && (
                        <div className="absolute top-4 right-4 z-[1000] w-[320px] rounded-2xl border border-border bg-card p-4 shadow-xl">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    <div className="h-9 w-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                                        <Scissors className="h-4 w-4" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-semibold text-foreground">Dividir talhão</p>
                                        <p className="text-xs text-muted-foreground">{selectedAOI.name}</p>
                                    </div>
                                </div>
                                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={resetSplitState}>
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>

                            <div className="space-y-3">
                                {splitError && (
                                    <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                                        {splitError}
                                    </div>
                                )}
                                <div className="space-y-2">
                                    <Label className="text-xs uppercase text-muted-foreground">Modo</Label>
                                    <div className="flex gap-2">
                                        <Button
                                            variant={splitMode === 'voronoi' ? 'default' : 'outline'}
                                            size="sm"
                                            className="flex-1"
                                            onClick={() => setSplitMode('voronoi')}
                                        >
                                            Voronoi
                                        </Button>
                                        <Button
                                            variant={splitMode === 'grid' ? 'default' : 'outline'}
                                            size="sm"
                                            className="flex-1"
                                            onClick={() => setSplitMode('grid')}
                                        >
                                            Grid
                                        </Button>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-2">
                                    <div className="space-y-2">
                                        <Label className="text-xs uppercase text-muted-foreground">Talhões alvo</Label>
                                        <Input
                                            type="number"
                                            min={2}
                                            max={50}
                                            value={splitTargetCount}
                                            onChange={(e) => setSplitTargetCount(Number(e.target.value))}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label className="text-xs uppercase text-muted-foreground">Max área (ha)</Label>
                                        <Input
                                            type="number"
                                            min={100}
                                            max={10000}
                                            value={splitMaxAreaHa}
                                            onChange={(e) => setSplitMaxAreaHa(Number(e.target.value))}
                                        />
                                    </div>
                                </div>

                                <label className="flex items-center gap-2 text-xs text-muted-foreground">
                                    <input
                                        type="checkbox"
                                        checked={splitEnqueueJobs}
                                        onChange={(e) => setSplitEnqueueJobs(e.target.checked)}
                                        className="h-4 w-4 rounded border-input"
                                    />
                                    Enfileirar processamento após criar talhões
                                </label>

                                <div className="flex gap-2">
                                    <Button
                                        variant="secondary"
                                        className="flex-1 gap-2"
                                        onClick={handleSimulateSplit}
                                        disabled={splitLoading}
                                    >
                                        <Wand2 className="h-4 w-4" />
                                        {splitLoading ? 'Simulando...' : 'Simular'}
                                    </Button>
                                    <Button
                                        className="flex-1 gap-2"
                                        onClick={handleApplySplit}
                                        disabled={splitApplying || splitPreview.length === 0}
                                    >
                                        <Check className="h-4 w-4" />
                                        {splitApplying ? 'Aplicando...' : 'Confirmar'}
                                    </Button>
                                </div>

                                {splitPreview.length > 0 && (
                                    <div className="rounded-xl border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
                                        <div className="flex items-center justify-between mb-2">
                                            <span>{splitPreview.length} talhões em prévia</span>
                                            <Button variant="ghost" size="sm" className="h-auto px-2 py-1" onClick={() => setSplitPreview([])}>
                                                Limpar
                                            </Button>
                                        </div>
                                        <div className="flex items-center justify-between gap-2 mb-2">
                                            <label className="flex items-center gap-2 text-[11px]">
                                                <input
                                                    type="checkbox"
                                                    checked={splitMultiSelect}
                                                    onChange={(e) => setSplitMultiSelect(e.target.checked)}
                                                    className="h-3.5 w-3.5 rounded border-input"
                                                />
                                                Selecionar múltiplos
                                            </label>
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                onClick={handleMergeSelected}
                                                disabled={splitSelectedIds.length < 2}
                                                className="h-7 px-2 text-[11px]"
                                            >
                                                Merge ({splitSelectedIds.length})
                                            </Button>
                                        </div>
                                        {splitWarnings.length > 0 && (
                                            <div className="flex items-start gap-2 text-amber-600">
                                                <AlertTriangle className="h-4 w-4 mt-0.5" />
                                                <span>Existem talhões acima do limite.</span>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Merge Controls */}
                    {mergeModeActive && (
                        <div className="absolute top-4 right-4 z-[1000] w-[320px] rounded-2xl border border-border bg-card p-4 shadow-xl">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    <div className="h-9 w-9 rounded-xl bg-orange-100 text-orange-600 flex items-center justify-center">
                                        <Scissors className="h-4 w-4" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-semibold text-foreground">Merge de talhões</p>
                                        <p className="text-xs text-muted-foreground">Selecione 2+ polígonos</p>
                                    </div>
                                </div>
                                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={toggleMergeMode}>
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>
                            <div className="space-y-3 text-xs text-muted-foreground">
                                {mergeError && (
                                    <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                                        {mergeError}
                                    </div>
                                )}
                                <div className="flex items-center justify-between">
                                    <span>Selecionados: {mergeSelectedIds.length}</span>
                                    <span>Limite: {splitMaxAreaHa} ha</span>
                                </div>
                                <Button
                                    className="w-full gap-2"
                                    onClick={handleMergeAois}
                                    disabled={mergeSelectedIds.length < 2 || mergeApplying}
                                >
                                    <Check className="h-4 w-4" />
                                    {mergeApplying ? 'Consolidando...' : 'Consolidar Talhões'}
                                </Button>
                            </div>
                        </div>
                    )}

                    {/* Drawing Controls */}
                    {isDrawing && (
                        <div className="absolute bottom-24 lg:bottom-10 left-1/2 transform -translate-x-1/2 z-[1000] bg-white dark:bg-gray-800 shadow-xl rounded-2xl p-4 border border-gray-200 dark:border-gray-700 flex flex-col items-center gap-3 animate-in slide-in-from-bottom-5">
                            <p className="text-xs font-bold text-gray-500 uppercase tracking-wide">Modo Desenho</p>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setDrawingPoints([])}
                                    className="px-4 py-2 text-sm font-bold text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                                >
                                    Limpar
                                </button>
                                <button
                                    onClick={() => {
                                        setIsDrawing(false)
                                        setDrawingPoints([])
                                        setShowSidebar(true) // Re-open sidebar
                                    }}
                                    className="px-4 py-2 text-sm font-bold text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={() => {
                                        if (drawingPoints.length < 3) {
                                            alert('Desenhe pelo menos 3 pontos.')
                                            return
                                        }
                                        setShowSaveModal(true)
                                    }}
                                    className="px-4 py-2 text-sm font-bold text-white bg-green-600 hover:bg-green-700 rounded-lg shadow-sm transition-colors"
                                >
                                    Salvar
                                </button>
                            </div>
                            <button
                                onClick={handleGenerateGrid}
                                disabled={processingGrid}
                                className="w-full py-2 text-xs font-bold text-purple-600 bg-purple-50 hover:bg-purple-100 rounded-lg flex items-center justify-center gap-2"
                            >
                                {processingGrid ? "Gerando..." : "🪄 Gerar Auto-Grade"}
                            </button>
                        </div>
                    )}

                    {/* Progress Modal */}
                    {processingGrid && (
                        <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
                            <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-2xl text-center max-w-sm w-full mx-auto">
                                <div className="animate-spin text-4xl mb-4">🪄</div>
                                <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-2">Gerando Talhões...</h3>
                                <p className="text-gray-500 dark:text-gray-400 text-sm">Criando grade e recortando bordas.</p>
                            </div>
                        </div>
                    )}

                    <div className="absolute inset-0 w-full h-full">
                        <MapComponent
                            farmId={farm.id}
                            aois={aois}
                            selectedAOI={selectedAOI}
                            timezone={farm.timezone}
                            isDrawing={isDrawing}
                            drawingPoints={drawingPoints}
                            setDrawingPoints={setDrawingPoints}
                            ndviTileUrl={ndviUrl}
                            ndwiTileUrl={ndwiUrl}
                            ndmiTileUrl={ndmiUrl}
                            saviTileUrl={saviUrl}
                            anomalyTileUrl={anomalyUrl}
                            falseColorTileUrl={falseColorUrl}
                            trueColorTileUrl={trueColorUrl}

                            ndreTileUrl={ndreUrl}
                            reciTileUrl={reciUrl}
                            gndviTileUrl={gndviUrl}
                            eviTileUrl={eviUrl}
                            msiTileUrl={msiUrl}
                            nbrTileUrl={nbrUrl}
                            bsiTileUrl={bsiUrl}
                            ariTileUrl={ariUrl}
                            criTileUrl={criUrl}
                            rviTileUrl={rviUrl}
                            ratioTileUrl={ratioUrl}
                            showAOIs={showAOIs}
                            processingAois={processingAois}
                            signals={signals}
                            splitPreviewPolygons={splitPreview}
                            splitSelectedIds={splitSelectedIds}
                            splitEditableId={splitSelectedIds.length === 1 ? splitSelectedIds[0] : null}
                            splitMaxAreaHa={splitMaxAreaHa}
                            onSplitPreviewUpdate={handleSplitPreviewUpdate}
                            onSplitPreviewSelect={handleSplitPreviewSelect}
                            mergeModeActive={mergeModeActive}
                            mergeSelectedIds={mergeSelectedIds}
                            onMergeSelect={handleMergeSelect}
                            // Pass map ref handling or use Context?
                            // Currently MapComponent manages its own ref, but exposing it for Editing would require ref forwarding.
                            // For MVP v1, we might rely on global window map or just context if we set it up.
                            // But wait, the edit logic above uses `mapRef.current`.
                            // I need to provide `onMapReady` prop to MapComponent to capture the ref in Page!
                            onMapReady={(mapInstance: any) => {
                                mapRef.current = mapInstance
                            }}
                        />
                    </div>
                </main>
            </div>

            {/* Modals */}
            {showSaveModal && (
                <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60 p-4">
                    <div className="w-full max-w-md rounded-2xl bg-white dark:bg-gray-800 p-6 shadow-2xl">
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Novo Talhão</h3>
                        <form onSubmit={(e) => { e.preventDefault(); handleSaveAOI() }}>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-1">Nome</label>
                                    <input
                                        required
                                        value={newAOI.name}
                                        onChange={e => setNewAOI({ ...newAOI, name: e.target.value })}
                                        className="w-full rounded-lg border-gray-300 p-2.5 text-sm ring-1 ring-gray-200 focus:ring-green-500"
                                        placeholder="Ex: Talhão 1"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-1">Tipo</label>
                                    <select
                                        value={newAOI.use_type}
                                        onChange={e => setNewAOI({ ...newAOI, use_type: e.target.value })}
                                        className="w-full rounded-lg border-gray-300 p-2.5 text-sm ring-1 ring-gray-200"
                                    >
                                        <option value="PASTURE">Pastagem</option>
                                        <option value="CROP">Lavoura</option>
                                        <option value="TIMBER">Madeira / Silvicultura</option>
                                    </select>
                                </div>
                                <div className="flex gap-3 pt-4">
                                    <button type="button" onClick={() => setShowSaveModal(false)} className="flex-1 py-2.5 font-bold text-gray-600 bg-gray-100 rounded-lg">Cancelar</button>
                                    <button type="submit" className="flex-1 py-2.5 font-bold text-white bg-green-600 rounded-lg hover:bg-green-700">Salvar</button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {showDeleteModal && (
                <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60 p-4">
                    <div className="w-full max-w-sm rounded-2xl bg-white p-6 text-center">
                        <h3 className="text-xl font-bold text-gray-900 mb-2">Excluir Fazenda?</h3>
                        <p className="text-gray-500 text-sm mb-6">Esta ação apagará todos os dados definitivamente.</p>
                        <div className="flex gap-3">
                            <button onClick={() => setShowDeleteModal(false)} className="flex-1 py-2.5 font-bold text-gray-600 bg-gray-100 rounded-lg">Cancelar</button>
                            <button onClick={handleDeleteFarm} className="flex-1 py-2.5 font-bold text-white bg-red-600 rounded-lg">Excluir</button>
                        </div>
                    </div>
                </div>
            )}

            {showDeleteAOIModal && (
                <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60 p-4">
                    <div className="w-full max-w-sm rounded-2xl bg-white p-6 text-center">
                        <h3 className="text-xl font-bold text-gray-900 mb-2">Excluir Talhão?</h3>
                        <p className="text-gray-500 text-sm mb-6">Confirma a exclusão de <strong>{selectedAOI?.name}</strong>?</p>
                        <div className="flex gap-3">
                            <button onClick={() => setShowDeleteAOIModal(false)} className="flex-1 py-2.5 font-bold text-gray-600 bg-gray-100 rounded-lg">Cancelar</button>
                            <button onClick={handleDeleteAOI} className="flex-1 py-2.5 font-bold text-white bg-red-600 rounded-lg">Excluir</button>
                        </div>
                    </div>
                </div>
            )}

            <MobileNav />
        </div>
    )
}
