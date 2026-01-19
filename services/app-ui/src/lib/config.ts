import { z } from 'zod'

/**
 * Environment Configuration Schema
 *
 * This schema validates all required environment variables at startup.
 * The application will fail fast if configuration is invalid.
 */
const envSchema = z.object({
    // API Configuration
    NEXT_PUBLIC_API_BASE: z.string().min(1, {
        message: 'NEXT_PUBLIC_API_BASE must handle relative paths for proxy'
    }),

    // Base Path Configuration
    NEXT_PUBLIC_BASE_PATH: z.string().optional().default('/app'),

    // Environment Type
    NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),

    // Feature Flags
    NEXT_PUBLIC_ENABLE_MOCK_AUTH: z
        .string()
        .default('true')
        .transform((val) => val === 'true'),
})

/**
 * Validate and parse environment variables
 * Throws error if validation fails
 */
function validateEnv() {
    const env = {
        NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000',
        NEXT_PUBLIC_BASE_PATH: process.env.NEXT_PUBLIC_BASE_PATH,
        NODE_ENV: process.env.NODE_ENV,
        NEXT_PUBLIC_ENABLE_MOCK_AUTH: process.env.NEXT_PUBLIC_ENABLE_MOCK_AUTH,
    }

    try {
        return envSchema.parse(env)
    } catch (error) {
        if (error instanceof z.ZodError) {
            const issues = error.issues.map(
                (issue) => `  - ${issue.path.join('.')}: ${issue.message}`
            ).join('\n')

            throw new Error(
                `❌ Invalid environment configuration:\n${issues}\n\n` +
                `Please check your .env file and ensure all required variables are set correctly.`
            )
        }
        throw error
    }
}

// Validate on module load
export const config = validateEnv()

/**
 * Security Checks
 */
export function performSecurityChecks() {
    const warnings: string[] = []
    const errors: string[] = []

    // CRITICAL: Mock auth must be disabled in production
    if (config.NODE_ENV === 'production' && config.NEXT_PUBLIC_ENABLE_MOCK_AUTH) {
        errors.push(
            '🚨 CRITICAL SECURITY ERROR: Mock authentication is ENABLED in production!\n' +
            '   Set NEXT_PUBLIC_ENABLE_MOCK_AUTH=false immediately.\n' +
            '   Current value: ' + config.NEXT_PUBLIC_ENABLE_MOCK_AUTH
        )
    }

    // Warning: Development API in production
    if (config.NODE_ENV === 'production' && config.NEXT_PUBLIC_API_BASE.includes('localhost')) {
        warnings.push(
            '⚠️  WARNING: API base URL points to localhost in production!\n' +
            '   Current value: ' + config.NEXT_PUBLIC_API_BASE
        )
    }

    // Warning: HTTP in production
    if (config.NODE_ENV === 'production' && config.NEXT_PUBLIC_API_BASE.startsWith('http://')) {
        warnings.push(
            '⚠️  WARNING: API uses HTTP instead of HTTPS in production!\n' +
            '   Current value: ' + config.NEXT_PUBLIC_API_BASE
        )
    }

    // Print warnings
    if (warnings.length > 0) {
        console.warn('\n' + '='.repeat(80))
        console.warn('SECURITY WARNINGS:')
        console.warn('='.repeat(80))
        warnings.forEach((warning) => console.warn(warning))
        console.warn('='.repeat(80) + '\n')
    }

    // Throw on errors
    if (errors.length > 0) {
        console.error('\n' + '='.repeat(80))
        console.error('SECURITY ERRORS:')
        console.error('='.repeat(80))
        errors.forEach((error) => console.error(error))
        console.error('='.repeat(80) + '\n')

        throw new Error(
            'Application startup blocked due to security configuration errors. ' +
            'See error messages above.'
        )
    }
}

/**
 * Application Constants
 * Centralized configuration to avoid hardcoding
 */
export const APP_CONFIG = {
    // API Configuration
    API_BASE_URL: config.NEXT_PUBLIC_API_BASE,
    BASE_PATH: config.NEXT_PUBLIC_BASE_PATH,

    // Feature Flags
    ENABLE_MOCK_AUTH: config.NEXT_PUBLIC_ENABLE_MOCK_AUTH,

    // Environment
    IS_PRODUCTION: config.NODE_ENV === 'production',
    IS_DEVELOPMENT: config.NODE_ENV === 'development',
    IS_TEST: config.NODE_ENV === 'test',

    // Session Configuration
    SESSION_TIMEOUT: 3600, // 1 hour in seconds

    // Default Values
    DEFAULT_TIMEZONE: 'America/Sao_Paulo',

    // Map Configuration
    DEFAULT_MAP_CENTER: [-23.5505, -46.6333] as [number, number], // São Paulo
    DEFAULT_MAP_ZOOM: 10,

    // Color Scheme
    COLORS: {
        AOI_TYPES: {
            PASTURE: '#10b981',  // Green
            CROP: '#f59e0b',      // Orange
            FOREST: '#059669',    // Dark green
            WATER: '#3b82f6',     // Blue
        },
        SIGNAL_TYPES: {
            CHANGE_DETECTED: 'bg-blue-100 text-blue-800',
            ANOMALY: 'bg-yellow-100 text-yellow-800',
            ALERT: 'bg-red-100 text-red-800',
        },
        SIGNAL_STATUS: {
            ACTIVE: 'bg-yellow-100 text-yellow-800',
            ACKNOWLEDGED: 'bg-blue-100 text-blue-800',
            RESOLVED: 'bg-green-100 text-green-800',
        },
    },

    // NDVI Configuration
    NDVI_RANGE: [0, 1] as [number, number],

    // UI Text (será substituído por i18n no futuro)
    TEXT: {
        LOADING: 'Carregando...',
        ERROR_GENERIC: 'Erro ao processar solicitação',
        ERROR_NETWORK: 'Erro de conexão. Verifique sua internet.',
        ERROR_UNAUTHORIZED: 'Sessão expirada. Faça login novamente.',
    },
} as const

// Type-safe access to config
export type AppConfig = typeof APP_CONFIG
