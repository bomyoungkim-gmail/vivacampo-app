import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Routes that require authentication
const protectedRoutes = [
    '/dashboard',
    '/farms',
    '/signals',
    '/ai-assistant'
]

// Routes that should redirect to dashboard if already authenticated
const authRoutes = ['/login']

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl
    const authToken = request.cookies.get('auth_token')?.value

    // Check if the route requires authentication
    const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route))
    const isAuthRoute = authRoutes.some(route => pathname.startsWith(route))

    // Redirect to login if accessing protected route without token
    if (isProtectedRoute && !authToken) {
        // console.log('[Middleware] REDIRECTING TO LOGIN (Protected route, no token)')
        const loginUrl = new URL('/app/login', request.url)
        loginUrl.searchParams.set('redirect', pathname)
        return NextResponse.redirect(loginUrl)
    }

    // Redirect to dashboard if accessing login with valid token
    if (isAuthRoute && authToken) {
        // console.log('[Middleware] REDIRECTING TO DASHBOARD (Auth route, token found)')
        return NextResponse.redirect(new URL('/app/dashboard', request.url))
    }

    // Add security headers to all responses
    const response = NextResponse.next()

    // Security headers
    response.headers.set('X-Content-Type-Options', 'nosniff')
    response.headers.set('X-Frame-Options', 'DENY')
    response.headers.set('X-XSS-Protection', '1; mode=block')
    response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')

    // Content Security Policy
    const csp = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
        "style-src 'self' 'unsafe-inline' https://unpkg.com",
        "img-src 'self' data: https: blob:",
        "font-src 'self' data:",
        "connect-src 'self' http://localhost:8000 https://unpkg.com",
        "frame-ancestors 'none'"
    ].join('; ')
    response.headers.set('Content-Security-Policy', csp)

    return response
}

export const config = {
    matcher: [
        /*
         * Match all request paths except:
         * - _next/static (static files)
         * - _next/image (image optimization)
         * - favicon.ico (favicon file)
         * - public files (public directory)
         */
        '/((?!_next/static|_next/image|favicon.ico|.*\\..*|api).*)',
    ],
}
