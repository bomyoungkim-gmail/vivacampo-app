'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import { AdminAuthGate } from '@/components/AdminAuthGate'
import { Button, DataTable, Input, type Column } from '@/components/ui'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface MissingWeeksItem {
    tenant_id: string
    aoi_id: string
    farm_name?: string
    aoi_name?: string
    missing_weeks: [number, number][]
    missing_count: number
}

interface MissingWeeksResponse {
    weeks: number
    items: MissingWeeksItem[]
}

function MissingWeeksContent({ token }: { token: string }) {
    const [loading, setLoading] = useState(true)
    const [items, setItems] = useState<MissingWeeksItem[]>([])
    const [weeks, setWeeks] = useState(8)
    const [limit, setLimit] = useState(50)
    const [reprocessLimit, setReprocessLimit] = useState(10)
    const [maxRuns, setMaxRuns] = useState(3)
    const [reprocessLoading, setReprocessLoading] = useState(false)

    useEffect(() => {
        loadMissingWeeks(token)
    }, [limit, token, weeks])

    const loadMissingWeeks = async (authToken: string) => {
        try {
            setLoading(true)
            const response = await axios.get<MissingWeeksResponse>(`${API_BASE}/v1/admin/ops/missing-weeks`, {
                headers: { Authorization: `Bearer ${authToken}` },
                params: { weeks, limit }
            })
            setItems(response.data.items || [])
        } catch (err) {
            console.error('Failed to load missing weeks:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleReprocess = async (authToken: string) => {
        try {
            setReprocessLoading(true)
            const response = await axios.post(
                `${API_BASE}/v1/admin/ops/reprocess-missing-weeks`,
                {},
                {
                    headers: { Authorization: `Bearer ${authToken}` },
                    params: { weeks, limit: reprocessLimit, max_runs_per_aoi: maxRuns }
                }
            )
            alert(`Backfill enfileirado: ${response.data.queued}`)
            loadMissingWeeks(authToken)
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Erro ao reprocessar semanas faltantes')
        } finally {
            setReprocessLoading(false)
        }
    }

    const renderWeeks = (weeksList: [number, number][]) => {
        const preview = weeksList.slice(0, 6).map(([y, w]) => `${y}-W${String(w).padStart(2, '0')}`)
        const suffix = weeksList.length > 6 ? ` +${weeksList.length - 6}` : ''
        return preview.join(', ') + suffix
    }

    // DataTable columns configuration
    const columns: Column<MissingWeeksItem>[] = [
        {
            key: 'farm_name',
            header: 'Fazenda',
            accessor: (row) => row.farm_name || '-',
            sortable: true,
            mobileLabel: 'Fazenda',
        },
        {
            key: 'aoi_name',
            header: 'Talhão (AOI)',
            accessor: (row) => row.aoi_name || row.aoi_id,
            sortable: true,
            mobileLabel: 'Talhão',
        },
        {
            key: 'missing_count',
            header: 'Missing',
            sortable: true,
            mobileLabel: 'Missing',
        },
        {
            key: 'missing_weeks',
            header: 'Semanas',
            accessor: (row) => (
                <span className="text-xs font-mono">
                    {renderWeeks(row.missing_weeks)}
                </span>
            ),
            mobileLabel: 'Semanas',
        },
    ]

    // Custom mobile card renderer
    const renderMobileCard = (item: MissingWeeksItem) => (
        <div className="rounded-lg bg-card p-4 shadow border border-border space-y-3">
            <div className="flex justify-between items-start">
                <div>
                    <span className="font-semibold text-foreground">{item.farm_name || '-'}</span>
                    <div className="text-sm text-muted-foreground mt-1">
                        {item.aoi_name || item.aoi_id}
                    </div>
                </div>
                <div className="rounded-full bg-destructive/10 px-3 py-1">
                    <span className="text-sm font-semibold text-destructive">{item.missing_count}</span>
                </div>
            </div>
            <div className="text-xs font-mono text-muted-foreground">
                {renderWeeks(item.missing_weeks)}
            </div>
        </div>
    )

    return (
        <div className="mx-auto max-w-7xl space-y-6">
            <div>
                <p className="text-sm text-muted-foreground">Identifique semanas faltantes e reprocese aois com dados incompletos.</p>
                <h2 className="text-2xl font-semibold text-foreground">Buracos de Dados</h2>
            </div>

            <div className="space-y-4">
                {/* Query Controls */}
                <div className="flex flex-wrap items-end gap-2 rounded-lg bg-card p-4 border border-border">
                    <Input
                        type="number"
                        label="Semanas"
                        min={1}
                        max={104}
                        value={weeks}
                        onChange={(e) => setWeeks(Number(e.target.value))}
                        className="w-24"
                    />
                    <Input
                        type="number"
                        label="Limite"
                        min={1}
                        max={200}
                        value={limit}
                        onChange={(e) => setLimit(Number(e.target.value))}
                        className="w-24"
                    />
                    <Button
                        onClick={() => loadMissingWeeks(token)}
                        variant="outline"
                        size="md"
                    >
                        Atualizar
                    </Button>
                </div>

                {/* Reprocess Controls */}
                <div className="rounded-lg bg-card p-4 border border-border">
                    <div className="flex flex-wrap items-end gap-2">
                        <Input
                            type="number"
                            label="Limite Reproc."
                            min={1}
                            max={200}
                            value={reprocessLimit}
                            onChange={(e) => setReprocessLimit(Number(e.target.value))}
                            className="w-32"
                        />
                        <Input
                            type="number"
                            label="Runs"
                            min={1}
                            max={6}
                            value={maxRuns}
                            onChange={(e) => setMaxRuns(Number(e.target.value))}
                            className="w-24"
                        />
                        <Button
                            onClick={() => handleReprocess(token)}
                            loading={reprocessLoading}
                            variant="primary"
                            size="md"
                        >
                            Reprocessar Buracos
                        </Button>
                    </div>
                </div>
            </div>

            {/* Missing Weeks DataTable */}
            <DataTable
                data={items}
                columns={columns}
                rowKey={(row) => row.aoi_id}
                loading={loading}
                emptyMessage="Nenhum buraco encontrado nas últimas semanas"
                mobileCardRender={renderMobileCard}
            />
        </div>
    )
}

export default function MissingWeeksPage() {
    return (
        <AdminAuthGate>
            {(token) => <MissingWeeksContent token={token} />}
        </AdminAuthGate>
    )
}
