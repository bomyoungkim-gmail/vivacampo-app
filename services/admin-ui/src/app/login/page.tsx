'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2, ShieldCheck } from 'lucide-react'

export default function AdminLoginPage() {
    const router = useRouter()
    const [token, setToken] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        await new Promise(resolve => setTimeout(resolve, 800)) // Fake delay for UX feel

        if (token.length > 5) {
            localStorage.setItem('admin_token', token)
            router.push('/dashboard')
        } else {
            setError('Credenciais inválidas. Verifique seu token.')
            setLoading(false)
        }
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-100 via-slate-100 to-emerald-50 relative overflow-hidden">
            {/* Animated Background Elements */}
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-emerald-400/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 animate-pulse" />
            <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-indigo-400/20 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2 animate-pulse delay-700" />

            <div className="w-full max-w-md relative z-10 p-4">
                <div className="glass-card rounded-2xl p-10 shadow-2xl animate-scale-in">
                    {/* Header */}
                    <div className="mb-10 text-center">
                        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg shadow-emerald-500/30">
                            <ShieldCheck className="h-8 w-8 text-white" />
                        </div>
                        <h1 className="text-3xl font-bold tracking-tight text-slate-800">
                            Portal Admin
                        </h1>
                        <p className="mt-2 text-sm text-slate-500 font-medium">
                            Acesso seguro ao gerenciamento do VivaCampo
                        </p>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleLogin} className="space-y-6">
                        <div className="relative group">
                            <input
                                id="token"
                                type="password"
                                required
                                value={token}
                                onChange={(e) => setToken(e.target.value)}
                                className="peer block w-full rounded-xl border-gray-200 bg-white/50 px-4 py-3.5 text-slate-900 shadow-sm ring-1 ring-inset ring-gray-200 placeholder:text-transparent focus:ring-2 focus:ring-inset focus:ring-emerald-500 sm:text-sm sm:leading-6 transition-all duration-200 hover:bg-white"
                                placeholder="Token de Acesso"
                            />
                            <label
                                htmlFor="token"
                                className="absolute left-4 top-0 -translate-y-1/2 bg-transparent px-1 text-xs font-medium text-gray-500 transition-all duration-200 peer-placeholder-shown:top-3.5 peer-placeholder-shown:text-base peer-focus:top-0 peer-focus:text-xs peer-focus:text-emerald-600"
                            >
                                Token de Acesso
                            </label>
                        </div>

                        {error && (
                            <div className="rounded-lg bg-red-50/80 p-3 text-sm text-red-600 border border-red-100 flex items-center animate-fade-in-up">
                                <span className="mr-2">⚠️</span> {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className={`
                                w-full rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-3.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 
                                transition-all duration-300 hover:scale-[1.02] hover:shadow-emerald-500/50 hover:from-emerald-500 hover:to-teal-500
                                disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:scale-100
                                flex items-center justify-center
                            `}
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Autenticando...
                                </>
                            ) : (
                                'Entrar no Sistema'
                            )}
                        </button>
                    </form>

                    {/* Footer */}
                    <div className="mt-8 text-center">
                        <p className="text-xs text-slate-400">
                            Ambiente Protegido &bull; VivaCampo v1.0
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

