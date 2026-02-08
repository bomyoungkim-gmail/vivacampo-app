'use client'

import { ReactNode } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuthProtection, useAuthRole, logout } from '@/lib/auth'
import { routes } from '@/lib/navigation'
import MobileNav from './MobileNav'
import ThemeToggle from './ThemeToggle'
import MapLayout from './MapLayout'
import MapComponent from './MapComponent'

interface ClientLayoutProps {
    children: ReactNode
}

export default function ClientLayout({ children }: ClientLayoutProps) {
    const pathname = usePathname()
    const { user } = useAuthProtection()
    const role = useAuthRole()
    const canAccessSettings = role === 'tenant_admin' || role === 'system_admin'
    const canAccessAnalytics = role === 'tenant_admin' || role === 'system_admin'

    const handleLogout = () => {
        logout()
    }

    const navItems = [
        { href: routes.dashboard, label: 'Dashboard' },
        { href: routes.farms, label: 'Fazendas' },
        { href: routes.signals, label: 'Sinais' },
        { href: routes.vision, label: 'Visão IA' },
        { href: routes.aiAssistant, label: 'AI Assistant' },
        ...(canAccessAnalytics ? [{ href: routes.analytics, label: 'Analytics' }] : []),
        ...(canAccessSettings ? [{ href: routes.settings, label: 'Configurações' }] : []),
    ]

    return (
        <div className="min-h-screen bg-background transition-colors">
            <MapLayout
                map={<MapComponent />}
                topLeft={
                    <div className="flex items-center gap-2 rounded-full border border-border/60 bg-background/80 px-3 py-1.5 text-sm font-semibold text-foreground shadow-sm">
                        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-green-500 to-blue-600">
                            <svg className="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        VivaCampo
                    </div>
                }
                topRight={
                    <div className="flex items-center gap-2 rounded-full border border-border/60 bg-background/80 px-2 py-1 shadow-sm">
                        <span className="hidden sm:inline text-xs text-muted-foreground max-w-[160px] truncate px-2">
                            {user?.email}
                        </span>
                        <ThemeToggle />
                        <button
                            onClick={handleLogout}
                            className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-foreground hover:bg-muted/70 min-h-touch min-w-touch transition-colors"
                        >
                            Sair
                        </button>
                    </div>
                }
            >
                <div className="flex h-full items-start justify-center p-4 sm:p-6 lg:p-8">
                    <div className="w-full max-w-5xl overflow-hidden rounded-3xl border border-border/60 bg-background/90 shadow-2xl backdrop-blur">
                        <div className="border-b border-border/60 px-4 py-3">
                            <nav className="flex flex-wrap gap-2">
                                {navItems.map((item) => {
                                    const isActive = pathname === item.href || (item.href !== routes.dashboard && pathname.startsWith(item.href))
                                    return (
                                        <Link
                                            key={item.href}
                                            href={item.href}
                                            className={`inline-flex min-h-touch min-w-touch items-center justify-center rounded-full px-4 py-2 text-xs sm:text-sm font-medium transition-colors ${isActive
                                                    ? 'bg-primary text-primary-foreground'
                                                    : 'bg-muted text-muted-foreground hover:bg-muted/70 hover:text-foreground'
                                                }`}
                                        >
                                            {item.label}
                                        </Link>
                                    )
                                })}
                            </nav>
                        </div>
                        <div className="max-h-[calc(100vh-220px)] overflow-y-auto px-4 py-4 sm:px-6 sm:py-6">
                            {children}
                        </div>
                    </div>
                </div>
                <MobileNav />
            </MapLayout>
        </div>
    )
}
