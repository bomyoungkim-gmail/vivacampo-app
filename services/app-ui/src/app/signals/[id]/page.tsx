'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { signalAPI } from '@/lib/api'
import { useAuthProtection } from '@/lib/auth'
import { APP_CONFIG } from '@/lib/config'
import ClientLayout from '@/components/ClientLayout'
import { useErrorHandler } from '@/lib/errorHandler'
import { ErrorToast, SuccessToast } from '@/components/Toast'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import type { Signal, SignalType, SignalStatus } from '@/lib/types'

export default function SignalDetailsPage({ params }: { params: { id: string } }) {
    const { isAuthenticated, isLoading: authLoading } = useAuthProtection()
    const { error, handleError, clearError } = useErrorHandler()
    const router = useRouter()

    const [signal, setSignal] = useState<Signal | null>(null)
    const [loading, setLoading] = useState(true)
    const [successMessage, setSuccessMessage] = useState<string | null>(null)
    const [processing, setProcessing] = useState(false)

    useEffect(() => {
        if (isAuthenticated && params.id) {
            loadSignal(params.id)
        }
    }, [isAuthenticated, params.id])

    const loadSignal = async (id: string) => {
        try {
            const response = await signalAPI.get(id)
            setSignal(response.data)
        } catch (err) {
            handleError(err, 'Failed to load signal details')
        } finally {
            setLoading(false)
        }
    }

    const handleAcknowledge = async () => {
        if (!signal) return

        try {
            setProcessing(true)
            await signalAPI.acknowledge(signal.id)
            setSuccessMessage('Sinal reconhecido com sucesso!')
            // Refresh data
            loadSignal(signal.id)
        } catch (err) {
            handleError(err, 'Failed to acknowledge signal')
        } finally {
            setProcessing(false)
        }
    }

    const getSignalColor = (type: string) => {
        return APP_CONFIG.COLORS.SIGNAL_TYPES[type as SignalType] || 'bg-gray-100 text-gray-800'
    }

    const getStatusColor = (status: SignalStatus) => {
        return APP_CONFIG.COLORS.SIGNAL_STATUS[status] || 'bg-gray-100 text-gray-800'
    }

    if (authLoading || loading) {
        return <LoadingSpinner />
    }

    if (!signal) {
        return (
            <ClientLayout>
                <div className="text-center py-12">
                    <h3 className="text-lg font-medium text-gray-900">Sinal não encontrado</h3>
                    <Link href="/dashboard" className="inline-flex min-h-touch items-center text-green-600 hover:text-green-700 mt-4">
                        &larr; Voltar para Dashboard
                    </Link>
                </div>
            </ClientLayout>
        )
    }

    return (
        <ClientLayout>
            <ErrorToast error={error} onClose={clearError} />
            <SuccessToast message={successMessage} onClose={() => setSuccessMessage(null)} />

            <div className="mb-6">
                <Link href="/dashboard" className="inline-flex min-h-touch items-center text-sm text-gray-500 hover:text-gray-700 mb-4">
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Voltar para Dashboard
                </Link>

                <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
                    <div className="px-6 py-5 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
                        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Detalhes do Sinal</h1>
                        <div className="flex gap-2">
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSignalColor(signal.signal_type)}`}>
                                {signal.signal_type}
                            </span>
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(signal.status)}`}>
                                {signal.status}
                            </span>
                        </div>
                    </div>

                    <div className="px-6 py-6 space-y-6">
                        {/* Main Info */}
                        {/* Main Info */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Área de Interesse (AOI)</h3>
                                <p className="mt-1 text-lg font-medium text-gray-900 dark:text-white">{signal.aoi_name || 'N/A'}</p>
                            </div>
                            <div>
                                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Score de Risco</h3>
                                <p className="mt-1 text-lg font-medium text-gray-900 dark:text-white">{(signal.score * 100).toFixed(1)}%</p>
                            </div>
                            <div>
                                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Detectado em</h3>
                                <p className="mt-1 text-lg text-gray-900 dark:text-white">
                                    {new Date(signal.created_at || signal.detected_at || new Date()).toLocaleString('pt-BR')}
                                </p>
                            </div>
                            <div>
                                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">ID do Sinal</h3>
                                <p className="mt-1 text-sm font-mono text-gray-600 dark:text-gray-300">{signal.id}</p>
                            </div>
                            <div>
                                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Tipo de Sinal</h3>
                                <p className="mt-1 text-lg text-gray-900 dark:text-white">
                                    {signal.signal_type === 'PASTURE_FORAGE_RISK' && 'Risco em Pastagem'}
                                    {signal.signal_type === 'CROP_STRESS' && 'Estresse Hídrico'}
                                    {signal.signal_type === 'PEST_OUTBREAK' && 'Alerta de Pragas'}
                                    {!['PASTURE_FORAGE_RISK', 'CROP_STRESS', 'PEST_OUTBREAK'].includes(signal.signal_type) && signal.signal_type}
                                </p>
                            </div>
                            <div>
                                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Severidade</h3>
                                <div className="mt-1 flex items-center">
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize
                                        ${signal.severity === 'HIGH' ? 'bg-red-100 text-red-800' :
                                            signal.severity === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                                                'bg-green-100 text-green-800'}`}>
                                        {signal.severity === 'HIGH' ? 'Alta' :
                                            signal.severity === 'MEDIUM' ? 'Média' : 'Baixa'}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Recommended Action */}
                        {signal.recommended_actions && signal.recommended_actions.length > 0 && (
                            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-100 dark:border-blue-800">
                                <h3 className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">Ações Recomendadas</h3>
                                <ul className="list-disc list-inside text-blue-700 dark:text-blue-200 space-y-1">
                                    {signal.recommended_actions.map((action, idx) => (
                                        <li key={idx}>{action}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Metadata */}
                        {signal.evidence_json && Object.keys(signal.evidence_json).length > 0 && (
                            <div>
                                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Evidências Técnicas</h3>
                                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 font-mono text-xs text-gray-700 dark:text-gray-300 overflow-x-auto border border-gray-200 dark:border-gray-700">
                                    <pre>{JSON.stringify(signal.evidence_json, null, 2)}</pre>
                                </div>
                            </div>
                        )}

                        {/* Actions */}
                        {signal.status === 'ACTIVE' && (
                            <div className="pt-6 border-t border-gray-200 dark:border-gray-700 flex justify-end">
                                <button
                                    onClick={handleAcknowledge}
                                    disabled={processing}
                                    className="min-h-touch bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    {processing ? 'Processando...' : 'Reconhecer Sinal'}
                                </button>
                            </div>
                        )}

                        {signal.status === 'ACKNOWLEDGED' && signal.acknowledged_at && (
                            <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    Reconhecido em {new Date(signal.acknowledged_at).toLocaleString('pt-BR')}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </ClientLayout>
    )
}
