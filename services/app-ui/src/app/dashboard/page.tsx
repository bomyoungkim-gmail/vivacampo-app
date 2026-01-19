'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { farmAPI, signalAPI, jobAPI } from '@/lib/api'
import { useAuthProtection } from '@/lib/auth'
import ClientLayout from '@/components/ClientLayout'
import { DashboardSkeleton } from '@/components/LoadingSkeleton'
import type { Signal, DashboardStats } from '@/lib/types'

export default function DashboardPage() {
    const { isAuthenticated, isLoading: authLoading } = useAuthProtection()
    const [stats, setStats] = useState<DashboardStats>({
        farms: 0,
        activeSignals: 0,
        pendingJobs: 0,
    })
    const [recentSignals, setRecentSignals] = useState<Signal[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (isAuthenticated) {
            loadDashboardData()
        }
    }, [isAuthenticated])

    const loadDashboardData = async () => {
        try {
            const [farmsRes, signalsRes, jobsRes] = await Promise.all([
                farmAPI.list(),
                signalAPI.list({ limit: 5 }),
                jobAPI.list({ limit: 10 }),
            ])

            setStats({
                farms: farmsRes.data.length,
                activeSignals: signalsRes.data.filter((s) => s.status === 'ACTIVE').length,
                pendingJobs: jobsRes.data.filter((j) => j.status === 'PENDING').length,
            })

            setRecentSignals(signalsRes.data.slice(0, 5))
        } catch (err) {
            console.error('Failed to load dashboard data:', err)
        } finally {
            setLoading(false)
        }
    }

    if (authLoading || loading) {
        return (
            <ClientLayout>
                <DashboardSkeleton />
            </ClientLayout>
        )
    }

    return (
        <ClientLayout>
            <div className="mb-4 sm:mb-6">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">Bem-vindo de volta!</h2>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">Aqui está um resumo da sua operação</p>
            </div>

            {/* Stats Grid */}
            <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 mb-6 sm:mb-8">
                <div className="rounded-lg bg-white dark:bg-gray-800 p-4 sm:p-6 shadow dark:shadow-gray-700/50 transition-colors">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                            </svg>
                        </div>
                        <div className="ml-4">
                            <p className="text-xs sm:text-sm font-medium text-gray-500 dark:text-gray-400">Fazendas</p>
                            <p className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-white">{stats.farms}</p>
                        </div>
                    </div>
                </div>

                <div className="rounded-lg bg-white dark:bg-gray-800 p-4 sm:p-6 shadow dark:shadow-gray-700/50 transition-colors">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <svg className="h-8 w-8 text-yellow-600 dark:text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        </div>
                        <div className="ml-4">
                            <p className="text-xs sm:text-sm font-medium text-gray-500 dark:text-gray-400">Sinais Ativos</p>
                            <p className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-white">{stats.activeSignals}</p>
                        </div>
                    </div>
                </div>

                <div className="rounded-lg bg-white dark:bg-gray-800 p-4 sm:p-6 shadow dark:shadow-gray-700/50 transition-colors">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <svg className="h-8 w-8 text-blue-600 dark:text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                            </svg>
                        </div>
                        <div className="ml-4">
                            <p className="text-xs sm:text-sm font-medium text-gray-500 dark:text-gray-400">Jobs Pendentes</p>
                            <p className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-white">{stats.pendingJobs}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Signals */}
            <div className="rounded-lg bg-white dark:bg-gray-800 shadow dark:shadow-gray-700/50 transition-colors">
                <div className="border-b border-gray-200 dark:border-gray-700 px-4 sm:px-6 py-3 sm:py-4">
                    <h3 className="text-base sm:text-lg font-medium text-gray-900 dark:text-white">Sinais Recentes</h3>
                </div>
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {recentSignals.length === 0 ? (
                        <div className="px-4 sm:px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                            Nenhum sinal encontrado
                        </div>
                    ) : (
                        recentSignals.map((signal) => (
                            <div key={signal.id} className="px-4 sm:px-6 py-3 sm:py-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                <div className="flex items-start sm:items-center justify-between gap-3">
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-gray-900 dark:text-white text-sm sm:text-base truncate">{signal.signal_type}</p>
                                        <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                                            Score: {signal.score.toFixed(2)} | {signal.aoi_name}
                                        </p>
                                    </div>
                                    <div className="flex flex-col sm:flex-row items-end sm:items-center gap-2">
                                        <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold whitespace-nowrap ${signal.status === 'ACTIVE' ? 'bg-yellow-100 text-yellow-800' :
                                            signal.status === 'ACKNOWLEDGED' ? 'bg-blue-100 text-blue-800' :
                                                'bg-green-100 text-green-800'
                                            }`}>
                                            {signal.status}
                                        </span>
                                        <Link
                                            href={`/signals/${signal.id}`}
                                            className="text-xs sm:text-sm font-medium text-green-600 hover:text-green-700 min-h-touch flex items-center"
                                        >
                                            Ver →
                                        </Link>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </ClientLayout>
    )
}
