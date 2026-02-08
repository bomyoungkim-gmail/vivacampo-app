'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import { AdminAuthGate } from '@/components/AdminAuthGate'
import { Button, DataTable, Badge, Input, type Column } from '@/components/ui'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Job {
    id: string
    job_type: string
    status: 'PENDING' | 'RUNNING' | 'DONE' | 'FAILED'
    tenant_id: string
    tenant_name: string | null
    farm_name: string | null
    aoi_id: string | null
    aoi_name: string | null
    error_message: string | null
    created_at: string
}

function JobsContent({ token }: { token: string }) {
    const [jobs, setJobs] = useState<Job[]>([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState('ALL')
    const [jobType, setJobType] = useState('')
    const [limit, setLimit] = useState(100)
    const [reprocessLoading, setReprocessLoading] = useState(false)
    const [reprocessDays, setReprocessDays] = useState(56)
    const [reprocessLimit, setReprocessLimit] = useState(200)

    const schemaOutdatedPattern = /(UndefinedColumn)|(column\s+"[^"]+"\s+of\s+relation\s+"observations_weekly"\s+does\s+not\s+exist)|(column\s+"updated_at"\s+of\s+relation\s+"observations_weekly"\s+does\s+not\s+exist)/i

    const hasSchemaOutdated = jobs.some((job) => {
        if (!job?.error_message) return false
        const message = String(job.error_message)
        return schemaOutdatedPattern.test(message)
    })

    useEffect(() => {
        loadJobs(token)
    }, [filter, jobType, limit, token])

    const loadJobs = async (authToken: string) => {
        try {
            const params: Record<string, string | number> = {}
            if (filter !== 'ALL') params.status = filter
            if (jobType.trim()) params.job_type = jobType.trim()
            if (limit) params.limit = limit
            const response = await axios.get(`${API_BASE}/v1/admin/jobs`, {
                headers: { Authorization: `Bearer ${authToken}` },
                params
            })
            setJobs(response.data)
        } catch (err) {
            console.error('Failed to load jobs:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleRetry = async (jobId: string, authToken: string) => {
        try {
            await axios.post(`${API_BASE}/v1/admin/jobs/${jobId}/retry`, {}, {
                headers: { Authorization: `Bearer ${authToken}` }
            })
            loadJobs(authToken)
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Erro ao retentar job')
        }
    }

    const handleReprocessMissing = async (authToken: string) => {
        try {
            setReprocessLoading(true)
            const response = await axios.post(
                `${API_BASE}/v1/admin/ops/reprocess-missing-aois`,
                {},
                {
                    headers: { Authorization: `Bearer ${authToken}` },
                    params: { days: reprocessDays, limit: reprocessLimit }
                }
            )
            alert(`Backfill enfileirado para ${response.data.queued} AOIs`)
            loadJobs(authToken)
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Erro ao reprocessar AOIs sem dados')
        } finally {
            setReprocessLoading(false)
        }
    }

    const getStatusVariant = (status: string): 'default' | 'success' | 'warning' | 'error' | 'info' => {
        switch (status) {
            case 'DONE': return 'success'
            case 'RUNNING': return 'info'
            case 'PENDING': return 'warning'
            case 'FAILED': return 'error'
            default: return 'default'
        }
    }

    // DataTable columns configuration
    const columns: Column<Job>[] = [
        {
            key: 'job_type',
            header: 'Job Type',
            sortable: true,
            mobileLabel: 'Tipo',
        },
        {
            key: 'tenant_name',
            header: 'Tenant',
            accessor: (row) => row.tenant_name || row.tenant_id || '-',
            sortable: true,
            mobileLabel: 'Tenant',
        },
        {
            key: 'farm_name',
            header: 'Fazenda',
            accessor: (row) => row.farm_name || '-',
            sortable: true,
            mobileLabel: 'Fazenda',
        },
        {
            key: 'aoi_name',
            header: 'Talhão',
            accessor: (row) => row.aoi_name || row.aoi_id || '-',
            sortable: true,
            mobileLabel: 'Talhão',
        },
        {
            key: 'status',
            header: 'Status',
            accessor: (row) => (
                <Badge variant={getStatusVariant(row.status)}>
                    {row.status}
                </Badge>
            ),
            sortable: true,
            mobileLabel: 'Status',
        },
        {
            key: 'error_message',
            header: 'Erro',
            accessor: (row) => {
                if (!row.error_message) return '-'
                const truncated = row.error_message.slice(0, 60)
                return (
                    <span title={row.error_message} className="text-xs">
                        {truncated}{row.error_message.length > 60 ? '…' : ''}
                    </span>
                )
            },
            className: 'max-w-xs',
            mobileLabel: 'Erro',
        },
        {
            key: 'created_at',
            header: 'Created',
            accessor: (row) => new Date(row.created_at).toLocaleString('pt-BR'),
            sortable: true,
            mobileLabel: 'Criado em',
        },
        {
            key: 'actions',
            header: 'Actions',
            accessor: (row) => (
                row.status === 'FAILED' ? (
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    handleRetry(row.id, token)
                                }}
                            >
                                Retry
                    </Button>
                ) : null
            ),
            mobileLabel: 'Ações',
        },
    ]

    // Custom mobile card renderer for better UX
    const renderMobileCard = (job: Job) => (
        <div className="rounded-lg bg-card p-4 shadow border border-border space-y-3">
            <div className="flex justify-between items-start">
                <div>
                    <span className="font-semibold text-foreground">{job.job_type}</span>
                    <div className="text-xs text-muted-foreground mt-1">
                        {new Date(job.created_at).toLocaleString('pt-BR')}
                    </div>
                </div>
                <Badge variant={getStatusVariant(job.status)}>
                    {job.status}
                </Badge>
            </div>
            <div className="space-y-1 text-sm">
                <div>
                    <span className="font-medium text-foreground">Tenant:</span>{' '}
                    <span className="text-muted-foreground">{job.tenant_name || job.tenant_id || '-'}</span>
                </div>
                <div>
                    <span className="font-medium text-foreground">Fazenda:</span>{' '}
                    <span className="text-muted-foreground">{job.farm_name || '-'}</span>
                </div>
                <div>
                    <span className="font-medium text-foreground">Talhão:</span>{' '}
                    <span className="text-muted-foreground">{job.aoi_name || job.aoi_id || '-'}</span>
                </div>
                {job.error_message && (
                    <div className="mt-2 p-2 rounded bg-destructive/10 text-xs text-destructive">
                        {job.error_message.slice(0, 100)}{job.error_message.length > 100 ? '…' : ''}
                    </div>
                )}
            </div>
            {job.status === 'FAILED' && (
                <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleRetry(job.id, token)}
                    className="w-full"
                >
                    Retry
                </Button>
            )}
        </div>
    )

    return (
        <div className="mx-auto max-w-7xl space-y-6">
            <div>
                <p className="text-sm text-muted-foreground">Filtre jobs por tipo, status e limite de resultados.</p>
                <h2 className="text-2xl font-semibold text-foreground">Jobs Monitor</h2>
            </div>

            {hasSchemaOutdated && (
                <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    Schema desatualizado detectado: jobs falhando por coluna inexistente em `observations_weekly`.
                    Aplique as migrações pendentes e reprocesse os jobs.
                </div>
            )}

            {/* Filters */}
            <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                    {['ALL', 'PENDING', 'RUNNING', 'DONE', 'FAILED'].map((status) => (
                        <Button
                            key={status}
                            onClick={() => setFilter(status)}
                            variant={filter === status ? 'primary' : 'outline'}
                            size="sm"
                        >
                            {status}
                        </Button>
                    ))}
                </div>

                <div className="flex flex-wrap items-end gap-2 rounded-lg bg-card p-4 border border-border">
                    <Input
                        type="text"
                        label="Job Type"
                        value={jobType}
                        onChange={(e) => setJobType(e.target.value)}
                        placeholder="PROCESS_WEEK"
                        className="min-w-[200px]"
                    />
                    <Input
                        type="number"
                        label="Limite"
                        min={10}
                        max={500}
                        value={limit}
                        onChange={(e) => setLimit(Number(e.target.value))}
                        className="w-24"
                    />
                    <Button variant="outline" size="sm" onClick={() => loadJobs(token)}>
                        Atualizar
                    </Button>
                </div>

                <div className="flex flex-wrap items-center gap-2 rounded-lg bg-card p-4 border border-border">
                    <Input
                        type="number"
                        min={7}
                        max={365}
                        value={reprocessDays}
                        onChange={(e) => setReprocessDays(Number(e.target.value))}
                        className="w-24"
                        placeholder="Dias"
                    />
                    <Input
                        type="number"
                        min={1}
                        max={500}
                        value={reprocessLimit}
                        onChange={(e) => setReprocessLimit(Number(e.target.value))}
                        className="w-24"
                        placeholder="Limite"
                    />
                    <Button
                        onClick={() => handleReprocessMissing(token)}
                        loading={reprocessLoading}
                        variant="primary"
                        size="md"
                    >
                        Reprocessar AOIs sem dados
                    </Button>
                </div>
            </div>

            {/* Jobs DataTable */}
            <DataTable
                data={jobs}
                columns={columns}
                rowKey={(row) => row.id}
                loading={loading}
                emptyMessage="Nenhum job encontrado"
                mobileCardRender={renderMobileCard}
            />
        </div>
    )
}

export default function AdminJobsPage() {
    return (
        <AdminAuthGate>
            {(token) => <JobsContent token={token} />}
        </AdminAuthGate>
    )
}
