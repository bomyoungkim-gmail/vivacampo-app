'use client'

import { ReactNode } from 'react'
import ThemeToggle from '@/components/ThemeToggle'
import { AdminSidebar } from '@/components/AdminSidebar'
import { Badge } from '@/components/ui'
import { CommandPalette } from '@/components/CommandPalette'

type AdminShellProps = {
    children: ReactNode
    title?: string
}

export function AdminShell({ children, title = 'Control Tower' }: AdminShellProps) {
    return (
        <div className="min-h-screen bg-background text-foreground">
            <div className="flex">
                <AdminSidebar />
                <div className="flex min-h-screen flex-1 flex-col">
                    <header className="sticky top-0 z-[var(--z-dropdown)] border-b border-border bg-background/80 backdrop-blur">
                        <div className="flex items-center justify-between px-6 py-4">
                            <div className="flex items-center gap-3">
                                <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
                                <Badge variant="info" className="uppercase tracking-[0.12em] text-[10px]">
                                    Ops
                                </Badge>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="hidden text-xs text-muted-foreground sm:flex sm:flex-col sm:items-end">
                                    <span className="font-medium text-foreground">VivaCampo Admin</span>
                                    <span>Observabilidade Operacional</span>
                                </div>
                                <CommandPalette />
                                <ThemeToggle />
                            </div>
                        </div>
                    </header>
                    <main className="flex-1 px-6 py-6">
                        {children}
                    </main>
                </div>
            </div>
        </div>
    )
}
