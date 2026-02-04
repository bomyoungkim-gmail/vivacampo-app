'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import { Loader2 } from 'lucide-react'
import ThemeToggle from '@/components/ThemeToggle'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function AdminAuditPage() {
    const router = useRouter()
    const [auditLogs, setAuditLogs] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState({ tenant_id: '', action: '' })

    useEffect(() => {
        const token = localStorage.getItem('admin_token')
        if (!token) {
            router.push('/login')
            return
        }

        loadAuditLogs()
    }, [router])

    const loadAuditLogs = async () => {
        try {
            const token = localStorage.getItem('admin_token')
            const response = await axios.get(`${API_BASE}/v1/admin/audit`, {
                headers: { Authorization: `Bearer ${token}` },
                params: filter
            })
            setAuditLogs(response.data)
        } catch (err) {
            console.error('Failed to load audit logs:', err)
        } finally {
            setLoading(false)
        }
    }

    const getActionColor = (action: string) => {
        switch (action) {
            case 'CREATE': return 'bg-primary/10 text-primary dark:bg-primary/20'
            case 'UPDATE': return 'bg-chart-2/10 text-chart-2 dark:bg-chart-2/20'
            case 'DELETE': return 'bg-destructive/10 text-destructive dark:bg-destructive/20'
            default: return 'bg-muted text-muted-foreground'
        }
    }

    return (
        <div className="min-h-screen bg-background">
            <header className="border-b border-border bg-card shadow-sm">
                <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8 flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-foreground">Global Audit Log</h1>
                    <ThemeToggle />
                </div>
            </header>

            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {/* Filters */}
                <div className="mb-6 rounded-lg bg-card p-4 shadow border border-border">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-2">Tenant ID</label>
                            <input
                                type="text"
                                value={filter.tenant_id}
                                onChange={(e) => setFilter({ ...filter, tenant_id: e.target.value })}
                                className="block w-full rounded-lg border border-input bg-background px-3 py-2 text-foreground min-h-touch focus:outline-none focus:ring-2 focus:ring-ring"
                                placeholder="Filter by tenant..."
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-2">Action</label>
                            <select
                                value={filter.action}
                                onChange={(e) => setFilter({ ...filter, action: e.target.value })}
                                className="block w-full rounded-lg border border-input bg-background px-3 py-2 text-foreground min-h-touch focus:outline-none focus:ring-2 focus:ring-ring"
                            >
                                <option value="">All Actions</option>
                                <option value="CREATE">CREATE</option>
                                <option value="UPDATE">UPDATE</option>
                                <option value="DELETE">DELETE</option>
                            </select>
                        </div>
                    </div>
                    <button
                        onClick={loadAuditLogs}
                        className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors min-h-touch min-w-touch"
                    >
                        Apply Filters
                    </button>
                </div>

                {/* Audit Log - Mobile Cards / Desktop Table */}
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-10 w-10 animate-spin text-primary" />
                    </div>
                ) : (
                    <>
                        {/* Mobile: Cards */}
                        <div className="block md:hidden space-y-4">
                            {auditLogs.map((log) => (
                                <div key={log.id} className="rounded-lg bg-card p-4 shadow border border-border">
                                    <div className="flex justify-between items-start mb-3">
                                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${getActionColor(log.action)}`}>
                                            {log.action}
                                        </span>
                                        <span className="text-xs text-muted-foreground">
                                            {new Date(log.created_at).toLocaleString('pt-BR')}
                                        </span>
                                    </div>
                                    <div className="space-y-2 text-sm">
                                        <div>
                                            <span className="font-medium text-foreground">Tenant:</span>{' '}
                                            <span className="text-muted-foreground">{log.tenant_id.substring(0, 8)}</span>
                                        </div>
                                        <div>
                                            <span className="font-medium text-foreground">Resource:</span>{' '}
                                            <span className="text-muted-foreground">
                                                {log.resource_type}: {log.resource_id?.substring(0, 8)}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="font-medium text-foreground">Actor:</span>{' '}
                                            <span className="text-muted-foreground">
                                                {log.actor_membership_id?.substring(0, 8) || 'System'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Desktop: Table */}
                        <div className="hidden md:block rounded-lg bg-card shadow border border-border overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-border">
                                    <thead className="bg-muted/50">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Timestamp</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Tenant</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Action</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Resource</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Actor</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border">
                                        {auditLogs.map((log) => (
                                            <tr key={log.id} className="table-row-interactive">
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                                    {new Date(log.created_at).toLocaleString('pt-BR')}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                                    {log.tenant_id.substring(0, 8)}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getActionColor(log.action)}`}>
                                                        {log.action}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                                                    {log.resource_type}: {log.resource_id?.substring(0, 8)}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                                    {log.actor_membership_id?.substring(0, 8) || 'System'}
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
