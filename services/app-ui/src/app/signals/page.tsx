'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { signalAPI } from '@/lib/api'
import { useAuthProtection } from '@/lib/auth'
import { APP_CONFIG } from '@/lib/config'
import ClientLayout from '@/components/ClientLayout'
import { useErrorHandler } from '@/lib/errorHandler'
import { ErrorToast, SuccessToast } from '@/components/Toast'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import type { Signal, SignalStatus, SignalType } from '@/lib/types'

type FilterOption = 'ALL' | SignalStatus

export default function SignalsPage() {
    const { isAuthenticated, isLoading: authLoading } = useAuthProtection()
    const { error, handleError, clearError } = useErrorHandler()
    const [signals, setSignals] = useState<Signal[]>([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState<FilterOption>('ALL')
    const [successMessage, setSuccessMessage] = useState<string | null>(null)

    useEffect(() => {
        if (isAuthenticated) {
            loadSignals()
        }
    }, [isAuthenticated, filter])

    const loadSignals = async () => {
        try {
            const params = filter !== 'ALL' ? { status: filter } : {}
            const response = await signalAPI.list(params)
            setSignals(response.data)
        } catch (err) {
            handleError(err, 'Failed to load signals')
        } finally {
            setLoading(false)
        }
    }

    const handleAcknowledge = async (signalId: string) => {
        try {
            await signalAPI.acknowledge(signalId)
            setSuccessMessage('Sinal reconhecido com sucesso!')
            loadSignals()
        } catch (err) {
            handleError(err, 'Failed to acknowledge signal')
        }
    }

    const getSignalColor = (type: SignalType) => {
        return APP_CONFIG.COLORS.SIGNAL_TYPES[type] || 'bg-gray-100 text-gray-800'
    }

    const getStatusColor = (status: SignalStatus) => {
        return APP_CONFIG.COLORS.SIGNAL_STATUS[status] || 'bg-gray-100 text-gray-800'
    }

    if (authLoading || loading) {
        return <LoadingSpinner />
    }

    return (
        <ClientLayout>
            {/* Toast Notifications */}
            <ErrorToast error={error} onClose={clearError} />
            <SuccessToast message={successMessage} onClose={() => setSuccessMessage(null)} />

            <div className="mb-4 sm:mb-6">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Sinais</h2>
                <p className="mt-1 text-xs sm:text-sm text-gray-600">
                    Monitore e gerencie os sinais detectados
                </p>
            </div>

            {/* Filters */}
            <div className="mb-4 sm:mb-6 flex gap-2 overflow-x-auto scrollbar-hide pb-2">
                {(['ALL', 'ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'] as const).map((status) => (
                    <button
                        key={status}
                        onClick={() => setFilter(status as FilterOption)}
                        className={`rounded-lg px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium whitespace-nowrap min-h-touch ${filter === status
                            ? 'bg-green-600 text-white'
                            : 'bg-white text-gray-700 hover:bg-gray-50'
                            }`}
                    >
                        {status === 'ALL' ? 'Todos' : status}
                    </button>
                ))}
            </div>

            {/* Signals List */}
            {loading ? (
                <div className="text-center py-12">
                    <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-green-600 border-r-transparent"></div>
                </div>
            ) : signals.length === 0 ? (
                <div className="rounded-lg bg-white p-8 sm:p-12 text-center shadow">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhum sinal encontrado</h3>
                    <p className="mt-1 text-sm text-gray-500">Os sinais aparecerão aqui quando detectados</p>
                </div>
            ) : (
                <div className="space-y-3 sm:space-y-4">
                    {signals.map((signal) => (
                        <div key={signal.id} className="rounded-lg bg-white p-4 sm:p-6 shadow hover:shadow-md transition-shadow">
                            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                                <div className="flex-1 min-w-0">
                                    <div className="flex flex-wrap items-center gap-2">
                                        <span className={`inline-flex rounded-full px-2 sm:px-3 py-1 text-xs font-semibold ${getSignalColor(signal.signal_type)}`}>
                                            {signal.signal_type}
                                        </span>
                                        <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getStatusColor(signal.status)}`}>
                                            {signal.status}
                                        </span>
                                    </div>
                                    <h3 className="mt-2 text-base sm:text-lg font-semibold text-gray-900">{signal.aoi_name}</h3>
                                    <p className="mt-1 text-xs sm:text-sm text-gray-600">
                                        Score: <span className="font-semibold">{signal.score.toFixed(2)}</span> |
                                        Detectado em: {new Date(signal.detected_at).toLocaleDateString('pt-BR')}
                                    </p>
                                    {signal.recommended_action && (
                                        <div className="mt-3 rounded-lg bg-blue-50 p-3">
                                            <p className="text-xs sm:text-sm font-medium text-blue-900">Ação Recomendada:</p>
                                            <p className="mt-1 text-xs sm:text-sm text-blue-700">{signal.recommended_action}</p>
                                        </div>
                                    )}
                                </div>
                                <div className="flex sm:flex-col gap-2 sm:ml-4">
                                    {signal.status === 'ACTIVE' && (
                                        <button
                                            onClick={() => handleAcknowledge(signal.id)}
                                            className="flex-1 sm:flex-none rounded-lg bg-blue-600 px-4 py-2 text-xs sm:text-sm font-semibold text-white hover:bg-blue-700 min-h-touch"
                                        >
                                            Reconhecer
                                        </button>
                                    )}
                                    <Link
                                        href={`/signals/${signal.id}`}
                                        className="flex-1 sm:flex-none rounded-lg border border-gray-300 px-4 py-2 text-center text-xs sm:text-sm font-medium text-gray-700 hover:bg-gray-50 min-h-touch flex items-center justify-center"
                                    >
                                        Ver Detalhes
                                    </Link>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </ClientLayout>
    )
}
