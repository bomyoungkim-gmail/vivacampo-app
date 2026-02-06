'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
    LayoutDashboard,
    Users,
    Activity,
    FileText,
    ChevronLeft,
    ChevronRight,
    LogOut,
    Settings
} from 'lucide-react'

const navItems = [
    { href: '/dashboard', label: 'Visão Geral', icon: LayoutDashboard },
    { href: '/tenants', label: 'Tenants', icon: Users },
    { href: '/jobs', label: 'Jobs & Filas', icon: Activity },
    { href: '/missing-weeks', label: 'Buracos', icon: Settings },
    { href: '/audit', label: 'Auditoria', icon: FileText },
]

export function AdminSidebar() {
    const [collapsed, setCollapsed] = useState(false)
    const pathname = usePathname()

    return (
        <aside
            className={`
        relative flex flex-col border-r transition-all duration-300 ease-in-out
        ${collapsed ? 'w-20' : 'w-72'}
        bg-background/80 backdrop-blur-md border-border shadow-lg
        h-screen sticky top-0
      `}
        >
            {/* Header / Logo */}
            <div className="flex items-center h-20 px-6 border-b border-border">
                <div className={`
          flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 text-white font-bold text-lg shadow-md
          ${collapsed ? 'mx-auto' : 'mr-3'}
        `}>
                    V
                </div>
                {!collapsed && (
                    <span className="font-bold text-foreground text-lg tracking-tight animate-fade-in-up">
                        VivaCampo <span className="text-primary font-medium text-sm">Admin</span>
                    </span>
                )}
            </div>

            {/* Navigation */}
            <nav className="flex-1 py-6 px-3 space-y-1">
                {navItems.map((item) => {
                    const isActive = pathname.startsWith(item.href)
                    const Icon = item.icon

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`
                flex items-center px-3 py-3 rounded-xl transition-all duration-200 group
                ${isActive
                                    ? 'bg-primary/10 text-primary font-medium shadow-sm ring-1 ring-primary/20'
                                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                                }
                ${collapsed ? 'justify-center' : ''}
              `}
                            title={collapsed ? item.label : undefined}
                        >
                            <Icon className={`
                w-5 h-5 transition-colors
                ${isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}
                ${collapsed ? '' : 'mr-3'}
              `} />

                            {!collapsed && (
                                <span>{item.label}</span>
                            )}
                        </Link>
                    )
                })}
            </nav>

            {/* Footer / Toggle */}
            <div className="p-4 border-t border-border">
                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="flex items-center justify-center w-full p-2 text-muted-foreground hover:bg-muted rounded-lg transition-colors mb-4"
                >
                    {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
                </button>

                <div className={`flex items-center ${collapsed ? 'justify-center' : 'px-2'}`}>
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center text-white font-medium text-xs shadow-md">
                        AD
                    </div>
                    {!collapsed && (
                        <div className="ml-3 overflow-hidden">
                            <p className="text-sm font-medium text-foreground truncate">Administrator</p>
                            <p className="text-xs text-muted-foreground truncate">admin@vivacampo.com</p>
                        </div>
                    )}
                    {!collapsed && (
                        <button
                            onClick={() => {
                                localStorage.removeItem('admin_token')
                                window.location.href = '/login'
                            }}
                            className="ml-auto text-muted-foreground hover:text-destructive transition-colors cursor-pointer"
                            aria-label="Logout"
                        >
                            <LogOut className="w-4 h-4" />
                        </button>
                    )}
                </div>
            </div>
        </aside>
    )
}
