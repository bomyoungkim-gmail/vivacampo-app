'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import useUserStore from '@/stores/useUserStore'
import { setAuthCookie } from '@/app/actions/auth'
import { getLandingRoute, routes } from '@/lib/navigation'
import { APP_CONFIG } from '@/lib/config'
import { trackGoal } from '@/lib/analytics'
import { getLandingPreference } from '@/lib/landingPreference'

export default function SignupPage() {
    const router = useRouter()
    const [fullName, setFullName] = useState('')
    const [companyName, setCompanyName] = useState('')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        try {
            const response = await axios.post(`${APP_CONFIG.API_BASE_URL}/v1/auth/signup`, {
                email,
                password,
                full_name: fullName,
                company_name: companyName || null,
            })

            const token = response.data?.access_token
            if (!token) {
                throw new Error('API response missing access_token')
            }

            useUserStore.getState().actions.login(response.data.identity, token)
            await setAuthCookie(token)
            trackGoal('Signup Completed')
            const preference = getLandingPreference(response.data.identity?.id)
            router.push(getLandingRoute(preference))
        } catch (err: any) {
            const apiMessage =
                err.response?.data?.error?.message ||
                err.response?.data?.detail ||
                'Erro ao criar conta.'
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
                        <h1 className="text-3xl font-bold text-gray-900">Criar conta</h1>
                        <p className="mt-2 text-sm text-gray-700">Comece a monitorar suas lavouras</p>
                    </div>

                    <form onSubmit={handleSignup} className="space-y-6">
                        <div>
                            <label htmlFor="fullName" className="block text-sm font-medium text-gray-700">
                                Nome completo
                            </label>
                            <input
                                id="fullName"
                                type="text"
                                autoComplete="name"
                                required
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-green-500 focus:outline-none focus:ring-green-500"
                                placeholder="Seu nome"
                            />
                        </div>

                        <div>
                            <label htmlFor="companyName" className="block text-sm font-medium text-gray-700">
                                Fazenda/Empresa (opcional)
                            </label>
                            <input
                                id="companyName"
                                type="text"
                                autoComplete="organization"
                                value={companyName}
                                onChange={(e) => setCompanyName(e.target.value)}
                                className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-green-500 focus:outline-none focus:ring-green-500"
                                placeholder="Nome da fazenda"
                            />
                        </div>

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
                                autoComplete="new-password"
                                required
                                minLength={8}
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
                            {loading ? 'Criando...' : 'Criar conta'}
                        </button>
                    </form>

                    <div className="mt-6 text-xs text-gray-700">
                        Ao criar uma conta, você concorda com nossos{' '}
                        <Link href="/terms" className="inline-flex min-h-touch items-center text-green-700 hover:text-green-800 underline underline-offset-2">
                            Termos de Uso
                        </Link>{' '}
                        e{' '}
                        <Link href="/privacy" className="inline-flex min-h-touch items-center text-green-700 hover:text-green-800 underline underline-offset-2">
                            Política de Privacidade
                        </Link>.
                    </div>

                    <div className="mt-6 text-center text-sm text-gray-700">
                        Já tem uma conta?{' '}
                        <Link href="/login" className="inline-flex min-h-touch items-center font-semibold text-green-700 hover:text-green-800 underline underline-offset-2">
                            Fazer login
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
