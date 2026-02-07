'use server'

import { cookies } from 'next/headers'

import { APP_CONFIG } from '@/lib/config'

export async function setAuthCookie(token: string) {
    const useSecure = process.env.NODE_ENV === 'production' && !APP_CONFIG.ENABLE_MOCK_AUTH

    cookies().set('access_token', token, {
        httpOnly: true,
        secure: useSecure,
        sameSite: 'strict',
        maxAge: 60 * 60, // 1 hour
        path: '/',
    })
}

export async function clearAuthCookie() {
    cookies().delete('access_token')
}
