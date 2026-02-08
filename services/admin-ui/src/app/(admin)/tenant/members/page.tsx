'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import { AdminAuthGate } from '@/components/AdminAuthGate'
import { Badge, Button, DataTable, Input, Select, type Column } from '@/components/ui'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

type Role = 'TENANT_ADMIN' | 'EDITOR' | 'VIEWER'
type Status = 'ACTIVE' | 'SUSPENDED'

interface Member {
    id: string
    identity_id: string
    email: string
    name: string
    role: Role
    status: Status
    created_at: string
}

interface TenantSettings {
    tier: string
    min_valid_pixel_ratio: number
    alert_thresholds: Record<string, unknown>
}

function TenantMembersContent({ token }: { token: string }) {
    const [members, setMembers] = useState<Member[]>([])
    const [settings, setSettings] = useState<TenantSettings | null>(null)
    const [loadingMembers, setLoadingMembers] = useState(true)
    const [loadingSettings, setLoadingSettings] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [roleDrafts, setRoleDrafts] = useState<Record<string, Role>>({})
    const [statusDrafts, setStatusDrafts] = useState<Record<string, Status>>({})
    const [updatingId, setUpdatingId] = useState<string | null>(null)
    const [inviteLoading, setInviteLoading] = useState(false)
    const [settingsLoading, setSettingsLoading] = useState(false)

    const [inviteForm, setInviteForm] = useState({
        name: '',
        email: '',
        role: 'EDITOR' as Role,
    })

    const [settingsForm, setSettingsForm] = useState({
        min_valid_pixel_ratio: '',
        alert_thresholds: '',
    })

    useEffect(() => {
        loadMembers(token)
        loadSettings(token)
    }, [token])

    const loadMembers = async (authToken: string) => {
        try {
            setLoadingMembers(true)
            const response = await axios.get(`${API_BASE}/v1/app/admin/tenant/members`, {
                headers: { Authorization: `Bearer ${authToken}` },
            })
            setMembers(response.data || [])
        } catch (err) {
            console.error('Failed to load members:', err)
            setError('Falha ao carregar membros.')
        } finally {
            setLoadingMembers(false)
        }
    }

    const loadSettings = async (authToken: string) => {
        try {
            setLoadingSettings(true)
            const response = await axios.get(`${API_BASE}/v1/app/admin/tenant/settings`, {
                headers: { Authorization: `Bearer ${authToken}` },
            })
            setSettings(response.data)
            setSettingsForm({
                min_valid_pixel_ratio: String(response.data?.min_valid_pixel_ratio ?? ''),
                alert_thresholds: response.data?.alert_thresholds
                    ? JSON.stringify(response.data.alert_thresholds)
                    : '',
            })
        } catch (err) {
            console.error('Failed to load tenant settings:', err)
            setError('Falha ao carregar configuracoes do tenant.')
        } finally {
            setLoadingSettings(false)
        }
    }

    const handleInvite = async () => {
        try {
            setInviteLoading(true)
            setError(null)
            await axios.post(
                `${API_BASE}/v1/app/admin/tenant/members/invite`,
                inviteForm,
                { headers: { Authorization: `Bearer ${token}` } }
            )
            setInviteForm({ name: '', email: '', role: 'EDITOR' })
            loadMembers(token)
        } catch (err) {
            console.error('Failed to invite member:', err)
            setError('Falha ao convidar membro.')
        } finally {
            setInviteLoading(false)
        }
    }

    const handleRoleSave = async (membershipId: string) => {
        const nextRole = roleDrafts[membershipId]
        if (!nextRole) return
        try {
            setUpdatingId(membershipId)
            setError(null)
            await axios.patch(
                `${API_BASE}/v1/app/admin/tenant/members/${membershipId}/role`,
                { role: nextRole },
                { headers: { Authorization: `Bearer ${token}` } }
            )
            setMembers((prev) =>
                prev.map((member) =>
                    member.id === membershipId ? { ...member, role: nextRole } : member
                )
            )
        } catch (err) {
            console.error('Failed to update role:', err)
            setError('Falha ao atualizar role.')
        } finally {
            setUpdatingId(null)
        }
    }

    const handleStatusSave = async (membershipId: string) => {
        const nextStatus = statusDrafts[membershipId]
        if (!nextStatus) return
        try {
            setUpdatingId(membershipId)
            setError(null)
            await axios.patch(
                `${API_BASE}/v1/app/admin/tenant/members/${membershipId}/status`,
                { status: nextStatus },
                { headers: { Authorization: `Bearer ${token}` } }
            )
            setMembers((prev) =>
                prev.map((member) =>
                    member.id === membershipId ? { ...member, status: nextStatus } : member
                )
            )
        } catch (err) {
            console.error('Failed to update status:', err)
            setError('Falha ao atualizar status.')
        } finally {
            setUpdatingId(null)
        }
    }

    const handleSettingsSave = async () => {
        try {
            setSettingsLoading(true)
            setError(null)
            let alertThresholdsPayload: Record<string, unknown> | undefined
            if (settingsForm.alert_thresholds.trim()) {
                alertThresholdsPayload = JSON.parse(settingsForm.alert_thresholds)
            }
            const payload: Record<string, unknown> = {}
            if (settingsForm.min_valid_pixel_ratio !== '') {
                payload.min_valid_pixel_ratio = Number(settingsForm.min_valid_pixel_ratio)
            }
            if (alertThresholdsPayload) {
                payload.alert_thresholds = alertThresholdsPayload
            }
            await axios.patch(`${API_BASE}/v1/app/admin/tenant/settings`, payload, {
                headers: { Authorization: `Bearer ${token}` },
            })
            loadSettings(token)
        } catch (err) {
            console.error('Failed to update settings:', err)
            setError('Falha ao atualizar configuracoes do tenant.')
        } finally {
            setSettingsLoading(false)
        }
    }

    const columns: Column<Member>[] = [
        {
            key: 'name',
            header: 'Nome',
            sortable: true,
            mobileLabel: 'Nome',
        },
        {
            key: 'email',
            header: 'Email',
            sortable: true,
            mobileLabel: 'Email',
        },
        {
            key: 'role',
            header: 'Role',
            accessor: (row) => (
                <div className="flex items-center gap-2">
                    <Badge variant="info">{row.role}</Badge>
                    <Select
                        aria-label={`Atualizar role de ${row.name}`}
                        value={roleDrafts[row.id] ?? row.role}
                        onChange={(e) => setRoleDrafts((prev) => ({ ...prev, [row.id]: e.target.value as Role }))}
                        options={[
                            { value: 'TENANT_ADMIN', label: 'TENANT_ADMIN' },
                            { value: 'EDITOR', label: 'EDITOR' },
                            { value: 'VIEWER', label: 'VIEWER' },
                        ]}
                        className="min-w-[150px]"
                    />
                    <Button
                        variant="outline"
                        size="sm"
                        loading={updatingId === row.id}
                        onClick={() => handleRoleSave(row.id)}
                    >
                        Salvar
                    </Button>
                </div>
            ),
            mobileLabel: 'Role',
        },
        {
            key: 'status',
            header: 'Status',
            accessor: (row) => (
                <div className="flex items-center gap-2">
                    <Badge variant={row.status === 'ACTIVE' ? 'success' : 'warning'}>{row.status}</Badge>
                    <Select
                        aria-label={`Atualizar status de ${row.name}`}
                        value={statusDrafts[row.id] ?? row.status}
                        onChange={(e) => setStatusDrafts((prev) => ({ ...prev, [row.id]: e.target.value as Status }))}
                        options={[
                            { value: 'ACTIVE', label: 'ACTIVE' },
                            { value: 'SUSPENDED', label: 'SUSPENDED' },
                        ]}
                        className="min-w-[140px]"
                    />
                    <Button
                        variant="outline"
                        size="sm"
                        loading={updatingId === row.id}
                        onClick={() => handleStatusSave(row.id)}
                    >
                        Salvar
                    </Button>
                </div>
            ),
            mobileLabel: 'Status',
        },
        {
            key: 'created_at',
            header: 'Criado em',
            accessor: (row) => new Date(row.created_at).toLocaleDateString('pt-BR'),
            sortable: true,
            mobileLabel: 'Criado em',
        },
    ]

    return (
        <div className="mx-auto max-w-7xl space-y-8">
            <div>
                <p className="text-sm text-muted-foreground">Gerencie membros, roles e configuracoes do tenant.</p>
                <h2 className="text-2xl font-semibold text-foreground">Tenant Members</h2>
            </div>

            {error && (
                <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    {error}
                </div>
            )}

            <div className="rounded-lg border border-border bg-card p-4 space-y-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-semibold text-foreground">Membros</h3>
                        <p className="text-sm text-muted-foreground">Acesso e permissoes por usuario.</p>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => loadMembers(token)}>
                        Atualizar
                    </Button>
                </div>
                <DataTable
                    data={members}
                    columns={columns}
                    rowKey={(row) => row.id}
                    loading={loadingMembers}
                    emptyMessage="Nenhum membro encontrado"
                />
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
                <div className="rounded-lg border border-border bg-card p-4 space-y-4">
                    <div>
                        <h3 className="text-lg font-semibold text-foreground">Convidar membro</h3>
                        <p className="text-sm text-muted-foreground">Envie convite para novos usuarios.</p>
                    </div>
                    <Input
                        label="Nome"
                        value={inviteForm.name}
                        onChange={(e) => setInviteForm((prev) => ({ ...prev, name: e.target.value }))}
                        placeholder="Nome completo"
                    />
                    <Input
                        label="Email"
                        value={inviteForm.email}
                        onChange={(e) => setInviteForm((prev) => ({ ...prev, email: e.target.value }))}
                        placeholder="email@dominio.com"
                    />
                    <Select
                        label="Role"
                        value={inviteForm.role}
                        onChange={(e) => setInviteForm((prev) => ({ ...prev, role: e.target.value as Role }))}
                        options={[
                            { value: 'EDITOR', label: 'EDITOR' },
                            { value: 'VIEWER', label: 'VIEWER' },
                        ]}
                    />
                    <Button variant="primary" size="md" loading={inviteLoading} onClick={handleInvite}>
                        Enviar convite
                    </Button>
                </div>

                <div className="rounded-lg border border-border bg-card p-4 space-y-4">
                    <div>
                        <h3 className="text-lg font-semibold text-foreground">Configuracoes do tenant</h3>
                        <p className="text-sm text-muted-foreground">Limites e thresholds operacionais.</p>
                    </div>
                    <Input
                        label="Min valid pixel ratio"
                        type="number"
                        min={0}
                        max={1}
                        step="0.01"
                        value={settingsForm.min_valid_pixel_ratio}
                        onChange={(e) =>
                            setSettingsForm((prev) => ({ ...prev, min_valid_pixel_ratio: e.target.value }))
                        }
                    />
                    <Input
                        label="Alert thresholds (JSON)"
                        value={settingsForm.alert_thresholds}
                        onChange={(e) =>
                            setSettingsForm((prev) => ({ ...prev, alert_thresholds: e.target.value }))
                        }
                        placeholder='{"ndvi_drop": 0.1}'
                    />
                    <Button
                        variant="primary"
                        size="md"
                        loading={settingsLoading || loadingSettings}
                        onClick={handleSettingsSave}
                    >
                        Salvar configuracoes
                    </Button>
                </div>
            </div>
        </div>
    )
}

export default function TenantMembersPage() {
    return (
        <AdminAuthGate>
            {(token) => <TenantMembersContent token={token} />}
        </AdminAuthGate>
    )
}
