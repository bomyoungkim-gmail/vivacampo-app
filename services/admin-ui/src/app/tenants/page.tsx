'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import ThemeToggle from '@/components/ThemeToggle'
import { DataTable, Badge, type Column } from '@/components/ui'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Tenant {
    id: string
    name: string
    type: string
    tier: string
    status: 'ACTIVE' | 'INACTIVE'
    created_at: string
}

export default function AdminTenantsPage() {
    const router = useRouter()
    const [tenants, setTenants] = useState<Tenant[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const token = localStorage.getItem('admin_token')
        if (!token) {
            router.push('/login')
            return
        }
        loadTenants()
    }, [router])

    const loadTenants = async () => {
        try {
            const token = localStorage.getItem('admin_token')
            const response = await axios.get(`${API_BASE}/v1/admin/tenants`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setTenants(response.data)
        } catch (err) {
            console.error('Failed to load tenants:', err)
        } finally {
            setLoading(false)
        }
    }

    const getStatusVariant = (status: string): 'success' | 'error' => {
        return status === 'ACTIVE' ? 'success' : 'error'
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
                <Badge variant={getStatusVariant(row.status)}>
                    {row.status}
                </Badge>
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
        <div className="min-h-screen bg-background">
            <header className="border-b border-border bg-card shadow-sm">
                <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8 flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-foreground">Tenants</h1>
                    <ThemeToggle />
                </div>
            </header>

            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                <DataTable
                    data={tenants}
                    columns={columns}
                    rowKey={(row) => row.id}
                    loading={loading}
                    emptyMessage="Nenhum tenant encontrado"
                />
            </main>
        </div>
    )
}
