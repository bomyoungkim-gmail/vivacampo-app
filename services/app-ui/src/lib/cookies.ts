/**
 * Secure Cookie Management
 *
 * This module provides utilities for working with cookies in a secure way.
 * While Next.js client-side code cannot set HttpOnly cookies,
 * this prepares the frontend for cookie-based auth when migrating to OIDC.
 *
 * NOTE: Actual secure cookies (HttpOnly, Secure, SameSite) must be set by the backend.
 * This is client-side preparation code.
 */

import { APP_CONFIG } from './config'

/**
 * Cookie options for client-side cookies
 * NOTE: These are NOT secure for tokens. Use backend HttpOnly cookies instead.
 */
export interface CookieOptions {
    path?: string
    domain?: string
    maxAge?: number
    expires?: Date
    secure?: boolean
    sameSite?: 'strict' | 'lax' | 'none'
}

/**
 * Parse document.cookie string into object
 */
export function parseCookies(): Record<string, string> {
    if (typeof document === 'undefined') {
        return {}
    }

    const cookies: Record<string, string> = {}

    document.cookie.split(';').forEach((cookie) => {
        const [name, ...rest] = cookie.split('=')
        const value = rest.join('=').trim()
        if (name) {
            cookies[name.trim()] = decodeURIComponent(value)
        }
    })

    return cookies
}

/**
 * Get a specific cookie value
 */
export function getCookie(name: string): string | null {
    const cookies = parseCookies()
    return cookies[name] || null
}

/**
 * Set a cookie (client-side only, NOT secure for tokens)
 *
 * WARNING: Do NOT use this for authentication tokens!
 * Tokens should be set via HttpOnly cookies from the backend.
 */
export function setCookie(
    name: string,
    value: string,
    options: CookieOptions = {}
): void {
    if (typeof document === 'undefined') {
        return
    }

    let cookieString = `${encodeURIComponent(name)}=${encodeURIComponent(value)}`

    if (options.path) {
        cookieString += `; path=${options.path}`
    } else {
        cookieString += `; path=/`
    }

    if (options.domain) {
        cookieString += `; domain=${options.domain}`
    }

    if (options.maxAge !== undefined) {
        cookieString += `; max-age=${options.maxAge}`
    }

    if (options.expires) {
        cookieString += `; expires=${options.expires.toUTCString()}`
    }

    if (options.secure || APP_CONFIG.IS_PRODUCTION) {
        cookieString += `; secure`
    }

    if (options.sameSite) {
        cookieString += `; samesite=${options.sameSite}`
    } else {
        cookieString += `; samesite=lax`
    }

    document.cookie = cookieString
}

/**
 * Delete a cookie
 */
export function deleteCookie(name: string, options: Pick<CookieOptions, 'path' | 'domain'> = {}): void {
    setCookie(name, '', {
        ...options,
        maxAge: -1,
        expires: new Date(0),
    })
}

/**
 * Check if a cookie exists
 */
export function hasCookie(name: string): boolean {
    return getCookie(name) !== null
}

/**
 * Get all cookies
 */
export function getAllCookies(): Record<string, string> {
    return parseCookies()
}

/**
 * Clear all client-side cookies
 *
 * NOTE: This cannot clear HttpOnly cookies (which is good for security)
 */
export function clearAllCookies(): void {
    const cookies = parseCookies()

    Object.keys(cookies).forEach((name) => {
        deleteCookie(name)
    })
}

/**
 * Utility to check if cookies are enabled in the browser
 */
export function areCookiesEnabled(): boolean {
    if (typeof document === 'undefined') {
        return false
    }

    try {
        // Try to set a test cookie
        const testCookie = '__cookie_test__'
        setCookie(testCookie, 'test', { maxAge: 1 })
        const enabled = hasCookie(testCookie)
        deleteCookie(testCookie)
        return enabled
    } catch {
        return false
    }
}

/**
 * FUTURE: When migrating to OIDC with backend cookie auth,
 * the auth token will be in an HttpOnly cookie that JavaScript cannot access.
 * This is the CORRECT and SECURE approach.
 *
 * Example backend response (FastAPI):
 * ```python
 * response.set_cookie(
 *     key="auth_token",
 *     value=token,
 *     httponly=True,      # JavaScript cannot access
 *     secure=True,        # HTTPS only
 *     samesite="strict",  # CSRF protection
 *     max_age=3600        # 1 hour
 * )
 * ```
 *
 * On the frontend, you won't need to manually handle tokens.
 * The browser will automatically send the cookie with each request.
 */
