/** @type {import('next').NextConfig} */
const cspHeader = `
  default-src 'self';
  script-src 'self' 'unsafe-eval' 'unsafe-inline' plausible.io;
  worker-src 'self' blob:;
  style-src 'self' 'unsafe-inline' fonts.googleapis.com;
  img-src 'self' blob: data: https:;
  font-src 'self' fonts.gstatic.com;
  connect-src 'self' plausible.io https://cdn.jsdelivr.net;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
`;

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
let apiOrigin = apiBaseUrl
try {
    apiOrigin = new URL(apiBaseUrl).origin
} catch (error) {
    apiOrigin = apiBaseUrl
}

const nextConfig = {
    basePath: '',
    output: 'standalone',
    reactStrictMode: true,
    env: {
        NEXT_PUBLIC_API_BASE: apiBaseUrl,
    },
    async headers() {
        return [
            {
                // Apply security headers to all routes
                source: '/:path*',
                headers: [
                    {
                        key: 'Content-Security-Policy',
                        value: cspHeader.replace(/\n/g, ''),
                    },
                    {
                        key: 'X-DNS-Prefetch-Control',
                        value: 'on'
                    },
                    {
                        key: 'Strict-Transport-Security',
                        value: 'max-age=63072000; includeSubDomains; preload'
                    },
                    {
                        key: 'X-Content-Type-Options',
                        value: 'nosniff'
                    },
                    {
                        key: 'X-Frame-Options',
                        value: 'DENY'
                    },
                    {
                        key: 'X-XSS-Protection',
                        value: '1; mode=block'
                    },
                    {
                        key: 'Referrer-Policy',
                        value: 'strict-origin-when-cross-origin'
                    },
                    {
                        key: 'Permissions-Policy',
                        value: 'camera=(), microphone=(), geolocation=()'
                    }
                ],
            },
        ]
    },
    async rewrites() {
        return [
            {
                source: '/app/login',
                destination: '/login',
            },
            {
                source: '/app/:path*',
                destination: '/:path*',
            },
            {
                source: '/api/cog/:path*',
                destination: 'http://tiler:8080/cog/:path*',
            },
            {
                source: '/api/v1/auth/oidc/login',
                destination: 'http://api:8000/v1/auth/oidc/login',
            },
            {
                source: '/api/:path*',
                destination: 'http://api:8000/:path*',
            },
        ]
    },
}

const defaultRuntimeCaching = require('next-pwa/cache')

const geometryCacheRule = {
    urlPattern: ({ url }) => url.origin === apiOrigin && url.pathname.startsWith('/v1/app/aois'),
    handler: 'CacheFirst',
    options: {
        cacheName: 'geometry-cache',
        expiration: {
            maxEntries: 100,
            maxAgeSeconds: 60 * 60 * 24,
        },
        cacheableResponse: {
            statuses: [0, 200],
        },
    },
}

const dynamicDataRule = {
    urlPattern: ({ url }) =>
        url.origin === apiOrigin &&
        /\/v1\/app\/aois\/[^/]+\/(history|radar\/history|weather\/history|nitrogen\/status|correlation)/.test(
            url.pathname
        ),
    handler: 'NetworkFirst',
    options: {
        cacheName: 'dynamic-data-cache',
        networkTimeoutSeconds: 6,
        expiration: {
            maxEntries: 60,
            maxAgeSeconds: 60 * 60,
        },
        cacheableResponse: {
            statuses: [0, 200],
        },
    },
}

const withPWA = require('next-pwa')({
    dest: 'public',
    disable: process.env.NODE_ENV === 'development',
    register: true,
    skipWaiting: true,
    cacheId: `vivacampo-app-ui-${process.env.NEXT_PUBLIC_BUILD_ID || process.env.VERCEL_GIT_COMMIT_SHA || 'dev'}`,
    runtimeCaching: [geometryCacheRule, dynamicDataRule, ...defaultRuntimeCaching],
})

if (process.env.STORYBOOK === 'true') {
    module.exports = nextConfig
} else {
    module.exports = withPWA(nextConfig)
}
