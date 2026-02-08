'use client'

import Link from 'next/link'
import { useEffect, useRef, useState } from 'react'
import { cn } from '../../lib/utils'
import { TrackLink } from './TrackLink'

type LandingHeaderProps = {
    displayClassName: string
}

export function LandingHeader({ displayClassName }: LandingHeaderProps) {
    const [open, setOpen] = useState(false)
    const menuRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (!open) return
        const previousOverflow = document.body.style.overflow
        document.body.style.overflow = 'hidden'
        return () => {
            document.body.style.overflow = previousOverflow
        }
    }, [open])

    useEffect(() => {
        if (!open) return
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                setOpen(false)
                return
            }
            if (event.key !== 'Tab') return
            const focusable = menuRef.current?.querySelectorAll<HTMLElement>(
                'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
            )
            if (!focusable || focusable.length === 0) return
            const first = focusable[0]
            const last = focusable[focusable.length - 1]
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault()
                last.focus()
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault()
                first.focus()
            }
        }
        document.addEventListener('keydown', handleKeyDown)
        const focusable = menuRef.current?.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )
        focusable?.[0]?.focus()
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [open])

    return (
        <header className="fixed left-4 right-4 top-4 z-50">
            <nav className="mx-auto flex max-w-7xl items-center justify-between rounded-full border border-white/10 bg-black/80 px-6 py-3 backdrop-blur-xl">
                <Link href="/" className="flex items-center gap-3 cursor-pointer">
                    <span className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 to-cyan-400 text-black">
                        <span className={cn('text-lg font-semibold', displayClassName)}>V</span>
                    </span>
                    <span className={cn('text-lg font-semibold', displayClassName)}>VivaCampo</span>
                </Link>
                <div className="hidden items-center gap-8 text-sm font-medium md:flex">
                    <a
                        href="#journey"
                        aria-label="Ir para seção Jornada"
                        className="inline-flex min-h-[44px] min-w-[44px] items-center justify-center px-3 transition-colors hover:text-cyan-300 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black/60"
                    >
                        Jornada
                    </a>
                    <a
                        href="#recursos"
                        aria-label="Ir para seção Recursos"
                        className="inline-flex min-h-[44px] min-w-[44px] items-center justify-center px-3 transition-colors hover:text-cyan-300 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black/60"
                    >
                        Recursos
                    </a>
                    <a
                        href="#planos"
                        aria-label="Ir para seção Planos"
                        className="inline-flex min-h-[44px] min-w-[44px] items-center justify-center px-3 transition-colors hover:text-cyan-300 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black/60"
                    >
                        Planos
                    </a>
                    <a
                        href="#api"
                        aria-label="Ir para seção API"
                        className="inline-flex min-h-[44px] min-w-[44px] items-center justify-center px-3 transition-colors hover:text-cyan-300 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black/60"
                    >
                        API
                    </a>
                </div>
                <div className="hidden items-center gap-4 md:flex">
                    <Link href="/login" className="inline-flex min-h-[44px] items-center justify-center px-4 text-sm font-medium transition-colors hover:text-cyan-300 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black/60">
                        Login
                    </Link>
                    <TrackLink
                        href="/signup"
                        goal="Signup Started"
                        metadata={{ placement: 'header' }}
                        className="inline-flex min-h-[44px] items-center justify-center rounded-full bg-blue-600 px-5 py-2 text-sm font-semibold transition-colors hover:bg-blue-500 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black/60"
                    >
                        Começar grátis
                    </TrackLink>
                </div>
                <button
                    className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-full border border-white/10 bg-white/5 md:hidden cursor-pointer"
                    aria-label={open ? 'Fechar menu' : 'Abrir menu'}
                    aria-expanded={open}
                    aria-controls="landing-mobile-menu"
                    type="button"
                    onClick={() => setOpen((prev) => !prev)}
                >
                    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={open ? 'M6 18L18 6M6 6l12 12' : 'M4 7h16M4 12h16M4 17h16'} />
                    </svg>
                </button>
            </nav>

            <div
                className={cn(
                    'fixed inset-0 z-40 flex flex-col bg-black/90 px-6 pb-10 pt-24 text-white transition-all duration-300 md:hidden',
                    open ? 'opacity-100' : 'pointer-events-none opacity-0',
                )}
                id="landing-mobile-menu"
                role="dialog"
                aria-modal="true"
                aria-hidden={!open}
                aria-labelledby="landing-mobile-menu-title"
                ref={menuRef}
                onClick={(event) => {
                    if (event.target === event.currentTarget) {
                        setOpen(false)
                    }
                }}
            >
                <h2 id="landing-mobile-menu-title" className="sr-only">
                    Menu de navegação
                </h2>
                <div className="flex flex-col gap-6 text-lg font-semibold">
                    <a
                        href="#journey"
                        aria-label="Ir para seção Jornada"
                        className="min-h-[44px] flex items-center cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black/80"
                        onClick={() => setOpen(false)}
                    >
                        Jornada
                    </a>
                    <a
                        href="#recursos"
                        aria-label="Ir para seção Recursos"
                        className="min-h-[44px] flex items-center cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black/80"
                        onClick={() => setOpen(false)}
                    >
                        Recursos
                    </a>
                    <a
                        href="#planos"
                        aria-label="Ir para seção Planos"
                        className="min-h-[44px] flex items-center cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black/80"
                        onClick={() => setOpen(false)}
                    >
                        Planos
                    </a>
                    <a
                        href="#api"
                        aria-label="Ir para seção API"
                        className="min-h-[44px] flex items-center cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black/80"
                        onClick={() => setOpen(false)}
                    >
                        API
                    </a>
                </div>
                <div className="mt-auto flex flex-col gap-4">
                    <Link href="/login" className="inline-flex min-h-[44px] items-center justify-center rounded-full border border-white/20 px-6 py-3 text-center font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black/80">
                        Login
                    </Link>
                    <TrackLink
                        href="/signup"
                        goal="Signup Started"
                        metadata={{ placement: 'mobile-menu' }}
                        className="inline-flex min-h-[44px] items-center justify-center rounded-full bg-blue-600 px-6 py-3 text-center font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black/80"
                    >
                        Começar grátis
                    </TrackLink>
                </div>
            </div>
        </header>
    )
}
