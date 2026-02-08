'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import useUserStore from '@/stores/useUserStore'
import { setAuthCookie } from '@/app/actions/auth'
import { getLandingRoute, routes } from '@/lib/navigation'
import { APP_CONFIG } from '@/lib/config'
import { getLandingPreference } from '@/lib/landingPreference'

export default function LoginPage() {
    const router = useRouter()
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        try {
            const response = await axios.post(`${APP_CONFIG.API_BASE_URL}/v1/auth/login`, {
                email,
                password,
            })

            const token = response.data?.access_token
            if (!token) {
                throw new Error('API response missing access_token')
            }

            useUserStore.getState().actions.login(response.data.identity, token)
            await setAuthCookie(token)
            const preference = getLandingPreference(response.data.identity?.id)
            router.push(getLandingRoute(preference))
        } catch (err: any) {
            const apiMessage =
                err.response?.data?.error?.message ||
                err.response?.data?.detail ||
                'Erro ao fazer login.'
            setError(apiMessage)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-green-50 to-blue-50">
            <main className="w-full max-w-md">
                <div className="rounded-2xl bg-white p-8 shadow-xl">
                    <div className="mb-8 text-center">
                        <div className="mb-2 inline-flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-green-500 to-blue-600">
                            <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <h1 className="text-3xl font-bold text-gray-900">VivaCampo</h1>
                        <p className="mt-2 text-sm text-gray-700">Monitoramento Agrícola via Satélite</p>
                    </div>

                    <form onSubmit={handleLogin} className="space-y-6">
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                                Email
                            </label>
                            <input
                                id="email"
                                type="email"
                                inputMode="email"
                                autoComplete="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-green-500 focus:outline-none focus:ring-green-500"
                                placeholder="seu@email.com"
                            />
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                                Senha
                            </label>
                            <input
                                id="password"
                                type="password"
                                autoComplete="current-password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-green-500 focus:outline-none focus:ring-green-500"
                                placeholder="••••••••"
                            />
                        </div>

                        {error && (
                            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600 break-words">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-lg bg-gradient-to-r from-green-500 to-blue-600 px-4 py-3 font-semibold text-white shadow-lg transition-all hover:from-green-600 hover:to-blue-700 disabled:opacity-50"
                        >
                            {loading ? 'Entrando...' : 'Entrar'}
                        </button>
                    </form>

                    <div className="mt-6 flex items-center justify-between text-sm text-gray-700">
                        <Link href="/forgot-password" className="inline-flex min-h-touch items-center hover:text-gray-900 underline underline-offset-2">
                            Esqueceu a senha?
                        </Link>
                        <Link href="/signup" className="inline-flex min-h-touch items-center font-semibold text-green-700 hover:text-green-800 underline underline-offset-2">
                            Criar conta
                        </Link>
                    </div>
                </div>

                <footer className="mt-8 text-center text-sm text-gray-700">
                    © 2026 VivaCampo. Todos os direitos reservados.
                </footer>
            </main>
        </div>
    )
}
