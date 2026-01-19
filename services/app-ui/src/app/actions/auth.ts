'use server'

import { cookies } from 'next/headers'

import { APP_CONFIG } from '@/lib/config'

export async function setAuthCookie(token: string) {
    // Determine if we should use secure cookies
    // In Docker + Localhost, we often run as 'production' build but over HTTP
    // So we must fallback to non-secure if MOCK_AUTH is enabled or if explicitly configured
    const useSecure = process.env.NODE_ENV === 'production' && !APP_CONFIG.ENABLE_MOCK_AUTH;

    console.log(`[AuthAction] Setting cookie: Secure=${useSecure}, Mock=${APP_CONFIG.ENABLE_MOCK_AUTH}`);

    cookies().set('auth_token', token, {
        httpOnly: false, // Accessible by JS for API calls if needed
        secure: useSecure,
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: '/',
    })
}

export async function clearAuthCookie() {
    cookies().delete('auth_token')
}
