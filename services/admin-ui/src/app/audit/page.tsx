'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import ThemeToggle from '@/components/ThemeToggle'
import { Button, DataTable, Badge, Input, Select, type Column } from '@/components/ui'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface AuditLog {
    id: string
    tenant_id: string
    action: 'CREATE' | 'UPDATE' | 'DELETE'
    resource_type: string
    resource_id: string | null
    actor_membership_id: string | null
    created_at: string
}

export default function AdminAuditPage() {
    const router = useRouter()
    const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
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

    const getActionVariant = (action: string): 'default' | 'success' | 'warning' | 'error' | 'info' | 'secondary' => {
        switch (action) {
            case 'CREATE': return 'info'
            case 'UPDATE': return 'warning'
            case 'DELETE': return 'error'
            default: return 'default'
        }
    }

    // DataTable columns configuration
    const columns: Column<AuditLog>[] = [
        {
            key: 'created_at',
            header: 'Timestamp',
            accessor: (row) => new Date(row.created_at).toLocaleString('pt-BR'),
            sortable: true,
            mobileLabel: 'Data',
        },
        {
            key: 'tenant_id',
            header: 'Tenant',
            accessor: (row) => row.tenant_id.substring(0, 8),
            sortable: true,
            mobileLabel: 'Tenant',
        },
        {
            key: 'action',
            header: 'Action',
            accessor: (row) => (
                <Badge variant={getActionVariant(row.action)}>
                    {row.action}
                </Badge>
            ),
            sortable: true,
            mobileLabel: 'Ação',
        },
        {
            key: 'resource',
            header: 'Resource',
            accessor: (row) => `${row.resource_type}: ${row.resource_id?.substring(0, 8) || 'N/A'}`,
            sortable: true,
            mobileLabel: 'Recurso',
        },
        {
            key: 'actor_membership_id',
            header: 'Actor',
            accessor: (row) => row.actor_membership_id?.substring(0, 8) || 'System',
            sortable: true,
            mobileLabel: 'Ator',
        },
    ]

    // Custom mobile card renderer
    const renderMobileCard = (log: AuditLog) => (
        <div className="rounded-lg bg-card p-4 shadow border border-border space-y-3">
            <div className="flex justify-between items-start">
                <Badge variant={getActionVariant(log.action)}>
                    {log.action}
                </Badge>
                <span className="text-xs text-muted-foreground">
                    {new Date(log.created_at).toLocaleString('pt-BR')}
                </span>
            </div>
            <div className="space-y-1 text-sm">
                <div>
                    <span className="font-medium text-foreground">Tenant:</span>{' '}
                    <span className="text-muted-foreground">{log.tenant_id.substring(0, 8)}</span>
                </div>
                <div>
                    <span className="font-medium text-foreground">Resource:</span>{' '}
                    <span className="text-muted-foreground">
                        {log.resource_type}: {log.resource_id?.substring(0, 8) || 'N/A'}
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
    )

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
                        <Input
                            type="text"
                            label="Tenant ID"
                            value={filter.tenant_id}
                            onChange={(e) => setFilter({ ...filter, tenant_id: e.target.value })}
                            placeholder="Filter by tenant..."
                        />
                        <Select
                            label="Action"
                            value={filter.action}
                            onChange={(e) => setFilter({ ...filter, action: e.target.value })}
                            options={[
                                { value: '', label: 'All Actions' },
                                { value: 'CREATE', label: 'CREATE' },
                                { value: 'UPDATE', label: 'UPDATE' },
                                { value: 'DELETE', label: 'DELETE' },
                            ]}
                        />
                    </div>
                    <Button
                        onClick={loadAuditLogs}
                        variant="primary"
                        size="md"
                        className="mt-4"
                    >
                        Apply Filters
                    </Button>
                </div>

                {/* Audit Log DataTable */}
                <DataTable
                    data={auditLogs}
                    columns={columns}
                    rowKey={(row) => row.id}
                    loading={loading}
                    emptyMessage="Nenhum log de auditoria encontrado"
                    mobileCardRender={renderMobileCard}
                />
            </main>
        </div>
    )
}
