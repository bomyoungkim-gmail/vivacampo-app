'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import axios from 'axios'
import { z } from 'zod'

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
            <div className="flex min-h-screen items-center justify-center">
                <div className="text-center">
                    <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
                    <p className="mt-2 text-gray-600">Carregando...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow">
                <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600">
                                <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                </svg>
                            </div>
                            <h1 className="text-2xl font-bold text-gray-900">VivaCampo Admin</h1>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="rounded-md bg-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-300"
                        >
                            Sair
                        </button>
                    </div>
                </div>
            </header>

            {/* Navigation */}
            <nav className="bg-white border-b border-gray-200">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="flex space-x-8">
                        <Link href="/dashboard" className="border-b-2 border-blue-600 px-1 py-4 text-sm font-medium text-blue-600">
                            Dashboard
                        </Link>
                        <Link href="/tenants" className="border-b-2 border-transparent px-1 py-4 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700">
                            Tenants
                        </Link>
                        <Link href="/jobs" className="border-b-2 border-transparent px-1 py-4 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700">
                            Jobs
                        </Link>
                        <Link href="/audit" className="border-b-2 border-transparent px-1 py-4 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700">
                            Audit Log
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="mb-6">
                    <h2 className="text-xl font-semibold text-gray-900">System Health</h2>
                </div>

                {/* Stats Grid */}
                <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-lg bg-white p-6 shadow">
                        <div className="text-sm font-medium text-gray-500">Database</div>
                        <div className="mt-2 text-2xl font-semibold text-gray-900">
                            {stats?.database === 'healthy' ? '✓' : '✗'}
                        </div>
                        <div className="mt-1 text-sm text-gray-600">{stats?.database}</div>
                    </div>

                    <div className="rounded-lg bg-white p-6 shadow">
                        <div className="text-sm font-medium text-gray-500">Pending Jobs</div>
                        <div className="mt-2 text-2xl font-semibold text-gray-900">
                            {stats?.jobs_24h?.pending || 0}
                        </div>
                        <div className="mt-1 text-sm text-gray-600">Last 24h</div>
                    </div>

                    <div className="rounded-lg bg-white p-6 shadow">
                        <div className="text-sm font-medium text-gray-500">Running Jobs</div>
                        <div className="mt-2 text-2xl font-semibold text-gray-900">
                            {stats?.jobs_24h?.running || 0}
                        </div>
                        <div className="mt-1 text-sm text-gray-600">Last 24h</div>
                    </div>

                    <div className="rounded-lg bg-white p-6 shadow">
                        <div className="text-sm font-medium text-gray-500">Failed Jobs</div>
                        <div className="mt-2 text-2xl font-semibold text-red-600">
                            {stats?.jobs_24h?.failed || 0}
                        </div>
                        <div className="mt-1 text-sm text-gray-600">Last 24h</div>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="mt-8">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        <Link
                            href="/tenants"
                            className="block rounded-lg bg-white p-6 shadow hover:shadow-md transition-shadow"
                        >
                            <h4 className="font-medium text-gray-900">Manage Tenants</h4>
                            <p className="mt-1 text-sm text-gray-600">View and manage all tenants</p>
                        </Link>
                        <Link
                            href="/jobs"
                            className="block rounded-lg bg-white p-6 shadow hover:shadow-md transition-shadow"
                        >
                            <h4 className="font-medium text-gray-900">Monitor Jobs</h4>
                            <p className="mt-1 text-sm text-gray-600">View job queue and retry failed jobs</p>
                        </Link>
                        <Link
                            href="/audit"
                            className="block rounded-lg bg-white p-6 shadow hover:shadow-md transition-shadow"
                        >
                            <h4 className="font-medium text-gray-900">Audit Log</h4>
                            <p className="mt-1 text-sm text-gray-600">Review system-wide audit trail</p>
                        </Link>
                    </div>
                </div>
            </main>
        </div>
    )
}
