'use client'

import { useEffect, useMemo, useState } from 'react'
import ClientLayout from '@/components/ClientLayout'
import { useAuthProtection, useAuthRole } from '@/lib/auth'
import { analyticsAPI } from '@/lib/api'
import type { AdoptionEventMetric, AdoptionPhaseMetric } from '@/lib/types'

type PhaseKey = 'F1' | 'F2' | 'F3'

const phaseLabels: Record<PhaseKey, { title: string; description: string }> = {
    F1: { title: 'F1 · Foundation', description: 'Onboarding e primeiros fluxos do Spatial OS.' },
    F2: { title: 'F2 · Map Intelligence', description: 'Interações no mapa e controles críticos.' },
    F3: { title: 'F3 · Post-Map First', description: 'Workflows avançados com cards/overlays.' },
}

const keyEvents: Array<{
    key: string
    label: string
    description: string
    phase: PhaseKey
}> = [
    {
        key: 'onboarding_step',
        label: 'Onboarding',
        description: 'Passos iniciados e concluídos no tour.',
        phase: 'F1',
    },
    {
        key: 'zoom_semantic_transition',
        label: 'Zoom Semântico',
        description: 'Transições de nível de zoom macro/meso/micro.',
        phase: 'F2',
    },
    {
        key: 'aoi_selected',
        label: 'Seleção de Talhão',
        description: 'Talhões selecionados diretamente no mapa.',
        phase: 'F2',
    },
    {
        key: 'aoi_created',
        label: 'Talhão Criado',
        description: 'Talhões criados manualmente no mapa.',
        phase: 'F2',
    },
    {
        key: 'aoi_batch_created',
        label: 'Talhões em Lote',
        description: 'Talhões criados via grid automático.',
        phase: 'F2',
    },
    {
        key: 'bottom_sheet_interaction',
        label: 'Bottom Sheet',
        description: 'Aberturas/fechamentos do sheet espacial.',
        phase: 'F3',
    },
]

