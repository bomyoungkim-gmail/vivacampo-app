'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function AdminJobsPage() {
    const router = useRouter()
    const [jobs, setJobs] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState('ALL')

    useEffect(() => {
        const token = localStorage.getItem('admin_token')
        if (!token) {
            router.push('/login')
            return
        }

        loadJobs()
    }, [router, filter])

    const loadJobs = async () => {
        try {
            const token = localStorage.getItem('admin_token')
            const params = filter !== 'ALL' ? { status: filter } : {}
            const response = await axios.get(`${API_BASE}/v1/admin/jobs`, {
                headers: { Authorization: `Bearer ${token}` },
                params
            })
            setJobs(response.data)
        } catch (err) {
            console.error('Failed to load jobs:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleRetry = async (jobId: string) => {
        try {
            const token = localStorage.getItem('admin_token')
            await axios.post(`${API_BASE}/v1/admin/jobs/${jobId}/retry`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            })
            loadJobs()
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Erro ao retentar job')
        }
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'COMPLETED': return 'bg-green-100 text-green-800'
            case 'RUNNING': return 'bg-blue-100 text-blue-800'
            case 'PENDING': return 'bg-yellow-100 text-yellow-800'
            case 'FAILED': return 'bg-red-100 text-red-800'
            default: return 'bg-gray-100 text-gray-800'
        }
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow">
                <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
                    <h1 className="text-2xl font-bold text-gray-900">Jobs Monitor</h1>
                </div>
            </header>

            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {/* Filters */}
                <div className="mb-6 flex space-x-2">
                    {['ALL', 'PENDING', 'RUNNING', 'COMPLETED', 'FAILED'].map((status) => (
                        <button
                            key={status}
                            onClick={() => setFilter(status)}
                            className={`rounded-lg px-4 py-2 text-sm font-medium ${filter === status
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-white text-gray-700 hover:bg-gray-50'
                                }`}
                        >
                            {status}
                        </button>
                    ))}
                </div>

                {/* Jobs Table */}
                {loading ? (
                    <div className="text-center py-12">
                        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
                    </div>
                ) : (
                    <div className="rounded-lg bg-white shadow overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Job Type</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tenant</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {jobs.map((job) => (
                                    <tr key={job.id}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{job.job_type}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{job.tenant_name}</td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getStatusColor(job.status)}`}>
                                                {job.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {new Date(job.created_at).toLocaleString('pt-BR')}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                                            {job.status === 'FAILED' && (
                                                <button
                                                    onClick={() => handleRetry(job.id)}
                                                    className="text-blue-600 hover:text-blue-700 font-medium"
                                                >
                                                    Retry
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </main>
        </div>
    )
}
