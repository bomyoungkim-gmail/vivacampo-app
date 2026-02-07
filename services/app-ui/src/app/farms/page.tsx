'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { farmAPI } from '@/lib/api'
import { useAuthProtection, useAuthRole } from '@/lib/auth'
import { APP_CONFIG } from '@/lib/config'
import ClientLayout from '@/components/ClientLayout'
import type { Farm, FarmFormData } from '@/lib/types'
import { ErrorToast } from '@/components/Toast'
import { useErrorHandler } from '@/lib/errorHandler'
import { useUser } from '@/stores/useUserStore'

export default function FarmsPage() {
    const { isAuthenticated, isLoading: authLoading } = useAuthProtection()
    const role = useAuthRole()
    const user = useUser()
    const [farms, setFarms] = useState<Farm[]>([])
    const [loading, setLoading] = useState(true)
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [newFarm, setNewFarm] = useState<FarmFormData>({
        name: '',
        timezone: APP_CONFIG.DEFAULT_TIMEZONE
    })

    // Error Handling
    const { error, handleError, clearError } = useErrorHandler()

    useEffect(() => {
        if (isAuthenticated) {
            loadFarms()
        }
    }, [isAuthenticated])

    const canCreateFarm = role === 'tenant_admin' || role === 'editor' || role === 'system_admin'

    const loadFarms = async () => {
        try {
            const response = await farmAPI.list()
            setFarms(response.data)
        } catch (err) {
            console.error('Failed to load farms:', err)
            handleError(err, 'Falha ao carregar fazendas')
        } finally {
            setLoading(false)
        }
    }

    const handleCreateFarm = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!canCreateFarm) {
            handleError(null, 'Sem permissão para criar fazendas')
            return
        }
        try {
            await farmAPI.create(newFarm)
            setShowCreateModal(false)
            setNewFarm({ name: '', timezone: APP_CONFIG.DEFAULT_TIMEZONE })
            loadFarms()
        } catch (err: any) {
            handleError(err, 'Erro ao criar fazenda')
        }
    }

    const handleDeleteFarm = async (farmId: string, farmName: string) => {
        const farm = farms.find((item) => item.id === farmId)
        const isOwner = farm?.created_by_user_id && user?.id ? farm.created_by_user_id === user.id : false
        const canDelete = role === 'tenant_admin' || role === 'system_admin' || (role === 'editor' && isOwner)
        if (!canDelete) {
            handleError(null, 'Sem permissão para excluir esta fazenda')
            return
        }
        if (confirm(`Tem certeza que deseja excluir a fazenda "${farmName}"?`)) {
            try {
                await farmAPI.delete(farmId)
                loadFarms()
            } catch (err) {
                handleError(err, 'Erro ao excluir fazenda')
            }
        }
    }

    if (authLoading || loading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <div className="text-center">
                    <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent"></div>
                    <p className="mt-2 text-gray-600">Carregando...</p>
                </div>
            </div>
        )
    }

    return (
        <ClientLayout>
            {/* Toast Notifications */}
            <ErrorToast error={error} onClose={clearError} />

            <div className="mb-4 sm:mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Fazendas</h2>
                    <p className="mt-1 text-xs sm:text-sm text-gray-600">
                        Gerencie suas fazendas e áreas de interesse
                    </p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    disabled={!canCreateFarm}
                    title={canCreateFarm ? 'Criar nova fazenda' : 'Sem permissão para criar fazendas'}
                    className={`rounded-lg px-4 py-2 text-sm font-semibold min-h-touch whitespace-nowrap ${canCreateFarm
                            ? 'bg-green-600 text-white hover:bg-green-700'
                            : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                        }`}
                >
                    + Nova Fazenda
                </button>
            </div>

            {/* Farms Grid */}
            {loading ? (
                <div className="text-center py-12">
                    <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-green-600 border-r-transparent"></div>
                </div>
            ) : farms.length === 0 ? (
                <div className="rounded-lg bg-white p-8 sm:p-12 text-center shadow">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma fazenda</h3>
                    <p className="mt-1 text-sm text-gray-500">Comece criando sua primeira fazenda</p>
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="mt-6 rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 min-h-touch"
                    >
                        + Nova Fazenda
                    </button>
                </div>
            ) : (
                <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                    {farms.map((farm) => (
                        <div key={farm.id} className="rounded-lg bg-white p-4 sm:p-6 shadow hover:shadow-md transition-shadow">
                            <div className="flex items-start justify-between gap-2">
                                <div className="flex-1 min-w-0">
                                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 truncate">{farm.name}</h3>
                                    <p className="mt-1 text-xs sm:text-sm text-gray-600 truncate">{farm.timezone}</p>
                                    <div className="mt-2 flex items-center gap-2">
                                        {farm.created_by_user_id && user?.id && (
                                            <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${farm.created_by_user_id === user.id
                                                    ? 'bg-blue-100 text-blue-800'
                                                    : 'bg-gray-100 text-gray-700'
                                                }`}>
                                                {farm.created_by_user_id === user.id ? 'Criada por você' : 'Criada por outro'}
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <span className="inline-flex rounded-full bg-green-100 px-2 py-1 text-xs font-semibold text-green-800 whitespace-nowrap">
                                    Ativa
                                </span>
                            </div>
                            <div className="mt-4 flex items-center justify-between">
                                <span className="text-xs sm:text-sm text-gray-500">
                                    {farm.aoi_count || 0} AOIs
                                </span>
                                <div className="flex items-center space-x-2 sm:space-x-3">
                                    {(() => {
                                        const isOwner = farm.created_by_user_id && user?.id ? farm.created_by_user_id === user.id : false
                                        const canDelete = role === 'tenant_admin' || role === 'system_admin' || (role === 'editor' && isOwner)
                                        return (
                                            <button
                                                onClick={() => handleDeleteFarm(farm.id, farm.name)}
                                                disabled={!canDelete}
                                                className={`transition-colors min-h-touch min-w-touch p-2 ${canDelete
                                                        ? 'text-gray-400 hover:text-red-600'
                                                        : 'text-gray-300 cursor-not-allowed'
                                                    }`}
                                                title={canDelete ? 'Excluir Fazenda' : 'Sem permissão para excluir'}
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                            </button>
                                        )
                                    })()}
                                    <Link
                                        href={`/farms/${farm.id}`}
                                        className="text-xs sm:text-sm font-medium text-green-600 hover:text-green-700 min-h-touch flex items-center"
                                    >
                                        Ver detalhes →
                                    </Link>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Create Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
                    <div className="w-full max-w-md rounded-lg bg-white p-4 sm:p-6 shadow-xl">
                        <h2 className="text-lg sm:text-xl font-bold text-gray-900">Nova Fazenda</h2>
                        <form onSubmit={handleCreateFarm} className="mt-4 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Nome</label>
                                <input
                                    type="text"
                                    required
                                    value={newFarm.name}
                                    onChange={(e) => setNewFarm({ ...newFarm, name: e.target.value })}
                                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 min-h-touch"
                                    placeholder="Fazenda Santa Maria"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Timezone</label>
                                <select
                                    value={newFarm.timezone}
                                    onChange={(e) => setNewFarm({ ...newFarm, timezone: e.target.value })}
                                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 min-h-touch"
                                >
                                    <option value="America/Sao_Paulo">America/Sao_Paulo (Brasília/Sudeste)</option>
                                    <option value="America/Manaus">America/Manaus (Amazonas)</option>
                                    <option value="America/Cuiaba">America/Cuiaba (Mato Grosso)</option>
                                    <option value="America/Campo_Grande">America/Campo_Grande (MS)</option>
                                    <option value="America/Rio_Branco">America/Rio_Branco (Acre)</option>
                                    <option value="America/Belem">America/Belem (Pará/Nordeste)</option>
                                    <option value="America/Fortaleza">America/Fortaleza (Nordeste)</option>
                                    <option value="America/Noronha">America/Noronha (Ilhas)</option>
                                </select>
                            </div>
                            <div className="flex gap-3">
                                <button
                                    type="button"
                                    onClick={() => setShowCreateModal(false)}
                                    className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 min-h-touch"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 min-h-touch"
                                >
                                    Criar
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </ClientLayout>
    )
}
