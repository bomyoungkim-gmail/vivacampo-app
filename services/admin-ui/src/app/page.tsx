'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function AdminHome() {
    const router = useRouter()

    useEffect(() => {
        // Check if admin is authenticated
        const token = localStorage.getItem('admin_token')
        if (token) {
            router.push('/admin/dashboard')
        } else {
            router.push('/admin/login')
        }
    }, [router])

    return (
        <div className="flex min-h-screen items-center justify-center">
            <div className="text-center">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
                <p className="mt-2 text-gray-600">Carregando...</p>
            </div>
        </div>
    )
}
