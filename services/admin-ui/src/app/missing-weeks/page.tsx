'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

type MissingWeeksItem = {
    tenant_id: string
    aoi_id: string
    farm_name?: string
    aoi_name?: string
    missing_weeks: [number, number][]
    missing_count: number
}

type MissingWeeksResponse = {
    weeks: number
    items: MissingWeeksItem[]
}

export default function MissingWeeksPage() {
    const router = useRouter()
    const [loading, setLoading] = useState(true)
    const [items, setItems] = useState<MissingWeeksItem[]>([])
    const [weeks, setWeeks] = useState(8)
    const [limit, setLimit] = useState(50)
    const [reprocessLimit, setReprocessLimit] = useState(10)
    const [maxRuns, setMaxRuns] = useState(3)
    const [reprocessLoading, setReprocessLoading] = useState(false)

    useEffect(() => {
        const token = localStorage.getItem('admin_token')
        if (!token) {
            router.push('/login')
            return
        }
        loadMissingWeeks()
    }, [router, weeks, limit])

    const loadMissingWeeks = async () => {
        try {
            setLoading(true)
            const token = localStorage.getItem('admin_token')
            const response = await axios.get<MissingWeeksResponse>(`${API_BASE}/v1/admin/ops/missing-weeks`, {
                headers: { Authorization: `Bearer ${token}` },
                params: { weeks, limit }
            })
            setItems(response.data.items || [])
        } catch (err) {
            console.error('Failed to load missing weeks:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleReprocess = async () => {
        try {
            setReprocessLoading(true)
            const token = localStorage.getItem('admin_token')
            const response = await axios.post(
                `${API_BASE}/v1/admin/ops/reprocess-missing-weeks`,
                {},
                {
                    headers: { Authorization: `Bearer ${token}` },
                    params: { weeks, limit: reprocessLimit, max_runs_per_aoi: maxRuns }
                }
            )
            alert(`Backfill enfileirado: ${response.data.queued}`)
            loadMissingWeeks()
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Erro ao reprocessar semanas faltantes')
        } finally {
            setReprocessLoading(false)
        }
    }

    const renderWeeks = (weeksList: [number, number][]) => {
        const preview = weeksList.slice(0, 6).map(([y, w]) => `${y}-W${String(w).padStart(2, '0')}`)
        const suffix = weeksList.length > 6 ? ` +${weeksList.length - 6}` : ''
        return preview.join(', ') + suffix
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow">
                <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
                    <h1 className="text-2xl font-bold text-gray-900">Buracos de Dados (Semanas)</h1>
                </div>
            </header>

            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="mb-6 flex flex-wrap items-center gap-2">
                    <input
                        type="number"
                        min={1}
                        max={104}
                        value={weeks}
                        onChange={(e) => setWeeks(Number(e.target.value))}
                        className="w-24 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700"
                        placeholder="Semanas"
                    />
                    <input
                        type="number"
                        min={1}
                        max={200}
                        value={limit}
                        onChange={(e) => setLimit(Number(e.target.value))}
                        className="w-24 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700"
                        placeholder="Limite"
                    />
                    <button
                        onClick={loadMissingWeeks}
                        className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                        Atualizar
                    </button>
                    <div className="ml-auto flex flex-wrap items-center gap-2">
                        <input
                            type="number"
                            min={1}
                            max={200}
                            value={reprocessLimit}
                            onChange={(e) => setReprocessLimit(Number(e.target.value))}
                            className="w-28 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700"
                            placeholder="Limite Reproc."
                        />
                        <input
                            type="number"
                            min={1}
                            max={6}
                            value={maxRuns}
                            onChange={(e) => setMaxRuns(Number(e.target.value))}
                            className="w-24 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700"
                            placeholder="Runs"
                        />
                        <button
                            onClick={handleReprocess}
                            disabled={reprocessLoading}
                            className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-60"
                        >
                            {reprocessLoading ? 'Enfileirando...' : 'Reprocessar Buracos'}
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="text-center py-12">
                        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
                    </div>
                ) : (
                    <div className="rounded-lg bg-white shadow overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fazenda</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Talhão (AOI)</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Missing</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Semanas</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {items.map((item) => (
                                    <tr key={item.aoi_id}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {item.farm_name || '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {item.aoi_name || item.aoi_id}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {item.missing_count}
                                        </td>
                                        <td className="px-6 py-4 text-xs text-gray-500 font-mono">
                                            {renderWeeks(item.missing_weeks)}
                                        </td>
                                    </tr>
                                ))}
                                {items.length === 0 && (
                                    <tr>
                                        <td className="px-6 py-6 text-sm text-gray-500" colSpan={4}>
                                            Nenhum buraco encontrado nas ultimas semanas.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </main>
        </div>
    )
}
