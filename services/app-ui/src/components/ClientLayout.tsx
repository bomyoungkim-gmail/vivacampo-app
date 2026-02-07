'use client'

import { ReactNode } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuthProtection, useAuthRole, logout } from '@/lib/auth'
import { routes } from '@/lib/navigation'
import MobileNav from './MobileNav'
import ThemeToggle from './ThemeToggle'

interface ClientLayoutProps {
    children: ReactNode
}

export default function ClientLayout({ children }: ClientLayoutProps) {
    const pathname = usePathname()
    const { user } = useAuthProtection()
    const role = useAuthRole()
    const canAccessSettings = role === 'tenant_admin' || role === 'system_admin'

    const handleLogout = () => {
        logout()
    }

    const navItems = [
        { href: routes.dashboard, label: 'Dashboard' },
        { href: routes.farms, label: 'Fazendas' },
        { href: routes.signals, label: 'Sinais' },
        { href: routes.vision, label: 'Visão IA' },
        { href: routes.aiAssistant, label: 'AI Assistant' },
        ...(canAccessSettings ? [{ href: routes.settings, label: 'Configurações' }] : []),
    ]

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-16 lg:pb-0 transition-colors">
            {/* Header */}
            <header className="bg-white dark:bg-gray-800 shadow dark:shadow-gray-700/50 transition-colors">
                <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8 lg:py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3 sm:space-x-4">
                            <div className="flex h-8 w-8 sm:h-10 sm:w-10 items-center justify-center rounded-full bg-gradient-to-br from-green-500 to-blue-600">
                                <svg className="h-5 w-5 sm:h-6 sm:w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <h1 className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white">VivaCampo</h1>
                        </div>
                        <div className="flex items-center gap-2 sm:gap-4">
                            <span className="hidden sm:inline text-xs sm:text-sm text-gray-600 dark:text-gray-300 truncate max-w-[150px]">{user?.email}</span>
                            <ThemeToggle />
                            <button
                                onClick={handleLogout}
                                className="rounded-md bg-gray-200 dark:bg-gray-700 px-3 py-2 sm:px-4 text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 min-h-touch min-w-touch transition-colors"
                            >
                                Sair
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Desktop Navigation */}
            <nav className="hidden lg:block bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 transition-colors">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="flex overflow-x-auto scrollbar-hide space-x-8">
                        {navItems.map((item) => {
                            const isActive = pathname === item.href || (item.href !== routes.dashboard && pathname.startsWith(item.href))
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={`border-b-2 whitespace-nowrap px-1 py-4 text-sm font-medium transition-colors ${isActive
                                            ? 'border-green-600 text-green-600 dark:text-green-400'
                                            : 'border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-200'
                                        }`}
                                >
                                    {item.label}
                                </Link>
                            )
                        })}
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="mx-auto max-w-7xl px-4 py-4 sm:py-8 sm:px-6 lg:px-8">
                {children}
            </main>

            {/* Mobile Navigation */}
            <MobileNav />
        </div>
    )
}
