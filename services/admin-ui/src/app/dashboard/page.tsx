'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import axios from 'axios'
import { z } from 'zod'
import { Loader2 } from 'lucide-react'
import ThemeToggle from '@/components/ThemeToggle'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

// Define the schema for the health stats API response
const HealthStatsSchema = z.object({
    database: z.string(),
    jobs_24h: z.object({
        pending: z.number(),
        running: z.number(),
        failed: z.number(),
        completed: z.number(),
    }),
});

// Infer the type from the schema
type HealthStats = z.infer<typeof HealthStatsSchema>;


export default function AdminDashboardPage() {
    const router = useRouter()
    const [stats, setStats] = useState<HealthStats | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const token = localStorage.getItem('admin_token')
        if (!token) {
            router.push('/login')
            return
        }

        loadStats()
    }, [router])

    const loadStats = async () => {
        try {
            const token = localStorage.getItem('admin_token')
            const response = await axios.get(`${API_BASE}/v1/admin/ops/health`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            // Validate the response data with the Zod schema
            const validatedStats = HealthStatsSchema.parse(response.data);
            setStats(validatedStats)
        } catch (err) {
            console.error('Failed to load or validate stats:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleLogout = () => {
        localStorage.removeItem('admin_token')
        router.push('/login')
    }

    if (loading) {
        return (
            <div className="flex min-h-[50vh] items-center justify-center bg-background">
                <Loader2 className="h-10 w-10 animate-spin text-primary" />
            </div>
        )
    }

    return (
        <div className="space-y-8">
            {/* Page Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">Visão Geral</h1>
                    <p className="mt-2 text-muted-foreground">Monitoramento em tempo real do sistema VivaCampo.</p>
                </div>
                <ThemeToggle />
            </div>

            {/* Stats Grid */}
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl bg-card p-6 shadow transition-all hover:shadow-lg border border-border">
                    <div className="text-sm font-medium text-muted-foreground">Banco de Dados</div>
                    <div className="mt-2 flex items-center">
                        <div className={`h-3 w-3 rounded-full mr-2 ${stats?.database === 'healthy' ? 'bg-primary' : 'bg-destructive'}`} />
                        <span className="text-2xl font-bold text-foreground">
                            {stats?.database === 'healthy' ? 'Online' : 'Offline'}
                        </span>
                    </div>
                </div>

                <div className="rounded-xl bg-card p-6 shadow transition-all hover:shadow-lg border border-border">
                    <div className="text-sm font-medium text-muted-foreground">Jobs na Fila</div>
                    <div className="mt-2 text-3xl font-bold text-foreground">
                        {stats?.jobs_24h?.pending || 0}
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">Aguardando processamento</div>
                </div>

                <div className="rounded-xl bg-card p-6 shadow transition-all hover:shadow-lg border border-border">
                    <div className="text-sm font-medium text-muted-foreground">Jobs Rodando</div>
                    <div className="mt-2 text-3xl font-bold text-primary">
                        {stats?.jobs_24h?.running || 0}
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">Processamento ativo</div>
                </div>

                <div className="rounded-xl bg-card p-6 shadow transition-all hover:shadow-lg border border-border">
                    <div className="text-sm font-medium text-muted-foreground">Falhas (24h)</div>
                    <div className="mt-2 text-3xl font-bold text-destructive">
                        {stats?.jobs_24h?.failed || 0}
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">Atenção requerida</div>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="mt-8">
                <h3 className="text-lg font-semibold text-foreground mb-4">Ações Rápidas</h3>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    <Link
                        href="/tenants"
                        className="interactive-card group relative overflow-hidden rounded-xl bg-card p-6 shadow-sm border border-border transition-all hover:shadow-md hover:border-primary/50"
                    >
                        <div className="absolute top-0 right-0 p-4 opacity-5 transition-opacity group-hover:opacity-10">
                            <svg className="w-16 h-16 text-primary" fill="currentColor" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" /></svg>
                        </div>
                        <h4 className="font-semibold text-foreground group-hover:text-primary transition-colors">Gerenciar Tenants</h4>
                        <p className="mt-1 text-sm text-muted-foreground">Visualizar e editar clientes da plataforma.</p>
                    </Link>

                    <Link
                        href="/jobs"
                        className="interactive-card group relative overflow-hidden rounded-xl bg-card p-6 shadow-sm border border-border transition-all hover:shadow-md hover:border-chart-2/50"
                    >
                        <div className="absolute top-0 right-0 p-4 opacity-5 transition-opacity group-hover:opacity-10">
                            <svg className="w-16 h-16 text-chart-2" fill="currentColor" viewBox="0 0 24 24"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" /></svg>
                        </div>
                        <h4 className="font-semibold text-foreground group-hover:text-chart-2 transition-colors">Monitorar Jobs</h4>
                        <p className="mt-1 text-sm text-muted-foreground">Acompanhar filas de processamento.</p>
                    </Link>

                    <Link
                        href="/audit"
                        className="interactive-card group relative overflow-hidden rounded-xl bg-card p-6 shadow-sm border border-border transition-all hover:shadow-md hover:border-chart-4/50"
                    >
                        <div className="absolute top-0 right-0 p-4 opacity-5 transition-opacity group-hover:opacity-10">
                            <svg className="w-16 h-16 text-chart-4" fill="currentColor" viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" /></svg>
                        </div>
                        <h4 className="font-semibold text-foreground group-hover:text-chart-4 transition-colors">Logs de Auditoria</h4>
                        <p className="mt-1 text-sm text-muted-foreground">Rastrear atividades do sistema.</p>
                    </Link>
                </div>
            </div>
        </div>
    )
}
