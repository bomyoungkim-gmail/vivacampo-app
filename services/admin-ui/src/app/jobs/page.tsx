'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import { Loader2 } from 'lucide-react'
import ThemeToggle from '@/components/ThemeToggle'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function AdminJobsPage() {
    const router = useRouter()
    const [jobs, setJobs] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState('ALL')
    const [reprocessLoading, setReprocessLoading] = useState(false)
    const [reprocessDays, setReprocessDays] = useState(56)
    const [reprocessLimit, setReprocessLimit] = useState(200)

    useEffect(() => {
        const token = localStorage.getItem('admin_token')
        if (!token) {
            router.push('/login')
            return
        }

        loadJobs()
    }, [router, filter])

    const loadJobs = async () => {
        try {
            const token = localStorage.getItem('admin_token')
            const params = filter !== 'ALL' ? { status: filter } : {}
            const response = await axios.get(`${API_BASE}/v1/admin/jobs`, {
                headers: { Authorization: `Bearer ${token}` },
                params
            })
            setJobs(response.data)
        } catch (err) {
            console.error('Failed to load jobs:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleRetry = async (jobId: string) => {
        try {
            const token = localStorage.getItem('admin_token')
            await axios.post(`${API_BASE}/v1/admin/jobs/${jobId}/retry`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            })
            loadJobs()
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Erro ao retentar job')
        }
    }

    const handleReprocessMissing = async () => {
        try {
            setReprocessLoading(true)
            const token = localStorage.getItem('admin_token')
            const response = await axios.post(
                `${API_BASE}/v1/admin/ops/reprocess-missing-aois`,
                {},
                {
                    headers: { Authorization: `Bearer ${token}` },
                    params: { days: reprocessDays, limit: reprocessLimit }
                }
            )
            alert(`Backfill enfileirado para ${response.data.queued} AOIs`)
            loadJobs()
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Erro ao reprocessar AOIs sem dados')
        } finally {
            setReprocessLoading(false)
        }
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'DONE': return 'bg-primary/10 text-primary dark:bg-primary/20'
            case 'RUNNING': return 'bg-chart-2/10 text-chart-2 dark:bg-chart-2/20'
            case 'PENDING': return 'bg-chart-3/10 text-chart-3 dark:bg-chart-3/20'
            case 'FAILED': return 'bg-destructive/10 text-destructive dark:bg-destructive/20'
            default: return 'bg-muted text-muted-foreground'
        }
    }

    return (
        <div className="min-h-screen bg-background">
            <header className="border-b border-border bg-card shadow-sm">
                <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8 flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-foreground">Jobs Monitor</h1>
                    <ThemeToggle />
                </div>
            </header>

            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {/* Filters */}
                <div className="mb-6 space-y-4">
                    <div className="flex flex-wrap items-center gap-2">
                        {['ALL', 'PENDING', 'RUNNING', 'DONE', 'FAILED'].map((status) => (
                            <button
                                key={status}
                                onClick={() => setFilter(status)}
                                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors min-h-touch ${filter === status
                                        ? 'bg-primary text-primary-foreground'
                                        : 'bg-card text-foreground hover:bg-muted border border-border'
                                    }`}
                            >
                                {status}
                            </button>
                        ))}
                    </div>

                    <div className="flex flex-wrap items-center gap-2 rounded-lg bg-card p-4 border border-border">
                        <input
                            type="number"
                            min={7}
                            max={365}
                            value={reprocessDays}
                            onChange={(e) => setReprocessDays(Number(e.target.value))}
                            className="w-24 rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground min-h-touch focus:outline-none focus:ring-2 focus:ring-ring"
                            placeholder="Dias"
                        />
                        <input
                            type="number"
                            min={1}
                            max={500}
                            value={reprocessLimit}
                            onChange={(e) => setReprocessLimit(Number(e.target.value))}
                            className="w-24 rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground min-h-touch focus:outline-none focus:ring-2 focus:ring-ring"
                            placeholder="Limite"
                        />
                        <button
                            onClick={handleReprocessMissing}
                            disabled={reprocessLoading}
                            className="rounded-lg bg-chart-3 px-4 py-2 text-sm font-medium text-white hover:bg-chart-3/90 disabled:opacity-60 transition-colors min-h-touch"
                            title="Enfileira backfill para AOIs sem derived_assets"
                        >
                            {reprocessLoading ? 'Enfileirando...' : 'Reprocessar AOIs sem dados'}
                        </button>
                    </div>
                </div>

                {/* Jobs List */}
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-10 w-10 animate-spin text-primary" />
                    </div>
                ) : (
                    <>
                        {/* Mobile: Cards */}
                        <div className="block lg:hidden space-y-4">
                            {jobs.map((job) => (
                                <div key={job.id} className="rounded-lg bg-card p-4 shadow border border-border">
                                    <div className="flex justify-between items-start mb-3">
                                        <div>
                                            <span className="font-semibold text-foreground">{job.job_type}</span>
                                            <div className="text-xs text-muted-foreground mt-1">
                                                {new Date(job.created_at).toLocaleString('pt-BR')}
                                            </div>
                                        </div>
                                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${getStatusColor(job.status)}`}>
                                            {job.status}
                                        </span>
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
                                        <button
                                            onClick={() => handleRetry(job.id)}
                                            className="mt-3 w-full rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors min-h-touch"
                                        >
                                            Retry
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>

                        {/* Desktop: Table with horizontal scroll */}
                        <div className="hidden lg:block rounded-lg bg-card shadow border border-border overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-border">
                                    <thead className="bg-muted/50">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Job Type</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Tenant</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Fazenda</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Talhão</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Erro</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Created</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border">
                                        {jobs.map((job) => (
                                            <tr key={job.id} className="table-row-interactive">
                                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-foreground">{job.job_type}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                                    {job.tenant_name || job.tenant_id || '-'}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                                    {job.farm_name || '-'}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                                    {job.aoi_name || job.aoi_id || '-'}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getStatusColor(job.status)}`}>
                                                        {job.status}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-xs text-muted-foreground max-w-xs truncate">
                                                    {job.error_message ? (
                                                        <span title={job.error_message}>
                                                            {job.error_message.slice(0, 60)}{job.error_message.length > 60 ? '…' : ''}
                                                        </span>
                                                    ) : '-'}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                                    {new Date(job.created_at).toLocaleString('pt-BR')}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                    {job.status === 'FAILED' && (
                                                        <button
                                                            onClick={() => handleRetry(job.id)}
                                                            className="text-primary hover:text-primary/80 font-medium transition-colors"
                                                        >
                                                            Retry
                                                        </button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </>
                )}
            </main>
        </div>
    )
}
