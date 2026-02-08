'use client'

import { useEffect, useState } from 'react'
import ClientLayout from '@/components/ClientLayout'
import { useAuthProtection, useAuthRole } from '@/lib/auth'
import { tenantAdminAPI } from '@/lib/api'
import { useErrorHandler } from '@/lib/errorHandler'
import { ErrorToast } from '@/components/Toast'
import type { InviteMemberRequest, Membership } from '@/lib/types'
import { getLandingPreference, setLandingPreference } from '@/lib/landingPreference'
import useUserStore from '@/stores/useUserStore'

export default function SettingsPage() {
    const { isAuthenticated, isLoading: authLoading } = useAuthProtection()
    const role = useAuthRole()
    const { error, handleError, clearError } = useErrorHandler()

    const [members, setMembers] = useState<Membership[]>([])
    const [loading, setLoading] = useState(true)
    const [showInviteModal, setShowInviteModal] = useState(false)
    const [inviteData, setInviteData] = useState<InviteMemberRequest>({
        name: '',
        email: '',
        role: 'EDITOR',
    })
    const [inviteLoading, setInviteLoading] = useState(false)
    const [inviteSuccess, setInviteSuccess] = useState<string | null>(null)
    const [landingPreference, setLandingPreferenceState] = useState<'dashboard' | 'map'>('dashboard')

    useEffect(() => {
        if (isAuthenticated) {
            loadMembers()
        }
    }, [isAuthenticated])

    useEffect(() => {
        if (typeof window === 'undefined') return
        const userId = useUserStore.getState().user?.id
        if (!userId) return
        setLandingPreferenceState(getLandingPreference(userId))
    }, [])

    const loadMembers = async () => {
        setLoading(true)
        try {
            const response = await tenantAdminAPI.listMembers()
            setMembers(response.data)
        } catch (err) {
            handleError(err, 'Falha ao carregar membros')
        } finally {
            setLoading(false)
        }
    }

    const handleInvite = async (e: React.FormEvent) => {
        e.preventDefault()
        setInviteLoading(true)
        setInviteSuccess(null)
        try {
            const response = await tenantAdminAPI.inviteMember(inviteData)
            setInviteSuccess(`Convite enviado para ${response.data.email}`)
            setInviteData({ name: '', email: '', role: 'EDITOR' })
            setShowInviteModal(false)
            loadMembers()
        } catch (err) {
            handleError(err, 'Falha ao enviar convite')
        } finally {
            setInviteLoading(false)
        }
    }

    const canInvite = role === 'tenant_admin' || role === 'system_admin'

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
            <ErrorToast error={error} onClose={clearError} />

            <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Configurações</h2>
                    <p className="mt-1 text-xs sm:text-sm text-gray-600">
                        Gerencie membros e permissões do seu workspace
                    </p>
                </div>
                <button
                    onClick={() => setShowInviteModal(true)}
                    disabled={!canInvite}
                    title={canInvite ? 'Convidar membro' : 'Sem permissão para convidar'}
                    className={`rounded-lg px-4 py-2 text-sm font-semibold min-h-touch whitespace-nowrap ${
                        canInvite
                            ? 'bg-green-600 text-white hover:bg-green-700'
                            : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    }`}
                >
                    + Convidar
                </button>
            </div>

            {inviteSuccess && (
                <div className="mb-4 rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-700">
                    {inviteSuccess}
                </div>
            )}

            <div className="mb-6 rounded-lg bg-white shadow">
                <div className="border-b border-gray-200 px-4 py-3">
                    <h3 className="text-sm font-semibold text-gray-900">Preferências</h3>
                </div>
                <div className="p-4 flex items-center justify-between gap-4">
                    <div>
                        <p className="text-sm font-semibold text-gray-900">Landing no mapa</p>
                        <p className="text-xs text-gray-600">
                            Ao entrar, abrir direto o mapa em vez do dashboard.
                        </p>
                    </div>
                    <button
                        type="button"
                        role="switch"
                        aria-checked={landingPreference === 'map'}
                        onClick={() => {
                            const userId = useUserStore.getState().user?.id
                            if (!userId) return
                            const next = landingPreference === 'map' ? 'dashboard' : 'map'
                            setLandingPreference(userId, next)
                            setLandingPreferenceState(next)
                        }}
                        className={`relative inline-flex min-h-touch min-w-touch h-7 w-12 items-center rounded-full transition-colors ${
                            landingPreference === 'map' ? 'bg-green-600' : 'bg-gray-300'
                        }`}
                        title={landingPreference === 'map' ? 'Abrir mapa ao entrar' : 'Abrir dashboard ao entrar'}
                    >
                        <span
                            className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
                                landingPreference === 'map' ? 'translate-x-6' : 'translate-x-1'
                            }`}
                        />
                    </button>
                </div>
            </div>

            <div className="rounded-lg bg-white shadow">
                <div className="border-b border-gray-200 px-4 py-3">
                    <h3 className="text-sm font-semibold text-gray-900">Membros</h3>
                </div>
                {members.length === 0 ? (
                    <div className="p-6 text-sm text-gray-500">Nenhum membro encontrado.</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                                <tr>
                                    <th className="px-4 py-3 text-left">Nome</th>
                                    <th className="px-4 py-3 text-left">Email</th>
                                    <th className="px-4 py-3 text-left">Role</th>
                                    <th className="px-4 py-3 text-left">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {members.map((member) => (
                                    <tr key={member.id} className="hover:bg-gray-50">
                                        <td className="px-4 py-3 text-gray-900">{member.name}</td>
                                        <td className="px-4 py-3 text-gray-600">{member.email}</td>
                                        <td className="px-4 py-3">
                                            <span className="inline-flex rounded-full bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-800">
                                                {member.role}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                                                member.status === 'ACTIVE'
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-yellow-100 text-yellow-800'
                                            }`}>
                                                {member.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {showInviteModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
                    <div className="w-full max-w-md rounded-lg bg-white p-4 sm:p-6 shadow-xl">
                        <h2 className="text-lg sm:text-xl font-bold text-gray-900">Convidar Membro</h2>
                        <form onSubmit={handleInvite} className="mt-4 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Nome</label>
                                <input
                                    type="text"
                                    autoComplete="name"
                                    required
                                    value={inviteData.name}
                                    onChange={(e) => setInviteData({ ...inviteData, name: e.target.value })}
                                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 min-h-touch"
                                    placeholder="Nome do membro"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Email</label>
                                <input
                                    type="email"
                                    inputMode="email"
                                    autoComplete="email"
                                    required
                                    value={inviteData.email}
                                    onChange={(e) => setInviteData({ ...inviteData, email: e.target.value })}
                                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 min-h-touch"
                                    placeholder="membro@empresa.com"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Role</label>
                                <select
                                    value={inviteData.role}
                                    onChange={(e) => setInviteData({ ...inviteData, role: e.target.value as InviteMemberRequest['role'] })}
                                    className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 min-h-touch"
                                >
                                    <option value="EDITOR">Editor</option>
                                    <option value="VIEWER">Viewer</option>
                                </select>
                            </div>
                            <div className="flex gap-3">
                                <button
                                    type="button"
                                    onClick={() => setShowInviteModal(false)}
                                    className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 min-h-touch"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    disabled={inviteLoading}
                                    className="flex-1 rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 min-h-touch disabled:opacity-50"
                                >
                                    {inviteLoading ? 'Enviando...' : 'Enviar convite'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </ClientLayout>
    )
}
