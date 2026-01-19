'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { routes } from '@/lib/navigation'

export default function MobileNav() {
    const pathname = usePathname()

    const navItems = [
        {
            href: routes.dashboard,
            label: 'Dashboard',
            icon: (active: boolean) => (
                <svg className={`h-6 w-6 ${active ? 'text-green-600' : 'text-gray-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
            )
        },
        {
            href: routes.farms,
            label: 'Fazendas',
            icon: (active: boolean) => (
                <svg className={`h-6 w-6 ${active ? 'text-green-600' : 'text-gray-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            )
        },
        {
            href: routes.signals,
            label: 'Sinais',
            icon: (active: boolean) => (
                <svg className={`h-6 w-6 ${active ? 'text-green-600' : 'text-gray-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
            )
        },
        {
            href: routes.aiAssistant,
            label: 'IA',
            icon: (active: boolean) => (
                <svg className={`h-6 w-6 ${active ? 'text-green-600' : 'text-gray-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
            )
        },
    ]

    return (
        <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 lg:hidden z-50 safe-area-inset-bottom">
            <div className="grid grid-cols-4 gap-1">
                {navItems.map((item) => {
                    const isActive = pathname === item.href || (item.href !== routes.dashboard && pathname.startsWith(item.href))

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex flex-col items-center justify-center py-2 px-1 min-h-touch transition-colors ${
                                isActive ? 'text-green-600' : 'text-gray-600'
                            }`}
                        >
                            {item.icon(isActive)}
                            <span className={`text-xs mt-1 font-medium ${isActive ? 'text-green-600' : 'text-gray-600'}`}>
                                {item.label}
                            </span>
                        </Link>
                    )
                })}
            </div>
        </nav>
    )
}
