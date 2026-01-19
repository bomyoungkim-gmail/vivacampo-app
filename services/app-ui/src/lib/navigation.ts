/**
 * Navigation Helper
 *
 * Centraliza todas as rotas da aplicação.
 *
 * IMPORTANTE: Não inclui basePath aqui porque o Next.js adiciona automaticamente
 * o basePath configurado em next.config.js a todas as rotas.
 */

/**
 * Rotas da aplicação (sem basePath - Next.js adiciona automaticamente)
 */
export const routes = {
    home: '/',
    login: '/login',
    dashboard: '/dashboard',
    farms: '/farms',
    signals: '/signals',
    aiAssistant: '/ai-assistant',
} as const

/**
 * Type-safe navigation helper
 */
export type RouteKey = keyof typeof routes

/**
 * Get route by key
 */
export function getRoute(key: RouteKey): string {
    return routes[key]
}

/**
 * Build farm detail route
 */
export function farmDetailRoute(farmId: string): string {
    return `/farms/${farmId}`
}
