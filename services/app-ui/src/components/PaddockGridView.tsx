'use client'

import { useMemo, useState } from 'react'
import type { AOI, Signal, FieldCalibrationCreateRequest } from '@/lib/types'
import { analyticsAPI } from '@/lib/api'
import { useErrorHandler } from '@/lib/errorHandler'
import { AlertTriangle, Loader2, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

type StatusFilter = 'ALL' | 'ALERTS' | 'PROCESSING'

interface PaddockGridViewProps {
    aois: AOI[]
    signals?: Signal[]
    processingAois?: Set<string>
    onSelect: (aoi: AOI) => void
    onAddAOI?: () => void
}

const statusColor = {
    alert: 'bg-red-100 text-red-700',
    warning: 'bg-amber-100 text-amber-700',
    processing: 'bg-blue-100 text-blue-700',
    normal: 'bg-emerald-100 text-emerald-700',
}

export default function PaddockGridView({
    aois,
    signals = [],
    processingAois = new Set(),
    onSelect,
    onAddAOI
}: PaddockGridViewProps) {
    const { handleError } = useErrorHandler()
    const [filter, setFilter] = useState<StatusFilter>('ALL')
    const [metricType, setMetricType] = useState<'biomass' | 'yield'>('yield')
    const [unit, setUnit] = useState<'kg_ha' | 'sc_ha'>('kg_ha')
    const [date, setDate] = useState<string>(() => new Date().toISOString().slice(0, 10))
    const [values, setValues] = useState<Record<string, string>>({})
    const [saving, setSaving] = useState(false)
    const [predictions, setPredictions] = useState<Record<string, number>>({})
    const [loadingPredictions, setLoadingPredictions] = useState(false)

    const getStatus = (aoi: AOI) => {
        if (processingAois.has(aoi.id)) return 'processing'
        const aoiSignals = signals.filter((signal) => signal.aoi_id === aoi.id)
        if (aoiSignals.some((signal) => signal.severity === 'HIGH')) return 'alert'
        if (aoiSignals.some((signal) => signal.severity === 'MEDIUM')) return 'warning'
        return 'normal'
    }

    const getBadges = (aoiId: string) => {
        const types = new Set<string>()
        signals
            .filter((signal) => signal.aoi_id === aoiId)
            .forEach((signal) => {
                if (signal.signal_type === 'CROP_STRESS') types.add('water_stress')
                else if (signal.signal_type === 'PEST_OUTBREAK') types.add('disease_risk')
                else if (signal.signal_type === 'PASTURE_FORAGE_RISK') types.add('yield_risk')
            })
        return Array.from(types)
    }

    const filtered = useMemo(() => {
        return aois.filter((aoi) => {
            const status = getStatus(aoi)
            if (filter === 'ALERTS') return status === 'alert' || status === 'warning'
            if (filter === 'PROCESSING') return status === 'processing'
            return true
        })
    }, [aois, filter, processingAois, signals])

    const handleBatchSave = async () => {
        const entries = Object.entries(values)
            .filter(([_, value]) => value && Number(value) > 0)
            .map(([aoiId, value]) => ({
                aoi_id: aoiId,
                date,
                metric_type: metricType,
                value: Number(value),
                unit,
            } as FieldCalibrationCreateRequest))

        if (entries.length === 0) return

        setSaving(true)
        try {
            await Promise.all(entries.map((payload) => analyticsAPI.createFieldCalibration(payload)))
            setValues({})
        } catch (err) {
            handleError(err, 'Erro ao salvar calibração em lote')
        } finally {
            setSaving(false)
        }
    }

    const handleLoadPredictions = async () => {
        setLoadingPredictions(true)
        try {
            const results = await Promise.all(
                filtered.map((aoi) =>
                    analyticsAPI.getPrediction(aoi.id, metricType).then((res) => [aoi.id, res.data.p50] as const)
                )
            )
            const next: Record<string, number> = {}
            results.forEach(([id, value]) => {
                next[id] = value
            })
            setPredictions(next)
        } catch (err) {
            handleError(err, 'Erro ao carregar estimativas')
        } finally {
            setLoadingPredictions(false)
        }
    }

    if (aois.length === 0) {
        return (
            <div className="flex h-full items-center justify-center p-10">
                <div className="max-w-sm text-center space-y-3">
                    <div className="mx-auto h-12 w-12 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center">
                        <AlertTriangle className="h-5 w-5" />
                    </div>
                    <p className="text-lg font-semibold text-foreground">Sem talhões</p>
                    <p className="text-sm text-muted-foreground">
                        Crie o primeiro talhão para liberar o modo grid e calibrar em lote.
                    </p>
                    {onAddAOI && (
                        <Button onClick={onAddAOI} className="mt-2">
                            Criar talhão
                        </Button>
                    )}
                </div>
            </div>
        )
    }

    return (
        <div className="flex h-full flex-col bg-background">
            <div className="border-b border-border bg-muted/40 px-4 py-3 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                        <Button
                            variant={filter === 'ALL' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setFilter('ALL')}
                        >
                            Todos
                        </Button>
                        <Button
                            variant={filter === 'ALERTS' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setFilter('ALERTS')}
                        >
                            Alertas
                        </Button>
                        <Button
                            variant={filter === 'PROCESSING' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setFilter('PROCESSING')}
                        >
                            Processando
                        </Button>
                    </div>
                    <Button variant="secondary" size="sm" onClick={handleLoadPredictions} disabled={loadingPredictions}>
                        {loadingPredictions ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                        Carregar estimativas
                    </Button>
                </div>

                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="space-y-1">
                        <Label className="text-xs uppercase text-muted-foreground">Data da medição</Label>
                        <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
                    </div>
                    <div className="space-y-1">
                        <Label className="text-xs uppercase text-muted-foreground">Métrica</Label>
                        <Select value={metricType} onValueChange={(value) => setMetricType(value as 'biomass' | 'yield')}>
                            <SelectTrigger>
                                <SelectValue placeholder="Métrica" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="yield">Produtividade</SelectItem>
                                <SelectItem value="biomass">Biomassa</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="space-y-1">
                        <Label className="text-xs uppercase text-muted-foreground">Unidade</Label>
                        <Select value={unit} onValueChange={(value) => setUnit(value as 'kg_ha' | 'sc_ha')}>
                            <SelectTrigger>
                                <SelectValue placeholder="Unidade" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="kg_ha">kg/ha</SelectItem>
                                <SelectItem value="sc_ha">sc/ha</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="flex items-end">
                        <Button className="w-full" onClick={handleBatchSave} disabled={saving}>
                            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <CheckCircle2 className="mr-2 h-4 w-4" />}
                            Salvar batch
                        </Button>
                    </div>
                </div>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Talhão</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>NDVI</TableHead>
                            <TableHead>Est. {metricType === 'yield' ? 'Yield' : 'Biomassa'}</TableHead>
                            <TableHead>Valor real</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {filtered.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={5} className="text-center text-sm text-muted-foreground">
                                    Nenhum talhão para este filtro.
                                </TableCell>
                            </TableRow>
                        ) : (
                            filtered.map((aoi) => {
                                const status = getStatus(aoi)
                                const alertCount = signals.filter((signal) => signal.aoi_id === aoi.id).length
                                return (
                                    <TableRow
                                        key={aoi.id}
                                        className="cursor-pointer hover:bg-muted/50"
                                        onClick={() => onSelect(aoi)}
                                    >
                                        <TableCell className="font-medium">{aoi.name}</TableCell>
                                        <TableCell>
                                            <Badge className={statusColor[status]}>
                                                {status === 'processing' ? 'Processando' : status === 'alert' ? 'Alerta' : status === 'warning' ? 'Atenção' : 'Ok'}
                                            </Badge>
                                            {alertCount > 0 && (
                                                <span className="ml-2 inline-flex items-center gap-1 text-[10px] text-amber-600">
                                                    <AlertTriangle className="h-3 w-3" /> {alertCount}
                                                </span>
                                            )}
                                            {getBadges(aoi.id).length > 0 && (
                                                <div className="mt-2 flex flex-wrap gap-1">
                                                    {getBadges(aoi.id).map((badge) => (
                                                        <span
                                                            key={badge}
                                                            title={badge === 'water_stress' ? 'Water Stress' : badge === 'disease_risk' ? 'Disease Risk' : 'Yield Risk'}
                                                            className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full uppercase
                                                                ${badge === 'water_stress' ? 'bg-blue-100 text-blue-700'
                                                                    : badge === 'disease_risk' ? 'bg-red-100 text-red-700'
                                                                        : 'bg-orange-100 text-orange-700'}
                                                            `}
                                                        >
                                                            {badge === 'water_stress' ? 'Water' : badge === 'disease_risk' ? 'Disease' : 'Yield'}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </TableCell>
                                        <TableCell>{aoi.ndvi_mean ? aoi.ndvi_mean.toFixed(2) : '--'}</TableCell>
                                        <TableCell>
                                            {predictions[aoi.id] !== undefined
                                                ? `${(unit === 'sc_ha' ? predictions[aoi.id] / 60 : predictions[aoi.id]).toFixed(1)} ${unit === 'sc_ha' ? 'sc/ha' : 'kg/ha'}`
                                                : '--'}
                                        </TableCell>
                                        <TableCell onClick={(e) => e.stopPropagation()}>
                                            <Input
                                                type="number"
                                                min={0}
                                                value={values[aoi.id] ?? ''}
                                                onChange={(e) => setValues((prev) => ({ ...prev, [aoi.id]: e.target.value }))}
                                                placeholder={unit === 'sc_ha' ? 'sc/ha' : 'kg/ha'}
                                            />
                                        </TableCell>
                                    </TableRow>
                                )
                            })
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    )
}
