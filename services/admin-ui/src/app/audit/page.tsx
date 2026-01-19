'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function AdminAuditPage() {
    const router = useRouter()
    const [auditLogs, setAuditLogs] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState({ tenant_id: '', action: '' })

    useEffect(() => {
        const token = localStorage.getItem('admin_token')
        if (!token) {
            router.push('/admin/login')
            return
        }

        loadAuditLogs()
    }, [router])

    const loadAuditLogs = async () => {
        try {
            const token = localStorage.getItem('admin_token')
            const response = await axios.get(`${API_BASE}/v1/admin/audit`, {
                headers: { Authorization: `Bearer ${token}` },
                params: filter
            })
            setAuditLogs(response.data)
        } catch (err) {
            console.error('Failed to load audit logs:', err)
        } finally {
            setLoading(false)
        }
    }

    const getActionColor = (action: string) => {
        switch (action) {
            case 'CREATE': return 'bg-green-100 text-green-800'
            case 'UPDATE': return 'bg-blue-100 text-blue-800'
            case 'DELETE': return 'bg-red-100 text-red-800'
            default: return 'bg-gray-100 text-gray-800'
        }
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow">
                <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
                    <h1 className="text-2xl font-bold text-gray-900">Global Audit Log</h1>
                </div>
            </header>

            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {/* Filters */}
                <div className="mb-6 rounded-lg bg-white p-4 shadow">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Tenant ID</label>
                            <input
                                type="text"
                                value={filter.tenant_id}
                                onChange={(e) => setFilter({ ...filter, tenant_id: e.target.value })}
                                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2"
                                placeholder="Filter by tenant..."
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Action</label>
                            <select
                                value={filter.action}
                                onChange={(e) => setFilter({ ...filter, action: e.target.value })}
                                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2"
                            >
                                <option value="">All Actions</option>
                                <option value="CREATE">CREATE</option>
                                <option value="UPDATE">UPDATE</option>
                                <option value="DELETE">DELETE</option>
                            </select>
                        </div>
                    </div>
                    <button
                        onClick={loadAuditLogs}
                        className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
                    >
                        Apply Filters
                    </button>
                </div>

                {/* Audit Log Table */}
                {loading ? (
                    <div className="text-center py-12">
                        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
                    </div>
                ) : (
                    <div className="rounded-lg bg-white shadow overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tenant</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Resource</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actor</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {auditLogs.map((log) => (
                                    <tr key={log.id}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {new Date(log.created_at).toLocaleString('pt-BR')}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{log.tenant_id.substring(0, 8)}</td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getActionColor(log.action)}`}>
                                                {log.action}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {log.resource_type}: {log.resource_id?.substring(0, 8)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {log.actor_membership_id?.substring(0, 8) || 'System'}
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
