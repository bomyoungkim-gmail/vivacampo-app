'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Command, Search } from 'lucide-react'
import { Button } from '@/components/ui'

type ActionItem = {
    id: string
    title: string
    description?: string
    href: string
    keywords?: string[]
}

const ACTIONS: ActionItem[] = [
    { id: 'dashboard', title: 'Dashboard', description: 'Visao geral do sistema', href: '/dashboard', keywords: ['home', 'overview'] },
    { id: 'tenants', title: 'Tenants', description: 'Gerenciar tenants', href: '/tenants', keywords: ['clientes', 'contas'] },
    { id: 'jobs', title: 'Jobs', description: 'Monitorar filas e jobs', href: '/jobs', keywords: ['fila', 'processamento'] },
    { id: 'missing-weeks', title: 'Buracos de Dados', description: 'Semanas faltantes', href: '/missing-weeks', keywords: ['buracos', 'semanas'] },
    { id: 'audit', title: 'Audit Log', description: 'Logs administrativos', href: '/audit', keywords: ['auditoria', 'logs'] },
    { id: 'members', title: 'Tenant Members', description: 'Membros e roles', href: '/tenant/members', keywords: ['membros', 'roles'] },
]

type CommandPaletteProps = {
    showTrigger?: boolean
}

export function CommandPalette({ showTrigger = true }: CommandPaletteProps) {
    const router = useRouter()
    const [open, setOpen] = useState(false)
    const [query, setQuery] = useState('')
    const inputRef = useRef<HTMLInputElement | null>(null)

    const filteredActions = useMemo(() => {
        const term = query.trim().toLowerCase()
        if (!term) return ACTIONS
        return ACTIONS.filter((action) => {
            const haystack = [
                action.title,
                action.description || '',
                ...(action.keywords || []),
            ].join(' ').toLowerCase()
            return haystack.includes(term)
        })
    }, [query])

    useEffect(() => {
        if (!open) return
        const handle = setTimeout(() => {
            inputRef.current?.focus()
        }, 10)
        return () => clearTimeout(handle)
    }, [open])

    useEffect(() => {
        const onKeyDown = (event: KeyboardEvent) => {
            const isMac = navigator.platform.toLowerCase().includes('mac')
            const hotkey = isMac ? event.metaKey : event.ctrlKey
            if (hotkey && event.key.toLowerCase() === 'k') {
                event.preventDefault()
                setOpen((prev) => !prev)
            }
            if (event.key === 'Escape') {
                setOpen(false)
            }
        }
        window.addEventListener('keydown', onKeyDown)
        return () => window.removeEventListener('keydown', onKeyDown)
    }, [])

    const handleSelect = (action: ActionItem) => {
        setOpen(false)
        setQuery('')
        router.push(action.href)
    }

    return (
        <>
            {showTrigger && (
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setOpen(true)}
                    className="gap-2"
                >
                    <Command className="h-4 w-4" />
                    <span className="hidden sm:inline">Comandos</span>
                    <span className="rounded border border-border px-2 py-0.5 text-[10px] text-muted-foreground">
                        ⌘K
                    </span>
                </Button>
            )}

            {open && (
                <div className="fixed inset-0 z-[var(--z-modal)]">
                    <button
                        aria-label="Fechar comando"
                        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
                        onClick={() => setOpen(false)}
                    />
                    <div className="relative mx-auto mt-24 w-full max-w-xl rounded-xl border border-border bg-card shadow-2xl">
                        <div className="flex items-center gap-2 border-b border-border px-4 py-3">
                            <Search className="h-4 w-4 text-muted-foreground" />
                            <input
                                ref={inputRef}
                                value={query}
                                onChange={(event) => setQuery(event.target.value)}
                                placeholder="Buscar comando..."
                                className="w-full bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
                            />
                        </div>
                        <div className="max-h-[320px] overflow-auto p-2">
                            {filteredActions.length ? (
                                filteredActions.map((action) => (
                                    <button
                                        key={action.id}
                                        onClick={() => handleSelect(action)}
                                        className="flex w-full items-start justify-between gap-4 rounded-lg px-3 py-2 text-left transition-colors hover:bg-muted"
                                    >
                                        <div>
                                            <p className="text-sm font-medium text-foreground">{action.title}</p>
                                            {action.description && (
                                                <p className="text-xs text-muted-foreground">{action.description}</p>
                                            )}
                                        </div>
                                        <span className="text-xs text-muted-foreground">{action.href}</span>
                                    </button>
                                ))
                            ) : (
                                <div className="px-3 py-6 text-sm text-muted-foreground">
                                    Nenhum comando encontrado.
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}
