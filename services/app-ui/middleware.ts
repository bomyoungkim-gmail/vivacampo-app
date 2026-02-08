import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const publicRoutes = [
    '/',
    '/login',
    '/signup',
    '/forgot-password',
    '/reset-password',
    '/terms',
    '/privacy',
    '/contact',
]

const roleProtectedRoutes: Record<string, string[]> = {
    '/admin': ['system_admin'],
    '/settings': ['tenant_admin', 'system_admin'],
}

function decodeRole(token: string | undefined): string | null {
    if (!token) return null
    try {
        const payload = token.split('.')[1]
        const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
        const decoded = JSON.parse(atob(base64))
        return decoded.role || null
    } catch {
        return null
    }
}

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl
    const authToken = request.cookies.get('access_token')?.value

    const isPublicRoute = publicRoutes.some(route =>
        pathname === route || pathname.startsWith(`${route}/`)
    )

    if (!isPublicRoute && !authToken) {
        const loginUrl = new URL('/login', request.url)
        loginUrl.searchParams.set('redirect', pathname)
        return NextResponse.redirect(loginUrl)
    }

    if ((pathname.startsWith('/login') || pathname.startsWith('/signup')) && authToken) {
        return NextResponse.redirect(new URL('/dashboard', request.url))
    }

    const role = decodeRole(authToken)
    for (const [prefix, allowedRoles] of Object.entries(roleProtectedRoutes)) {
        if (pathname.startsWith(prefix)) {
            if (!role || !allowedRoles.includes(role)) {
                return NextResponse.redirect(new URL('/dashboard', request.url))
            }
        }
    }

    const response = NextResponse.next()
    response.headers.set('X-Content-Type-Options', 'nosniff')
    response.headers.set('X-Frame-Options', 'DENY')
    response.headers.set('X-XSS-Protection', '1; mode=block')
    response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')

    const csp = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
        "style-src 'self' 'unsafe-inline' https://unpkg.com",
        "img-src 'self' data: https: blob:",
        "worker-src 'self' blob:",
        "font-src 'self' data:",
        "connect-src 'self' http://localhost:8000 https://unpkg.com https://cdn.jsdelivr.net",
        "frame-ancestors 'none'",
    ].join('; ')
    response.headers.set('Content-Security-Policy', csp)

    return response
}

export const config = {
    matcher: [
        '/((?!_next/static|_next/image|favicon.ico|.*\\..*|api).*)',
    ],
}
