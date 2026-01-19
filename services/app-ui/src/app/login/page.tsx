'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import useUserStore from '@/stores/useUserStore'
import { setAuthCookie } from '@/app/actions/auth'
import { routes } from '@/lib/navigation'
import { APP_CONFIG } from '@/lib/config'

/**
 * SECURITY WARNING - DEVELOPMENT ONLY
 *
 * This function generates a MOCK JWT token for development purposes.
 * It creates a fake signature that bypasses real authentication.
 *
 * ⚠️ CRITICAL: This MUST be removed or disabled in production!
 *
 * For production, implement:
 * 1. Real OIDC provider integration (Google, Azure AD, Auth0, etc.)
 * 2. Proper JWT validation with secret keys
 * 3. Token signing with cryptographic algorithms
 * 4. Refresh token rotation
 *
 * Current security issues:
 * - Anyone can login with any email address
 * - No password verification
 * - Fake signature ('mock-signature')
 * - No rate limiting
 */
const generateMockToken = (email: string) => {
    // Helper to generic Base64Url encoded string
    const base64Url = (str: string) => {
        return btoa(str)
            .replace(/\+/g, '-')
            .replace(/\//g, '_')
            .replace(/=+$/, '')
    }

    // Create a mock JWT (header.payload.signature)
    const header = base64Url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
    const payload = base64Url(JSON.stringify({
        sub: 'mock-user-' + email, // Stable subject to avoid DB constraint errors
        email: email,
        name: email.split('@')[0],
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 3600
    }))
    const signature = 'mock-signature'
    return `${header}.${payload}.${signature}`
}

export default function LoginPage() {
    const router = useRouter()
    const [email, setEmail] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    // Security check on component mount
    useEffect(() => {
        // Block mock auth in production ONLY if explicitly disabled
        if (APP_CONFIG.IS_PRODUCTION && !APP_CONFIG.ENABLE_MOCK_AUTH) {
            setError(
                '🚨 Autenticação mock desabilitada. ' +
                'Configure um provedor OIDC para fazer login.'
            )
        }
    }, [])

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError('')
        console.log("LOGIN PAGE V2 - FIXED ARGS DETECTED")

        try {
            // Security check: Block mock auth if explicitly disabled
            if (!APP_CONFIG.ENABLE_MOCK_AUTH) {
                throw new Error(
                    'Mock authentication is disabled. ' +
                    'Please configure an OIDC provider.'
                )
            }

            // Mock OIDC login - generates a token that the backend accepts in local mode
            const idToken = generateMockToken(email)

            const response = await axios.post(`${APP_CONFIG.API_BASE_URL}/v1/auth/oidc/login`, {
                id_token: idToken,
                provider: 'local'
            })

            if (!response.data.access_token) {
                throw new Error('API response missing access_token')
            }

            // Store authentication data using centralized auth helper
            console.log('[Login Page] Received Token from Backend:', response.data.access_token)
            useUserStore.getState().actions.login(response.data.identity, response.data.access_token)

            // Set server-side cookie for middleware
            await setAuthCookie(response.data.access_token)

            // FALLBACK: Force cookie on client-side to ensure persistence
            // This fixes issues where Server Action Set-Cookie headers are ignored/delayed
            document.cookie = `auth_token=${response.data.access_token}; path=/; max-age=86400; SameSite=Lax`

            router.push(routes.dashboard)
        } catch (err: any) {
            console.error('Login error:', err)
            const detail = err.response?.data?.detail
            if (Array.isArray(detail)) {
                // Handle Pydantic validation errors (array of objects)
                setError(detail.map((e: any) => e.msg).join(', '))
            } else if (typeof detail === 'string') {
                setError(detail)
            } else {
                setError('Erro ao fazer login. Verifique o console.')
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-green-50 to-blue-50">
            <div className="w-full max-w-md">
                <div className="rounded-2xl bg-white p-8 shadow-xl">
                    {/* Logo */}
                    <div className="mb-8 text-center">
                        <div className="mb-2 inline-flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-green-500 to-blue-600">
                            <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <h1 className="text-3xl font-bold text-gray-900">VivaCampo</h1>
                        <p className="mt-2 text-sm text-gray-600">Monitoramento Agrícola via Satélite</p>
                    </div>

                    {/* Login Form */}
                    <form onSubmit={handleLogin} className="space-y-6">
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                                Email
                            </label>
                            <input
                                id="email"
                                type="email"
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

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-lg bg-gradient-to-r from-green-500 to-blue-600 px-4 py-3 font-semibold text-white shadow-lg transition-all hover:from-green-600 hover:to-blue-700 disabled:opacity-50"
                        >
                            {loading ? 'Entrando...' : 'Entrar com OIDC'}
                        </button>
                    </form>

                    {/* Demo Info */}
                    <div className="mt-6 rounded-lg bg-blue-50 p-4">
                        <p className="text-xs text-blue-800">
                            <strong>Demo:</strong> Use qualquer email para testar. Em produção, isso redirecionaria para o provedor OIDC configurado.
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <p className="mt-8 text-center text-sm text-gray-600">
                    © 2026 VivaCampo. Todos os direitos reservados.
                </p>
            </div>
        </div>
    )
}
