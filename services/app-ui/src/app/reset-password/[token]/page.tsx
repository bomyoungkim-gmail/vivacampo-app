'use client'

import { useState } from 'react'
import Link from 'next/link'
import axios from 'axios'
import { APP_CONFIG } from '@/lib/config'

type ResetPasswordPageProps = {
    params: { token: string }
}

export default function ResetPasswordPage({ params }: ResetPasswordPageProps) {
    const [password, setPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState('')
    const [error, setError] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setMessage('')
        setError('')

        if (password !== confirmPassword) {
            setError('As senhas não conferem.')
            setLoading(false)
            return
        }

        try {
            const response = await axios.post(`${APP_CONFIG.API_BASE_URL}/v1/auth/reset-password`, {
                token: params.token,
                new_password: password,
            })
            setMessage(response.data?.message || 'Senha atualizada com sucesso.')
        } catch (err: any) {
            const apiMessage =
                err.response?.data?.error?.message ||
                err.response?.data?.detail ||
                'Erro ao redefinir senha.'
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
                        <h1 className="text-3xl font-bold text-gray-900">Nova senha</h1>
                        <p className="mt-2 text-sm text-gray-600">Defina uma nova senha para sua conta</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                                Nova senha
                            </label>
                            <input
                                id="password"
                                type="password"
                                required
                                minLength={8}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-green-500 focus:outline-none focus:ring-green-500"
                                placeholder="••••••••"
                            />
                        </div>

                        <div>
                            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                                Confirmar senha
                            </label>
                            <input
                                id="confirmPassword"
                                type="password"
                                required
                                minLength={8}
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-green-500 focus:outline-none focus:ring-green-500"
                                placeholder="••••••••"
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
                            {loading ? 'Atualizando...' : 'Atualizar senha'}
                        </button>
                    </form>

                    <div className="mt-6 text-center text-sm text-gray-600">
                        <Link href="/login" className="font-semibold text-green-600 hover:text-green-700">
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
