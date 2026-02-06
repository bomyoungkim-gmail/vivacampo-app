'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function AdminLoginPage() {
    const router = useRouter()
    const [token, setToken] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        // In production, validate token with API
        // For now, just store it
        if (token.length > 10) {
            localStorage.setItem('admin_token', token)
            router.push('/dashboard')
        } else {
            setError('Token inválido')
            setLoading(false)
        }
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
            <div className="w-full max-w-md">
                <div className="rounded-2xl bg-white p-8 shadow-xl">
                    {/* Logo */}
                    <div className="mb-8 text-center">
                        <div className="mb-2 inline-flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600">
                            <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                            </svg>
                        </div>
                        <h1 className="text-3xl font-bold text-gray-900">Admin Portal</h1>
                        <p className="mt-2 text-sm text-gray-600">VivaCampo System Administration</p>
                    </div>

                    {/* Login Form */}
                    <form onSubmit={handleLogin} className="space-y-6">
                        <div>
                            <label htmlFor="token" className="block text-sm font-medium text-gray-700">
                                System Admin Token
                            </label>
                            <input
                                id="token"
                                type="password"
                                required
                                value={token}
                                onChange={(e) => setToken(e.target.value)}
                                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
                                placeholder="Digite o token de administrador"
                            />
                        </div>

                        {error && (
                            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 px-4 py-3 font-semibold text-white shadow-lg transition-all hover:from-blue-600 hover:to-purple-700 disabled:opacity-50"
                        >
                            {loading ? 'Verificando...' : 'Acessar Admin'}
                        </button>
                    </form>

                    {/* Info */}
                    <div className="mt-6 rounded-lg bg-blue-50 p-4">
                        <p className="text-xs text-blue-800">
                            <strong>Acesso Restrito:</strong> Este portal é exclusivo para administradores do sistema. O token deve ser configurado via variáveis de ambiente.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
