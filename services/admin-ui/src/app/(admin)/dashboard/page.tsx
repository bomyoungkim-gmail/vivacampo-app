'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import axios from 'axios'
import { z } from 'zod'
import { AdminAuthGate } from '@/components/AdminAuthGate'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, LoadingSpinner, Badge } from '@/components/ui'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

// Define the schema for the health stats API response
const HealthStatsSchema = z.object({
    database: z.string(),
    jobs_24h: z.object({
        pending: z.number(),
        running: z.number(),
        failed: z.number(),
        completed: z.number().optional(),
    }),
});

// Infer the type from the schema
type HealthStats = z.infer<typeof HealthStatsSchema>;

const QueuesSchema = z.record(z.record(z.number()))
type QueueStats = z.infer<typeof QueuesSchema>

const ProvidersSchema = z.object({
    providers: z.array(z.object({
        name: z.string(),
        status: z.string().optional(),
        message: z.string().optional(),
        updated_at: z.string().optional(),
    })).optional(),
    cache: z.object({
        last_refresh: z.string().optional(),
        ttl_seconds: z.number().optional(),
    }).optional(),
})
type ProvidersStatus = z.infer<typeof ProvidersSchema>


function DashboardContent({ token }: { token: string }) {
    const [stats, setStats] = useState<HealthStats | null>(null)
    const [queues, setQueues] = useState<QueueStats | null>(null)
    const [providers, setProviders] = useState<ProvidersStatus | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [lastUpdated, setLastUpdated] = useState<string | null>(null)

    useEffect(() => {
        let mounted = true
        const run = async () => {
            await loadStats(token, mounted)
        }

        run()
        const interval = setInterval(run, 5000)
        return () => {
            mounted = false
            clearInterval(interval)
        }
    }, [token])

    const loadStats = async (authToken: string, mounted: boolean) => {
        try {
            setError(null)
            const [healthResponse, queuesResponse, providersResponse] = await Promise.all([
                axios.get(`${API_BASE}/v1/admin/ops/health`, {
                    headers: { Authorization: `Bearer ${authToken}` }
                }),
                axios.get(`${API_BASE}/v1/admin/ops/queues`, {
                    headers: { Authorization: `Bearer ${authToken}` }
                }),
                axios.get(`${API_BASE}/v1/admin/providers/status`, {
                    headers: { Authorization: `Bearer ${authToken}` }
                })
            ])
            const validatedStats = HealthStatsSchema.parse(healthResponse.data)
            const validatedQueues = QueuesSchema.parse(queuesResponse.data)
            const validatedProviders = ProvidersSchema.parse(providersResponse.data)
            if (!mounted) return
            setStats(validatedStats)
            setQueues(validatedQueues)
            setProviders(validatedProviders)
            setLastUpdated(new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }))
        } catch (err) {
            console.error('Failed to load or validate stats:', err)
            if (!mounted) return
            setError('Nao foi possivel atualizar o HUD. Tente novamente.')
        } finally {
            if (mounted) setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="flex min-h-[50vh] items-center justify-center bg-background">
                <LoadingSpinner size="lg" label="Carregando estatísticas..." />
            </div>
        )
    }

    return (
        <div className="space-y-8">
            <div>
                <p className="text-sm text-muted-foreground">Monitoramento em tempo real do sistema VivaCampo.</p>
                <h2 className="text-2xl font-semibold text-foreground">Visao Geral</h2>
                {lastUpdated && (
                    <p className="mt-1 text-xs text-muted-foreground">Atualizado as {lastUpdated}</p>
                )}
            </div>

            {error && (
                <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    {error}
                </div>
            )}

            {/* Stats Grid */}
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-sm font-medium text-muted-foreground">Banco de Dados</div>
                        <div className="mt-2 flex items-center">
                            <div className={`h-3 w-3 rounded-full mr-2 ${stats?.database === 'healthy' ? 'bg-primary' : 'bg-destructive'}`} />
                            <span className="text-2xl font-bold text-foreground">
                                {stats?.database === 'healthy' ? 'Online' : 'Offline'}
                            </span>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="text-sm font-medium text-muted-foreground">Jobs na Fila</div>
                        <div className="mt-2 text-3xl font-bold text-foreground">
                            {stats?.jobs_24h?.pending || 0}
                        </div>
                        <div className="mt-1 text-xs text-muted-foreground">Aguardando processamento</div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="text-sm font-medium text-muted-foreground">Jobs Rodando</div>
                        <div className="mt-2 text-3xl font-bold text-primary">
                            {stats?.jobs_24h?.running || 0}
                        </div>
                        <div className="mt-1 text-xs text-muted-foreground">Processamento ativo</div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="text-sm font-medium text-muted-foreground">Falhas (24h)</div>
                        <div className="mt-2 text-3xl font-bold text-destructive">
                            {stats?.jobs_24h?.failed || 0}
                        </div>
                        <div className="mt-1 text-xs text-muted-foreground">Atenção requerida</div>
                    </CardContent>
                </Card>
            </div>

            {/* Queue Breakdown */}
            <div className="rounded-lg border border-border bg-card p-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-semibold text-foreground">Status HUD</h3>
                        <p className="text-sm text-muted-foreground">Fila por tipo de job e status.</p>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => loadStats(token, true)}>
                        Atualizar
                    </Button>
                </div>
                <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {queues
                        ? Object.entries(queues).map(([jobType, statuses]) => (
                            <Card key={jobType} variant="interactive">
                                <CardHeader>
                                    <CardTitle className="text-sm uppercase tracking-wide text-muted-foreground">
                                        {jobType}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-2">
                                    {Object.entries(statuses).map(([status, count]) => (
                                        <div key={status} className="flex items-center justify-between text-sm">
                                            <span className="text-muted-foreground">{status}</span>
                                            <span className="font-semibold text-foreground">{count}</span>
                                        </div>
                                    ))}
                                </CardContent>
                            </Card>
                        ))
                        : (
                            <div className="text-sm text-muted-foreground">Sem dados de fila.</div>
                        )}
                </div>
            </div>

            {/* Providers Status */}
            <div className="rounded-lg border border-border bg-card p-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-semibold text-foreground">Providers Status</h3>
                        <p className="text-sm text-muted-foreground">Monitoramento das fontes satelitais.</p>
                    </div>
                    {providers?.cache?.last_refresh && (
                        <span className="text-xs text-muted-foreground">
                            Cache: {providers.cache.last_refresh}
                        </span>
                    )}
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {providers?.providers?.length ? (
                        providers.providers.map((provider) => (
                            <Card key={provider.name} variant="interactive" className="p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-semibold text-foreground">{provider.name}</p>
                                        {provider.message && (
                                            <p className="text-xs text-muted-foreground">{provider.message}</p>
                                        )}
                                    </div>
                                    <Badge variant={provider.status === 'healthy' ? 'success' : 'warning'}>
                                        {provider.status ?? 'unknown'}
                                    </Badge>
                                </div>
                                {provider.updated_at && (
                                    <p className="mt-2 text-xs text-muted-foreground">Atualizado: {provider.updated_at}</p>
                                )}
                            </Card>
                        ))
                    ) : (
                        <div className="text-sm text-muted-foreground">Sem dados de providers.</div>
                    )}
                </div>
            </div>

            {/* Quick Actions */}
            <div className="mt-8">
                <h3 className="text-lg font-semibold text-foreground mb-4">Ações Rápidas</h3>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    <Link href="/tenants">
                        <Card variant="interactive" className="group relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-5 transition-opacity group-hover:opacity-10">
                                <svg className="w-16 h-16 text-primary" fill="currentColor" viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" /></svg>
                            </div>
                            <CardHeader>
                                <CardTitle className="group-hover:text-primary transition-colors">Gerenciar Tenants</CardTitle>
                                <CardDescription>Visualizar e editar clientes da plataforma.</CardDescription>
                            </CardHeader>
                        </Card>
                    </Link>

                    <Link href="/jobs">
                        <Card variant="interactive" className="group relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-5 transition-opacity group-hover:opacity-10">
                                <svg className="w-16 h-16 text-chart-2" fill="currentColor" viewBox="0 0 24 24"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" /></svg>
                            </div>
                            <CardHeader>
                                <CardTitle className="group-hover:text-chart-2 transition-colors">Monitorar Jobs</CardTitle>
                                <CardDescription>Acompanhar filas de processamento.</CardDescription>
                            </CardHeader>
                        </Card>
                    </Link>

                    <Link href="/audit">
                        <Card variant="interactive" className="group relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-5 transition-opacity group-hover:opacity-10">
                                <svg className="w-16 h-16 text-chart-4" fill="currentColor" viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" /></svg>
                            </div>
                            <CardHeader>
                                <CardTitle className="group-hover:text-chart-4 transition-colors">Logs de Auditoria</CardTitle>
                                <CardDescription>Rastrear atividades do sistema.</CardDescription>
                            </CardHeader>
                        </Card>
                    </Link>
                </div>
            </div>
        </div>
    )
}

export default function AdminDashboardPage() {
    return (
        <AdminAuthGate>
            {(token) => <DashboardContent token={token} />}
        </AdminAuthGate>
    )
}
