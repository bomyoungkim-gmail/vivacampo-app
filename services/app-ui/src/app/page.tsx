'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthToken, useHasHydrated } from '@/stores/useUserStore'
import { routes } from '@/lib/navigation'

export default function Home() {
    const router = useRouter()
    const token = useAuthToken()
    const hasHydrated = useHasHydrated()

    useEffect(() => {
        if (!hasHydrated) return

        // Check if user is authenticated and redirect accordingly
        router.push(token ? routes.dashboard : routes.login)
    }, [router, token, hasHydrated])

    return (
        <div className="flex min-h-screen items-center justify-center">
            <div className="text-center">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent"></div>
                <p className="mt-2 text-gray-600">Carregando...</p>
            </div>
        </div>
    )
}
