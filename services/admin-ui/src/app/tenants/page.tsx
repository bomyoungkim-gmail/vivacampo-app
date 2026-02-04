'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import { Loader2 } from 'lucide-react'
import ThemeToggle from '@/components/ThemeToggle'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function AdminTenantsPage() {
    const router = useRouter()
    const [tenants, setTenants] = useState<any[]>([])
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

    const getStatusColor = (status: string) => {
        return status === 'ACTIVE'
            ? 'bg-primary/10 text-primary dark:bg-primary/20'
            : 'bg-destructive/10 text-destructive dark:bg-destructive/20'
    }

    return (
        <div className="min-h-screen bg-background">
            <header className="border-b border-border bg-card shadow-sm">
                <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8 flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-foreground">Tenants</h1>
                    <ThemeToggle />
                </div>
            </header>

            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-10 w-10 animate-spin text-primary" />
                    </div>
                ) : (
                    <>
                        {/* Mobile: Cards */}
                        <div className="block md:hidden space-y-4">
                            {tenants.map((tenant) => (
                                <div key={tenant.id} className="rounded-lg bg-card p-4 shadow border border-border">
                                    <div className="flex justify-between items-start mb-3">
                                        <div>
                                            <h3 className="font-semibold text-foreground">{tenant.name}</h3>
                                            <p className="text-xs text-muted-foreground mt-1">{tenant.type}</p>
                                        </div>
                                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${getStatusColor(tenant.status)}`}>
                                            {tenant.status}
                                        </span>
                                    </div>
                                    <div className="space-y-1 text-sm">
                                        <div>
                                            <span className="font-medium text-foreground">Tier:</span>{' '}
                                            <span className="text-muted-foreground">{tenant.tier}</span>
                                        </div>
                                        <div>
                                            <span className="font-medium text-foreground">Created:</span>{' '}
                                            <span className="text-muted-foreground">
                                                {new Date(tenant.created_at).toLocaleDateString('pt-BR')}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Desktop: Table */}
                        <div className="hidden md:block rounded-lg bg-card shadow border border-border overflow-hidden">
                            <table className="min-w-full divide-y divide-border">
                                <thead className="bg-muted/50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Name</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Type</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Tier</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Created</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {tenants.map((tenant) => (
                                        <tr key={tenant.id} className="table-row-interactive">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-foreground">
                                                {tenant.name}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                                {tenant.type}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                                {tenant.tier}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getStatusColor(tenant.status)}`}>
                                                    {tenant.status}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                                {new Date(tenant.created_at).toLocaleDateString('pt-BR')}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </>
                )}
            </main>
        </div>
    )
}
