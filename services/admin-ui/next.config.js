/** @type {import('next').NextConfig} */
const nextConfig = {
    basePath: '/admin',
    output: 'standalone',
    reactStrictMode: true,
    env: {
        NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000',
    },
    async headers() {
        return [
            {
                // Apply security headers to all routes
                source: '/:path*',
                headers: [
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
}

module.exports = nextConfig