export default function AnalyticsDashboardPage() {
    const { isAuthenticated, isLoading: authLoading } = useAuthProtection()
    const role = useAuthRole()
    const canView = role === 'tenant_admin' || role === 'system_admin'
    const [events, setEvents] = useState<AdoptionEventMetric[]>([])
    const [phases, setPhases] = useState<AdoptionPhaseMetric[]>([])
    const [lastUpdated, setLastUpdated] = useState<string | null>(null)
    const [loading, setLoading] = useState(false)
    const [phaseFilter, setPhaseFilter] = useState<PhaseKey | 'ALL'>('ALL')
    const [sortMode, setSortMode] = useState<'label' | 'count'>('count')

    useEffect(() => {
        if (!isAuthenticated || !canView) {
            return
        }
        setLoading(true)
        analyticsAPI
            .getAdoptionSummary()
            .then((response) => {
                setEvents(response.data.events ?? [])
                setPhases(response.data.phases ?? [])
                setLastUpdated(new Date().toISOString())
            })
            .finally(() => {
                setLoading(false)
            })
    }, [isAuthenticated, canView])

    const phaseMetrics = useMemo(() => {
        return (Object.keys(phaseLabels) as PhaseKey[]).map((phase) => {
            const total = phases.find((item) => item.phase === phase)?.count ?? 0
            return { phase, total }
        })
    }, [phases])

    const filteredEvents = useMemo(() => {
        const withCounts = keyEvents.map((event) => ({
            ...event,
            count: events.find((item) => item.event_name === event.key)?.count ?? 0,
            lastSeen: events.find((item) => item.event_name === event.key)?.last_seen ?? null,
        }))

        const phaseFiltered = phaseFilter === 'ALL'
            ? withCounts
            : withCounts.filter((event) => event.phase === phaseFilter)

        if (sortMode === 'count') {
            return [...phaseFiltered].sort((a, b) => b.count - a.count)
        }
        return [...phaseFiltered].sort((a, b) => a.label.localeCompare(b.label))
    }, [events, phaseFilter, sortMode])

    const handleRefresh = () => {
        setLoading(true)
        analyticsAPI
            .getAdoptionSummary()
            .then((response) => {
                setEvents(response.data.events ?? [])
                setPhases(response.data.phases ?? [])
                setLastUpdated(new Date().toISOString())
            })
            .finally(() => {
                setLoading(false)
            })
    }

    if (authLoading) {
        return (
            <ClientLayout>
                <div className="animate-pulse space-y-4">
                    <div className="h-6 w-40 rounded bg-muted" />
                    <div className="h-24 rounded-2xl bg-muted" />
                    <div className="h-24 rounded-2xl bg-muted" />
                </div>
            </ClientLayout>
        )
    }

    if (!isAuthenticated) {
        return null
    }

    return (
        <ClientLayout>
            <div className="space-y-6">
                <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                        <h2 className="text-xl sm:text-2xl font-bold text-foreground">Analytics de Adoção</h2>
                        <p className="mt-1 text-sm text-muted-foreground">
                            Monitoramento local de eventos chave do Spatial OS.
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 rounded-full border border-border/60 bg-background/80 px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                            <button
                                onClick={() => setSortMode('count')}
                                className={`min-h-touch rounded-full px-3 py-1 transition-colors ${sortMode === 'count'
                                        ? 'bg-primary text-primary-foreground'
                                        : 'hover:text-foreground'
                                    }`}
                            >
                                Por Volume
                            </button>
                            <button
                                onClick={() => setSortMode('label')}
                                className={`min-h-touch rounded-full px-3 py-1 transition-colors ${sortMode === 'label'
                                        ? 'bg-primary text-primary-foreground'
                                        : 'hover:text-foreground'
                                    }`}
                            >
                                Alfabético
                            </button>
                        </div>
                        <button
                            onClick={handleRefresh}
                            className="min-h-touch rounded-full border border-border/60 bg-background/80 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground hover:text-foreground transition-colors"
                        >
                            Atualizar
                        </button>
                    </div>
                </div>

                {!canView && (
                    <div className="rounded-2xl border border-border/60 bg-background/90 p-4 text-sm text-muted-foreground">
                        Este painel é destinado a administradores do tenant.
                    </div>
                )}

                <div className="grid gap-4 md:grid-cols-3">
                    {phaseMetrics.map((phase) => (
                        <div key={phase.phase} className="rounded-2xl border border-border/60 bg-background/90 p-4 shadow-sm">
                            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                                {phaseLabels[phase.phase].title}
                            </p>
                            <p className="mt-2 text-3xl font-semibold text-foreground">{phase.total}</p>
                            <p className="mt-1 text-xs text-muted-foreground">{phaseLabels[phase.phase].description}</p>
                        </div>
                    ))}
                </div>

                <div className="rounded-2xl border border-border/60 bg-background/90 shadow-sm">
                    <div className="border-b border-border/60 px-4 py-3">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                            <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                                Eventos Chave
                            </h3>
                            <div className="flex flex-wrap items-center gap-2">
                                {(['ALL', 'F1', 'F2', 'F3'] as const).map((phase) => (
                                    <button
                                        key={phase}
                                        onClick={() => setPhaseFilter(phase)}
                                        className={`min-h-touch rounded-full border border-border/60 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] transition-colors ${phaseFilter === phase
                                                ? 'bg-primary text-primary-foreground'
                                                : 'bg-background/80 text-muted-foreground hover:text-foreground'
                                            }`}
                                    >
                                        {phase === 'ALL' ? 'Todas' : phase}
                                    </button>
                                ))}
                            </div>
                            {lastUpdated && (
                                <span className="text-xs text-muted-foreground">
                                    Atualizado em {new Date(lastUpdated).toLocaleString('pt-BR')}
                                </span>
                            )}
                        </div>
                    </div>
                    <div className="divide-y divide-border/60">
                        {filteredEvents.map((event) => {
                            return (
                                <div key={event.key} className="flex flex-col gap-2 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
                                    <div>
                                        <p className="text-sm font-semibold text-foreground">
                                            {event.label}
                                            <span className="ml-2 rounded-full border border-border/60 bg-muted px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                                                {event.phase}
                                            </span>
                                        </p>
                                        <p className="text-xs text-muted-foreground">{event.description}</p>
                                    </div>
                                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                        <span className="rounded-full border border-border/60 bg-muted px-3 py-1 text-xs font-semibold text-foreground">
                                            {event.count}
                                        </span>
                                        <span>
                                            {event.lastSeen
                                                ? `Último: ${new Date(event.lastSeen).toLocaleString('pt-BR')}`
                                                : 'Sem eventos'}
                                        </span>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>

                {loading && (
                    <div className="rounded-2xl border border-border/60 bg-background/90 p-4 text-xs text-muted-foreground">
                        Atualizando métricas...
                    </div>
                )}
            </div>
        </ClientLayout>
    )
}
