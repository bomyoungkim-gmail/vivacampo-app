'use client'

import { useState } from 'react'
import Link from 'next/link'
import axios from 'axios'
import { APP_CONFIG } from '@/lib/config'

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState('')
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState('')
    const [error, setError] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setMessage('')
        setError('')

        try {
            const response = await axios.post(`${APP_CONFIG.API_BASE_URL}/v1/auth/forgot-password`, {
                email,
            })
            setMessage(response.data?.message || 'Se o email existir, enviaremos instruções.')
        } catch (err: any) {
            const apiMessage =
                err.response?.data?.error?.message ||
                err.response?.data?.detail ||
                'Erro ao solicitar recuperação.'
            setError(apiMessage)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-green-50 to-blue-50">
            <div className="w-full max-w-md">
                <div className="rounded-2xl bg-white p-8 shadow-xl">
                    <div className="mb-8 text-center">
                        <h1 className="text-3xl font-bold text-gray-900">Recuperar senha</h1>
                        <p className="mt-2 text-sm text-gray-600">Enviaremos um link para redefinir sua senha</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
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

                        {error && (
                            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600 break-words">
                                {error}
                            </div>
                        )}

                        {message && (
                            <div className="rounded-lg bg-green-50 p-3 text-sm text-green-700 break-words">
                                {message}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-lg bg-gradient-to-r from-green-500 to-blue-600 px-4 py-3 font-semibold text-white shadow-lg transition-all hover:from-green-600 hover:to-blue-700 disabled:opacity-50"
                        >
                            {loading ? 'Enviando...' : 'Enviar link'}
                        </button>
                    </form>

                    <div className="mt-6 text-center text-sm text-gray-600">
                        <Link href="/login" className="inline-flex min-h-touch items-center font-semibold text-green-600 hover:text-green-700">
                            Voltar ao login
                        </Link>
                    </div>
                </div>

                <p className="mt-8 text-center text-sm text-gray-600">
                    © 2026 VivaCampo. Todos os direitos reservados.
                </p>
            </div>
        </div>
    )
}
