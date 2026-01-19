'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function TenantsPage() {
    const router = useRouter()
    const [tenants, setTenants] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const token = localStorage.getItem('admin_token')
        if (!token) {
            router.push('/admin/login')
            return
        }

        loadTenants()
    }, [router])

    const loadTenants = async () => {
        try {
            const token = localStorage.getItem('admin_token')
            const response = await axios.get(`${API_BASE}/v1/admin/tenants`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setTenants(response.data)
        } catch (err) {
            console.error('Failed to load tenants:', err)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow">
                <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
                    <h1 className="text-2xl font-bold text-gray-900">Tenant Management</h1>
                </div>
            </header>

            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {loading ? (
                    <div className="text-center py-12">
                        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
                    </div>
                ) : (
                    <div className="rounded-lg bg-white shadow overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tier</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {tenants.map((tenant) => (
                                    <tr key={tenant.id}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{tenant.name}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{tenant.type}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{tenant.tier}</td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${tenant.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                                }`}>
                                                {tenant.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {new Date(tenant.created_at).toLocaleDateString('pt-BR')}
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
