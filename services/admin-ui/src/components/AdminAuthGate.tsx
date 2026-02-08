'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { LoadingSpinner } from '@/components/ui'

const DEFAULT_REDIRECT = '/login?reason=signin_required'
const UNAUTHORIZED_REDIRECT = '/login?reason=unauthorized'

type AdminRole = 'SYSTEM_ADMIN' | 'TENANT_ADMIN' | 'EDITOR' | 'VIEWER'

type AdminAuthGateProps = {
    children: (token: string) => React.ReactNode
    redirectTo?: string
    requiredRole?: AdminRole | AdminRole[]
}

function hasRequiredRole(requiredRole: AdminRole | AdminRole[] | undefined, role: string | null) {
    if (!requiredRole) return true
    if (!role) return false
    if (Array.isArray(requiredRole)) {
        return requiredRole.includes(role as AdminRole)
    }
    return role === requiredRole
}

export function AdminAuthGate({ children, redirectTo, requiredRole }: AdminAuthGateProps) {
    const router = useRouter()
    const [token, setToken] = useState<string | null>(null)
    const [checking, setChecking] = useState(true)

    useEffect(() => {
        const storedToken = localStorage.getItem('admin_token')
        if (!storedToken) {
            router.replace(redirectTo || DEFAULT_REDIRECT)
            return
        }

        const storedRole = localStorage.getItem('admin_role')
        if (!hasRequiredRole(requiredRole, storedRole)) {
            router.replace(UNAUTHORIZED_REDIRECT)
            return
        }

        setToken(storedToken)
        setChecking(false)
    }, [redirectTo, requiredRole, router])

    if (checking || !token) {
        return (
            <div className="flex min-h-[50vh] items-center justify-center bg-background">
                <LoadingSpinner size="lg" label="Verificando acesso..." />
            </div>
        )
    }

    return <>{children(token)}</>
}
