'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import { AdminAuthGate } from '@/components/AdminAuthGate'
import { Button, DataTable, Badge, Select, type Column } from '@/components/ui'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Tenant {
    id: string
    name: string
    type: string
    tier: string
    status: 'ACTIVE' | 'SUSPENDED'
    created_at: string
}

function TenantsContent({ token }: { token: string }) {
    const [tenants, setTenants] = useState<Tenant[]>([])
    const [loading, setLoading] = useState(true)
    const [statusDrafts, setStatusDrafts] = useState<Record<string, Tenant['status']>>({})
    const [updatingId, setUpdatingId] = useState<string | null>(null)
    const [updateError, setUpdateError] = useState<string | null>(null)

    useEffect(() => {
        loadTenants(token)
    }, [token])

    const loadTenants = async (authToken: string) => {
        try {
            const response = await axios.get(`${API_BASE}/v1/admin/tenants`, {
                headers: { Authorization: `Bearer ${authToken}` }
            })
            setTenants(response.data)
        } catch (err) {
            console.error('Failed to load tenants:', err)
        } finally {
            setLoading(false)
        }
    }

    const getStatusVariant = (status: string): 'success' | 'error' | 'warning' => {
        return status === 'ACTIVE' ? 'success' : 'warning'
    }

    const handleStatusChange = (tenantId: string, nextStatus: Tenant['status']) => {
        setStatusDrafts((prev) => ({ ...prev, [tenantId]: nextStatus }))
    }

    const handleStatusSave = async (tenantId: string) => {
        const nextStatus = statusDrafts[tenantId]
        if (!nextStatus) return
        setUpdatingId(tenantId)
        setUpdateError(null)
        try {
            await axios.patch(
                `${API_BASE}/v1/admin/tenants/${tenantId}`,
                { status: nextStatus },
                { headers: { Authorization: `Bearer ${token}` } }
            )
            setTenants((prev) =>
                prev.map((tenant) =>
                    tenant.id === tenantId ? { ...tenant, status: nextStatus } : tenant
                )
            )
        } catch (err) {
            console.error('Failed to update tenant status:', err)
            setUpdateError('Falha ao atualizar status do tenant.')
        } finally {
            setUpdatingId(null)
        }
    }

    // DataTable columns configuration
    const columns: Column<Tenant>[] = [
        {
            key: 'name',
            header: 'Name',
            sortable: true,
            mobileLabel: 'Nome',
        },
        {
            key: 'type',
            header: 'Type',
            sortable: true,
            mobileLabel: 'Tipo',
        },
        {
            key: 'tier',
            header: 'Tier',
            sortable: true,
            mobileLabel: 'Tier',
        },
        {
            key: 'status',
            header: 'Status',
            accessor: (row) => (
                <div className="flex items-center gap-3">
                    <Badge variant={getStatusVariant(row.status)}>
                        {row.status}
                    </Badge>
                    <Select
                        aria-label={`Atualizar status de ${row.name}`}
                        value={statusDrafts[row.id] ?? row.status}
                        onChange={(e) => handleStatusChange(row.id, e.target.value as Tenant['status'])}
                        options={[
                            { value: 'ACTIVE', label: 'ACTIVE' },
                            { value: 'SUSPENDED', label: 'SUSPENDED' },
                        ]}
                        className="min-w-[140px]"
                    />
                    <Button
                        variant="outline"
                        size="sm"
                        loading={updatingId === row.id}
                        onClick={() => handleStatusSave(row.id)}
                    >
                        Salvar
                    </Button>
                </div>
            ),
            sortable: true,
            mobileLabel: 'Status',
        },
        {
            key: 'created_at',
            header: 'Created',
            accessor: (row) => new Date(row.created_at).toLocaleDateString('pt-BR'),
            sortable: true,
            mobileLabel: 'Criado em',
        },
    ]

    return (
        <div className="mx-auto max-w-7xl space-y-6">
            <div>
                <p className="text-sm text-muted-foreground">Administre tenants e controle o status de acesso.</p>
                <h2 className="text-2xl font-semibold text-foreground">Tenants</h2>
            </div>

            {updateError && (
                <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    {updateError}
                </div>
            )}

            <DataTable
                data={tenants}
                columns={columns}
                rowKey={(row) => row.id}
                loading={loading}
                emptyMessage="Nenhum tenant encontrado"
            />
        </div>
    )
}

export default function AdminTenantsPage() {
    return (
        <AdminAuthGate>
            {(token) => <TenantsContent token={token} />}
        </AdminAuthGate>
    )
}
